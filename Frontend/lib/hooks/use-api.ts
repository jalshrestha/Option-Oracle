'use client'

import useSWR from 'swr'
import {
  getHotStocks,
  getPortfolioSummary,
  getPositions,
  getSystemHealth,
  getLLMProvider,
  getTechnical,
  getAnalysisHistory,
  getEducationContent,
  getLearningPath,
  getGlossary,
  getRecentSignals,
  getSystemMetrics,
  getPortfolioPerformance,
} from '@/lib/api/client'
import type {
  HotStock,
  PortfolioSummaryResponse,
  PositionSchema,
  SystemHealth,
  LLMProvider,
  TechnicalResponse,
  AnalysisResponse,
  EducationContent,
  LearningPath,
  GlossaryTerm,
  RecentSignalItem,
  SystemMetrics,
} from '@/lib/api/types'

// Hot stocks - revalidate every 60s
export function useHotStocks() {
  return useSWR<HotStock[]>('hot-stocks', getHotStocks, {
    refreshInterval: 60000,
    revalidateOnFocus: false,
  })
}

// Portfolio summary - revalidate every 30s
export function usePortfolioSummary() {
  return useSWR<PortfolioSummaryResponse>('portfolio-summary', getPortfolioSummary, {
    refreshInterval: 30000,
    revalidateOnFocus: false,
  })
}

// Positions - revalidate every 30s
export function usePositions() {
  return useSWR<PositionSchema[]>('positions', getPositions, {
    refreshInterval: 30000,
    revalidateOnFocus: false,
  })
}

// System health - revalidate every 15s
export function useSystemHealth() {
  return useSWR<SystemHealth>('system-health', getSystemHealth, {
    refreshInterval: 15000,
    revalidateOnFocus: false,
  })
}

// LLM Provider - no auto revalidate
export function useLLMProvider() {
  return useSWR<LLMProvider>('llm-provider', getLLMProvider, {
    revalidateOnFocus: false,
  })
}

// Technical data - no auto revalidate (on-demand)
export function useTechnical(symbol: string | null) {
  return useSWR<TechnicalResponse>(
    symbol ? `technical-${symbol}` : null,
    () => (symbol ? getTechnical(symbol) : null) as Promise<TechnicalResponse>,
    {
      revalidateOnFocus: false,
    }
  )
}

// Analysis history - no auto revalidate
export function useAnalysisHistory(symbol: string | null) {
  return useSWR<AnalysisResponse[]>(
    symbol ? `analysis-history-${symbol}` : null,
    () => (symbol ? getAnalysisHistory(symbol) : null) as Promise<AnalysisResponse[]>,
    {
      revalidateOnFocus: false,
    }
  )
}

// Education content
export function useEducationContent(filters?: {
  difficulty?: string
  type?: string
  topic?: string
}) {
  const key = filters
    ? `education-content-${JSON.stringify(filters)}`
    : 'education-content'
  return useSWR<EducationContent[]>(key, () => getEducationContent(filters), {
    revalidateOnFocus: false,
  })
}

// Learning path
export function useLearningPath(level?: string) {
  return useSWR<LearningPath>(
    level ? `learning-path-${level}` : 'learning-path',
    () => getLearningPath(level),
    {
      revalidateOnFocus: false,
    }
  )
}

// Glossary
export function useGlossary(search?: string, category?: string) {
  const key = `glossary-${search || ''}-${category || ''}`
  return useSWR<GlossaryTerm[]>(key, () => getGlossary(search, category), {
    revalidateOnFocus: false,
  })
}

// Recent signals across all symbols - revalidate every 30s
export function useRecentSignals(limit = 20) {
  return useSWR<RecentSignalItem[]>(
    `recent-signals-${limit}`,
    () => getRecentSignals(limit),
    {
      refreshInterval: 30000,
      revalidateOnFocus: false,
    }
  )
}

// System metrics
export function useSystemMetrics(type?: 'performance' | 'business' | 'errors') {
  return useSWR<SystemMetrics>(
    `system-metrics-${type || 'all'}`,
    () => getSystemMetrics(type),
    {
      refreshInterval: 15000,
      revalidateOnFocus: false,
    }
  )
}

// Portfolio performance history
export function usePortfolioPerformance() {
  return useSWR(
    'portfolio-performance',
    () => getPortfolioPerformance(),
    {
      revalidateOnFocus: false,
    }
  )
}
