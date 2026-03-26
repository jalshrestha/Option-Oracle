'use client'

import { Activity } from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Progress } from '@/components/ui/progress'
import { Skeleton } from '@/components/ui/skeleton'
import { SignalBadge } from '@/components/analysis/signal-badge'
import { formatTimeAgo } from '@/lib/utils/format'
import { useRecentSignals } from '@/lib/hooks/use-api'
import type { MarketScenario } from '@/lib/api/types'

function ScenarioBadge({ scenario }: { scenario: string }) {
  const colors: Record<string, string> = {
    BREAKOUT: 'bg-blue-500/20 text-blue-500',
    TRENDING: 'bg-green-500/20 text-green-500',
    RANGE_BOUND: 'bg-amber-500/20 text-amber-500',
    VOLATILE: 'bg-red-500/20 text-red-500',
    NEUTRAL: 'bg-gray-500/20 text-gray-500',
  }
  const cls = colors[scenario] || 'bg-gray-500/20 text-gray-500'

  return (
    <span
      className={`inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium ${cls}`}
    >
      {scenario.replace('_', ' ')}
    </span>
  )
}

export function RecentSignals() {
  const { data: signals, isLoading } = useRecentSignals(20)

  return (
    <Card className="border-border">
      <CardHeader>
        <CardTitle className="flex items-center gap-2 text-lg font-semibold">
          <Activity className="h-5 w-5 text-primary" />
          Recent Signals
        </CardTitle>
      </CardHeader>
      <CardContent>
        {isLoading ? (
          <div className="space-y-2">
            {Array.from({ length: 8 }).map((_, i) => (
              <Skeleton key={i} className="h-10 w-full" />
            ))}
          </div>
        ) : !signals || signals.length === 0 ? (
          <div className="py-12 text-center text-sm text-muted-foreground">
            No signals yet — run an analysis to generate signals.
          </div>
        ) : (
          <div className="relative overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead className="border-b border-border text-xs uppercase text-muted-foreground">
                <tr>
                  <th className="px-3 py-3 font-medium">Symbol</th>
                  <th className="px-3 py-3 font-medium">Direction</th>
                  <th className="px-3 py-3 font-medium">Strength</th>
                  <th className="px-3 py-3 font-medium">Confidence</th>
                  <th className="px-3 py-3 font-medium">Scenario</th>
                  <th className="px-3 py-3 font-medium">Time</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border">
                {signals.map((signal) => (
                  <tr
                    key={signal.id}
                    className="transition-colors hover:bg-muted/50"
                  >
                    <td className="px-3 py-3">
                      <span className="font-mono font-semibold">{signal.symbol}</span>
                    </td>
                    <td className="px-3 py-3">
                      <SignalBadge direction={signal.direction} size="sm" />
                    </td>
                    <td className="px-3 py-3">
                      <span className="capitalize text-muted-foreground">
                        {signal.strength ?? '—'}
                      </span>
                    </td>
                    <td className="px-3 py-3">
                      <div className="flex items-center gap-2">
                        <Progress
                          value={signal.confidence_score * 100}
                          className="h-2 w-16"
                        />
                        <span className="font-mono text-xs tabular-nums text-muted-foreground">
                          {Math.round(signal.confidence_score * 100)}%
                        </span>
                      </div>
                    </td>
                    <td className="px-3 py-3">
                      <ScenarioBadge scenario={signal.market_scenario} />
                    </td>
                    <td className="px-3 py-3 text-muted-foreground">
                      {signal.created_at ? formatTimeAgo(signal.created_at) : '—'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </CardContent>
    </Card>
  )
}
