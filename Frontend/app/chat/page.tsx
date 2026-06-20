'use client'

import { useCallback, useEffect, useRef, useState } from 'react'
import { useRouter } from 'next/navigation'
import { AnimatePresence, motion } from 'framer-motion'
import {
  Activity,
  CheckCircle2,
  ChevronDown,
  Clock3,
  FileText,
  LineChart,
  MessageSquareText,
  Plus,
  Search,
  Send,
  ShieldCheck,
  Sparkles,
  TrendingUp,
} from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Textarea } from '@/components/ui/textarea'
import { Card, CardContent } from '@/components/ui/card'
import { ScrollArea } from '@/components/ui/scroll-area'
import { Spinner } from '@/components/ui/spinner'
import { SignalBadge } from '@/components/analysis/signal-badge'
import { ConfidenceMeter } from '@/components/analysis/confidence-meter'
import { MarkdownRenderer } from '@/components/ui/markdown-renderer'
import { getChatThread, listChatThreads, sendChat, streamChat } from '@/lib/api/client'
import type { ChatProgressEvent, ChatResponse, ChatThreadSummary } from '@/lib/api/types'
import { useSession } from '@/providers/session-provider'

interface Message {
  id: string
  role: 'user' | 'assistant'
  content: string
  data?: ChatResponse
}

interface LoadingPhase {
  label: string
  detail: string
  icon: React.ElementType
  meta?: string
}

const starterPrompts = [
  'Price of TSLA',
  'Analyze AAPL',
  'NVDA options flow',
  'Risk-managed SPY setup',
]

const visibleProgressTools = new Set([
  'analyze_stock',
  'get_quote',
  'get_market_trends',
  'portfolio_analysis',
  'buy_option',
  'buy_multiple_options',
])

function progressToPhase(event?: ChatProgressEvent): LoadingPhase {
  if (!event) {
    return {
      label: 'Connecting',
      detail: 'Opening a live progress stream with Oracle.',
      icon: Activity,
    }
  }

  const stage = event.stage || ''
  const tool = event.tool || ''
  const icon =
    stage === 'routing' ? Search
      : tool === 'analyze_stock' ? LineChart
        : tool === 'get_quote' ? Activity
          : tool === 'portfolio_analysis' ? ShieldCheck
            : stage === 'write_response' ? FileText
              : Sparkles

  return {
    label: event.label || 'Working',
    detail: event.detail || 'Oracle is processing the request.',
    icon,
    meta: event.tool ? event.tool.replaceAll('_', ' ') : event.stage?.replaceAll('_', ' '),
  }
}

function shouldShowProgressCard(event?: ChatProgressEvent) {
  if (!event) return false
  if (event.stage === 'tool_start' || event.stage === 'tool_complete') {
    return Boolean(event.tool && visibleProgressTools.has(event.tool))
  }
  if (event.stage === 'tools_selected') {
    return Boolean(event.tools?.some((tool) => visibleProgressTools.has(tool)))
  }
  if (event.stage === 'fallback') return true
  return false
}

function CompactTypingBubble() {
  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -6 }}
      className="mx-auto flex w-full max-w-3xl px-4"
    >
      <div className="min-w-0 flex-1">
        <div className="inline-flex items-center gap-1.5 rounded-2xl border border-border bg-muted px-3 py-2">
          {[0, 1, 2].map((dot) => (
            <motion.span
              key={dot}
              className="h-1.5 w-1.5 rounded-full bg-muted-foreground"
              animate={{ opacity: [0.35, 1, 0.35] }}
              transition={{
                duration: 0.9,
                repeat: Infinity,
                delay: dot * 0.14,
                ease: 'easeInOut',
              }}
            />
          ))}
        </div>
      </div>
    </motion.div>
  )
}

