import { describe, expect, it } from 'vitest'

import {
  formatCompact,
  formatCurrency,
  formatPercent,
  formatPrice,
  getPriceColorClass,
  getSignalColorClass,
} from './format'

describe('format utilities', () => {
  it('formats prices and currency values', () => {
    expect(formatPrice(12.3)).toBe('$12.30')
    expect(formatCurrency(1234.5)).toBe('$1,234.50')
  })

  it('formats percentages with direction signs', () => {
    expect(formatPercent(1.234)).toBe('+1.23%')
    expect(formatPercent(-1.234)).toBe('-1.23%')
    expect(formatPercent(0)).toBe('0.00%')
  })

  it('formats compact large numbers', () => {
    expect(formatCompact(1500)).toBe('1.5K')
    expect(formatCompact(2_500_000)).toBe('2.5M')
    expect(formatCompact(4_200_000_000)).toBe('4.2B')
  })

  it('returns semantic color classes', () => {
    expect(getPriceColorClass(1)).toBe('text-chart-up')
    expect(getPriceColorClass(-1)).toBe('text-chart-down')
    expect(getPriceColorClass(0)).toBe('text-muted-foreground')
    expect(getSignalColorClass('BUY')).toContain('green')
  })
})
