'use client'

import Link from 'next/link'
import { Flame, ArrowRight } from 'lucide-react'
import { motion } from 'framer-motion'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Skeleton } from '@/components/ui/skeleton'
import { SparklineChart } from '@/components/charts/sparkline-chart'
import { useHotStocks } from '@/lib/hooks/use-api'
import { formatPrice, formatPercent, getAIScoreColor, getPriceColorClass } from '@/lib/utils/format'
import { cn } from '@/lib/utils'
import type { HotStock } from '@/lib/api/types'


function StockCard({ stock, index }: { stock: HotStock; index: number }) {
  const scoreColor = getAIScoreColor(stock.aiScore)
  const changeColor = getPriceColorClass(stock.changePercent)

  return (
    <motion.div
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: index * 0.05 }}
    >
      <Card className="group relative overflow-hidden border-border bg-card transition-all duration-200 hover:-translate-y-0.5 hover:shadow-lg hover:shadow-primary/5">
        <CardContent className="p-4">
          <div className="mb-3 flex items-start justify-between">
            <div>
              <h3 className="font-mono text-lg font-bold">{stock.symbol}</h3>
              <p className="text-xs text-muted-foreground">{stock.name}</p>
            </div>
            <div className="text-right">
              <p className={cn('font-mono text-lg font-bold tabular-nums', changeColor)}>
                {formatPrice(stock.price)}
              </p>
              <Badge
                variant="secondary"
                className={cn('font-mono text-xs tabular-nums', changeColor)}
              >
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

          <div className="mb-3 flex flex-wrap gap-1">
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

export function HotStocksGrid() {
  const { data: stocks, isLoading, error } = useHotStocks()

  return (
    <Card className="border-border">
      <CardHeader className="flex flex-row items-center justify-between">
        <CardTitle className="flex items-center gap-2 text-lg font-semibold">
          <Flame className="h-5 w-5 text-amber-500" />
          Trending Now
        </CardTitle>
        <Link href="/analyze">
          <Button variant="ghost" size="sm" className="gap-1 text-xs">
            View All
            <ArrowRight className="h-3 w-3" />
          </Button>
        </Link>
      </CardHeader>
      <CardContent>
        {isLoading ? (
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6">
            {Array.from({ length: 6 }).map((_, i) => (
              <Skeleton key={i} className="h-52" />
            ))}
          </div>
        ) : error || !stocks || stocks.length === 0 ? (
          <div className="py-12 text-center text-sm text-muted-foreground">
            {error ? 'Unable to load trending stocks.' : 'No trending stocks available.'}
          </div>
        ) : (
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6">
            {stocks.slice(0, 6).map((stock, index) => (
              <StockCard key={stock.symbol} stock={stock} index={index} />
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  )
}