function TypingBubble({
  phase,
}: {
  phase: LoadingPhase
}) {
  const Icon = phase.icon

  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -6 }}
      className="mx-auto flex w-full max-w-3xl px-4"
    >
      <div className="min-w-0 flex-1">
        <div className="w-full max-w-md rounded-2xl border border-border bg-card px-4 py-3 shadow-sm">
          <div className="flex items-start gap-3">
            <div className="mt-0.5 flex h-8 w-8 shrink-0 items-center justify-center rounded-xl bg-primary/10 text-primary">
              <Icon className="h-4 w-4" />
            </div>
            <div className="min-w-0 flex-1">
              <div className="flex items-center justify-between gap-3">
                <span className="text-sm font-medium text-foreground">{phase.label}</span>
                {phase.meta && <span className="text-[11px] text-muted-foreground">{phase.meta}</span>}
              </div>
              <p className="mt-0.5 text-xs leading-5 text-muted-foreground">{phase.detail}</p>
              <div className="mt-3 h-1 overflow-hidden rounded-full bg-muted">
                <motion.div
                  className="h-full rounded-full bg-primary"
                  initial={{ x: '-100%' }}
                  animate={{ x: '100%' }}
                  transition={{ duration: 1.15, ease: 'easeInOut', repeat: Infinity }}
                  style={{ width: '55%' }}
                />
              </div>
            </div>
          </div>
        </div>
      </div>
    </motion.div>
  )
}

const runningAnalysisSteps = [
  { name: 'technical', label: 'Technical', detail: 'Price levels, trend, RSI, MACD, volume' },
  { name: 'flow', label: 'Options flow', detail: 'Chain volume, put/call, liquidity' },
  { name: 'sentiment', label: 'Sentiment', detail: 'News, StockTwits, market proxies' },
  { name: 'history', label: 'History', detail: 'Recent pattern, volatility, key levels' },
  { name: 'risk', label: 'Risk', detail: 'Confidence gate and contract safety' },
  { name: 'education', label: 'Trade brief', detail: 'Decision context and explanation' },
]

type AgentProgressState = Record<string, 'pending' | 'active' | 'done' | 'failed'>

function AnalysisRunningTrace({
  symbol,
  progress,
}: {
  symbol?: string
  progress: AgentProgressState
}) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -6 }}
      className="mx-auto flex w-full max-w-3xl px-4"
    >
      <div className="w-full rounded-2xl border border-border bg-card p-3 shadow-sm">
        <div className="mb-3 flex items-center justify-between gap-3 px-1">
          <div className="flex items-center gap-2">
            <div className="flex h-7 w-7 items-center justify-center rounded-xl bg-primary/10 text-primary">
              <LineChart className="h-4 w-4" />
            </div>
            <div>
              <div className="text-sm font-medium">Analyzing {symbol || 'ticker'}</div>
              <div className="text-xs text-muted-foreground">Building the option-trade evidence packet</div>
            </div>
          </div>
          <Spinner className="h-4 w-4 text-primary" />
        </div>
        <div className="grid gap-2 md:grid-cols-2">
          {runningAnalysisSteps.map((step) => {
            const status = progress[step.name] || 'pending'
            const done = status === 'done'
            const active = status === 'active'
            const failed = status === 'failed'

            return (
              <div
                key={step.name}
                className={[
                  'rounded-xl border px-3 py-2.5 transition-colors',
                  failed
                    ? 'border-red-400/30 bg-red-500/8'
                    : active
                    ? 'border-primary/35 bg-primary/10'
                    : done
                      ? 'border-emerald-500/25 bg-emerald-500/10'
                      : 'border-border bg-muted/30',
                ].join(' ')}
              >
                <div className="flex items-start gap-2.5">
                  <div className={[
                    'mt-0.5 flex h-5 w-5 shrink-0 items-center justify-center rounded-full',
                    failed ? 'bg-red-500/15 text-red-600 dark:text-red-300' : done ? 'bg-emerald-500/15 text-emerald-600 dark:text-emerald-300' : active ? 'bg-primary/15 text-primary' : 'bg-muted text-muted-foreground',
                  ].join(' ')}
                  >
                    {done ? <CheckCircle2 className="h-3.5 w-3.5" /> : active ? <Spinner className="h-3.5 w-3.5" /> : <span className="h-1.5 w-1.5 rounded-full bg-current" />}
                  </div>
                  <div className="min-w-0">
                    <div className="text-xs font-medium text-foreground">{step.label}</div>
                    <div className="mt-0.5 text-[11px] leading-4 text-muted-foreground">{step.detail}</div>
                  </div>
                </div>
              </div>
            )
          })}
        </div>
      </div>
    </motion.div>
  )
}

