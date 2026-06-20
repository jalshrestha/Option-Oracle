'use client'

import { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  CardDescription,
} from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Switch } from '@/components/ui/switch'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Progress } from '@/components/ui/progress'
import { Label } from '@/components/ui/label'
import { Skeleton } from '@/components/ui/skeleton'
import {
  Activity,
  Cpu,
  CheckCircle,
  AlertCircle,
  RefreshCw,
  Settings,
  Zap,
  Server,
  MemoryStick,
  TrendingUp,
  Moon,
  Sun,
  Bell,
} from 'lucide-react'
import { useSystemHealth, useSystemMetrics, useLLMProvider } from '@/lib/hooks/use-api'
import { getSystemConfig } from '@/lib/api/client'
import useSWR from 'swr'

// Static architectural agents — these are real, just not queryable at runtime
const AGENTS = [
  { id: 'technical', name: 'Technical Analysis Agent', model: 'GPT-4o', weight: '60%' },
  { id: 'sentiment', name: 'Sentiment Analysis Agent', model: 'GPT-4o-mini', weight: '10%' },
  { id: 'flow', name: 'Options Flow Agent', model: 'GPT-4o-mini', weight: '10%' },
  { id: 'historical', name: 'Historical Pattern Agent', model: 'GPT-4o', weight: '20%' },
  { id: 'risk', name: 'Risk Management Agent', model: 'GPT-4o', weight: '—' },
]

function statusColor(status: string) {
  if (status === 'healthy' || status === 'configured') return 'text-green-500'
  if (status === 'degraded' || status === 'disabled' || status === 'unconfigured') {
    return 'text-amber-500'
  }
  return 'text-red-500'
}

