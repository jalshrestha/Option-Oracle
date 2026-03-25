'use client'

import { Wallet, Shield, LineChart } from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Skeleton } from '@/components/ui/skeleton'
import { usePortfolioSummary } from '@/lib/hooks/use-api'
import { formatCurrency } from '@/lib/utils/format'

export function ActiveSessionCard() {
  const { data: portfolio, isLoading } = usePortfolioSummary()

  return (
    <Card className="glass dark:glass border-border">
      <CardHeader className="flex flex-row items-center justify-between pb-2">
        <CardTitle className="flex items-center gap-2 text-sm font-medium">
          <Wallet className="h-4 w-4 text-primary" />
          Active Session
        </CardTitle>
        <Badge variant="secondary" className="gap-1">
          <Shield className="h-3 w-3" />
          Moderate
        </Badge>
      </CardHeader>
      <CardContent className="space-y-4">
        {isLoading ? (
          <>
            <Skeleton className="h-12 w-full" />
            <Skeleton className="h-8 w-full" />
          </>
        ) : (
          <>
            <div>
              <p className="text-xs text-muted-foreground">Paper Trading Balance</p>
              <p className="font-mono text-2xl font-bold tabular-nums text-foreground">
                {formatCurrency(portfolio?.total_value ?? 0)}
              </p>
            </div>
            <div className="flex items-center justify-between rounded-lg bg-muted/50 px-3 py-2">
              <div className="flex items-center gap-2">
                <LineChart className="h-4 w-4 text-muted-foreground" />
                <span className="text-sm text-muted-foreground">Open Positions</span>
              </div>
              <span className="font-mono text-sm font-semibold">
                {portfolio?.open_positions ?? 0}
              </span>
            </div>
            <div className="flex items-center gap-2">
              <div className="h-2 w-2 rounded-full bg-green-500" />
              <span className="text-xs text-muted-foreground">Authenticated</span>
            </div>
          </>
        )}
      </CardContent>
    </Card>
  )
}
