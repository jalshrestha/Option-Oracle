// Option Oracle API Client

import type {
  AnalysisResponse,
  ChatResponse,
  ChatProgressEvent,
  ChatThreadDetail,
  ChatThreadSummary,
  HotStock,
  LLMProvider,
  OptionsChain,
  PortfolioSummaryResponse,
  PositionSchema,
  RiskProfile,
  SessionResponse,
  SystemHealth,
  SystemMetrics,
  TechnicalResponse,
  TradeRequest,
  TradeResponse,
  AnalyzeBuyRequest,
  TradeRecommendationResponse,
  ExecuteRecommendationRequest,
  Greeks,
  RiskMetrics,
  TokenResponse,
  UserProfile,
  RecentSignalItem,
} from './types'

const BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8080'

const ACCESS_TOKEN_KEY = 'oracle_access_token'
const REFRESH_TOKEN_KEY = 'oracle_refresh_token'
const SESSION_TOKEN_KEY = 'oracle_session_token'

export function getAccessToken(): string | null {
  if (typeof window === 'undefined') return null
  const token = localStorage.getItem(ACCESS_TOKEN_KEY)
  return token?.startsWith('guest_') ? null : token
}

export function getRefreshToken(): string | null {
  if (typeof window === 'undefined') return null
  return localStorage.getItem(REFRESH_TOKEN_KEY)
}

export function setTokens(access: string, refresh: string): void {
  if (typeof window === 'undefined') return
  localStorage.setItem(ACCESS_TOKEN_KEY, access)
  localStorage.setItem(REFRESH_TOKEN_KEY, refresh)
}

export function clearTokens(): void {
  if (typeof window === 'undefined') return
  localStorage.removeItem(ACCESS_TOKEN_KEY)
  localStorage.removeItem(REFRESH_TOKEN_KEY)
}

export function getSessionToken(): string | null {
  if (typeof window === 'undefined') return null
  return localStorage.getItem(SESSION_TOKEN_KEY)
}

export function setSessionToken(token: string): void {
  if (typeof window === 'undefined') return
  localStorage.setItem(SESSION_TOKEN_KEY, token)
}

export function clearSessionToken(): void {
  if (typeof window === 'undefined') return
  localStorage.removeItem(SESSION_TOKEN_KEY)
}

let isRefreshing = false
let refreshListeners: Array<(token: string | null) => void> = []

async function attemptRefresh(): Promise<string | null> {
  const refreshToken = getRefreshToken()
  if (!refreshToken) return null

  const response = await fetch(`${BASE_URL}/api/v1/auth/refresh`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ refresh_token: refreshToken }),
  })

  if (!response.ok) {
    clearTokens()
    return null
  }

  const data: TokenResponse = await response.json()
  setTokens(data.access_token, data.refresh_token || refreshToken)
  return data.access_token
}

async function getValidAccessToken(): Promise<string | null> {
  const token = getAccessToken()
  if (!token) return null
  return token
}

async function apiRequest<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const token = await getValidAccessToken()

  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...(options.headers as Record<string, string>),
  }

  if (token) {
    headers['Authorization'] = `Bearer ${token}`
  }

  const response = await fetch(`${BASE_URL}${endpoint}`, {
    ...options,
    headers,
  })

  if (response.status === 401) {
    // Try refresh
    if (!isRefreshing) {
      isRefreshing = true
      try {
        const newToken = await attemptRefresh()
        isRefreshing = false
        refreshListeners.forEach((cb) => cb(newToken))
        refreshListeners = []

        if (newToken) {
          headers['Authorization'] = `Bearer ${newToken}`
          const retryResponse = await fetch(`${BASE_URL}${endpoint}`, {
            ...options,
            headers,
          })
          if (!retryResponse.ok) {
            throw new Error(`API Error: ${retryResponse.status}`)
          }
          return retryResponse.json()
        }
      } catch (err) {
        isRefreshing = false
        refreshListeners.forEach((cb) => cb(null))
        refreshListeners = []
        clearTokens()
      }
    } else {
      // Queue behind the ongoing refresh
      await new Promise<void>((resolve) => {
        refreshListeners.push(() => resolve())
      })
      const newToken = getAccessToken()
      if (newToken) {
        headers['Authorization'] = `Bearer ${newToken}`
        const retryResponse = await fetch(`${BASE_URL}${endpoint}`, {
          ...options,
          headers,
        })
        if (!retryResponse.ok) {
          throw new Error(`API Error: ${retryResponse.status}`)
        }
        return retryResponse.json()
      }
    }

    throw new Error('Unauthorized')
  }

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}))
    throw new Error(
      (errorData as any)?.detail || `API Error: ${response.status}`
    )
  }

  return response.json()
}

