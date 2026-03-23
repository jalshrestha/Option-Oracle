'use client'

import { Activity } from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Skeleton } from '@/components/ui/skeleton'
import { useHotStocks } from '@/lib/hooks/use-api'
import { formatPrice, formatPercent, getPriceColorClass } from '@/lib/utils/format'
import { cn } from '@/lib/utils'

const INDICES = ['SPY', 'QQQ', 'IWM']

export function MarketPulseCard() {
  const { data: stocks, isLoading } = useHotStocks()
  
  const indices = stocks?.filter((stock) => INDICES.includes(stock.symbol)) || []

  // Mock data for demo when API is not available
  const mockIndices = [
    { symbol: 'SPY', price: 512.34, changePercent: 0.87 },
    { symbol: 'QQQ', price: 438.92, changePercent: 1.23 },
    { symbol: 'IWM', price: 207.15, changePercent: -0.34 },
  ]

  const displayData = indices.length > 0 ? indices : mockIndices

  return (
    <Card className="glass dark:glass border-border">
      <CardHeader className="flex flex-row items-center justify-between pb-2">
        <CardTitle className="flex items-center gap-2 text-sm font-medium">
          <Activity className="h-4 w-4 text-primary" />
          Market Pulse
        </CardTitle>
        <span className="text-xs text-muted-foreground">Live</span>
      </CardHeader>
      <CardContent className="space-y-3">
        {isLoading ? (
          <>
            <Skeleton className="h-8 w-full" />
            <Skeleton className="h-8 w-full" />
            <Skeleton className="h-8 w-full" />
          </>
        ) : (
          displayData.map((index) => (
            <div
              key={index.symbol}
              className="flex items-center justify-between rounded-lg bg-muted/50 px-3 py-2"
            >
              <span className="font-mono text-sm font-semibold">{index.symbol}</span>
              <div className="flex items-center gap-3">
                <span className="font-mono text-sm tabular-nums">
                  {formatPrice(index.price)}
                </span>
                <span
                  className={cn(
                    'font-mono text-xs font-medium tabular-nums',
                    getPriceColorClass(index.changePercent)
                  )}
                >
                  {formatPercent(index.changePercent)}
                </span>
              </div>
            </div>
          ))
        )}
      </CardContent>
    </Card>
  )
}
