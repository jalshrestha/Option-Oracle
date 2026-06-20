'use client'

import { Cpu, Database, Server, Wifi } from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Skeleton } from '@/components/ui/skeleton'
import { useSystemHealth, useLLMProvider } from '@/lib/hooks/use-api'
import { cn } from '@/lib/utils'
import type { ServiceStatus } from '@/lib/api/types'

function StatusDot({ status }: { status: ServiceStatus }) {
  return (
    <div
      className={cn(
        'h-2 w-2 rounded-full',
        (status === 'healthy' || status === 'configured') && 'bg-green-500',
        (status === 'degraded' || status === 'disabled' || status === 'unconfigured') &&
          'bg-amber-500',
        status === 'unhealthy' && 'bg-red-500'
      )}
    />
  )
}

function HealthRow({
  icon: Icon,
  label,
  status,
  detail,
}: {
  icon: typeof Server
  label: string
  status: ServiceStatus
  detail?: string
}) {
  return (
    <div className="flex items-center justify-between rounded-lg bg-muted/50 px-3 py-2">
      <div className="flex min-w-0 items-center gap-2">
        <Icon className="h-4 w-4 shrink-0 text-muted-foreground" />
        <span className="truncate text-sm text-muted-foreground">{label}</span>
      </div>
      <div className="flex shrink-0 items-center gap-2">
        <StatusDot status={status} />
        <span className="max-w-28 truncate text-xs capitalize text-muted-foreground">
          {detail ?? status}
        </span>
      </div>
    </div>
  )
}

export function SystemHealthCard() {
  const { data: health, isLoading: healthLoading, error: healthError } = useSystemHealth()
  const { data: llmProvider, isLoading: llmLoading, error: llmError } = useLLMProvider()

  const isLoading = healthLoading || llmLoading
  const apiStatus = health?.components.api?.status ?? (healthError ? 'unhealthy' : 'disabled')
  const databaseStatus = health?.components.database?.status ?? 'disabled'
  const redisStatus = health?.components.redis?.status ?? 'disabled'
  const llmStatus =
    health?.components.external_services?.openai?.status ??
    health?.components.external_services?.gemini?.status ??
    (llmError ? 'unhealthy' : 'unconfigured')
  const llmLabel = llmProvider?.provider ?? 'LLM'

  return (
    <Card className="glass dark:glass border-border">
      <CardHeader className="flex flex-row items-center justify-between pb-2">
        <CardTitle className="flex items-center gap-2 text-sm font-medium">
          <Server className="h-4 w-4 text-primary" />
          System Health
        </CardTitle>
        <StatusDot status={health?.overall_status ?? (healthError ? 'unhealthy' : 'disabled')} />
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
            <HealthRow icon={Server} label="API" status={apiStatus} />
            <HealthRow icon={Database} label="Database" status={databaseStatus} />
            <HealthRow icon={Wifi} label="Redis" status={redisStatus} />
            <HealthRow icon={Cpu} label={llmLabel} status={llmStatus} detail={llmStatus} />
          </>
        )}
      </CardContent>
    </Card>
  )
}
