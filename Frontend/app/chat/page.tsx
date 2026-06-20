'use client'

import { useEffect, useRef, useState } from 'react'
import { AnimatePresence, motion } from 'framer-motion'
import {
  Activity,
  Bot,
  Brain,
  ChevronDown,
  FileText,
  LineChart,
  Plus,
  Search,
  Send,
  ShieldCheck,
  Sparkles,
} from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Textarea } from '@/components/ui/textarea'
import { Badge } from '@/components/ui/badge'
import { Card, CardContent } from '@/components/ui/card'
import { ScrollArea } from '@/components/ui/scroll-area'
import { Spinner } from '@/components/ui/spinner'
import { SignalBadge } from '@/components/analysis/signal-badge'
import { ConfidenceMeter } from '@/components/analysis/confidence-meter'
import { MarkdownRenderer } from '@/components/ui/markdown-renderer'
import { sendChat, streamChat } from '@/lib/api/client'
import type { ChatProgressEvent, ChatResponse } from '@/lib/api/types'

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

function visibleSuggestions(suggestions: string[] = []) {
  const blocked = ['what are options', 'explain', 'education', 'quiz', 'learn']
  return suggestions
    .filter((suggestion) => {
      const lower = suggestion.toLowerCase()
      return !blocked.some((term) => lower.includes(term))
    })
    .slice(0, 3)
}

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

