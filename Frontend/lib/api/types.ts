// Option Oracle API Types

export type SignalDirection = 'BUY' | 'SELL' | 'HOLD' | 'STRONG_BUY' | 'STRONG_SELL'
export type SignalStrength = 'strong' | 'moderate' | 'weak'
export type MarketScenario = 'BREAKOUT' | 'TRENDING' | 'RANGE_BOUND' | 'VOLATILE' | 'NEUTRAL'
export type OptionType = 'call' | 'put'
export type RiskProfile = 'conservative' | 'moderate' | 'aggressive'
export type ContentDifficulty = 'BEGINNER' | 'INTERMEDIATE' | 'ADVANCED'
export type ContentType = 'lesson' | 'quiz' | 'interactive'

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
  timestamp: string | number
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

export interface EducationContent {
  id?: string
  content_id?: string
  title: string
  difficulty: ContentDifficulty
  type?: ContentType
  content_type?: string
  duration?: string
  estimated_duration_minutes?: number
  topics?: string[]
  topic?: string
  description?: string
}

export interface LearningPath {
  current_level: string
  learning_path: { module: string; duration_minutes: number; topics: string[] }[]
  total_duration_minutes: number
  estimated_completion_days: number
  next_milestone: string
  interests: string[]
}

export interface GlossaryTerm {
  term: string
  category: string
  definition: string
  example?: string
  related_terms: string[]
}

export interface QuizQuestion {
  id: string
  question: string
  options: string[]
  correct_index: number
  explanation: string
}

export interface Quiz {
  topic: string
  questions: QuizQuestion[]
}

export interface ExplainResponse {
  simple_explanation: string
  technical_explanation: string
  example: string
  related_concepts: string[]
}

export interface SystemHealth {
  status: 'healthy' | 'degraded' | 'unhealthy'
  uptime: number
  response_time: number
  active_connections: number
  database: {
    status: 'healthy' | 'unhealthy'
    connection_pool: number
    response_time: number
  }
  external_services: {
    openai: 'healthy' | 'degraded' | 'unhealthy'
    alpaca: 'healthy' | 'degraded' | 'unhealthy'
    jigsawstack: 'healthy' | 'degraded' | 'unhealthy'
  }
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
  action: 'BUY' | 'SELL'
  option_type?: OptionType
  strike?: number
  expiry?: string
  quantity: number
  order_type: 'MARKET' | 'LIMIT'
  limit_price?: number
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
