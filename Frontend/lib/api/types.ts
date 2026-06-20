// Option Oracle API Types

export type SignalDirection = 'BUY' | 'SELL' | 'HOLD' | 'STRONG_BUY' | 'STRONG_SELL'
export type SignalStrength = 'strong' | 'moderate' | 'weak'
export type MarketScenario = 'BREAKOUT' | 'TRENDING' | 'RANGE_BOUND' | 'VOLATILE' | 'NEUTRAL'
export type OptionType = 'call' | 'put'
export type RiskProfile = 'conservative' | 'moderate' | 'aggressive'

export interface SignalSchema {
  direction: SignalDirection
  strength: SignalStrength
  confidence: number
  decision_score: number
  strategy_type: string
  market_scenario: MarketScenario
  reasoning: string
}

export interface StrikeRecommendation {
  option_type: OptionType
  strike: number
  expiry: string
  delta?: number
  premium?: number
  risk_reward?: number
  rationale: string
}

export interface AgentResult {
  name: string
  signal: SignalDirection
  confidence: number
  scenario: MarketScenario
  weighted_score: number
  insights: string[]
  full_analysis?: string
}

export interface AgentWeights {
  technical: number
  sentiment: number
  flow: number
  historical: number
}

export interface AnalysisResponse {
  symbol: string
  signal: SignalSchema
  agent_results: Record<string, AgentResult>
  strike_recommendations: StrikeRecommendation[]
  educational_content?: string
  confidence: number
  market_scenario: MarketScenario
  agent_weights: AgentWeights
  analysis_time_seconds: number
  timestamp: string
}

export interface HotStock {
  symbol: string
  name: string
  price: number
  change: number
  changePercent: number
  volume: number
  sparklineData: number[]
  aiScore: number
  signals: string[]
  trending: boolean
}

export interface Greeks {
  delta: number
  gamma: number
  theta: number
  vega: number
  rho: number
}

export interface RiskMetrics {
  var_95: number
  max_loss: number
  beta: number
  sharpe_ratio: number
  max_drawdown: number
}

export interface PositionSchema {
  id: string
  symbol: string
  option_type?: OptionType
  strike_price?: number
  expiry_date?: string
  quantity: number
  entry_price: number
  current_price: number
  unrealized_pnl: number
  status: string
  greeks?: Greeks
}

export interface PortfolioAllocation {
  symbol: string
  percentage: number
  value: number
}

export interface PortfolioSummaryResponse {
  total_value: number
  cash_balance: number
  unrealized_pnl: number
  realized_pnl: number
  open_positions: number
  total_return_pct: number
  greeks: Greeks
  risk_metrics: RiskMetrics
  allocation: PortfolioAllocation[]
}

export interface ChatResponse {
  response: string
  intent?: string
  symbol?: string
  confidence?: number
  data?: {
    analysis_result?: AnalysisResponse
  }
  actions?: Record<string, any>
  suggestions: string[]
  agents_triggered: string[]
  thread_id?: string
  timestamp: string | number
}

export interface ChatProgressEvent {
  event: 'progress' | 'final' | 'error'
  stage?: string
  label?: string
  detail?: string
  tool?: string
  tools?: string[]
  agent?: string
  symbol?: string
  success?: boolean
  data?: ChatResponse
}

export interface ChatHistoryMessage {
  id: string
  role: 'user' | 'assistant'
  content: string
  metadata?: Omit<ChatResponse, 'response'>
  created_at: string
}

export interface ChatThreadSummary {
  id: string
  title: string
  last_message_preview?: string | null
  created_at: string
  updated_at: string
}

export interface ChatThreadDetail extends ChatThreadSummary {
  messages: ChatHistoryMessage[]
}

export interface TechnicalIndicators {
  sma_5: number
  sma_20: number
  sma_50: number
  sma_200: number
  rsi: number
  stochastic_k: number
  stochastic_d: number
  williams_r: number
  cci: number
  macd: number
  macd_signal: number
  macd_histogram: number
  adx: number
  supertrend: 'bullish' | 'bearish'
  bb_upper: number
  bb_middle: number
  bb_lower: number
  bb_position: number
  atr: number
  volatility: number
  volatility_percentile: number
  volume: number
  avg_volume: number
  obv: number
  mfi: number
  cmf: number
  vwap: number
}

