'use client'

import { Server, Database, Cpu } from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Skeleton } from '@/components/ui/skeleton'
import { useSystemHealth, useLLMProvider } from '@/lib/hooks/use-api'
import { cn } from '@/lib/utils'

function StatusDot({ status }: { status: 'healthy' | 'degraded' | 'unhealthy' | string }) {
  return (
    <div
      className={cn(
        'h-2 w-2 rounded-full',
        status === 'healthy' && 'bg-green-500',
        status === 'degraded' && 'bg-amber-500',
        status === 'unhealthy' && 'bg-red-500'
      )}
    />
  )
}

export function SystemHealthCard() {
  const { data: health, isLoading: healthLoading } = useSystemHealth()
  const { data: llmProvider, isLoading: llmLoading } = useLLMProvider()

  const isLoading = healthLoading || llmLoading

  // Mock data for demo
  const displayHealth = health || {
    status: 'healthy',
    database: { status: 'healthy' },
  }

  const displayLLM = llmProvider || {
    provider: 'OpenAI',
    large_model: 'gpt-4o',
  }

  return (
    <Card className="glass dark:glass border-border">
      <CardHeader className="flex flex-row items-center justify-between pb-2">
        <CardTitle className="flex items-center gap-2 text-sm font-medium">
          <Server className="h-4 w-4 text-primary" />
          System Health
        </CardTitle>
        <StatusDot status={displayHealth.status} />
      </CardHeader>
      <CardContent className="space-y-3">
        {isLoading ? (
          <>
            <Skeleton className="h-8 w-full" />
            <Skeleton className="h-8 w-full" />
            <Skeleton className="h-8 w-full" />
          </>
        ) : (
          <>
            <div className="flex items-center justify-between rounded-lg bg-muted/50 px-3 py-2">
              <div className="flex items-center gap-2">
                <Server className="h-4 w-4 text-muted-foreground" />
                <span className="text-sm text-muted-foreground">API</span>
              </div>
              <div className="flex items-center gap-2">
                <StatusDot status={displayHealth.status} />
                <span className="text-xs capitalize text-muted-foreground">
                  {displayHealth.status}
                </span>
              </div>
            </div>
            <div className="flex items-center justify-between rounded-lg bg-muted/50 px-3 py-2">
              <div className="flex items-center gap-2">
                <Database className="h-4 w-4 text-muted-foreground" />
                <span className="text-sm text-muted-foreground">Database</span>
              </div>
              <div className="flex items-center gap-2">
                <StatusDot status={displayHealth.database?.status || 'healthy'} />
                <span className="text-xs capitalize text-muted-foreground">
                  {displayHealth.database?.status || 'healthy'}
                </span>
              </div>
            </div>
            <div className="flex items-center justify-between rounded-lg bg-muted/50 px-3 py-2">
              <div className="flex items-center gap-2">
                <Cpu className="h-4 w-4 text-muted-foreground" />
                <span className="text-sm text-muted-foreground">LLM</span>
              </div>
              <span className="font-mono text-xs text-primary">
                {displayLLM.provider}
              </span>
            </div>
          </>
        )}
      </CardContent>
    </Card>
  )
}
