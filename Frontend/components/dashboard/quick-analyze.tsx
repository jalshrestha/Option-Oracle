'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import { Brain, Search, Sparkles } from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Badge } from '@/components/ui/badge'
import { OracleLoading } from '@/components/analysis/oracle-loading'
import { analyzeStock } from '@/lib/api/client'
import { cn } from '@/lib/utils'

const popularSymbols = ['AAPL', 'GOOGL', 'MSFT', 'TSLA', 'AMZN', 'NVDA', 'META', 'NFLX']

export function QuickAnalyze() {
  const router = useRouter()
  const [symbol, setSymbol] = useState('')
  const [isAnalyzing, setIsAnalyzing] = useState(false)
  const [suggestions, setSuggestions] = useState<string[]>([])

  const handleInputChange = (value: string) => {
    const upperValue = value.toUpperCase()
    setSymbol(upperValue)

    if (upperValue.length > 0) {
      const filtered = popularSymbols.filter((s) => s.startsWith(upperValue))
      setSuggestions(filtered)
    } else {
      setSuggestions([])
    }
  }

  const handleAnalyze = async (targetSymbol: string) => {
    if (!targetSymbol) return

    setIsAnalyzing(true)
    try {
      // Navigate immediately to analysis page
      router.push(`/analyze/${targetSymbol}`)
    } catch (error) {
      console.error('Failed to analyze:', error)
      setIsAnalyzing(false)
    }
  }

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    handleAnalyze(symbol)
  }

  if (isAnalyzing) {
    return <OracleLoading symbol={symbol} />
  }

  return (
    <Card className="border-border">
      <CardHeader>
        <CardTitle className="flex items-center gap-2 text-lg font-semibold">
          <Sparkles className="h-5 w-5 text-primary" />
          Quick Analyze
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
            <Input
              type="text"
              placeholder="Enter stock symbol..."
              value={symbol}
              onChange={(e) => handleInputChange(e.target.value)}
              className="pl-10 font-mono uppercase"
            />
            {suggestions.length > 0 && (
              <div className="absolute top-full z-10 mt-1 w-full rounded-lg border border-border bg-popover p-1 shadow-lg">
                {suggestions.map((s) => (
                  <button
                    key={s}
                    type="button"
                    onClick={() => {
                      setSymbol(s)
                      setSuggestions([])
                    }}
                    className="flex w-full items-center rounded px-3 py-2 text-left font-mono text-sm hover:bg-accent"
                  >
                    {s}
                  </button>
                ))}
              </div>
            )}
          </div>

          <Button
            type="submit"
            disabled={!symbol}
            className="w-full gap-2 brand-gradient text-white"
          >
            <Brain className="h-4 w-4" />
            Analyze Now
          </Button>
        </form>

        <div className="space-y-2">
          <p className="text-xs text-muted-foreground">Popular symbols:</p>
          <div className="flex flex-wrap gap-1">
            {popularSymbols.map((s) => (
              <Badge
                key={s}
                variant="outline"
                className={cn(
                  'cursor-pointer font-mono transition-colors hover:bg-primary hover:text-primary-foreground',
                  symbol === s && 'bg-primary text-primary-foreground'
                )}
                onClick={() => setSymbol(s)}
              >
                {s}
              </Badge>
            ))}
          </div>
        </div>

        <div className="rounded-lg bg-muted/50 p-4">
          <p className="text-xs text-muted-foreground">
            Analysis includes technical indicators, sentiment analysis, options flow,
            historical patterns, risk assessment, and AI-powered recommendations.
            Takes approximately 35 seconds.
          </p>
        </div>
      </CardContent>
    </Card>
  )
}
