'use client'

import { Calendar, CheckCircle, Clock, FileText, TrendingDown, TrendingUp } from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Separator } from '@/components/ui/separator'
import { formatPercent } from '@/lib/utils/format'
import type { AnalysisResponse } from '@/lib/api/types'

interface ReportTabProps {
  analysis: AnalysisResponse
}

export function ReportTab({ analysis }: ReportTabProps) {
  const agentEntries = Object.values(analysis.agent_results)
  const topInsights = agentEntries.flatMap((agent) => agent.insights).slice(0, 8)
  const isBullish = analysis.signal.direction.includes('BUY')
  const isBearish = analysis.signal.direction.includes('SELL')
  const DirectionIcon = isBullish ? TrendingUp : isBearish ? TrendingDown : CheckCircle

  return (
    <div className="space-y-6">
      <Card className="border-border bg-card">
        <CardContent className="p-6">
          <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
            <div className="flex items-center gap-4">
              <div className="rounded-lg bg-primary/10 p-3">
                <FileText className="h-8 w-8 text-primary" />
              </div>
              <div>
                <h2 className="text-2xl font-bold">Analysis Report: {analysis.symbol}</h2>
                <div className="mt-1 flex flex-wrap items-center gap-4 text-sm text-muted-foreground">
                  <span className="flex items-center gap-1">
                    <Calendar className="h-4 w-4" />
                    {new Date(analysis.timestamp).toLocaleDateString()}
                  </span>
                  <span className="flex items-center gap-1">
                    <Clock className="h-4 w-4" />
                    {new Date(analysis.timestamp).toLocaleTimeString()}
                  </span>
                </div>
              </div>
            </div>
            <Badge variant="outline">{analysis.market_scenario.replace('_', ' ')}</Badge>
          </div>
        </CardContent>
      </Card>

      <Card className="border-border bg-card">
        <CardHeader>
          <CardTitle>Executive Summary</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <p className="text-sm leading-6 text-muted-foreground">
            {analysis.signal.reasoning ||
              'The current backend response includes the final signal, confidence, agent outputs, and strike recommendations.'}
          </p>

          <Separator />

          <div className="grid gap-4 md:grid-cols-4">
            <div className="rounded-lg bg-muted/50 p-4 text-center">
              <DirectionIcon className="mx-auto mb-2 h-5 w-5 text-primary" />
              <div className="text-xl font-bold">{analysis.signal.direction.replace('_', ' ')}</div>
              <div className="text-sm text-muted-foreground">Overall Signal</div>
            </div>
            <div className="rounded-lg bg-muted/50 p-4 text-center">
              <div className="text-xl font-bold text-primary">
                {formatPercent(analysis.confidence * 100)}
              </div>
              <div className="text-sm text-muted-foreground">Confidence</div>
            </div>
            <div className="rounded-lg bg-muted/50 p-4 text-center">
              <div className="text-xl font-bold">{agentEntries.length}</div>
              <div className="text-sm text-muted-foreground">Agents</div>
            </div>
            <div className="rounded-lg bg-muted/50 p-4 text-center">
              <div className="text-xl font-bold">{analysis.strike_recommendations.length}</div>
              <div className="text-sm text-muted-foreground">Strikes</div>
            </div>
          </div>
        </CardContent>
      </Card>

      <Card className="border-border bg-card">
        <CardHeader>
          <CardTitle>Key Findings</CardTitle>
        </CardHeader>
        <CardContent>
          {topInsights.length > 0 ? (
            <div className="space-y-3">
              {topInsights.map((insight, index) => (
                <div key={index} className="flex items-start gap-3">
                  <CheckCircle className="mt-0.5 h-5 w-5 shrink-0 text-primary" />
                  <p className="text-sm text-muted-foreground">{insight}</p>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-sm text-muted-foreground">
              No detailed findings were returned by the agents.
            </p>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