function AssistantAvatar() {
  return (
    <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full border border-white/10 bg-gradient-to-br from-sky-500 via-blue-500 to-emerald-400 text-white shadow-[0_0_24px_rgba(59,130,246,0.22)]">
      <Bot className="h-4 w-4" />
    </div>
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
      className="mx-auto flex w-full max-w-3xl gap-3 px-4"
    >
      <AssistantAvatar />
      <div className="min-w-0 flex-1">
        <div className="w-full max-w-md rounded-2xl border border-white/10 bg-white/[0.045] px-4 py-3 shadow-sm">
          <div className="flex items-start gap-3">
            <div className="mt-0.5 flex h-8 w-8 shrink-0 items-center justify-center rounded-xl bg-blue-500/12 text-blue-300">
              <Icon className="h-4 w-4" />
            </div>
            <div className="min-w-0 flex-1">
              <div className="flex items-center justify-between gap-3">
                <span className="text-sm font-medium text-foreground">{phase.label}</span>
                {phase.meta && <span className="text-[11px] text-muted-foreground">{phase.meta}</span>}
              </div>
              <p className="mt-0.5 text-xs leading-5 text-muted-foreground">{phase.detail}</p>
              <div className="mt-3 h-1 overflow-hidden rounded-full bg-white/[0.08]">
                <motion.div
                  className="h-full rounded-full bg-blue-400"
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

function AnalysisCard({ data }: { data: ChatResponse }) {
  if (!data.data?.analysis_result) return null

  const analysis = data.data.analysis_result
  const signal = analysis.signal

  return (
    <Card className="mt-4 max-w-2xl overflow-hidden rounded-2xl border-white/10 bg-white/[0.045] shadow-[0_18px_50px_rgba(0,0,0,0.18)]">
      <CardContent className="p-4">
        <div className="mb-3 flex flex-wrap items-center justify-between gap-3">
          <div className="flex items-center gap-3">
            <span className="font-mono text-lg font-semibold">{analysis.symbol}</span>
            <SignalBadge direction={signal.direction} size="md" />
          </div>
          <ConfidenceMeter value={signal.confidence} size="sm" />
        </div>
        <p className="text-sm leading-6 text-muted-foreground">{signal.reasoning}</p>
      </CardContent>
    </Card>
  )
}

function MessageRow({ message, onSuggestion }: {
  message: Message
  onSuggestion: (suggestion: string) => void
}) {
  const suggestions = visibleSuggestions(message.data?.suggestions)

  if (message.role === 'user') {
    return (
      <motion.div
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        className="mx-auto flex w-full max-w-3xl justify-end px-4"
      >
        <div className="max-w-[78%] rounded-2xl rounded-tr-md bg-blue-600 px-4 py-2.5 text-sm leading-6 text-white shadow-[0_12px_30px_rgba(37,99,235,0.28)]">
          {message.content}
        </div>
      </motion.div>
    )
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      className="mx-auto flex w-full max-w-3xl gap-3 px-4"
    >
      <AssistantAvatar />
      <div className="min-w-0 flex-1">
        <div className="mb-1 flex items-center gap-2">
          <span className="text-sm font-medium">Oracle</span>
          {message.data?.intent && message.data.intent !== 'GENERAL_CHAT' && (
            <Badge variant="outline" className="h-5 border-white/10 bg-white/[0.04] px-2 text-[10px]">
              {message.data.intent.replaceAll('_', ' ').toLowerCase()}
            </Badge>
          )}
        </div>
        <div className="prose-chat max-w-none text-sm leading-7 text-foreground">
          <MarkdownRenderer content={message.content} />
        </div>
        {message.data && <AnalysisCard data={message.data} />}
        {suggestions.length > 0 && (
          <div className="mt-3 flex flex-wrap gap-2">
            {suggestions.map((suggestion) => (
              <button
                key={suggestion}
                onClick={() => onSuggestion(suggestion)}
                className="rounded-full border border-white/10 bg-white/[0.035] px-3 py-1 text-xs text-muted-foreground transition-colors hover:bg-white/[0.08] hover:text-foreground"
              >
                {suggestion}
              </button>
            ))}
          </div>
        )}
      </div>
    </motion.div>
  )
}

export default function ChatPage() {
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [progressEvent, setProgressEvent] = useState<ChatProgressEvent | undefined>()
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const loadingPhase = progressToPhase(progressEvent)

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth', block: 'end' })
  }, [messages, isLoading, progressEvent])

  const handleSend = async (text?: string) => {
    const messageText = (text || input).trim()
    if (!messageText || isLoading) return

    setMessages((previous) => [
      ...previous,
      { id: crypto.randomUUID(), role: 'user', content: messageText },
    ])
    setInput('')
    setIsLoading(true)
    setProgressEvent(undefined)

    try {
      let response: ChatResponse
      try {
        response = await streamChat(messageText, (event) => {
          if (event.event === 'progress') setProgressEvent(event)
        })
      } catch {
        setProgressEvent({
          event: 'progress',
          stage: 'fallback',
          label: 'Using standard request',
          detail: 'Live progress stream was unavailable, so Oracle is waiting for the normal chat response.',
        })
        response = await sendChat(messageText)
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
    }
  }

  const handleKeyDown = (event: React.KeyboardEvent) => {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault()
      handleSend()
    }
  }

  return (
    <div className="flex h-screen min-h-[640px] flex-col overflow-hidden rounded-none border-border/70 bg-[#080b11] text-foreground">
      <header className="relative z-10 flex h-14 shrink-0 items-center justify-between border-b border-white/10 px-4 md:px-6">
        <div className="flex items-center gap-3">
          <AssistantAvatar />
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-sm font-semibold">Option Oracle</h1>
              <span className="h-1.5 w-1.5 rounded-full bg-emerald-400" />
            </div>
            <p className="text-xs text-muted-foreground">DeepSeek market assistant</p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <Button
            variant="ghost"
            size="sm"
            onClick={() => setMessages([])}
            className="hidden gap-2 rounded-full border border-white/10 bg-white/[0.035] hover:bg-white/[0.07] sm:flex"
          >
            <Plus className="h-4 w-4" />
            New chat
          </Button>
          <Badge variant="outline" className="border-emerald-500/25 bg-emerald-500/8 text-emerald-300">
            Live
          </Badge>
        </div>
      </header>

      <ScrollArea className="relative z-10 min-h-0 flex-1">
        {messages.length === 0 ? (
          <div className="mx-auto flex min-h-full w-full max-w-4xl flex-col items-center justify-center px-4 py-12 text-center">
            <div className="mb-6 flex h-14 w-14 items-center justify-center rounded-2xl border border-white/10 bg-white/[0.045] shadow-[0_20px_70px_rgba(37,99,235,0.20)]">
              <Sparkles className="h-6 w-6 text-blue-300" />
            </div>
            <h2 className="max-w-2xl text-balance text-4xl font-semibold tracking-tight md:text-5xl">
              Ask Oracle anything about the market.
            </h2>
            <p className="mt-4 max-w-xl text-sm leading-6 text-muted-foreground">
              Quick quotes stay instant. Full ticker requests can run deeper technical, flow, risk, and sentiment checks.
            </p>
            <div className="mt-8 grid w-full max-w-2xl gap-2 sm:grid-cols-2">
              {starterPrompts.map((prompt) => (
                <button
                  key={prompt}
                  onClick={() => handleSend(prompt)}
                  className="group rounded-2xl border border-white/10 bg-white/[0.035] px-4 py-3 text-left text-sm transition-all hover:border-blue-400/30 hover:bg-white/[0.07] hover:shadow-[0_18px_50px_rgba(37,99,235,0.12)]"
                >
                  <div className="flex items-center justify-between gap-3">
                    <span>{prompt}</span>
                    <ChevronDown className="-rotate-90 h-4 w-4 text-muted-foreground transition-colors group-hover:text-blue-300" />
                  </div>
                </button>
              ))}
            </div>
          </div>
        ) : (
          <div className="space-y-8 py-8">
            <AnimatePresence initial={false}>
              {messages.map((message) => (
                <MessageRow key={message.id} message={message} onSuggestion={handleSend} />
              ))}
              {isLoading && (
                <TypingBubble
                  phase={loadingPhase}
                />
              )}
            </AnimatePresence>
            <div ref={messagesEndRef} />
          </div>
        )}
      </ScrollArea>

      <div className="relative z-10 shrink-0 border-t border-white/10 bg-[#080b11]/90 px-4 py-4 backdrop-blur-xl">
        <div className="mx-auto max-w-3xl">
          <div className="rounded-3xl border border-blue-400/25 bg-white/[0.055] p-2 shadow-[0_24px_80px_rgba(0,0,0,0.34)] focus-within:border-blue-400/55">
            <div className="flex items-end gap-2">
              <div className="hidden h-10 w-10 shrink-0 items-center justify-center rounded-2xl bg-white/[0.05] text-blue-300 sm:flex">
                <Brain className="h-4 w-4" />
              </div>
              <Textarea
                value={input}
                onChange={(event) => setInput(event.target.value)}
                onKeyDown={handleKeyDown}
                placeholder="Message Oracle..."
                className="max-h-40 min-h-12 resize-none border-0 bg-transparent px-2 py-3 shadow-none focus-visible:ring-0"
                rows={1}
              />
              <Button
                onClick={() => handleSend()}
                disabled={!input.trim() || isLoading}
                className="mb-1 h-10 w-10 shrink-0 rounded-2xl bg-blue-600 p-0 text-white shadow-[0_12px_36px_rgba(37,99,235,0.32)] hover:bg-blue-500"
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
