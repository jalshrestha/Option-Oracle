'use client'

import { useState, useEffect, use } from 'react'
import { motion } from 'framer-motion'
import { RefreshCw, Clock, ArrowUpRight, ArrowDownRight } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { OracleLoading } from '@/components/analysis/oracle-loading'
import { OverviewTab } from '@/components/analysis/tabs/overview-tab'
import { AgentsTab } from '@/components/analysis/tabs/agents-tab'
import { OptionsTab } from '@/components/analysis/tabs/options-tab'
import { TechnicalTab } from '@/components/analysis/tabs/technical-tab'
import { EducationTab } from '@/components/analysis/tabs/education-tab'
import { analyzeStock, getTechnical } from '@/lib/api/client'
import { formatPrice, formatPercent, getPriceColorClass, formatTimeAgo } from '@/lib/utils/format'
import { cn } from '@/lib/utils'
import type { AnalysisResponse, TechnicalResponse } from '@/lib/api/types'

// Mock analysis data for demo
const mockAnalysis: AnalysisResponse = {
  symbol: 'NVDA',
  signal: {
    direction: 'STRONG_BUY',
    strength: 'strong',
    confidence: 0.87,
    decision_score: 0.75,
    strategy_type: 'momentum',
    market_scenario: 'BREAKOUT',
    reasoning:
      'NVDA shows strong bullish momentum with breakout confirmation above key resistance. Technical indicators align positively, options flow shows institutional accumulation, and sentiment remains extremely bullish driven by AI demand narrative.',
  },
  agent_results: {
    technical: {
      name: 'Technical Agent',
      signal: 'STRONG_BUY',
      confidence: 0.89,
      scenario: 'BREAKOUT',
      weighted_score: 0.53,
      insights: [
        'Price broke above 52-week high with strong volume',
        'RSI at 68 - bullish but approaching overbought',
        'MACD showing strong bullish momentum',
      ],
    },
    sentiment: {
      name: 'Sentiment Agent',
      signal: 'BUY',
      confidence: 0.82,
      scenario: 'TRENDING',
      weighted_score: 0.08,
      insights: [
        'Social sentiment extremely positive',
        'News coverage remains bullish on AI theme',
        'Analyst upgrades outpacing downgrades 5:1',
      ],
    },
    flow: {
      name: 'Flow Agent',
      signal: 'STRONG_BUY',
      confidence: 0.85,
      scenario: 'BREAKOUT',
      weighted_score: 0.09,
      insights: [
        'Unusual call activity at higher strikes',
        'Put/Call ratio at 0.45 - bullish',
        'Dark pool prints showing accumulation',
      ],
    },
    historical: {
      name: 'Historical Agent',
      signal: 'BUY',
      confidence: 0.72,
      scenario: 'TRENDING',
      weighted_score: 0.14,
      insights: [
        'Similar breakout patterns led to +15% moves historically',
        'Seasonality favors tech in this period',
        'Earnings momentum strong over last 4 quarters',
      ],
    },
    risk: {
      name: 'Risk Agent',
      signal: 'BUY',
      confidence: 0.68,
      scenario: 'VOLATILE',
      weighted_score: 0.0,
      insights: [
        'Volatility elevated but manageable',
        'Position size recommended: moderate',
        'Stop loss suggested at $820',
      ],
    },
    education: {
      name: 'Education Agent',
      signal: 'HOLD',
      confidence: 0.9,
      scenario: 'NEUTRAL',
      weighted_score: 0.0,
      insights: [
        'Breakout trading requires patience for confirmation',
        'Consider scaling into position',
        'Monitor volume for continuation signal',
      ],
    },
  },
  strike_recommendations: [
    {
      option_type: 'call',
      strike: 900,
      expiry: '2024-02-16',
      delta: 0.45,
      premium: 28.5,
      risk_reward: 2.8,
      rationale: 'Near ATM call for directional play with manageable premium',
    },
    {
      option_type: 'call',
      strike: 950,
      expiry: '2024-02-16',
      delta: 0.28,
      premium: 14.2,
      risk_reward: 4.2,
      rationale: 'OTM call for higher leverage play if breakout continues',
    },
    {
      option_type: 'put',
      strike: 820,
      expiry: '2024-02-16',
      delta: -0.22,
      premium: 18.0,
      risk_reward: 1.5,
      rationale: 'Protective put to hedge long position',
    },
  ],
  educational_content:
    'A breakout occurs when price moves above a key resistance level with increased volume. This often signals the start of a new trend. Key factors to watch: volume confirmation, retest of breakout level, and follow-through in subsequent sessions.',
  confidence: 0.87,
  market_scenario: 'BREAKOUT',
  agent_weights: {
    technical: 0.6,
    sentiment: 0.1,
    flow: 0.1,
    historical: 0.2,
  },
  analysis_time_seconds: 34.2,
  timestamp: new Date().toISOString(),
}

const mockTechnical: TechnicalResponse = {
  symbol: 'NVDA',
  price: 878.35,
  change: 23.45,
  change_percent: 2.74,
  bid: 878.20,
  ask: 878.50,
  volume: 45200000,
  avg_volume: 38500000,
  indicators: {
    sma_5: 865.2,
    sma_20: 842.8,
    sma_50: 795.4,
    sma_200: 620.3,
    rsi: 68.5,
    stochastic_k: 82.3,
    stochastic_d: 78.6,
    williams_r: -17.7,
    cci: 125.4,
    macd: 12.45,
    macd_signal: 9.82,
    macd_histogram: 2.63,
    adx: 42.8,
    supertrend: 'bullish',
    bb_upper: 905.2,
    bb_middle: 862.5,
    bb_lower: 819.8,
    bb_position: 0.69,
    atr: 28.5,
    volatility: 32.5,
    volatility_percentile: 65,
    volume: 45200000,
    avg_volume: 38500000,
    obv: 2850000000,
    mfi: 62.4,
    cmf: 0.18,
    vwap: 872.3,
  },
  candles: [],
  last_updated: new Date().toISOString(),
}

