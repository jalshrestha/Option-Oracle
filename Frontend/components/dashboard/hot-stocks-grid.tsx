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

// Mock data for demo
const mockStocks: HotStock[] = [
  {
    symbol: 'NVDA',
    name: 'NVIDIA Corp',
    price: 878.35,
    change: 23.45,
    changePercent: 2.74,
    volume: 45200000,
    sparklineData: [820, 835, 845, 830, 855, 870, 865, 880, 875, 878],
    aiScore: 85,
    signals: ['BULLISH', 'HIGH VOLUME'],
    trending: true,
  },
  {
    symbol: 'AAPL',
    name: 'Apple Inc',
    price: 178.72,
    change: -1.28,
    changePercent: -0.71,
    volume: 32100000,
    sparklineData: [182, 180, 179, 181, 180, 178, 179, 177, 178, 179],
    aiScore: 62,
    signals: ['NEUTRAL'],
    trending: true,
  },
  {
    symbol: 'TSLA',
    name: 'Tesla Inc',
    price: 248.50,
    change: 8.92,
    changePercent: 3.72,
    volume: 89500000,
    sparklineData: [235, 238, 240, 236, 242, 245, 248, 250, 247, 249],
    aiScore: 78,
    signals: ['BULLISH', 'BREAKOUT'],
    trending: true,
  },
  {
    symbol: 'MSFT',
    name: 'Microsoft Corp',
    price: 415.60,
    change: 5.20,
    changePercent: 1.27,
    volume: 21300000,
    sparklineData: [408, 410, 412, 409, 413, 415, 414, 416, 415, 416],
    aiScore: 72,
    signals: ['BULLISH'],
    trending: true,
  },
  {
    symbol: 'META',
    name: 'Meta Platforms',
    price: 505.20,
    change: 12.35,
    changePercent: 2.51,
    volume: 18700000,
    sparklineData: [488, 492, 495, 490, 498, 502, 500, 505, 503, 505],
    aiScore: 81,
    signals: ['BULLISH', 'MOMENTUM'],
    trending: true,
  },
  {
    symbol: 'AMZN',
    name: 'Amazon.com',
    price: 178.25,
    change: 2.15,
    changePercent: 1.22,
    volume: 28400000,
    sparklineData: [174, 175, 176, 174, 177, 178, 177, 179, 178, 178],
    aiScore: 68,
    signals: ['NEUTRAL'],
    trending: true,
  },
]

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
  const { data: stocks, isLoading } = useHotStocks()

  const displayStocks = stocks && stocks.length > 0 ? stocks.slice(0, 6) : mockStocks

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
        ) : (
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6">
            {displayStocks.map((stock, index) => (
              <StockCard key={stock.symbol} stock={stock} index={index} />
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  )
}
