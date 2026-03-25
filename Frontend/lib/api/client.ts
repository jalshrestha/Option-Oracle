// Option Oracle API Client

import type {
  AnalysisResponse,
  ChatResponse,
  EducationContent,
  ExplainResponse,
  GlossaryTerm,
  HotStock,
  LearningPath,
  LLMProvider,
  OptionsChain,
  PortfolioSummaryResponse,
  PositionSchema,
  Quiz,
  RiskProfile,
  SystemHealth,
  SystemMetrics,
  TechnicalResponse,
  TradeRequest,
  Greeks,
  RiskMetrics,
  TokenResponse,
  UserProfile,
  RecentSignalItem,
} from './types'

const BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8080'

const ACCESS_TOKEN_KEY = 'oracle_access_token'
const REFRESH_TOKEN_KEY = 'oracle_refresh_token'

export function getAccessToken(): string | null {
  if (typeof window === 'undefined') return null
  return localStorage.getItem(ACCESS_TOKEN_KEY)
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
    throw new Error((err as any)?.detail || `Register failed: ${response.status}`)
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
    throw new Error((err as any)?.detail || `Login failed: ${response.status}`)
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
  selectedStock?: string
): Promise<ChatResponse> {
  return apiRequest('/api/v1/chat/message', {
    method: 'POST',
    body: JSON.stringify({ message, selectedStock }),
  })
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
  action: 'BUY' | 'SELL'
}): Promise<{ success: boolean; position_id: string }> {
  return apiRequest('/api/v1/options/execute', {
    method: 'POST',
    body: JSON.stringify(payload),
  })
}

// Trading
export async function executeTrade(
  tradeRequest: TradeRequest
): Promise<{ success: boolean; position_id: string }> {
  return apiRequest('/api/v1/trading/execute', {
    method: 'POST',
    body: JSON.stringify(tradeRequest),
  })
}

export async function closePosition(
  positionId: string
): Promise<{ success: boolean; realized_pnl: number }> {
  return apiRequest(`/api/v1/trading/positions/${positionId}/close`, {
    method: 'POST',
  })
}

export async function getPositions(): Promise<PositionSchema[]> {
  return apiRequest('/api/v1/trading/positions')
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

// Education
export async function getEducationContent(filters?: {
  difficulty?: string
  type?: string
  topic?: string
}): Promise<EducationContent[]> {
  const params = new URLSearchParams()
  if (filters?.difficulty) params.append('difficulty', filters.difficulty)
  if (filters?.type) params.append('type', filters.type)
  if (filters?.topic) params.append('topic', filters.topic)
  const query = params.toString() ? `?${params.toString()}` : ''
  return apiRequest(`/api/v1/education/content${query}`)
}

export async function generateQuiz(request: {
  topic: string
  difficulty: string
  count?: number
}): Promise<Quiz> {
  return apiRequest('/api/v1/education/quiz', {
    method: 'POST',
    body: JSON.stringify({
      topic: request.topic,
      difficulty: request.difficulty,
      question_count: request.count ?? 5,
    }),
  })
}

export async function explainConcept(concept: string): Promise<ExplainResponse> {
  const res = await apiRequest<any>(
    `/api/v1/education/explain?concept=${encodeURIComponent(concept)}`
  )
  const inner = res.explanation || res
  return {
    simple_explanation: inner.simple_explanation || '',
    technical_explanation: inner.technical_explanation || '',
    example: inner.practical_example || inner.example || '',
    related_concepts: inner.related_concepts || [],
  }
}

export async function getGlossary(
  search?: string,
  category?: string
): Promise<GlossaryTerm[]> {
  const params = new URLSearchParams()
  if (search) params.append('search', search)
  if (category) params.append('category', category)
  const query = params.toString() ? `?${params.toString()}` : ''
  const res = await apiRequest<any>(`/api/v1/education/glossary${query}`)
  const glossaryObj = res.glossary || res
  return Object.values(glossaryObj) as GlossaryTerm[]
}

export async function getLearningPath(level?: string): Promise<LearningPath> {
  const query = level ? `?current_level=${level}` : ''
  return apiRequest(`/api/v1/education/learning-path${query}`)
}

// Legacy compat — kept so old imports don't break while migrating
export const getSessionToken = getAccessToken
export const setSessionToken = (token: string) =>
  typeof window !== 'undefined' && localStorage.setItem(ACCESS_TOKEN_KEY, token)
export const clearSessionToken = clearTokens
