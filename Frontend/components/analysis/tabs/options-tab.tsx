'use client'

import { motion } from 'framer-motion'
import { Calendar, DollarSign, Target, TrendingDown, TrendingUp, Zap } from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { formatCurrency } from '@/lib/utils/format'
import type { AnalysisResponse, StrikeRecommendation } from '@/lib/api/types'

interface OptionsTabProps {
  analysis: AnalysisResponse
}

function StrikeRecommendationCard({
  recommendation,
  index,
}: {
  recommendation: StrikeRecommendation
  index: number
}) {
  const isCall = recommendation.option_type === 'call'
  const Icon = isCall ? TrendingUp : TrendingDown

  return (
    <motion.div
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: index * 0.08 }}
      className="rounded-lg border border-border bg-background/50 p-4"
    >
      <div className="flex items-start justify-between gap-4">
        <div className="space-y-3">
          <div className="flex flex-wrap items-center gap-2">
            <Badge variant={isCall ? 'default' : 'destructive'}>
              {recommendation.option_type.toUpperCase()}
            </Badge>
            <span className="font-mono text-xl font-semibold">
              ${recommendation.strike}
            </span>
            <span className="flex items-center gap-1 text-sm text-muted-foreground">
              <Calendar className="h-3.5 w-3.5" />
              {recommendation.expiry}
            </span>
          </div>
          <p className="text-sm leading-6 text-muted-foreground">
            {recommendation.rationale}
          </p>
        </div>
        <div className="rounded-lg bg-muted p-2">
          <Icon className="h-5 w-5 text-primary" />
        </div>
      </div>

      <div className="mt-4 grid gap-3 sm:grid-cols-3">
        <div className="rounded-lg bg-muted/40 p-3">
          <div className="text-xs text-muted-foreground">Delta</div>
          <div className="font-mono font-semibold">
            {recommendation.delta == null ? '-' : recommendation.delta.toFixed(2)}
          </div>
        </div>
        <div className="rounded-lg bg-muted/40 p-3">
          <div className="text-xs text-muted-foreground">Premium</div>
          <div className="font-mono font-semibold">
            {recommendation.premium == null
              ? '-'
              : formatCurrency(recommendation.premium)}
          </div>
        </div>
        <div className="rounded-lg bg-muted/40 p-3">
          <div className="text-xs text-muted-foreground">Risk/Reward</div>
          <div className="font-mono font-semibold">
            {recommendation.risk_reward == null
              ? '-'
              : `${recommendation.risk_reward.toFixed(1)}x`}
          </div>
        </div>
      </div>

      <div className="mt-4 flex gap-2">
        <Button size="sm" className="gap-2">
          <Zap className="h-4 w-4" />
          Execute
        </Button>
        <Button size="sm" variant="outline">
          Add To Watchlist
        </Button>
      </div>
    </motion.div>
  )
}

export function OptionsTab({ analysis }: OptionsTabProps) {
  const recommendations = analysis.strike_recommendations || []
  const calls = recommendations.filter((item) => item.option_type === 'call').length
  const puts = recommendations.filter((item) => item.option_type === 'put').length

  return (
    <div className="space-y-6">
      <Card className="border-border bg-card">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Target className="h-5 w-5 text-primary" />
            Strike Recommendations
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="mb-4 grid gap-3 sm:grid-cols-3">
            <div className="rounded-lg bg-muted/40 p-3">
              <div className="text-xs text-muted-foreground">Total Ideas</div>
              <div className="font-mono text-2xl font-semibold">{recommendations.length}</div>
            </div>
            <div className="rounded-lg bg-muted/40 p-3">
              <div className="text-xs text-muted-foreground">Calls</div>
              <div className="font-mono text-2xl font-semibold text-green-500">{calls}</div>
            </div>
            <div className="rounded-lg bg-muted/40 p-3">
              <div className="text-xs text-muted-foreground">Puts</div>
              <div className="font-mono text-2xl font-semibold text-red-500">{puts}</div>
            </div>
          </div>

          {recommendations.length > 0 ? (
            <div className="grid gap-4">
              {recommendations.map((recommendation, index) => (
                <StrikeRecommendationCard
                  key={`${recommendation.option_type}-${recommendation.strike}-${recommendation.expiry}-${index}`}
                  recommendation={recommendation}
                  index={index}
                />
              ))}
            </div>
          ) : (
            <div className="rounded-lg border border-dashed border-border p-6 text-center">
              <DollarSign className="mx-auto mb-3 h-8 w-8 text-muted-foreground" />
              <p className="text-sm text-muted-foreground">
                No strike recommendations were returned for this analysis.
              </p>
            </div>
          )}
        </CardContent>
      </Card>

      <Card className="border-border bg-card">
        <CardHeader>
          <CardTitle className="text-base">Execution Notes</CardTitle>
        </CardHeader>
        <CardContent className="text-sm leading-6 text-muted-foreground">
          Validate bid/ask spread, open interest, implied volatility, and expiry risk before
          executing. The backend currently returns recommendation-level strike data, not a full
          multi-leg strategy payload.
        </CardContent>
      </Card>
    </div>
  )
}
