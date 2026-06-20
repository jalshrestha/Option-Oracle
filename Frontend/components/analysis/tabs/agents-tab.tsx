'use client'

import { useState } from 'react'
import { motion } from 'framer-motion'
import {
  BarChart3,
  Activity,
  TrendingUp,
  Clock,
  Shield,
  ChevronDown,
} from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Progress } from '@/components/ui/progress'
import { Badge } from '@/components/ui/badge'
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from '@/components/ui/collapsible'
import { SignalBadge } from '@/components/analysis/signal-badge'
import { cn } from '@/lib/utils'
import type { AnalysisResponse, AgentResult, SignalDirection } from '@/lib/api/types'

interface AgentsTabProps {
  analysis: AnalysisResponse
}

const agentIcons: Record<string, React.ElementType> = {
  technical: BarChart3,
  sentiment: Activity,
  flow: TrendingUp,
  historical: Clock,
  risk: Shield,
}

const agentColors: Record<string, string> = {
  technical: 'text-blue-500',
  sentiment: 'text-pink-500',
  flow: 'text-green-500',
  historical: 'text-amber-500',
  risk: 'text-red-500',
}

function AgentCard({
  name,
  result,
  index,
}: {
  name: string
  result: AgentResult
  index: number
}) {
  const [isOpen, setIsOpen] = useState(false)
  const Icon = agentIcons[name] || BarChart3
  const colorClass = agentColors[name] || 'text-primary'

  return (
    <motion.div
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: index * 0.05 }}
    >
      <Collapsible open={isOpen} onOpenChange={setIsOpen}>
        <Card className="border-border bg-card">
          <CardHeader className="pb-3">
            <div className="flex items-start justify-between">
              <div className="flex items-center gap-3">
                <div className={cn('rounded-lg bg-muted p-2', colorClass)}>
                  <Icon className="h-5 w-5" />
                </div>
                <div>
                  <CardTitle className="text-base">{result.name}</CardTitle>
                  <Badge variant="outline" className="mt-1 text-xs">
                    {result.scenario.replace('_', ' ')}
                  </Badge>
                </div>
              </div>
              <SignalBadge direction={result.signal as SignalDirection} size="sm" />
            </div>
          </CardHeader>
          <CardContent className="space-y-4">
            {/* Confidence Bar */}
            <div>
              <div className="mb-1 flex justify-between text-xs">
                <span className="text-muted-foreground">Confidence</span>
                <span className="font-mono font-medium">
                  {Math.round(result.confidence * 100)}%
                </span>
              </div>
              <Progress value={result.confidence * 100} className="h-2" />
            </div>

            {/* Weighted Score */}
            {result.weighted_score > 0 && (
              <div className="flex items-center justify-between rounded-lg bg-muted/50 px-3 py-2">
                <span className="text-sm text-muted-foreground">Weighted Score</span>
                <div className="flex items-center gap-2">
                  <span className="font-mono text-sm font-semibold">
                    {(result.weighted_score * 100).toFixed(1)}%
                  </span>
                  <div className="h-2 w-16 rounded-full bg-muted">
                    <div
                      className="h-full rounded-full bg-primary transition-all"
                      style={{ width: `${result.weighted_score * 100}%` }}
                    />
                  </div>
                </div>
              </div>
            )}

            {/* Key Insights */}
            <div>
              <h4 className="mb-2 text-xs font-medium uppercase text-muted-foreground">
                Key Insights
              </h4>
              <ul className="space-y-1">
                {result.insights.map((insight, i) => (
                  <li key={i} className="flex items-start gap-2 text-sm">
                    <span className="mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full bg-primary" />
                    <span className="text-muted-foreground">{insight}</span>
                  </li>
                ))}
              </ul>
            </div>

            {/* Expandable Full Analysis */}
            {result.full_analysis && (
              <CollapsibleTrigger asChild>
                <button className="flex w-full items-center justify-between rounded-lg border border-border px-3 py-2 text-sm hover:bg-muted/50">
                  <span>Full Analysis</span>
                  <ChevronDown
                    className={cn(
                      'h-4 w-4 transition-transform',
                      isOpen && 'rotate-180'
                    )}
                  />
                </button>
              </CollapsibleTrigger>
            )}
            <CollapsibleContent>
              {result.full_analysis && (
                <div className="rounded-lg bg-muted/50 p-3">
                  <p className="text-sm text-muted-foreground">{result.full_analysis}</p>
                </div>
              )}
            </CollapsibleContent>
          </CardContent>
        </Card>
      </Collapsible>
    </motion.div>
  )
}

export function AgentsTab({ analysis }: AgentsTabProps) {
  const agentEntries = Object.entries(analysis.agent_results).filter(
    ([name]) => name !== 'education'
  )

  return (
    <div className="space-y-6">
      {/* Weight Adjustment Info */}
      <Card className="border-border bg-muted/30">
        <CardContent className="p-4">
          <div className="flex items-center gap-3">
            <div className="rounded-lg bg-primary/10 p-2">
              <Activity className="h-5 w-5 text-primary" />
            </div>
            <div>
              <p className="text-sm font-medium">Dynamic Weight Adjustment</p>
              <p className="text-xs text-muted-foreground">
                Agent weights were adjusted based on the {analysis.market_scenario.replace('_', ' ').toLowerCase()} market scenario
              </p>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Agent Grid */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        {agentEntries.map(([name, result], index) => (
          <AgentCard key={name} name={name} result={result} index={index} />
        ))}
      </div>
    </div>
  )
}
