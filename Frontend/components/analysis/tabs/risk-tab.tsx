'use client'

import { AlertTriangle, Gauge, Shield, Target } from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Progress } from '@/components/ui/progress'
import type { AnalysisResponse } from '@/lib/api/types'

interface RiskTabProps {
  analysis: AnalysisResponse
}

export function RiskTab({ analysis }: RiskTabProps) {
  const confidencePercent = Math.round(analysis.confidence * 100)
  const decisionScorePercent = Math.round(((analysis.signal.decision_score + 1) / 2) * 100)
  const riskTone =
    analysis.signal.strength === 'strong'
      ? 'Elevated conviction requires tighter execution discipline.'
      : analysis.signal.strength === 'moderate'
        ? 'Moderate conviction supports measured position sizing.'
        : 'Weak conviction should be treated as watchlist-level only.'

  return (
    <div className="space-y-6">
      <Card className="border-border bg-card">
        <CardContent className="p-6">
          <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
            <div className="flex items-center gap-4">
              <div className="rounded-full bg-primary/10 p-3">
                <Shield className="h-8 w-8 text-primary" />
              </div>
              <div>
                <h3 className="text-lg font-semibold">Signal Risk Review</h3>
                <p className="text-sm text-muted-foreground">{riskTone}</p>
              </div>
            </div>
            <Badge variant="outline">{analysis.signal.strength} strength</Badge>
          </div>
        </CardContent>
      </Card>

      <div className="grid gap-4 md:grid-cols-3">
        <Card className="border-border bg-card">
          <CardHeader className="pb-2">
            <CardTitle className="flex items-center gap-2 text-sm font-medium">
              <Gauge className="h-4 w-4 text-primary" />
              Confidence
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="mb-2 font-mono text-3xl font-semibold">{confidencePercent}%</div>
            <Progress value={confidencePercent} className="h-2" />
          </CardContent>
        </Card>

        <Card className="border-border bg-card">
          <CardHeader className="pb-2">
            <CardTitle className="flex items-center gap-2 text-sm font-medium">
              <Target className="h-4 w-4 text-primary" />
              Decision Score
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="mb-2 font-mono text-3xl font-semibold">
              {decisionScorePercent}%
            </div>
            <Progress value={decisionScorePercent} className="h-2" />
          </CardContent>
        </Card>

        <Card className="border-border bg-card">
          <CardHeader className="pb-2">
            <CardTitle className="flex items-center gap-2 text-sm font-medium">
              <AlertTriangle className="h-4 w-4 text-primary" />
              Market Scenario
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-semibold">
              {analysis.market_scenario.replace('_', ' ')}
            </div>
            <p className="mt-2 text-sm text-muted-foreground">
              Scenario-specific sizing rules should be applied before execution.
            </p>
          </CardContent>
        </Card>
      </div>

      <Card className="border-border bg-card">
        <CardHeader>
          <CardTitle className="text-base">Practical Risk Checks</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid gap-3 md:grid-cols-2">
            {[
              'Confirm spread width before entry.',
              'Check open interest and volume on the selected contract.',
              'Define max loss before placing the order.',
              'Avoid increasing size because of AI confidence alone.',
            ].map((item) => (
              <div key={item} className="rounded-lg border border-border bg-background/50 p-3">
                <p className="text-sm text-muted-foreground">{item}</p>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