function ToolLoadingBubble({
  event,
  phase,
  analysisProgress,
}: {
  event?: ChatProgressEvent
  phase: LoadingPhase
  analysisProgress: AgentProgressState
}) {
  const tools = event?.tools || []
  const isAnalysis = event?.tool === 'analyze_stock' || tools.includes('analyze_stock')

  if (isAnalysis) {
    return <AnalysisRunningTrace symbol={event?.symbol} progress={analysisProgress} />
  }

  return <TypingBubble phase={phase} />
}

function formatMoney(value: unknown) {
  const number = Number(value)
  if (!Number.isFinite(number)) return 'unavailable'
  return `$${number.toLocaleString(undefined, { maximumFractionDigits: 2 })}`
}

function formatNumber(value: unknown, digits = 2) {
  const number = Number(value)
  if (!Number.isFinite(number)) return 'unavailable'
  return number.toFixed(digits)
}

function formatCompact(value: unknown) {
  const number = Number(value)
  if (!Number.isFinite(number)) return 'unavailable'
  return Intl.NumberFormat(undefined, { notation: 'compact', maximumFractionDigits: 1 }).format(number)
}

function getAnalysisSteps(analysis: any) {
  const agents = analysis.agent_results || {}
  const technical = agents.technical || {}
  const flow = agents.flow || {}
  const sentiment = agents.sentiment || {}
  const history = agents.history || {}
  const tradeDecision = analysis.trade_decision || {}
  const signal = analysis.signal || {}
  const snapshot = technical.market_data_snapshot || {}
  const levels = technical.support_resistance || {}
  const flowMetrics = flow.metrics || {}

  return [
    {
      name: 'technical',
      label: 'Technical',
      checked: `Price ${formatMoney(signal.current_price || snapshot.current_price)} near support ${formatMoney(levels.support?.[0])}; RSI ${formatNumber(snapshot.rsi, 1)}, MACD ${formatNumber(snapshot.macd, 2)} vs signal ${formatNumber(snapshot.macd_signal, 2)}.`,
      result: `${technical.scenario || analysis.market_scenario || 'Market'} read, score ${formatNumber(technical.weighted_score, 2)}, confidence ${formatNumber((technical.confidence || 0) * 100, 0)}%.`,
    },
    {
      name: 'flow',
      label: 'Options flow',
      checked: `Put/call ${formatNumber(flowMetrics.put_call_ratio, 2)} with ${formatCompact(flowMetrics.call_volume)} calls and ${formatCompact(flowMetrics.put_volume)} puts.`,
      result: `${flow.flow_sentiment || 'neutral'} chain bias; confirmed unusual activity: ${flow.unusual_activity ? 'yes' : 'no'}.`,
    },
    {
      name: 'sentiment',
      label: 'Sentiment',
      checked: `News, StockTwits, and market proxy read: score ${formatNumber(sentiment.aggregate_score, 2)}, trend ${sentiment.sentiment_trend || 'unknown'}.`,
      result: `Sentiment confidence ${formatNumber((sentiment.confidence || 0) * 100, 0)}%.`,
    },
    {
      name: 'history',
      label: 'History',
      checked: `Pattern ${history.dominant_pattern || 'unknown'} with support ${formatMoney(history.key_levels?.support?.[0])} and resistance ${formatMoney(history.key_levels?.resistance?.[0])}.`,
      result: `Historical score ${formatNumber(history.pattern_score, 2)}, confidence ${formatNumber((history.confidence || 0) * 100, 0)}%.`,
    },
    {
      name: 'risk',
      label: 'Risk',
      checked: `Trade gate checked signal confidence ${formatNumber((signal.confidence || 0) * 100, 1)}% and available real option candidates.`,
      result: tradeDecision.rationale?.[0] || 'Risk check completed.',
    },
    {
      name: 'setup',
      label: 'Trade setup',
      checked: `Decision ${tradeDecision.decision || 'NO_TRADE'}; direction ${tradeDecision.direction || 'neutral'}.`,
      result: tradeDecision.entry_trigger || 'Wait for a cleaner setup.',
    },
  ]
}

