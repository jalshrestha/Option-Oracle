'use client'

import { useEffect, useRef, useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { cn } from '@/lib/utils'
import { formatPrice, formatPercent, getPriceColorClass } from '@/lib/utils/format'

interface PriceTickerProps {
  price: number
  change: number
  changePercent: number
  showChange?: boolean
  size?: 'sm' | 'md' | 'lg'
  className?: string
}

const sizeClasses = {
  sm: { price: 'text-sm', change: 'text-xs' },
  md: { price: 'text-lg', change: 'text-sm' },
  lg: { price: 'text-2xl', change: 'text-base' },
}

export function PriceTicker({
  price,
  change,
  changePercent,
  showChange = true,
  size = 'md',
  className,
}: PriceTickerProps) {
  const [flash, setFlash] = useState<'up' | 'down' | null>(null)
  const prevPrice = useRef(price)

  useEffect(() => {
    if (price !== prevPrice.current) {
      setFlash(price > prevPrice.current ? 'up' : 'down')
      prevPrice.current = price
      const timer = setTimeout(() => setFlash(null), 300)
      return () => clearTimeout(timer)
    }
  }, [price])

  const colorClass = getPriceColorClass(change)
  const { price: priceSize, change: changeSize } = sizeClasses[size]

  return (
    <div className={cn('flex items-baseline gap-2', className)}>
      <AnimatePresence mode="wait">
        <motion.span
          key={price}
          initial={{ opacity: 0.8 }}
          animate={{
            opacity: 1,
            backgroundColor: flash
              ? flash === 'up'
                ? 'rgba(34, 197, 94, 0.3)'
                : 'rgba(239, 68, 68, 0.3)'
              : 'transparent',
          }}
          transition={{ duration: 0.3 }}
          className={cn(
            'font-mono font-bold tabular-nums rounded px-1 -mx-1',
            priceSize,
            colorClass
          )}
        >
          {formatPrice(price)}
        </motion.span>
      </AnimatePresence>
      {showChange && (
        <span className={cn('font-mono tabular-nums', changeSize, colorClass)}>
          {formatPercent(changePercent)}
        </span>
      )}
    </div>
  )
}
