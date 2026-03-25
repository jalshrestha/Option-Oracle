'use client'

import { useState } from 'react'
import { motion } from 'framer-motion'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Input } from '@/components/ui/input'
import { Skeleton } from '@/components/ui/skeleton'
import {
  Search,
  Activity,
  ArrowUpRight,
  ArrowDownRight,
} from 'lucide-react'
import { formatCurrency, formatPercent } from '@/lib/utils/format'
import { getOptionsChain } from '@/lib/api/client'
import type { OptionsChain } from '@/lib/api/types'

export default function OptionsChainPage() {
  const [inputSymbol, setInputSymbol] = useState('AAPL')
  const [showGreeks, setShowGreeks] = useState(false)
  const [chain, setChain] = useState<OptionsChain | null>(null)
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  async function fetchChain(symbol: string) {
    setIsLoading(true)
    setError(null)
    try {
      const data = await getOptionsChain(symbol.toUpperCase())
      setChain(data)
    } catch (err: any) {
      setError(err.message || 'Failed to load options chain')
      setChain(null)
    } finally {
      setIsLoading(false)
    }
  }

  function handleSearch() {
    if (inputSymbol.trim()) fetchChain(inputSymbol.trim())
  }

  return (
    <div className="space-y-6 p-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Options Chain</h1>
          <p className="text-muted-foreground">
            Real-time options data with AI-powered analysis
          </p>
        </div>
      </div>

      {/* Symbol search */}
      <Card className="border-border/50 bg-card/50 backdrop-blur">
        <CardContent className="p-4">
          <div className="flex gap-2">
            <div className="relative flex-1 max-w-xs">
              <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
              <Input
                value={inputSymbol}
                onChange={(e) => setInputSymbol(e.target.value.toUpperCase())}
                onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
                placeholder="Symbol (e.g. AAPL)"
                className="pl-9 font-mono"
                maxLength={5}
              />
            </div>
            <Button onClick={handleSearch} disabled={isLoading}>
              <Search className="mr-2 h-4 w-4" />
              {isLoading ? 'Loading…' : 'Load Chain'}
            </Button>
            <Button
              variant={showGreeks ? 'default' : 'outline'}
              onClick={() => setShowGreeks(!showGreeks)}
            >
              Greeks
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Stock header */}
      {chain && (
        <Card className="border-accent/30 bg-gradient-to-br from-accent/10 to-transparent">
          <CardContent className="flex flex-wrap items-center gap-6 p-4">
            <div>
              <span className="text-2xl font-bold">{chain.symbol}</span>
              <div className="text-sm text-muted-foreground">Expiry: {chain.expiry}</div>
            </div>
            <div className="flex items-center gap-4 text-sm">
              <div>
                <span className="text-muted-foreground">Put/Call Ratio: </span>
                <span className="font-mono font-semibold">{chain.put_call_ratio.toFixed(2)}</span>
              </div>
              <div>
                <span className="text-muted-foreground">Call Vol: </span>
                <span className="font-mono font-semibold text-green-500">{chain.total_call_volume.toLocaleString()}</span>
              </div>
              <div>
                <span className="text-muted-foreground">Put Vol: </span>
                <span className="font-mono font-semibold text-red-500">{chain.total_put_volume.toLocaleString()}</span>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Loading state */}
      {isLoading && (
        <Card className="border-border/50 bg-card/50">
          <CardContent className="p-4 space-y-2">
            {Array.from({ length: 10 }).map((_, i) => (
              <Skeleton key={i} className="h-10 w-full" />
            ))}
          </CardContent>
        </Card>
      )}

      {/* Error state */}
      {error && (
        <Card className="border-destructive/30">
          <CardContent className="p-6 text-center text-sm text-destructive">
            {error}
          </CardContent>
        </Card>
      )}

      {/* Empty / instructions */}
      {!chain && !isLoading && !error && (
        <Card className="border-border/50 bg-card/50">
          <CardContent className="py-16 text-center text-sm text-muted-foreground">
            Enter a symbol and click "Load Chain" to view the options chain.
          </CardContent>
        </Card>
      )}

      {/* Options chain table */}
      {chain && !isLoading && (
        <Card className="border-border/50 bg-card/50 backdrop-blur">
          <CardHeader className="pb-2">
            <CardTitle className="flex items-center gap-2">
              <Activity className="h-5 w-5 text-accent" />
              Options Chain — {chain.symbol} ({chain.expiry})
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-border/50">
                    <th
                      colSpan={showGreeks ? 7 : 5}
                      className="bg-green-500/10 px-4 py-3 text-center font-medium text-green-500"
                    >
                      CALLS
                    </th>
                    <th className="border-x border-border/50 bg-muted/50 px-4 py-3 text-center font-medium">
                      Strike
                    </th>
                    <th
                      colSpan={showGreeks ? 7 : 5}
                      className="bg-red-500/10 px-4 py-3 text-center font-medium text-red-500"
                    >
                      PUTS
                    </th>
                  </tr>
                  <tr className="border-b border-border/50 text-xs text-muted-foreground">
                    {['Last', 'Bid', 'Ask', 'Vol', 'OI'].map((h) => (
                      <th key={`c-${h}`} className="px-2 py-2 text-right">{h}</th>
                    ))}
                    {showGreeks && ['IV', 'Delta'].map((h) => (
                      <th key={`cg-${h}`} className="px-2 py-2 text-right">{h}</th>
                    ))}
                    <th className="border-x border-border/50 bg-muted/30 px-4 py-2 text-center font-medium">$</th>
                    {['Last', 'Bid', 'Ask', 'Vol', 'OI'].map((h) => (
                      <th key={`p-${h}`} className="px-2 py-2 text-right">{h}</th>
                    ))}
                    {showGreeks && ['IV', 'Delta'].map((h) => (
                      <th key={`pg-${h}`} className="px-2 py-2 text-right">{h}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {chain.calls.map((call, i) => {
                    const put = chain.puts.find((p) => p.strike === call.strike)
                    return (
                      <motion.tr
                        key={call.strike}
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        transition={{ delay: i * 0.01 }}
                        className={`border-b border-border/30 transition-colors hover:bg-muted/30 ${
                          call.itm ? 'bg-green-500/5' : ''
                        }`}
                      >
                        <td className="px-2 py-2 text-right font-mono">{call.last.toFixed(2)}</td>
                        <td className="px-2 py-2 text-right font-mono">{call.bid.toFixed(2)}</td>
                        <td className="px-2 py-2 text-right font-mono">{call.ask.toFixed(2)}</td>
                        <td className="px-2 py-2 text-right">{call.volume.toLocaleString()}</td>
                        <td className="px-2 py-2 text-right">{call.open_interest.toLocaleString()}</td>
                        {showGreeks && (
                          <>
                            <td className="px-2 py-2 text-right">{formatPercent(call.iv)}</td>
                            <td className="px-2 py-2 text-right">{call.delta.toFixed(2)}</td>
                          </>
                        )}
                        <td className="border-x border-border/50 bg-muted/30 px-4 py-2 text-center font-semibold">
                          ${call.strike}
                        </td>
                        {put ? (
                          <>
                            <td className="px-2 py-2 text-right font-mono">{put.last.toFixed(2)}</td>
                            <td className="px-2 py-2 text-right font-mono">{put.bid.toFixed(2)}</td>
                            <td className="px-2 py-2 text-right font-mono">{put.ask.toFixed(2)}</td>
                            <td className="px-2 py-2 text-right">{put.volume.toLocaleString()}</td>
                            <td className="px-2 py-2 text-right">{put.open_interest.toLocaleString()}</td>
                            {showGreeks && (
                              <>
                                <td className="px-2 py-2 text-right">{formatPercent(put.iv)}</td>
                                <td className="px-2 py-2 text-right">{put.delta.toFixed(2)}</td>
                              </>
                            )}
                          </>
                        ) : (
                          <td colSpan={showGreeks ? 7 : 5} className="px-2 py-2 text-center text-muted-foreground">—</td>
                        )}
                      </motion.tr>
                    )
                  })}
                </tbody>
              </table>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  )
}
