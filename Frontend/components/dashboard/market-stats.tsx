'use client'

import { BarChart3, Flame, Gauge, TrendingDown, TrendingUp, Volume2 } from 'lucide-react'
import { Card, CardContent } from '@/components/ui/card'
import { Skeleton } from '@/components/ui/skeleton'
import { formatCompact, formatPercent } from '@/lib/utils/format'
import { cn } from '@/lib/utils'
import type { MarketStatsSummary } from './market-dashboard-utils'

interface MarketStatsProps {
  stats: MarketStatsSummary
  isLoading?: boolean
}

export function MarketStats({ stats, isLoading = false }: MarketStatsProps) {
  const statRows = [
    {
      label: 'Tracked Symbols',
      value: String(stats.totalStocks),
      detail: `${stats.trendingCount} trending`,
      icon: Flame,
      tone: 'text-amber-500',
    },
    {
      label: 'Gainers / Decliners',
      value: `${stats.gainers}/${stats.decliners}`,
      detail: stats.gainers >= stats.decliners ? 'Positive breadth' : 'Negative breadth',
      icon: stats.gainers >= stats.decliners ? TrendingUp : TrendingDown,
      tone: stats.gainers >= stats.decliners ? 'text-chart-up' : 'text-chart-down',
    },
    {
      label: 'Average AI Score',
      value: String(stats.averageAiScore),
      detail: stats.averageAiScore >= 70 ? 'Constructive setup' : 'Mixed setup',
      icon: Gauge,
      tone: stats.averageAiScore >= 70 ? 'text-chart-up' : 'text-amber-500',
    },
    {
      label: 'Top Mover',
      value: stats.topMover?.symbol ?? '—',
      detail: stats.topMover ? formatPercent(stats.topMover.changePercent) : 'No quote',
      icon: BarChart3,
      tone:
        (stats.topMover?.changePercent ?? 0) >= 0 ? 'text-chart-up' : 'text-chart-down',
    },
    {
      label: 'Highest Volume',
      value: stats.highestVolume?.symbol ?? '—',
      detail: stats.highestVolume ? formatCompact(stats.highestVolume.volume) : 'No volume',
      icon: Volume2,
      tone: 'text-primary',
    },
  ]

  return (
    <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-5">
      {statRows.map((row) => (
        <Card key={row.label} className="border-border">
          <CardContent className="flex h-24 items-center gap-3 p-4">
            <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-md bg-muted">
              <row.icon className={cn('h-4 w-4', row.tone)} />
            </div>
            <div className="min-w-0">
              <p className="truncate text-xs text-muted-foreground">{row.label}</p>
              {isLoading ? (
                <Skeleton className="mt-1 h-6 w-16" />
              ) : (
                <p className="truncate font-mono text-xl font-semibold tabular-nums">
                  {row.value}
                </p>
              )}
              <p className={cn('truncate text-xs', isLoading ? 'text-muted-foreground' : row.tone)}>
                {isLoading ? 'Loading' : row.detail}
              </p>
            </div>
          </CardContent>
        </Card>
      ))}
    </div>
  )
}
