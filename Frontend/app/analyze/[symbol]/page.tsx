'use client'

import { useState, useEffect, use } from 'react'
import { motion } from 'framer-motion'
import { RefreshCw, Clock, ArrowUpRight, ArrowDownRight } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { OracleLoading } from '@/components/analysis/oracle-loading'
import { OverviewTab } from '@/components/analysis/tabs/overview-tab'
import { AgentsTab } from '@/components/analysis/tabs/agents-tab'
import { OptionsTab } from '@/components/analysis/tabs/options-tab'
import { TechnicalTab } from '@/components/analysis/tabs/technical-tab'
import { EducationTab } from '@/components/analysis/tabs/education-tab'
import { analyzeStock, getTechnical } from '@/lib/api/client'
import { formatPrice, formatPercent, getPriceColorClass, formatTimeAgo } from '@/lib/utils/format'
import { cn } from '@/lib/utils'
import type { AnalysisResponse, TechnicalResponse } from '@/lib/api/types'

export default function AnalyzePage(props: { params: Promise<{ symbol: string }> }) {
  const params = use(props.params)
  const symbol = params.symbol.toUpperCase()

  const [analysis, setAnalysis] = useState<AnalysisResponse | null>(null)
  const [technical, setTechnical] = useState<TechnicalResponse | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [isReanalyzing, setIsReanalyzing] = useState(false)

  useEffect(() => {
    const loadData = async () => {
      setIsLoading(true)
      try {
        const [analysisData, technicalData] = await Promise.all([
          analyzeStock(symbol),
          getTechnical(symbol),
        ])
        setAnalysis(analysisData)
        setTechnical(technicalData)
      } catch (error) {
        // Leave analysis null — error state is shown below
      } finally {
        setIsLoading(false)
      }
    }

    loadData()
  }, [symbol])

  const handleReanalyze = async () => {
    setIsReanalyzing(true)
    try {
      const newAnalysis = await analyzeStock(symbol)
      setAnalysis(newAnalysis)
    } catch (error) {
      // Keep existing analysis
    } finally {
      setIsReanalyzing(false)
    }
  }

  if (isLoading) {
    return <OracleLoading symbol={symbol} />
  }

  if (!analysis || !technical) {
    return (
      <div className="flex h-96 flex-col items-center justify-center gap-4">
        <p className="text-muted-foreground">Analysis failed for {symbol}. Please try again.</p>
        <Button onClick={() => window.location.reload()}>
          <RefreshCw className="mr-2 h-4 w-4" />
          Retry
        </Button>
      </div>
    )
  }

  const changeColor = getPriceColorClass(technical.change_percent)
  const ChangeIcon = technical.change_percent >= 0 ? ArrowUpRight : ArrowDownRight

  return (
    <motion.div
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      className="space-y-6"
    >
      {/* Symbol Header Bar */}
      <div className="flex flex-col gap-4 rounded-xl border border-border bg-card p-6 lg:flex-row lg:items-center lg:justify-between">
        <div className="flex items-center gap-6">
          <div>
            <h1 className="font-mono text-4xl font-bold tracking-tight">{symbol}</h1>
            <p className="text-muted-foreground">Analysis Report</p>
          </div>
          <div className="flex items-baseline gap-3">
            <span className={cn('font-mono text-3xl font-bold tabular-nums', changeColor)}>
              {formatPrice(technical.price)}
            </span>
            <div className={cn('flex items-center gap-1', changeColor)}>
              <ChangeIcon className="h-5 w-5" />
              <span className="font-mono text-lg font-medium tabular-nums">
                {formatPercent(technical.change_percent)}
              </span>
            </div>
          </div>
        </div>

        <div className="flex flex-wrap items-center gap-4">
          <div className="flex items-center gap-2 text-sm text-muted-foreground">
            <span>Bid/Ask:</span>
            <span className="font-mono tabular-nums">
              {formatPrice(technical.bid)} / {formatPrice(technical.ask)}
            </span>
          </div>
          <div className="flex items-center gap-2 text-sm text-muted-foreground">
            <span>Vol:</span>
            <span className="font-mono tabular-nums">
              {(technical.volume / 1e6).toFixed(1)}M
            </span>
            <Badge variant={technical.volume > technical.avg_volume ? 'default' : 'secondary'}>
              {((technical.volume / technical.avg_volume) * 100).toFixed(0)}% avg
            </Badge>
          </div>
          <div className="flex items-center gap-2 text-xs text-muted-foreground">
            <Clock className="h-3 w-3" />
            <span>Updated {formatTimeAgo(analysis.timestamp)}</span>
          </div>
          <Button
            variant="outline"
            size="sm"
            onClick={handleReanalyze}
            disabled={isReanalyzing}
            className="gap-2"
          >
            <RefreshCw className={cn('h-4 w-4', isReanalyzing && 'animate-spin')} />
            Re-analyze
          </Button>
        </div>
      </div>

      {/* Tabs */}
      <Tabs defaultValue="overview" className="space-y-6">
        <TabsList className="grid w-full grid-cols-5 lg:w-auto lg:grid-cols-none">
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="agents">Agents</TabsTrigger>
          <TabsTrigger value="options">Options</TabsTrigger>
          <TabsTrigger value="technical">Technical</TabsTrigger>
          <TabsTrigger value="education">Education</TabsTrigger>
        </TabsList>

        <TabsContent value="overview">
          <OverviewTab analysis={analysis} />
        </TabsContent>

        <TabsContent value="agents">
          <AgentsTab analysis={analysis} />
        </TabsContent>

        <TabsContent value="options">
          <OptionsTab analysis={analysis} symbol={symbol} />
        </TabsContent>

        <TabsContent value="technical">
          <TechnicalTab technical={technical} />
        </TabsContent>

        <TabsContent value="education">
          <EducationTab analysis={analysis} />
        </TabsContent>
      </Tabs>

      {isReanalyzing && <OracleLoading symbol={symbol} />}
    </motion.div>
  )
}
