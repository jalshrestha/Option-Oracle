'use client'

import { motion } from 'framer-motion'
import { Clock, Plus, Play } from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Progress } from '@/components/ui/progress'
import { SignalBadge } from '@/components/analysis/signal-badge'
import { ConfidenceMeter } from '@/components/analysis/confidence-meter'
import { RadarChart } from '@/components/charts/radar-chart'
import { formatPrice, formatPercent } from '@/lib/utils/format'
import { cn } from '@/lib/utils'
import type { AnalysisResponse } from '@/lib/api/types'

interface OverviewTabProps {
  analysis: AnalysisResponse
}

function StrikeCard({
  strike,
  index,
}: {
  strike: AnalysisResponse['strike_recommendations'][0]
  index: number
}) {
  const isCall = strike.option_type === 'call'

  return (
    <motion.div
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: index * 0.1 }}
    >
      <Card className="border-border bg-card">
        <CardContent className="p-4">
          <div className="mb-3 flex items-center justify-between">
            <Badge variant={isCall ? 'default' : 'destructive'}>
              {strike.option_type.toUpperCase()}
            </Badge>
            <span className="font-mono text-2xl font-bold">${strike.strike}</span>
          </div>

          <div className="mb-4 space-y-2 text-sm">
            <div className="flex justify-between">
              <span className="text-muted-foreground">Expiry</span>
              <span className="font-mono">{strike.expiry}</span>
            </div>
            {strike.delta && (
              <div className="flex justify-between">
                <span className="text-muted-foreground">Delta</span>
                <span className="font-mono">{strike.delta.toFixed(2)}</span>
              </div>
            )}
            {strike.premium && (
              <div className="flex justify-between">
                <span className="text-muted-foreground">Premium</span>
                <span className="font-mono">{formatPrice(strike.premium)}</span>
              </div>
            )}
            {strike.risk_reward && (
              <div className="flex justify-between">
                <span className="text-muted-foreground">Risk/Reward</span>
                <span className="font-mono text-green-500">
                  {strike.risk_reward.toFixed(1)}x
                </span>
              </div>
            )}
          </div>

          <p className="mb-4 text-xs text-muted-foreground">{strike.rationale}</p>

          <div className="flex gap-2">
            <Button variant="outline" size="sm" className="flex-1 gap-1">
              <Plus className="h-3 w-3" />
              Watchlist
            </Button>
            <Button size="sm" className="flex-1 gap-1 brand-gradient text-white">
              <Play className="h-3 w-3" />
              Execute
            </Button>
          </div>
        </CardContent>
      </Card>
    </motion.div>
  )
}

export function OverviewTab({ analysis }: OverviewTabProps) {
  const { signal, strike_recommendations, agent_weights } = analysis

  // Convert decision_score from -1..1 to 0..100 for display
  const decisionScorePercent = ((signal.decision_score + 1) / 2) * 100

  return (
    <div className="grid gap-6 lg:grid-cols-5">
      {/* Left Column - Signal & Strikes */}
      <div className="space-y-6 lg:col-span-3">
        {/* Signal Card */}
        <Card
          className={cn(
            'relative overflow-hidden border-2',
            signal.direction === 'STRONG_BUY' && 'border-green-500/50',
            signal.direction === 'STRONG_SELL' && 'border-red-500/50',
            !['STRONG_BUY', 'STRONG_SELL'].includes(signal.direction) && 'border-border'
          )}
        >
          {(signal.direction === 'STRONG_BUY' || signal.direction === 'STRONG_SELL') && (
            <div
              className={cn(
                'absolute inset-0 opacity-10 animate-gradient-border',
                signal.direction === 'STRONG_BUY' &&
                  'bg-gradient-to-r from-green-500 via-green-400 to-green-600',
                signal.direction === 'STRONG_SELL' &&
                  'bg-gradient-to-r from-red-500 via-red-400 to-red-600'
              )}
            />
          )}
          <CardContent className="relative p-6">
            <div className="flex flex-col items-center gap-6 lg:flex-row lg:items-start lg:justify-between">
              <div className="text-center lg:text-left">
                <div className="mb-2">
                  <SignalBadge direction={signal.direction} size="lg" />
                </div>
                <Badge variant="outline" className="mb-4">
                  {signal.market_scenario.replace('_', ' ')}
                </Badge>
                <p className="max-w-xl text-muted-foreground">{signal.reasoning}</p>
                <div className="mt-4 flex items-center gap-4">
                  <Badge variant="secondary">{signal.strategy_type}</Badge>
                  <Badge variant="secondary" className="capitalize">
                    {signal.strength} signal
                  </Badge>
                </div>
              </div>

              <div className="flex flex-col items-center gap-4">
                <ConfidenceMeter value={signal.confidence} size="lg" />
                <p className="text-xs text-muted-foreground">Confidence Score</p>
              </div>
            </div>

            {/* Decision Score Bar */}
            <div className="mt-6">
              <div className="mb-2 flex justify-between text-xs text-muted-foreground">
                <span>SELL</span>
                <span>NEUTRAL</span>
                <span>BUY</span>
              </div>
              <div className="relative h-3 rounded-full bg-gradient-to-r from-red-500 via-amber-500 to-green-500">
                <motion.div
                  initial={{ left: '50%' }}
                  animate={{ left: `${decisionScorePercent}%` }}
                  transition={{ duration: 0.5 }}
                  className="absolute top-1/2 h-5 w-5 -translate-x-1/2 -translate-y-1/2 rounded-full border-2 border-white bg-white shadow-lg"
                />
              </div>
              <p className="mt-1 text-center text-xs text-muted-foreground">
                Decision Score: {signal.decision_score.toFixed(2)}
              </p>
            </div>
          </CardContent>
        </Card>

        {/* Strike Recommendations */}
        <div>
          <h3 className="mb-4 text-lg font-semibold">Strike Recommendations</h3>
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {strike_recommendations.map((strike, i) => (
              <StrikeCard key={i} strike={strike} index={i} />
            ))}
          </div>
        </div>
      </div>

      {/* Right Column - Radar & Info */}
      <div className="space-y-6 lg:col-span-2">
        {/* Agent Weights Radar */}
        <Card className="border-border">
          <CardHeader>
            <CardTitle className="text-sm font-medium">Agent Weights</CardTitle>
          </CardHeader>
          <CardContent>
            <RadarChart weights={agent_weights} />
          </CardContent>
        </Card>

        {/* Analysis Timer */}
        <Card className="border-border">
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <Clock className="h-5 w-5 text-primary" />
              <div>
                <p className="text-sm font-medium">
                  Completed in {analysis.analysis_time_seconds.toFixed(1)}s
                </p>
                <p className="text-xs text-muted-foreground">
                  {Object.keys(analysis.agent_results).length} agents consulted
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
