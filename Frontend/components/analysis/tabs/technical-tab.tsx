'use client'

import {
  Activity,
  BarChart3,
  Gauge,
  LineChart,
  TrendingDown,
  TrendingUp,
} from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Progress } from '@/components/ui/progress'
import {
  formatCompact,
  formatPercent,
  formatPrice,
  getPriceColorClass,
} from '@/lib/utils/format'
import type { TechnicalResponse } from '@/lib/api/types'

interface TechnicalTabProps {
  technical: TechnicalResponse
}

function MetricCard({
  label,
  value,
  detail,
  icon: Icon,
}: {
  label: string
  value: string
  detail?: string
  icon: React.ElementType
}) {
  return (
    <Card className="border-border bg-card">
      <CardContent className="p-4">
        <div className="mb-3 flex items-center justify-between">
          <span className="text-sm text-muted-foreground">{label}</span>
          <Icon className="h-4 w-4 text-primary" />
        </div>
        <div className="font-mono text-2xl font-semibold">{value}</div>
        {detail && <p className="mt-1 text-xs text-muted-foreground">{detail}</p>}
      </CardContent>
    </Card>
  )
}

function IndicatorRow({
  label,
  value,
  signal,
}: {
  label: string
  value: string
  signal?: 'bullish' | 'bearish' | 'neutral'
}) {
  return (
    <div className="flex items-center justify-between rounded-lg border border-border bg-background/50 px-3 py-2">
      <span className="text-sm text-muted-foreground">{label}</span>
      <div className="flex items-center gap-2">
        {signal && (
          <Badge
            variant={
              signal === 'bullish'
                ? 'default'
                : signal === 'bearish'
                  ? 'destructive'
                  : 'secondary'
            }
          >
            {signal}
          </Badge>
        )}
        <span className="font-mono text-sm font-medium">{value}</span>
      </div>
    </div>
  )
}

export function TechnicalTab({ technical }: TechnicalTabProps) {
  const { indicators } = technical
  const priceVsSma20 = technical.price >= indicators.sma_20 ? 'bullish' : 'bearish'
  const rsiSignal =
    indicators.rsi >= 70 ? 'bearish' : indicators.rsi <= 30 ? 'bullish' : 'neutral'
  const macdSignal =
    indicators.macd > indicators.macd_signal
      ? 'bullish'
      : indicators.macd < indicators.macd_signal
        ? 'bearish'
        : 'neutral'

  return (
    <div className="space-y-6">
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <MetricCard
          label="Last Price"
          value={formatPrice(technical.price)}
          detail={formatPercent(technical.change_percent)}
          icon={technical.change_percent >= 0 ? TrendingUp : TrendingDown}
        />
        <MetricCard
          label="Volume"
          value={formatCompact(technical.volume)}
          detail={`${formatCompact(technical.avg_volume)} average`}
          icon={BarChart3}
        />
        <MetricCard
          label="RSI"
          value={indicators.rsi.toFixed(1)}
          detail={rsiSignal === 'neutral' ? 'balanced momentum' : `${rsiSignal} setup`}
          icon={Gauge}
        />
        <MetricCard
          label="Volatility"
          value={formatPercent(indicators.volatility)}
          detail={`ATR ${indicators.atr.toFixed(2)}`}
          icon={Activity}
        />
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        <Card className="border-border bg-card">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-base">
              <LineChart className="h-5 w-5 text-primary" />
              Trend Structure
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            <IndicatorRow
              label="SMA 5"
              value={formatPrice(indicators.sma_5)}
              signal={technical.price >= indicators.sma_5 ? 'bullish' : 'bearish'}
            />
            <IndicatorRow
              label="SMA 20"
              value={formatPrice(indicators.sma_20)}
              signal={priceVsSma20}
            />
            <IndicatorRow
              label="SMA 50"
              value={formatPrice(indicators.sma_50)}
              signal={technical.price >= indicators.sma_50 ? 'bullish' : 'bearish'}
            />
            <IndicatorRow
              label="SMA 200"
              value={formatPrice(indicators.sma_200)}
              signal={technical.price >= indicators.sma_200 ? 'bullish' : 'bearish'}
            />
          </CardContent>
        </Card>

        <Card className="border-border bg-card">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-base">
              <Activity className="h-5 w-5 text-primary" />
              Momentum
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div>
              <div className="mb-2 flex items-center justify-between text-sm">
                <span className="text-muted-foreground">RSI</span>
                <span className="font-mono font-medium">{indicators.rsi.toFixed(1)}</span>
              </div>
              <Progress value={Math.max(0, Math.min(100, indicators.rsi))} className="h-2" />
            </div>
            <IndicatorRow
              label="MACD"
              value={indicators.macd.toFixed(3)}
              signal={macdSignal}
            />
            <IndicatorRow
              label="MACD Signal"
              value={indicators.macd_signal.toFixed(3)}
            />
            <IndicatorRow
              label="Stochastic K"
              value={indicators.stochastic_k.toFixed(1)}
            />
            <IndicatorRow
              label="Supertrend"
              value={indicators.supertrend}
              signal={indicators.supertrend}
            />
          </CardContent>
        </Card>
      </div>

      <Card className="border-border bg-card">
        <CardHeader>
          <CardTitle className="text-base">Price Range</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid gap-3 md:grid-cols-3">
            <IndicatorRow label="Bid" value={formatPrice(technical.bid)} />
            <IndicatorRow label="Ask" value={formatPrice(technical.ask)} />
            <IndicatorRow
              label="VWAP"
              value={formatPrice(indicators.vwap)}
              signal={technical.price >= indicators.vwap ? 'bullish' : 'bearish'}
            />
          </div>
          <div className="mt-4 flex items-center justify-between rounded-lg bg-muted/40 px-3 py-2 text-sm">
            <span className="text-muted-foreground">Current price bias</span>
            <span className={getPriceColorClass(technical.price - indicators.sma_20)}>
              {technical.price >= indicators.sma_20 ? 'Above short-term trend' : 'Below short-term trend'}
            </span>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
