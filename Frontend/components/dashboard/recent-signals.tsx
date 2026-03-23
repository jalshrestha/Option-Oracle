'use client'

import { Activity } from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Progress } from '@/components/ui/progress'
import { SignalBadge } from '@/components/analysis/signal-badge'
import { formatTimeAgo } from '@/lib/utils/format'
import type { SignalDirection, MarketScenario } from '@/lib/api/types'

interface RecentSignal {
  symbol: string
  direction: SignalDirection
  strength: string
  confidence: number
  scenario: MarketScenario
  timestamp: string
}

// Mock data for demo
const mockSignals: RecentSignal[] = [
  {
    symbol: 'NVDA',
    direction: 'STRONG_BUY',
    strength: 'strong',
    confidence: 0.87,
    scenario: 'BREAKOUT',
    timestamp: new Date(Date.now() - 5 * 60000).toISOString(),
  },
  {
    symbol: 'TSLA',
    direction: 'BUY',
    strength: 'moderate',
    confidence: 0.72,
    scenario: 'TRENDING',
    timestamp: new Date(Date.now() - 15 * 60000).toISOString(),
  },
  {
    symbol: 'AAPL',
    direction: 'HOLD',
    strength: 'weak',
    confidence: 0.54,
    scenario: 'RANGE_BOUND',
    timestamp: new Date(Date.now() - 30 * 60000).toISOString(),
  },
  {
    symbol: 'META',
    direction: 'BUY',
    strength: 'moderate',
    confidence: 0.68,
    scenario: 'TRENDING',
    timestamp: new Date(Date.now() - 45 * 60000).toISOString(),
  },
  {
    symbol: 'AMZN',
    direction: 'HOLD',
    strength: 'moderate',
    confidence: 0.61,
    scenario: 'NEUTRAL',
    timestamp: new Date(Date.now() - 60 * 60000).toISOString(),
  },
  {
    symbol: 'MSFT',
    direction: 'BUY',
    strength: 'strong',
    confidence: 0.79,
    scenario: 'BREAKOUT',
    timestamp: new Date(Date.now() - 90 * 60000).toISOString(),
  },
  {
    symbol: 'GOOGL',
    direction: 'SELL',
    strength: 'weak',
    confidence: 0.45,
    scenario: 'VOLATILE',
    timestamp: new Date(Date.now() - 120 * 60000).toISOString(),
  },
  {
    symbol: 'AMD',
    direction: 'STRONG_BUY',
    strength: 'strong',
    confidence: 0.82,
    scenario: 'BREAKOUT',
    timestamp: new Date(Date.now() - 180 * 60000).toISOString(),
  },
]

function ScenarioBadge({ scenario }: { scenario: MarketScenario }) {
  const colors: Record<MarketScenario, string> = {
    BREAKOUT: 'bg-blue-500/20 text-blue-500',
    TRENDING: 'bg-green-500/20 text-green-500',
    RANGE_BOUND: 'bg-amber-500/20 text-amber-500',
    VOLATILE: 'bg-red-500/20 text-red-500',
    NEUTRAL: 'bg-gray-500/20 text-gray-500',
  }

  return (
    <span
      className={`inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium ${colors[scenario]}`}
    >
      {scenario.replace('_', ' ')}
    </span>
  )
}

export function RecentSignals() {
  return (
    <Card className="border-border">
      <CardHeader>
        <CardTitle className="flex items-center gap-2 text-lg font-semibold">
          <Activity className="h-5 w-5 text-primary" />
          Recent Signals
        </CardTitle>
      </CardHeader>
      <CardContent>
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
              {mockSignals.map((signal, index) => (
                <tr
                  key={`${signal.symbol}-${index}`}
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
                      {signal.strength}
                    </span>
                  </td>
                  <td className="px-3 py-3">
                    <div className="flex items-center gap-2">
                      <Progress
                        value={signal.confidence * 100}
                        className="h-2 w-16"
                      />
                      <span className="font-mono text-xs tabular-nums text-muted-foreground">
                        {Math.round(signal.confidence * 100)}%
                      </span>
                    </div>
                  </td>
                  <td className="px-3 py-3">
                    <ScenarioBadge scenario={signal.scenario} />
                  </td>
                  <td className="px-3 py-3 text-muted-foreground">
                    {formatTimeAgo(signal.timestamp)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </CardContent>
    </Card>
  )
}