export default function AnalyzePage(props: { params: Promise<{ symbol: string }> }) {
  const params = use(props.params)
  const symbol = params.symbol.toUpperCase()

  const [analysis, setAnalysis] = useState<AnalysisResponse | null>(null)
  const [technical, setTechnical] = useState<TechnicalResponse | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [isReanalyzing, setIsReanalyzing] = useState(false)

  useEffect(() => {
    const loadData = async () => {
      setIsLoading(true)
      try {
        const [analysisData, technicalData] = await Promise.all([
          analyzeStock(symbol),
          getTechnical(symbol),
        ])
        setAnalysis(analysisData)
        setTechnical(technicalData)
      } catch (error) {
        // Use mock data for demo
        setAnalysis({ ...mockAnalysis, symbol })
        setTechnical({ ...mockTechnical, symbol })
      } finally {
        setIsLoading(false)
      }
    }

    loadData()
  }, [symbol])

  const handleReanalyze = async () => {
    setIsReanalyzing(true)
    try {
      const newAnalysis = await analyzeStock(symbol)
      setAnalysis(newAnalysis)
    } catch (error) {
      // Keep existing analysis
    } finally {
      setIsReanalyzing(false)
    }
  }

  if (isLoading) {
    return <OracleLoading symbol={symbol} />
  }

  if (!analysis || !technical) {
    return (
      <div className="flex h-96 items-center justify-center">
        <p className="text-muted-foreground">Failed to load analysis data</p>
      </div>
    )
  }

  const changeColor = getPriceColorClass(technical.change_percent)
  const ChangeIcon = technical.change_percent >= 0 ? ArrowUpRight : ArrowDownRight

  return (
    <motion.div
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      className="space-y-6"
    >
      {/* Symbol Header Bar */}
      <div className="flex flex-col gap-4 rounded-xl border border-border bg-card p-6 lg:flex-row lg:items-center lg:justify-between">
        <div className="flex items-center gap-6">
          <div>
            <h1 className="font-mono text-4xl font-bold tracking-tight">{symbol}</h1>
            <p className="text-muted-foreground">Analysis Report</p>
          </div>
          <div className="flex items-baseline gap-3">
            <span className={cn('font-mono text-3xl font-bold tabular-nums', changeColor)}>
              {formatPrice(technical.price)}
            </span>
            <div className={cn('flex items-center gap-1', changeColor)}>
              <ChangeIcon className="h-5 w-5" />
              <span className="font-mono text-lg font-medium tabular-nums">
                {formatPercent(technical.change_percent)}
              </span>
            </div>
          </div>
        </div>

        <div className="flex flex-wrap items-center gap-4">
          <div className="flex items-center gap-2 text-sm text-muted-foreground">
            <span>Bid/Ask:</span>
            <span className="font-mono tabular-nums">
              {formatPrice(technical.bid)} / {formatPrice(technical.ask)}
            </span>
          </div>
          <div className="flex items-center gap-2 text-sm text-muted-foreground">
            <span>Vol:</span>
            <span className="font-mono tabular-nums">
              {(technical.volume / 1e6).toFixed(1)}M
            </span>
            <Badge variant={technical.volume > technical.avg_volume ? 'default' : 'secondary'}>
              {((technical.volume / technical.avg_volume) * 100).toFixed(0)}% avg
            </Badge>
          </div>
          <div className="flex items-center gap-2 text-xs text-muted-foreground">
            <Clock className="h-3 w-3" />
            <span>Updated {formatTimeAgo(analysis.timestamp)}</span>
          </div>
          <Button
            variant="outline"
            size="sm"
            onClick={handleReanalyze}
            disabled={isReanalyzing}
            className="gap-2"
          >
            <RefreshCw className={cn('h-4 w-4', isReanalyzing && 'animate-spin')} />
            Re-analyze
          </Button>
        </div>
      </div>

      {/* Tabs */}
      <Tabs defaultValue="overview" className="space-y-6">
        <TabsList className="grid w-full grid-cols-5 lg:w-auto lg:grid-cols-none">
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="agents">Agents</TabsTrigger>
          <TabsTrigger value="options">Options</TabsTrigger>
          <TabsTrigger value="technical">Technical</TabsTrigger>
          <TabsTrigger value="education">Education</TabsTrigger>
        </TabsList>

        <TabsContent value="overview">
          <OverviewTab analysis={analysis} />
        </TabsContent>

        <TabsContent value="agents">
          <AgentsTab analysis={analysis} />
        </TabsContent>

        <TabsContent value="options">
          <OptionsTab analysis={analysis} symbol={symbol} />
        </TabsContent>

        <TabsContent value="technical">
          <TechnicalTab technical={technical} />
        </TabsContent>

        <TabsContent value="education">
          <EducationTab analysis={analysis} />
        </TabsContent>
      </Tabs>

      {isReanalyzing && <OracleLoading symbol={symbol} />}
    </motion.div>
  )
}
