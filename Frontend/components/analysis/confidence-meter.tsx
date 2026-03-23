'use client'

import { useEffect, useState } from 'react'
import { motion, useSpring, useTransform } from 'framer-motion'
import { getConfidenceColor } from '@/lib/utils/format'
import { cn } from '@/lib/utils'

interface ConfidenceMeterProps {
  value: number // 0-1
  size?: 'sm' | 'md' | 'lg'
  showLabel?: boolean
  className?: string
}

const sizes = {
  sm: { width: 48, strokeWidth: 4, fontSize: 'text-xs' },
  md: { width: 80, strokeWidth: 6, fontSize: 'text-lg' },
  lg: { width: 120, strokeWidth: 8, fontSize: 'text-2xl' },
}

export function ConfidenceMeter({
  value,
  size = 'md',
  showLabel = true,
  className,
}: ConfidenceMeterProps) {
  const [mounted, setMounted] = useState(false)
  const { width, strokeWidth, fontSize } = sizes[size]
  const radius = (width - strokeWidth) / 2
  const circumference = 2 * Math.PI * radius

  const spring = useSpring(0, { stiffness: 100, damping: 30 })
  const strokeDashoffset = useTransform(
    spring,
    (v) => circumference - (v / 100) * circumference
  )

  useEffect(() => {
    setMounted(true)
    spring.set(value * 100)
  }, [spring, value])

  const color = getConfidenceColor(value)
  const percentage = Math.round(value * 100)
  const showGlow = value >= 0.8

  if (!mounted) {
    return (
      <div
        className={cn('relative inline-flex items-center justify-center', className)}
        style={{ width, height: width }}
      >
        <svg width={width} height={width} className="-rotate-90">
          <circle
            cx={width / 2}
            cy={width / 2}
            r={radius}
            fill="none"
            stroke="currentColor"
            strokeWidth={strokeWidth}
            className="text-muted/20"
          />
        </svg>
      </div>
    )
  }

  return (
    <div
      className={cn('relative inline-flex items-center justify-center', className)}
      style={{ width, height: width }}
    >
      <svg width={width} height={width} className="-rotate-90">
        {/* Background circle */}
        <circle
          cx={width / 2}
          cy={width / 2}
          r={radius}
          fill="none"
          stroke="currentColor"
          strokeWidth={strokeWidth}
          className="text-muted/20"
        />
        {/* Animated progress circle */}
        <motion.circle
          cx={width / 2}
          cy={width / 2}
          r={radius}
          fill="none"
          stroke={color}
          strokeWidth={strokeWidth}
          strokeLinecap="round"
          strokeDasharray={circumference}
          style={{
            strokeDashoffset,
            filter: showGlow ? `drop-shadow(0 0 6px ${color})` : undefined,
          }}
        />
      </svg>
      {showLabel && (
        <span
          className={cn(
            'absolute font-mono font-bold',
            fontSize
          )}
          style={{ color }}
        >
          {percentage}%
        </span>
      )}
    </div>
  )
}
