'use client'

import { cn } from '@/lib/utils'
import type { SignalDirection } from '@/lib/api/types'

interface SignalBadgeProps {
  direction: SignalDirection
  size?: 'sm' | 'md' | 'lg'
  className?: string
}

const sizeClasses = {
  sm: 'px-2 py-0.5 text-xs',
  md: 'px-3 py-1 text-sm',
  lg: 'px-4 py-2 text-base font-semibold',
}

export function SignalBadge({ direction, size = 'md', className }: SignalBadgeProps) {
  const baseClasses = 'inline-flex items-center justify-center rounded-full font-medium transition-all'
  
  const colorClasses: Record<SignalDirection, string> = {
    STRONG_BUY: 'bg-green-600 text-white animate-pulse-glow',
    BUY: 'bg-green-500 text-white',
    HOLD: 'bg-amber-500 text-black',
    SELL: 'bg-red-500 text-white',
    STRONG_SELL: 'bg-red-600 text-white animate-pulse-glow-red',
  }

  const labels: Record<SignalDirection, string> = {
    STRONG_BUY: 'STRONG BUY',
    BUY: 'BUY',
    HOLD: 'HOLD',
    SELL: 'SELL',
    STRONG_SELL: 'STRONG SELL',
  }

  return (
    <span
      className={cn(
        baseClasses,
        sizeClasses[size],
        colorClasses[direction],
        className
      )}
    >
      {labels[direction]}
    </span>
  )
}