export default function SystemPage() {
  const [isRefreshing, setIsRefreshing] = useState(false)
  const [autoRefresh, setAutoRefresh] = useState(true)

  const { data: health, mutate: refreshHealth } = useSystemHealth()
  const { data: metrics, mutate: refreshMetrics } = useSystemMetrics('performance')
  const { data: llm } = useLLMProvider()
  const { data: logs } = useSWR(
    'system-logs',
    () => getSystemConfig(),
    { refreshInterval: autoRefresh ? 15000 : 0 }
  )
  const overallStatus = health?.overall_status ?? 'unknown'
  const apiHealth = health?.components.api
  const databaseHealth = health?.components.database
  const externalServices = health?.components.external_services ?? {}

  async function handleRefresh() {
    setIsRefreshing(true)
    await Promise.all([refreshHealth(), refreshMetrics()])
    setIsRefreshing(false)
  }

  return (
    <div className="space-y-6 p-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">System Status</h1>
          <p className="text-muted-foreground">
            Monitor AI agents, API health, and system performance
          </p>
        </div>
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2">
            <Switch
              id="auto-refresh"
              checked={autoRefresh}
              onCheckedChange={setAutoRefresh}
            />
            <Label htmlFor="auto-refresh" className="text-sm">Auto-refresh</Label>
          </div>
          <Button variant="outline" onClick={handleRefresh} disabled={isRefreshing}>
            <RefreshCw className={`mr-2 h-4 w-4 ${isRefreshing ? 'animate-spin' : ''}`} />
            Refresh
          </Button>
        </div>
      </div>

      {/* Overview cards */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }}>
          <Card
            className={
              overallStatus === 'healthy'
                ? 'border-green-500/30 bg-green-500/10'
                : 'border-amber-500/30 bg-amber-500/10'
            }
          >
            <CardContent className="p-6">
              {!health ? (
                <Skeleton className="h-12 w-full" />
              ) : (
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <div className="rounded-lg bg-green-500/20 p-2">
                      {overallStatus === 'healthy' ? (
                        <CheckCircle className="h-5 w-5 text-green-500" />
                      ) : (
                        <AlertCircle className="h-5 w-5 text-amber-500" />
                      )}
                    </div>
                    <div>
                      <p className="text-sm text-muted-foreground">System Status</p>
                      <p className={`text-xl font-bold capitalize ${statusColor(overallStatus)}`}>
                        {overallStatus}
                      </p>
                    </div>
                  </div>
                  <div className="text-right">
                    <p className="text-2xl font-bold">{health.version ?? '—'}</p>
                    <p className="text-xs text-muted-foreground">Version</p>
                  </div>
                </div>
              )}
            </CardContent>
          </Card>
        </motion.div>

        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.1 }}>
          <Card className="border-border/50 bg-card/50">
            <CardContent className="p-6">
              {!metrics ? (
                <Skeleton className="h-12 w-full" />
              ) : (
                <div className="flex items-center gap-3">
                  <div className="rounded-lg bg-muted p-2">
                    <Cpu className="h-5 w-5 text-muted-foreground" />
                  </div>
                  <div className="flex-1">
                    <p className="text-sm text-muted-foreground">CPU Usage</p>
                    <p className="text-xl font-bold">{metrics.cpu_usage?.toFixed(1) ?? '—'}%</p>
                    <Progress value={metrics.cpu_usage ?? 0} className="mt-2 h-1.5" />
                  </div>
                </div>
              )}
            </CardContent>
          </Card>
        </motion.div>

        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.2 }}>
          <Card className="border-border/50 bg-card/50">
            <CardContent className="p-6">
              {!metrics ? (
                <Skeleton className="h-12 w-full" />
              ) : (
                <div className="flex items-center gap-3">
                  <div className="rounded-lg bg-muted p-2">
                    <MemoryStick className="h-5 w-5 text-muted-foreground" />
                  </div>
                  <div className="flex-1">
                    <p className="text-sm text-muted-foreground">Memory</p>
                    <p className="text-xl font-bold">{metrics.memory_usage?.toFixed(1) ?? '—'}%</p>
                    <Progress value={metrics.memory_usage ?? 0} className="mt-2 h-1.5" />
                  </div>
                </div>
              )}
            </CardContent>
          </Card>
        </motion.div>

        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.3 }}>
          <Card className="border-border/50 bg-card/50">
            <CardContent className="p-6">
              {!metrics ? (
                <Skeleton className="h-12 w-full" />
              ) : (
                <div className="flex items-center gap-3">
                  <div className="rounded-lg bg-muted p-2">
                    <Activity className="h-5 w-5 text-accent" />
                  </div>
                  <div>
                    <p className="text-sm text-muted-foreground">Analyses Today</p>
                    <p className="text-xl font-bold">{metrics.analyses_today ?? 0}</p>
                    <p className="text-xs text-muted-foreground">
                      {metrics.active_positions ?? 0} active positions
                    </p>
                  </div>
                </div>
              )}
            </CardContent>
          </Card>
        </motion.div>
      </div>

      <Tabs defaultValue="agents" className="space-y-6">
        <TabsList>
          <TabsTrigger value="agents" className="flex items-center gap-2">
            <Zap className="h-4 w-4" />
            AI Agents
          </TabsTrigger>
          <TabsTrigger value="health" className="flex items-center gap-2">
            <Server className="h-4 w-4" />
            Health
          </TabsTrigger>
          <TabsTrigger value="llm" className="flex items-center gap-2">
            <TrendingUp className="h-4 w-4" />
            LLM Provider
          </TabsTrigger>
        </TabsList>

        <TabsContent value="agents" className="space-y-4">
          <Card className="border-border/50 bg-card/50 backdrop-blur">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Zap className="h-5 w-5 text-accent" />
                AI Agent Architecture
              </CardTitle>
              <CardDescription>
                Five specialized agents that collaborate on every analysis
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {AGENTS.map((agent, i) => (
                  <motion.div
                    key={agent.id}
                    initial={{ opacity: 0, x: -20 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: i * 0.07 }}
                    className="flex items-center justify-between rounded-lg border border-border/50 bg-background/50 p-4"
                  >
                    <div className="flex items-center gap-4">
                      <div className="h-3 w-3 rounded-full bg-green-500 animate-pulse" />
                      <div>
                        <div className="font-medium">{agent.name}</div>
                        <div className="text-sm text-muted-foreground">{agent.model}</div>
                      </div>
                    </div>
                    <div className="flex items-center gap-4">
                      {agent.weight !== '—' && (
                        <div className="text-right">
                          <div className="text-sm font-medium">{agent.weight}</div>
                          <div className="text-xs text-muted-foreground">weight</div>
                        </div>
                      )}
                      <Badge className="bg-green-500/20 text-green-500">active</Badge>
                    </div>
                  </motion.div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="health" className="space-y-4">
          {!health ? (
            <Skeleton className="h-64 w-full" />
          ) : (
            <div className="grid gap-4 md:grid-cols-2">
              <Card className="border-border/50 bg-card/50">
                <CardHeader>
                  <CardTitle>Database</CardTitle>
                </CardHeader>
                <CardContent className="space-y-2">
                  <div className="flex justify-between">
                    <span className="text-sm text-muted-foreground">Status</span>
                    <span className={`text-sm font-medium capitalize ${statusColor(databaseHealth?.status ?? 'unhealthy')}`}>
                      {databaseHealth?.status ?? 'unknown'}
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-sm text-muted-foreground">Response Time</span>
                    <span className="text-sm font-mono">{databaseHealth?.response_time_ms ?? '—'}ms</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-sm text-muted-foreground">Connection Pool</span>
                    <span className="text-sm font-mono">{databaseHealth?.connection_pool ?? '—'}</span>
                  </div>
                </CardContent>
              </Card>

              <Card className="border-border/50 bg-card/50">
                <CardHeader>
                  <CardTitle>External Services</CardTitle>
                </CardHeader>
                <CardContent className="space-y-2">
                  {Object.entries(externalServices).map(([svc, service]) => (
                    <div key={svc} className="flex justify-between">
                      <span className="text-sm text-muted-foreground capitalize">{svc}</span>
                      <span className={`text-sm font-medium capitalize ${statusColor(service.status)}`}>
                        {service.status}
                      </span>
                    </div>
                  ))}
                </CardContent>
              </Card>

              <Card className="border-border/50 bg-card/50">
                <CardHeader>
                  <CardTitle>API Metrics</CardTitle>
                </CardHeader>
                <CardContent className="space-y-2">
                  <div className="flex justify-between">
                    <span className="text-sm text-muted-foreground">Response Time</span>
                    <span className="text-sm font-mono">{apiHealth?.response_time_ms?.toFixed(0) ?? '—'}ms</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-sm text-muted-foreground">Active Connections</span>
                    <span className="text-sm font-mono">{apiHealth?.active_connections ?? 0}</span>
                  </div>
                  {metrics && (
                    <div className="flex justify-between">
                      <span className="text-sm text-muted-foreground">Error Rate</span>
                      <span className="text-sm font-mono">{(metrics.error_rate * 100).toFixed(2)}%</span>
                    </div>
                  )}
                </CardContent>
              </Card>
            </div>
          )}
        </TabsContent>

        <TabsContent value="llm" className="space-y-4">
          {!llm ? (
            <Skeleton className="h-48 w-full" />
          ) : (
            <Card className="border-border/50 bg-card/50">
              <CardHeader>
                <CardTitle>LLM Provider</CardTitle>
                <CardDescription>Active AI model configuration</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="flex justify-between">
                  <span className="text-sm text-muted-foreground">Provider</span>
                  <Badge>{llm.provider}</Badge>
                </div>
                <div className="flex justify-between">
                  <span className="text-sm text-muted-foreground">Large Model</span>
                  <span className="text-sm font-mono">{llm.large_model}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-sm text-muted-foreground">Small Model</span>
                  <span className="text-sm font-mono">{llm.small_model}</span>
                </div>
              </CardContent>
            </Card>
          )}
        </TabsContent>
      </Tabs>
    </div>
  )
}
