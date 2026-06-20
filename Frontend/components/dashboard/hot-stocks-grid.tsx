'use client'

import Link from 'next/link'
import { ArrowRight, Flame, TrendingDown, TrendingUp } from 'lucide-react'
import { motion } from 'framer-motion'
import { Card, CardContent } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Skeleton } from '@/components/ui/skeleton'
import { SparklineChart } from '@/components/charts/sparkline-chart'
import {
  formatPrice,
  formatPercent,
  formatVolume,
  getAIScoreColor,
  getPriceColorClass,
} from '@/lib/utils/format'
import { cn } from '@/lib/utils'
import type { HotStock } from '@/lib/api/types'

function StockCard({ stock, index }: { stock: HotStock; index: number }) {
  const scoreColor = getAIScoreColor(stock.aiScore)
  const changeColor = getPriceColorClass(stock.changePercent)
  const TrendIcon = stock.changePercent >= 0 ? TrendingUp : TrendingDown

  return (
    <motion.div
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: index * 0.05 }}
    >
      <Card className="group relative overflow-hidden border-border bg-card transition-all duration-200 hover:-translate-y-0.5 hover:shadow-lg hover:shadow-primary/5">
        <CardContent className="p-4">
          <div className="mb-3 flex items-start justify-between">
            <div className="min-w-0">
              <div className="flex items-center gap-2">
                <h3 className="font-mono text-lg font-bold">{stock.symbol}</h3>
                {stock.trending ? (
                  <Badge variant="outline" className="gap-1 text-[10px]">
                    <Flame className="h-3 w-3 text-amber-500" />
                    Hot
                  </Badge>
                ) : null}
              </div>
              <p className="text-xs text-muted-foreground">{stock.name}</p>
            </div>
            <div className="text-right">
              <p className={cn('font-mono text-lg font-bold tabular-nums', changeColor)}>
                {formatPrice(stock.price)}
              </p>
              <Badge
                variant="secondary"
                className={cn('gap-1 font-mono text-xs tabular-nums', changeColor)}
              >
                <TrendIcon className="h-3 w-3" />
                {formatPercent(stock.changePercent)}
              </Badge>
            </div>
          </div>

          <div className="mb-3 flex items-center justify-between">
            <SparklineChart
              data={stock.sparklineData}
              color={stock.changePercent >= 0 ? 'up' : 'down'}
            />
            <div className="text-right">
              <p className="text-xs text-muted-foreground">AI Score</p>
              <p className={cn('font-mono text-xl font-bold', scoreColor)}>
                {stock.aiScore}
              </p>
            </div>
          </div>

          <div className="mb-3 flex items-center justify-between rounded-md bg-muted/40 px-2 py-1.5">
            <span className="text-xs text-muted-foreground">Volume</span>
            <span className="font-mono text-xs font-medium tabular-nums">
              {formatVolume(stock.volume)}
            </span>
          </div>

          <div className="mb-3 flex min-h-6 flex-wrap gap-1">
            {stock.signals.slice(0, 2).map((signal) => (
              <Badge
                key={signal}
                variant="outline"
                className="text-[10px] font-medium"
              >
                {signal}
              </Badge>
            ))}
          </div>

          <Link href={`/analyze/${stock.symbol}`}>
            <Button
              variant="secondary"
              size="sm"
              className="w-full gap-2 transition-colors group-hover:bg-primary group-hover:text-primary-foreground"
            >
              Analyze
              <ArrowRight className="h-3 w-3" />
            </Button>
          </Link>
        </CardContent>
      </Card>
    </motion.div>
  )
}

interface HotStocksGridProps {
  stocks: HotStock[]
  isLoading?: boolean
  hasActiveFilters?: boolean
}

export function HotStocksGrid({
  stocks,
  isLoading = false,
  hasActiveFilters = false,
}: HotStocksGridProps) {
  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-medium text-muted-foreground">
          {hasActiveFilters ? 'Filtered results' : 'Market watchlist'}
        </h3>
        <Link href="/analyze">
          <Button variant="ghost" size="sm" className="gap-1 text-xs">
            Analyze
            <ArrowRight className="h-3 w-3" />
          </Button>
        </Link>
      </div>

      {isLoading ? (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
          {Array.from({ length: 8 }).map((_, i) => (
            <Skeleton key={i} className="h-56" />
          ))}
        </div>
      ) : stocks.length === 0 ? (
        <div className="rounded-lg border border-dashed border-border py-12 text-center text-sm text-muted-foreground">
          {hasActiveFilters
            ? 'No stocks match the current filters.'
            : 'No hot stocks are available from the backend feed.'}
        </div>
      ) : (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
          {stocks.map((stock, index) => (
            <StockCard key={stock.symbol} stock={stock} index={index} />
          ))}
        </div>
      )}
    </div>
  )
}