// Auth
export async function register(
  email: string,
  username: string,
  password: string
): Promise<TokenResponse> {
  const response = await fetch(`${BASE_URL}/api/v1/auth/register`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, username, password }),
  })
  if (!response.ok) {
    const err = await response.json().catch(() => ({}))
    const detail = (err as any)?.detail
    const oracleError = (err as any)?.error  // custom error handler format
    const msg = oracleError
      ? oracleError
      : Array.isArray(detail)
        ? detail.map((d: any) => d.msg || d.message || String(d)).join('; ')
        : typeof detail === 'string' ? detail : `Register failed: ${response.status}`
    throw new Error(`${response.status}:${msg}`)
  }
  const data: TokenResponse = await response.json()
  setTokens(data.access_token, data.refresh_token)
  return data
}

export async function login(
  email: string,
  password: string
): Promise<TokenResponse> {
  const response = await fetch(`${BASE_URL}/api/v1/auth/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, password }),
  })
  if (!response.ok) {
    const err = await response.json().catch(() => ({}))
    const detail = (err as any)?.detail
    const oracleError = (err as any)?.error  // custom error handler format
    const msg = oracleError
      ? oracleError
      : Array.isArray(detail)
        ? detail.map((d: any) => d.msg || d.message || String(d)).join('; ')
        : typeof detail === 'string' ? detail : `Login failed: ${response.status}`
    throw new Error(`${response.status}:${msg}`)
  }
  const data: TokenResponse = await response.json()
  setTokens(data.access_token, data.refresh_token)
  return data
}

export async function logout(): Promise<void> {
  try {
    await apiRequest('/api/v1/auth/logout', { method: 'POST' })
  } finally {
    clearTokens()
  }
}

export async function getMe(): Promise<UserProfile> {
  return apiRequest('/api/v1/auth/me')
}

// Health & System
export async function getHealth(): Promise<{ status: string }> {
  const response = await fetch(`${BASE_URL}/health`)
  return response.json()
}

export async function getSystemHealth(): Promise<SystemHealth> {
  return apiRequest('/api/v1/system/health')
}

export async function getSystemMetrics(
  type?: 'performance' | 'business' | 'errors'
): Promise<SystemMetrics> {
  const query = type ? `?type=${type}` : ''
  return apiRequest(`/api/v1/system/metrics${query}`)
}

export async function getLLMProvider(): Promise<LLMProvider> {
  return apiRequest('/api/v1/system/llm-provider')
}

export async function getSystemConfig(): Promise<Record<string, string>> {
  return apiRequest('/api/v1/system/config')
}

// Analysis
export async function analyzeStock(symbol: string): Promise<AnalysisResponse> {
  return apiRequest(`/api/v1/analysis/analyze/${symbol}`, { method: 'POST' })
}

export async function getAnalysisHistory(
  symbol: string,
  limit = 10
): Promise<AnalysisResponse[]> {
  return apiRequest(`/api/v1/analysis/history/${symbol}?limit=${limit}`)
}

export async function getRecentSignals(
  limit = 20
): Promise<RecentSignalItem[]> {
  return apiRequest(`/api/v1/analysis/signals/recent?limit=${limit}`)
}

// Stocks
export async function getHotStocks(): Promise<HotStock[]> {
  const res = await apiRequest<{ stocks: any[] }>('/api/v1/stocks/hot-stocks')
  return (res.stocks || []).map((s: any) => ({
    ...s,
    price: Number(s.price) || 0,
    change: Number(s.change) || 0,
    changePercent: Number(s.changePercent) || 0,
    volume: Number(s.volume) || 0,
    aiScore: Number(s.aiScore) || 0,
    signals: Array.isArray(s.signals) ? s.signals : [],
    trending: Boolean(s.trending),
    sparklineData: Array.isArray(s.sparklineData)
      ? s.sparklineData.map((p: any) => (typeof p === 'object' ? p.value : p))
      : [],
  }))
}

// Technical Analysis
export async function getTechnical(symbol: string): Promise<TechnicalResponse> {
  return apiRequest(`/api/v1/technical/${symbol}`)
}

export async function getSignals(
  symbol: string
): Promise<{ symbol: string; signals: string[] }> {
  return apiRequest(`/api/v1/signals/${symbol}`)
}

// Chat
export async function sendChat(
  message: string,
  selectedStock?: string,
  threadId?: string
): Promise<ChatResponse> {
  const sessionId = getSessionToken()
  return apiRequest('/api/v1/chat/message', {
    method: 'POST',
    body: JSON.stringify({ message, selectedStock, session_id: sessionId, thread_id: threadId }),
  })
}

export async function streamChat(
  message: string,
  onEvent: (event: ChatProgressEvent) => void,
  selectedStock?: string,
  threadId?: string
): Promise<ChatResponse> {
  const sessionId = getSessionToken()
  const response = await fetch(`${BASE_URL}/api/v1/chat/stream`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      ...(getAccessToken() ? { Authorization: `Bearer ${getAccessToken()}` } : {}),
    },
    body: JSON.stringify({ message, selectedStock, session_id: sessionId, thread_id: threadId }),
  })

  if (!response.ok || !response.body) {
    throw new Error(`Chat stream failed with ${response.status}`)
  }

  const reader = response.body.getReader()
  const decoder = new TextDecoder()
  let buffer = ''
  let finalResponse: ChatResponse | null = null

  while (true) {
    const { done, value } = await reader.read()
    if (done) break

    buffer += decoder.decode(value, { stream: true })
    const chunks = buffer.split('\n\n')
    buffer = chunks.pop() || ''

    for (const chunk of chunks) {
      const line = chunk.split('\n').find((entry) => entry.startsWith('data: '))
      if (!line) continue
      const event = JSON.parse(line.slice(6)) as ChatProgressEvent
      onEvent(event)
      if ((event.event === 'final' || event.event === 'error') && event.data) {
        finalResponse = event.data
      }
    }
  }

  if (!finalResponse) {
    throw new Error('Chat stream ended without a final response')
  }

  return finalResponse
}

export async function listChatThreads(): Promise<ChatThreadSummary[]> {
  const sessionId = getSessionToken()
  if (!sessionId) return []
  return apiRequest(`/api/v1/chat/threads?session_id=${encodeURIComponent(sessionId)}`)
}

export async function getChatThread(threadId: string): Promise<ChatThreadDetail> {
  const sessionId = getSessionToken()
  if (!sessionId) {
    throw new Error('No chat session available')
  }
  return apiRequest(`/api/v1/chat/threads/${threadId}?session_id=${encodeURIComponent(sessionId)}`)
}

export async function sendTradeChat(
  message: string,
  symbol: string
): Promise<ChatResponse> {
  return apiRequest('/api/v1/chat/trade', {
    method: 'POST',
    body: JSON.stringify({ message, symbol }),
  })
}

// Options
export async function getOptionsChain(
  symbol: string,
  expiry?: string
): Promise<OptionsChain> {
  const query = expiry ? `?expiry=${expiry}` : ''
  return apiRequest(`/api/v1/options/${symbol}${query}`)
}

export async function executeOptions(payload: {
  symbol: string
  option_type: 'call' | 'put'
  strike: number
  expiry: string
  quantity: number
  action: 'buy' | 'sell'
}): Promise<{ success: boolean; position_id: string }> {
  return apiRequest('/api/v1/options/execute', {
    method: 'POST',
    body: JSON.stringify(payload),
  })
}

// Trading
export async function executeTrade(
  tradeRequest: TradeRequest
): Promise<TradeResponse> {
  return apiRequest('/api/v1/trading/execute', {
    method: 'POST',
    body: JSON.stringify(tradeRequest),
  })
}

export async function closePosition(
  positionId: string
): Promise<PositionSchema> {
  return apiRequest(`/api/v1/trading/positions/${positionId}/close`, {
    method: 'POST',
  })
}

export async function getPositions(): Promise<PositionSchema[]> {
  return apiRequest('/api/v1/trading/positions')
}

export async function analyzeBuyRecommendation(
  request: AnalyzeBuyRequest
): Promise<TradeRecommendationResponse> {
  return apiRequest('/api/v1/trading/analyze-buy', {
    method: 'POST',
    body: JSON.stringify(request),
  })
}

export async function getBuyRecommendations(
  symbol: string
): Promise<TradeRecommendationResponse[]> {
  return apiRequest(`/api/v1/trading/buy-recommendations/${symbol}`)
}

export async function executeRecommendation(
  request: ExecuteRecommendationRequest
): Promise<TradeResponse> {
  return apiRequest('/api/v1/trading/execute-recommendation', {
    method: 'POST',
    body: JSON.stringify(request),
  })
}

// Portfolio
export async function getPortfolioSummary(): Promise<PortfolioSummaryResponse> {
  return apiRequest('/api/v1/trading/portfolio/summary')
}

export async function getPortfolioPerformance(): Promise<{
  total_return: number
  total_return_percent: number
  win_rate: number
  performance_history: { date: string; value: number }[]
}> {
  return apiRequest('/api/v1/portfolio/performance')
}

export async function getGreeks(): Promise<Greeks> {
  return apiRequest('/api/v1/portfolio/greeks')
}

export async function getRiskMetrics(): Promise<RiskMetrics> {
  return apiRequest('/api/v1/portfolio/risk')
}

// Legacy compat — kept so old imports don't break while migrating
export async function createSession(
  riskProfile: RiskProfile = 'moderate'
): Promise<SessionResponse> {
  const existing = getSessionToken()
  if (existing) {
    return {
      session_token: existing,
      risk_profile: riskProfile,
      expires_in: 3600,
      created_at: Math.floor(Date.now() / 1000),
    }
  }

  try {
    const response = await fetch(`${BASE_URL}/api/v1/session/create?risk_profile=${encodeURIComponent(riskProfile)}`, {
      method: 'POST',
    })
    if (response.ok) {
      const data: SessionResponse = await response.json()
      setSessionToken(data.session_token)
      return data
    }
  } catch {
    // Local fallback keeps chat usable during backend restarts.
  }

  const token = `guest_${crypto.randomUUID()}`
  setSessionToken(token)
  return {
    session_token: token,
    risk_profile: riskProfile,
    expires_in: 86400,
    created_at: Math.floor(Date.now() / 1000),
  }
}
