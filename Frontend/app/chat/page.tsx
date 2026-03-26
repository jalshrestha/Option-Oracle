'use client'

import { useState, useRef, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import {
  Send,
  Sparkles,
  Plus,
  User,
  ChevronRight,
  MessageSquare,
} from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Textarea } from '@/components/ui/textarea'
import { Badge } from '@/components/ui/badge'
import { Card, CardContent } from '@/components/ui/card'
import { ScrollArea } from '@/components/ui/scroll-area'
import { Spinner } from '@/components/ui/spinner'
import { SignalBadge } from '@/components/analysis/signal-badge'
import { ConfidenceMeter } from '@/components/analysis/confidence-meter'
import { sendChat } from '@/lib/api/client'
import { cn } from '@/lib/utils'
import type { ChatResponse, SignalDirection } from '@/lib/api/types'

interface Message {
  id: string
  role: 'user' | 'assistant'
  content: string
  data?: ChatResponse
  timestamp: Date
}

interface Conversation {
  id: string
  title: string
  timestamp: Date
  messages: Message[]
}

const quickSymbols = ['AAPL', 'TSLA', 'NVDA', 'META']

const starterPrompts = [
  { text: 'Analyze AAPL for me', icon: Sparkles },
  { text: 'Should I buy NVDA calls or puts?', icon: MessageSquare },
  { text: "What's the options flow saying about TSLA?", icon: MessageSquare },
  { text: "Explain implied volatility like I'm new to options", icon: MessageSquare },
  { text: 'Show me my best risk-adjusted trade for this week', icon: MessageSquare },
]

