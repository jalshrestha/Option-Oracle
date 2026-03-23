// Number formatting utilities for Option Oracle

/**
 * Format price with 2 decimal places and $ prefix
 */
export function formatPrice(value: number): string {
  return `$${value.toFixed(2)}`
}

/**
 * Format percentage with 2 decimal places, % suffix, and + prefix for positive
 */
export function formatPercent(value: number): string {
  const prefix = value > 0 ? '+' : ''
  return `${prefix}${value.toFixed(2)}%`
}

/**
 * Format large numbers with K/M/B suffix
 */
export function formatCompact(value: number): string {
  if (Math.abs(value) >= 1e9) {
    return `${(value / 1e9).toFixed(1)}B`
  }
  if (Math.abs(value) >= 1e6) {
    return `${(value / 1e6).toFixed(1)}M`
  }
  if (Math.abs(value) >= 1e3) {
    return `${(value / 1e3).toFixed(1)}K`
  }
  return value.toFixed(0)
}

/**
 * Format Greek values with 4 decimal places
 */
export function formatGreek(value: number): string {
  return value.toFixed(4)
}

/**
 * Format currency with full precision for display
 */
export function formatCurrency(value: number): string {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(value)
}

/**
 * Format volume numbers
 */
export function formatVolume(value: number): string {
  return formatCompact(value)
}

/**
 * Get color class based on value (positive = green, negative = red)
 */
export function getPriceColorClass(value: number): string {
  if (value > 0) return 'text-chart-up'
  if (value < 0) return 'text-chart-down'
  return 'text-muted-foreground'
}

/**
 * Get background color class for signals
 */
export function getSignalColorClass(signal: string): string {
  switch (signal) {
    case 'STRONG_BUY':
      return 'bg-green-600 text-white'
    case 'BUY':
      return 'bg-green-500 text-white'
    case 'HOLD':
      return 'bg-amber-500 text-black'
    case 'SELL':
      return 'bg-red-500 text-white'
    case 'STRONG_SELL':
      return 'bg-red-600 text-white'
    default:
      return 'bg-muted text-muted-foreground'
  }
}

/**
 * Get AI score color based on value
 */
export function getAIScoreColor(score: number): string {
  if (score >= 67) return 'text-green-500'
  if (score >= 34) return 'text-amber-500'
  return 'text-red-500'
}

/**
 * Get confidence color based on value (0-1)
 */
export function getConfidenceColor(value: number): string {
  if (value >= 0.8) return '#22c55e' // bright green with glow
  if (value >= 0.6) return '#22c55e' // green
  if (value >= 0.4) return '#f59e0b' // amber
  return '#ef4444' // red
}

/**
 * Format time ago
 */
export function formatTimeAgo(date: string | Date): string {
  const now = new Date()
  const past = new Date(date)
  const diffInSeconds = Math.floor((now.getTime() - past.getTime()) / 1000)

  if (diffInSeconds < 60) return 'just now'
  if (diffInSeconds < 3600) return `${Math.floor(diffInSeconds / 60)}m ago`
  if (diffInSeconds < 86400) return `${Math.floor(diffInSeconds / 3600)}h ago`
  return `${Math.floor(diffInSeconds / 86400)}d ago`
}