function AgentTrace({ analysis }: { analysis: any }) {
  const steps = getAnalysisSteps(analysis)

  return (
    <div className="mt-4 rounded-2xl border border-border bg-card p-3 shadow-sm">
      <div className="mb-3 flex items-center justify-between gap-3 px-1">
        <div className="flex items-center gap-2">
          <div className="flex h-7 w-7 items-center justify-center rounded-xl bg-primary/10 text-primary">
            <TrendingUp className="h-4 w-4" />
          </div>
          <span className="text-sm font-medium">Analysis run</span>
        </div>
        <span className="text-xs text-muted-foreground">{steps.length} checks</span>
      </div>
      <div className="space-y-2">
        {steps.map((step, index) => (
          <motion.div
            key={step.name}
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: index * 0.08, duration: 0.22 }}
            className="rounded-xl border border-border bg-muted/30 px-3 py-3"
          >
            <div className="flex items-start gap-3">
              <div className="mt-0.5 flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-emerald-500/15 text-emerald-600 dark:text-emerald-300">
                <CheckCircle2 className="h-3.5 w-3.5" />
              </div>
              <div className="min-w-0 flex-1">
                <div className="text-sm font-medium text-foreground">{step.label}</div>
                <p className="mt-1 text-xs leading-5 text-muted-foreground">{step.checked}</p>
                <p className="mt-1 text-xs leading-5 text-foreground/85">{step.result}</p>
              </div>
            </div>
          </motion.div>
        ))}
      </div>
    </div>
  )
}

function AnalysisCard({ data }: { data: ChatResponse }) {
  if (!data.data?.analysis_result) return null

  const analysis = data.data.analysis_result
  const signal = analysis.signal

  return (
    <Card className="mt-4 max-w-2xl overflow-hidden rounded-2xl border-border bg-card shadow-sm">
      <CardContent className="p-4">
        <div className="mb-3 flex flex-wrap items-center justify-between gap-3">
          <div className="flex items-center gap-3">
            <span className="font-mono text-lg font-semibold">{analysis.symbol}</span>
            <SignalBadge direction={signal.direction} size="md" />
          </div>
          <ConfidenceMeter value={signal.confidence} size="sm" />
        </div>
        <p className="text-sm leading-6 text-muted-foreground">{signal.reasoning}</p>
        <AgentTrace analysis={analysis} />
      </CardContent>
    </Card>
  )
}

function MessageRow({ message }: {
  message: Message
}) {
  if (message.role === 'user') {
    return (
      <motion.div
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        className="mx-auto flex w-full max-w-3xl justify-end px-4"
      >
        <div className="max-w-[78%] rounded-2xl rounded-tr-md bg-primary px-4 py-2.5 text-sm leading-6 text-primary-foreground shadow-sm">
          {message.content}
        </div>
      </motion.div>
    )
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      className="mx-auto flex w-full max-w-3xl px-4"
    >
      <div className="min-w-0 flex-1">
        <div className="prose-chat max-w-none text-sm leading-7 text-foreground">
          <MarkdownRenderer content={message.content} />
        </div>
        {message.data && <AnalysisCard data={message.data} />}
      </div>
    </motion.div>
  )
}

function buildMessageData(content: string, metadata?: Record<string, any>): ChatResponse | undefined {
  if (!metadata || !metadata.intent) return undefined
  return {
    response: content,
    intent: metadata.intent,
    symbol: metadata.symbol,
    confidence: metadata.confidence,
    data: metadata.data,
    actions: metadata.actions,
    suggestions: metadata.suggestions || [],
    agents_triggered: metadata.agents_triggered || [],
    thread_id: metadata.thread_id,
    timestamp: metadata.timestamp || Date.now(),
  }
}