function AnalysisCard({ data }: { data: ChatResponse }) {
  if (!data.data?.analysis_result) return null

  const analysis = data.data.analysis_result
  const signal = analysis.signal

  return (
    <Card className="mt-4 border-border bg-surface-elevated">
      <CardContent className="p-4">
        <div className="mb-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <span className="font-mono text-xl font-bold">{analysis.symbol}</span>
            <SignalBadge direction={signal.direction} size="md" />
          </div>
          <ConfidenceMeter value={signal.confidence} size="sm" />
        </div>

        <p className="mb-4 text-sm text-muted-foreground">{signal.reasoning}</p>

        {analysis.strike_recommendations && analysis.strike_recommendations.length > 0 && (
          <div className="grid gap-2 sm:grid-cols-2">
            {analysis.strike_recommendations.slice(0, 2).map((strike, i) => (
              <div
                key={i}
                className="rounded-lg bg-muted/50 p-3"
              >
                <div className="mb-1 flex items-center gap-2">
                  <Badge variant={strike.option_type === 'call' ? 'default' : 'destructive'}>
                    {strike.option_type.toUpperCase()}
                  </Badge>
                  <span className="font-mono text-sm font-semibold">
                    ${strike.strike}
                  </span>
                </div>
                <p className="text-xs text-muted-foreground">{strike.rationale}</p>
              </div>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  )
}

function TypewriterText({ text }: { text: string }) {
  const [displayedText, setDisplayedText] = useState('')
  const [currentIndex, setCurrentIndex] = useState(0)

  useEffect(() => {
    if (currentIndex < text.length) {
      const timeout = setTimeout(() => {
        setDisplayedText(text.slice(0, currentIndex + 1))
        setCurrentIndex(currentIndex + 1)
      }, 15)
      return () => clearTimeout(timeout)
    }
  }, [currentIndex, text])

  return <>{displayedText}</>
}

export default function ChatPage() {
  const [conversations, setConversations] = useState<Conversation[]>([])
  const [activeConversation, setActiveConversation] = useState<string | null>(null)
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const textareaRef = useRef<HTMLTextAreaElement>(null)

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  const handleSend = async (text?: string) => {
    const messageText = text || input
    if (!messageText.trim() || isLoading) return

    const userMessage: Message = {
      id: Date.now().toString(),
      role: 'user',
      content: messageText.trim(),
      timestamp: new Date(),
    }

    setMessages((prev) => [...prev, userMessage])
    setInput('')
    setIsLoading(true)

    try {
      // Detect symbol from message
      const symbolMatch = messageText.match(/\b([A-Z]{1,5})\b/)
      const detectedSymbol = symbolMatch ? symbolMatch[1] : undefined

      const response = await sendChat(messageText, detectedSymbol)

      const assistantMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: response.response,
        data: response,
        timestamp: new Date(),
      }

      setMessages((prev) => [...prev, assistantMessage])
    } catch (error: any) {
      const errorMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: 'Oracle is temporarily unavailable. Please try again.',
        timestamp: new Date(),
      }
      setMessages((prev) => [...prev, errorMessage])
    } finally {
      setIsLoading(false)
    }
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  const handleNewChat = () => {
    if (messages.length > 0) {
      const newConv: Conversation = {
        id: Date.now().toString(),
        title: messages[0]?.content.slice(0, 30) + '...' || 'New Chat',
        timestamp: new Date(),
        messages: messages,
      }
      setConversations((prev) => [newConv, ...prev])
    }
    setMessages([])
    setActiveConversation(null)
  }

  const loadConversation = (conv: Conversation) => {
    setMessages(conv.messages)
    setActiveConversation(conv.id)
  }

  return (
    <div className="flex h-[calc(100vh-8rem)] gap-4">
      {/* Left Panel - Conversations */}
      <div className="hidden w-72 flex-col rounded-lg border border-border bg-card lg:flex">
        <div className="border-b border-border p-4">
          <Button
            onClick={handleNewChat}
            className="w-full gap-2 brand-gradient text-white"
          >
            <Plus className="h-4 w-4" />
            New Chat
          </Button>
        </div>
        <ScrollArea className="flex-1">
          <div className="space-y-1 p-2">
            {conversations.map((conv) => (
              <button
                key={conv.id}
                onClick={() => loadConversation(conv)}
                className={cn(
                  'flex w-full items-center gap-2 rounded-lg px-3 py-2 text-left text-sm transition-colors hover:bg-accent',
                  activeConversation === conv.id && 'bg-accent'
                )}
              >
                <MessageSquare className="h-4 w-4 shrink-0 text-muted-foreground" />
                <span className="truncate">{conv.title}</span>
              </button>
            ))}
            {conversations.length === 0 && (
              <p className="px-3 py-8 text-center text-sm text-muted-foreground">
                No conversations yet
              </p>
            )}
          </div>
        </ScrollArea>
      </div>

      {/* Main Chat Area */}
      <div className="flex flex-1 flex-col rounded-lg border border-border bg-card">
        {/* Messages */}
        <ScrollArea className="flex-1 p-4">
          {messages.length === 0 ? (
            <div className="flex h-full flex-col items-center justify-center">
              <div className="mb-8 flex h-16 w-16 items-center justify-center rounded-full brand-gradient">
                <Sparkles className="h-8 w-8 text-white" />
              </div>
              <h2 className="mb-2 text-2xl font-semibold">
                Ask <span className="text-primary">Oracle</span> anything
              </h2>
              <p className="mb-8 text-center text-muted-foreground">
                Get AI-powered insights on stocks, options, and trading strategies
              </p>
              <div className="grid w-full max-w-2xl gap-3 sm:grid-cols-2">
                {starterPrompts.map((prompt, i) => (
                  <motion.button
                    key={i}
                    initial={{ opacity: 0, y: 16 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: i * 0.05 }}
                    onClick={() => handleSend(prompt.text)}
                    className="flex items-center gap-3 rounded-lg border border-border bg-muted/50 p-4 text-left text-sm transition-all hover:-translate-y-0.5 hover:border-primary/50 hover:bg-muted"
                  >
                    <prompt.icon className="h-4 w-4 shrink-0 text-primary" />
                    <span>{prompt.text}</span>
                  </motion.button>
                ))}
              </div>
            </div>
          ) : (
            <div className="space-y-6">
              <AnimatePresence>
                {messages.map((message) => (
                  <motion.div
                    key={message.id}
                    initial={{ opacity: 0, y: 16 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, y: -16 }}
                    className={cn(
                      'flex gap-4',
                      message.role === 'user' && 'justify-end'
                    )}
                  >
                    {message.role === 'assistant' && (
                      <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full brand-gradient">
                        <Sparkles className="h-4 w-4 text-white" />
                      </div>
                    )}
                    <div
                      className={cn(
                        'max-w-2xl rounded-2xl px-4 py-3',
                        message.role === 'user'
                          ? 'bg-primary text-primary-foreground'
                          : 'bg-muted'
                      )}
                    >
                      {message.role === 'assistant' ? (
                        <TypewriterText text={message.content} />
                      ) : (
                        message.content
                      )}
                      {message.data && <AnalysisCard data={message.data} />}
                      {message.data?.suggestions && message.data.suggestions.length > 0 && (
                        <div className="mt-3 flex flex-wrap gap-2">
                          {message.data.suggestions.map((suggestion, i) => (
                            <Badge
                              key={i}
                              variant="outline"
                              className="cursor-pointer hover:bg-primary hover:text-primary-foreground"
                              onClick={() => handleSend(suggestion)}
                            >
                              {suggestion}
                            </Badge>
                          ))}
                        </div>
                      )}
                      {message.data?.agents_triggered && message.data.agents_triggered.length > 0 && (
                        <p className="mt-2 text-xs text-muted-foreground">
                          Analyzed by: {message.data.agents_triggered.join(', ')}
                        </p>
                      )}
                    </div>
                    {message.role === 'user' && (
                      <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-muted">
                        <User className="h-4 w-4" />
                      </div>
                    )}
                  </motion.div>
                ))}
              </AnimatePresence>
              {isLoading && (
                <motion.div
                  initial={{ opacity: 0, y: 16 }}
                  animate={{ opacity: 1, y: 0 }}
                  className="flex gap-4"
                >
                  <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full brand-gradient">
                    <Sparkles className="h-4 w-4 text-white" />
                  </div>
                  <div className="flex items-center gap-2 rounded-2xl bg-muted px-4 py-3">
                    <Spinner className="h-4 w-4" />
                    <span className="text-sm text-muted-foreground">
                      Oracle is thinking...
                    </span>
                  </div>
                </motion.div>
              )}
              <div ref={messagesEndRef} />
            </div>
          )}
        </ScrollArea>

        {/* Input Bar */}
        <div className="border-t border-border p-4">
          <div className="mb-3 flex gap-2">
            {quickSymbols.map((symbol) => (
              <Badge
                key={symbol}
                variant="outline"
                className="cursor-pointer font-mono hover:bg-primary hover:text-primary-foreground"
                onClick={() => setInput((prev) => prev + ' ' + symbol)}
              >
                {symbol}
              </Badge>
            ))}
          </div>
          <div className="flex gap-3">
            <Textarea
              ref={textareaRef}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Ask Oracle about stocks, options, or trading strategies..."
              className="min-h-[48px] max-h-32 resize-none"
              rows={1}
            />
            <Button
              onClick={() => handleSend()}
              disabled={!input.trim() || isLoading}
              className="h-12 w-12 shrink-0 brand-gradient p-0 text-white"
            >
              {isLoading ? (
                <Spinner className="h-5 w-5" />
              ) : (
                <Send className="h-5 w-5" />
              )}
            </Button>
          </div>
        </div>
      </div>
    </div>
  )
}