export interface TechnicalResponse {
  symbol: string
  price: number
  change: number
  change_percent: number
  bid: number
  ask: number
  volume: number
  avg_volume: number
  indicators: TechnicalIndicators
  candles: CandleData[]
  last_updated: string
}

export interface CandleData {
  date: string
  open: number
  high: number
  low: number
  close: number
  volume: number
}

export interface OptionsChainRow {
  strike: number
  type: OptionType
  last: number
  bid: number
  ask: number
  volume: number
  open_interest: number
  iv: number
  delta: number
  itm: boolean
}

export interface OptionsChain {
  symbol: string
  expiry: string
  calls: OptionsChainRow[]
  puts: OptionsChainRow[]
  put_call_ratio: number
  total_call_volume: number
  total_put_volume: number
}

export type ServiceStatus =
  | 'healthy'
  | 'degraded'
  | 'unhealthy'
  | 'disabled'
  | 'configured'
  | 'unconfigured'
  | string

export interface ExternalServiceHealth {
  status: ServiceStatus
  enabled?: boolean
  last_check?: number
  message?: string
}

export interface SystemHealth {
  overall_status: 'healthy' | 'degraded' | 'unhealthy' | string
  components: {
    api?: {
      status: ServiceStatus
      response_time_ms?: number
      active_connections?: number
    }
    database?: {
      status: ServiceStatus
      response_time_ms?: number
      connection_pool?: string
    }
    redis?: {
      status: ServiceStatus
      enabled?: boolean
    }
    ingestion?: {
      status: ServiceStatus
    }
    external_services?: {
      openai?: ExternalServiceHealth
      gemini?: ExternalServiceHealth
      alpaca?: ExternalServiceHealth
      jigsawstack?: ExternalServiceHealth
    }
  }
  timestamp: number
  version: string
}

export interface SystemMetrics {
  cpu_usage: number
  memory_usage: number
  disk_usage: number
  analyses_today: number
  active_positions: number
  session_count: number
  error_rate: number
  common_errors: { error: string; count: number }[]
}

export interface LLMProvider {
  provider: 'OpenAI' | 'Gemini'
  large_model: string
  small_model: string
}

export interface TradeRequest {
  symbol: string
  action: 'buy' | 'sell'
  quantity: number
  order_type: 'market' | 'limit'
  limit_price?: number
  option_details?: {
    option_type: OptionType
    strike: number
    expiry: string
  }
}

export interface TradeResponse {
  trade_id: string
  status: 'executed' | 'failed' | 'simulated'
  position_id?: string
  execution_price?: number
  message: string
}

export interface AnalyzeBuyRequest {
  symbol: string
  user_query?: string
  risk_profile?: Record<string, unknown>
}

export interface RecommendationLeg {
  asset_type: 'stock' | 'option'
  action: 'buy' | 'sell'
  quantity: number
  option_type?: OptionType
  strike?: number
  expiry?: string
  estimated_price: number
}

export interface TradeRecommendationResponse {
  id: string
  symbol: string
  strategy: string
  action: 'buy' | 'sell'
  status: 'draft' | 'confirmed' | 'executed' | 'expired' | 'rejected'
  mode: 'paper' | 'live'
  legs: RecommendationLeg[]
  rationale: string
  source: string
  source_analysis_id?: string
  estimated_cost: number
  max_loss: number
  confidence: number
  risk_score: number
  expires_at: string
  executed_position_id?: string
  created_at?: string
}

export interface ExecuteRecommendationRequest {
  recommendation_id: string
  mode: 'paper' | 'live'
  confirmed: boolean
  quantity?: number
}

export interface SessionResponse {
  session_token: string
  risk_profile: RiskProfile
  expires_in: number
  created_at: number
}

export interface TokenResponse {
  access_token: string
  refresh_token: string
  token_type: string
  expires_in: number
}

export interface UserProfile {
  id: string
  email: string
  username: string
  risk_profile: RiskProfile
  is_active: boolean
  is_verified: boolean
  created_at: string
}

export interface RecentSignalItem {
  id: string
  symbol: string
  direction: SignalDirection
  strength: SignalStrength
  confidence_score: number
  market_scenario: MarketScenario
  created_at: string
}

// AnalysisResult alias for component compatibility
export type AnalysisResult = AnalysisResponse