export default function ChatPage() {
  const router = useRouter()
  const { isReady: sessionReady } = useSession()
  const [messages, setMessages] = useState<Message[]>([])
  const [threads, setThreads] = useState<ChatThreadSummary[]>([])
  const [activeThreadId, setActiveThreadId] = useState<string | undefined>()
  const [historyOpen, setHistoryOpen] = useState(false)
  const [input, setInput] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [isLoadingThread, setIsLoadingThread] = useState(false)
  const [progressEvent, setProgressEvent] = useState<ChatProgressEvent | undefined>()
  const [hasToolProgress, setHasToolProgress] = useState(false)
  const [analysisProgress, setAnalysisProgress] = useState<AgentProgressState>({})
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const historyMenuRef = useRef<HTMLDivElement>(null)
  const loadingPhase = progressToPhase(progressEvent)

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth', block: 'end' })
  }, [messages, isLoading, progressEvent])

  const refreshThreads = useCallback(async () => {
    if (!sessionReady) return
    try {
      setThreads(await listChatThreads())
    } catch {
      setThreads([])
    }
  }, [sessionReady])

  useEffect(() => {
    refreshThreads()
  }, [refreshThreads])

  useEffect(() => {
    if (!historyOpen) return

    const handlePointerDown = (event: PointerEvent) => {
      if (!historyMenuRef.current?.contains(event.target as Node)) {
        window.setTimeout(() => setHistoryOpen(false), 0)
      }
    }

    const handleEscape = (event: KeyboardEvent) => {
      if (event.key === 'Escape') {
        setHistoryOpen(false)
      }
    }

    document.addEventListener('pointerdown', handlePointerDown)
    document.addEventListener('keydown', handleEscape)
    return () => {
      document.removeEventListener('pointerdown', handlePointerDown)
      document.removeEventListener('keydown', handleEscape)
    }
  }, [historyOpen])

  const handleNewChat = () => {
    setActiveThreadId(undefined)
    setHistoryOpen(false)
    setMessages([])
    setInput('')
    router.replace('/chat')
  }

  const handleOpenThread = useCallback(async (threadId: string) => {
    if (isLoading) return
    setIsLoadingThread(true)
    try {
      const thread = await getChatThread(threadId)
      setActiveThreadId(thread.id)
      setHistoryOpen(false)
      setMessages(thread.messages.map((message) => ({
        id: message.id,
        role: message.role,
        content: message.content,
        data: message.role === 'assistant' ? buildMessageData(message.content, message.metadata) : undefined,
      })))
    } catch {
      setHistoryOpen(false)
      setMessages([{
        id: crypto.randomUUID(),
        role: 'assistant',
        content: 'I could not open that saved chat. Please refresh and try again.',
      }])
    } finally {
      setIsLoadingThread(false)
    }
  }, [isLoading])

  const openThreadFromHistory = useCallback((threadId: string) => {
    router.push(`/chat?thread=${encodeURIComponent(threadId)}`)
    void handleOpenThread(threadId)
  }, [handleOpenThread, router])

  useEffect(() => {
    if (!sessionReady) return
    const threadId = new URLSearchParams(window.location.search).get('thread')
    if (threadId && threadId !== activeThreadId) {
      void handleOpenThread(threadId)
    }
  }, [activeThreadId, handleOpenThread, sessionReady])

  const handleSend = async (text?: string) => {
    const messageText = (text || input).trim()
    if (!messageText || isLoading || !sessionReady) return

    setMessages((previous) => [
      ...previous,
      { id: crypto.randomUUID(), role: 'user', content: messageText },
    ])
    setInput('')
    setIsLoading(true)
    setProgressEvent(undefined)
    setHasToolProgress(false)
    setAnalysisProgress({})

    try {
      let response: ChatResponse
      try {
        response = await streamChat(messageText, (event) => {
          if (event.event === 'progress') {
            if (event.tool === 'analyze_stock' && event.stage === 'agent_start' && event.agent) {
              setAnalysisProgress((previous) => ({
                ...previous,
                [event.agent as string]: 'active',
              }))
            }
            if (event.tool === 'analyze_stock' && event.stage === 'agent_complete' && event.agent) {
              setAnalysisProgress((previous) => ({
                ...previous,
                [event.agent as string]: event.success === false ? 'failed' : 'done',
              }))
            }
            if (shouldShowProgressCard(event)) {
              setHasToolProgress(true)
              setProgressEvent(event)
            }
          }
        }, undefined, activeThreadId)
      } catch {
        setHasToolProgress(true)
        setProgressEvent({
          event: 'progress',
          stage: 'fallback',
          label: 'Using standard request',
          detail: 'Progress updates were unavailable, so Oracle is waiting for the normal chat response.',
        })
        response = await sendChat(messageText, undefined, activeThreadId)
      }

      if (response.thread_id) {
        setActiveThreadId(response.thread_id)
      }
      setMessages((previous) => [
        ...previous,
        {
          id: crypto.randomUUID(),
          role: 'assistant',
          content: response.response,
          data: response,
        },
      ])
      await refreshThreads()
    } catch {
      setMessages((previous) => [
        ...previous,
        {
          id: crypto.randomUUID(),
          role: 'assistant',
          content: 'Oracle is temporarily unavailable. Please try again.',
        },
      ])
    } finally {
      setIsLoading(false)
      setProgressEvent(undefined)
      setHasToolProgress(false)
      setAnalysisProgress({})
    }
  }

  const handleKeyDown = (event: React.KeyboardEvent) => {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault()
      handleSend()
    }
  }

  return (
    <div className="flex h-screen min-h-[640px] flex-col overflow-hidden rounded-none border-border/70 bg-background text-foreground">
      <header className="relative z-50 flex h-14 shrink-0 items-center justify-between border-b border-border bg-background/95 px-4 backdrop-blur md:px-6">
        <div className="flex items-center">
          <h1 className="text-sm font-semibold">Oracle</h1>
        </div>
        <div className="flex items-center gap-2">
          <div ref={historyMenuRef}>
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setHistoryOpen((open) => !open)}
              className="hidden gap-2 rounded-full border border-border bg-card hover:bg-muted sm:flex"
            >
              <Clock3 className="h-4 w-4" />
              History
            </Button>
            {historyOpen && (
              <motion.div
                initial={{ opacity: 0, y: -6, scale: 0.98 }}
                animate={{ opacity: 1, y: 0, scale: 1 }}
                exit={{ opacity: 0, y: -6, scale: 0.98 }}
                className="fixed right-6 top-16 z-[100] hidden w-[360px] overflow-hidden rounded-2xl border border-border bg-popover text-popover-foreground shadow-xl md:block"
              >
                <div className="flex items-center justify-between border-b border-border px-3 py-3">
                  <div>
                    <div className="text-sm font-medium">Chat history</div>
                    <div className="text-xs text-muted-foreground">Open a previous Oracle thread</div>
                  </div>
                  <button
                    onClick={handleNewChat}
                    className="flex h-8 w-8 items-center justify-center rounded-full border border-border bg-card text-muted-foreground hover:bg-muted hover:text-foreground"
                    aria-label="New chat"
                  >
                    <Plus className="h-4 w-4" />
                  </button>
                </div>
                <ScrollArea className="max-h-96">
                  <div className="space-y-1 p-2">
                    {threads.length === 0 ? (
                      <div className="rounded-xl border border-dashed border-border px-3 py-6 text-center text-xs leading-5 text-muted-foreground">
                        Previous chats will appear here.
                      </div>
                    ) : (
                      threads.map((thread) => (
                        <button
                          type="button"
                          key={thread.id}
                          onClick={(event) => {
                            event.stopPropagation()
                            openThreadFromHistory(thread.id)
                          }}
                          disabled={isLoadingThread}
                          className={[
                            'block w-full cursor-pointer rounded-xl px-3 py-3 text-left transition-colors disabled:cursor-wait disabled:opacity-70',
                            activeThreadId === thread.id
                              ? 'bg-primary/10 text-foreground'
                              : 'text-muted-foreground hover:bg-muted hover:text-foreground',
                          ].join(' ')}
                        >
                          <div className="flex items-start gap-2">
                            <MessageSquareText className="mt-0.5 h-4 w-4 shrink-0" />
                            <div className="min-w-0">
                              <div className="truncate text-sm font-medium">{thread.title}</div>
                              {thread.last_message_preview && (
                                <div className="mt-1 line-clamp-2 text-xs leading-4 text-muted-foreground">
                                  {thread.last_message_preview}
                                </div>
                              )}
                            </div>
                          </div>
                        </button>
                      ))
                    )}
                  </div>
                </ScrollArea>
              </motion.div>
            )}
          </div>
          <Button
            variant="ghost"
            size="sm"
            onClick={handleNewChat}
            className="hidden gap-2 rounded-full border border-border bg-card hover:bg-muted sm:flex"
          >
            <Plus className="h-4 w-4" />
            New chat
          </Button>
        </div>
      </header>

      <div className="relative z-0 flex min-h-0 flex-1">
        <ScrollArea className="min-h-0 flex-1">
          {messages.length === 0 ? (
            <div className="mx-auto flex min-h-full w-full max-w-3xl flex-col items-center justify-center px-4 py-12 text-center">
            <h2 className="max-w-2xl text-balance text-3xl font-semibold tracking-tight md:text-4xl">
              How can I help?
            </h2>
            <p className="mt-4 max-w-xl text-sm leading-6 text-muted-foreground">
              Ask for a quote, analysis, or options setup.
            </p>
            <div className="mt-8 grid w-full max-w-2xl gap-2 sm:grid-cols-2">
              {starterPrompts.map((prompt) => (
                <button
                  key={prompt}
                  onClick={() => handleSend(prompt)}
                  className="group rounded-2xl border border-border bg-card px-4 py-3 text-left text-sm transition-colors hover:bg-muted"
                >
                  <div className="flex items-center justify-between gap-3">
                    <span>{prompt}</span>
                    <ChevronDown className="-rotate-90 h-4 w-4 text-muted-foreground transition-colors group-hover:text-foreground" />
                  </div>
                </button>
              ))}
            </div>
            </div>
          ) : (
            <div className="space-y-8 py-8">
            <AnimatePresence initial={false}>
              {messages.map((message) => (
                <MessageRow key={message.id} message={message} />
              ))}
              {isLoading && (
                hasToolProgress ? (
                  <ToolLoadingBubble event={progressEvent} phase={loadingPhase} analysisProgress={analysisProgress} />
                ) : (
                  <CompactTypingBubble />
                )
              )}
            </AnimatePresence>
            <div ref={messagesEndRef} />
            </div>
          )}
        </ScrollArea>
      </div>

      <div className="relative z-10 shrink-0 border-t border-border bg-background/95 px-4 py-4 backdrop-blur">
        <div className="mx-auto max-w-3xl">
          <div className="rounded-3xl border border-border bg-card p-2 shadow-sm transition-colors focus-within:border-ring">
            <div className="flex items-end gap-2">
              <Textarea
                value={input}
                onChange={(event) => setInput(event.target.value)}
                onKeyDown={handleKeyDown}
                placeholder="Message Oracle..."
                className="max-h-40 min-h-12 resize-none border-0 bg-transparent px-3 py-3 shadow-none focus-visible:ring-0"
                rows={1}
              />
              <Button
                onClick={() => handleSend()}
                disabled={!input.trim() || isLoading || !sessionReady}
                className="mb-1 h-10 w-10 shrink-0 rounded-2xl bg-primary p-0 text-primary-foreground shadow-sm hover:bg-primary/90"
                aria-label="Send message"
              >
                {isLoading ? <Spinner className="h-4 w-4" /> : <Send className="h-4 w-4" />}
              </Button>
            </div>
          </div>
          <p className="mt-2 text-center text-[11px] text-muted-foreground">
            Oracle can be wrong. Verify live prices and risk before trading.
          </p>
        </div>
      </div>
    </div>
  )
}
