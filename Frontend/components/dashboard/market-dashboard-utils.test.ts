import { describe, expect, it } from 'vitest'
import {
  filterAndSortHotStocks,
  getMarketStatsSummary,
  type StockFilterKey,
} from './market-dashboard-utils'
import type { HotStock } from '@/lib/api/types'

const stocks: HotStock[] = [
  {
    symbol: 'AAPL',
    name: 'Apple Inc',
    price: 200,
    change: 4,
    changePercent: 2,
    volume: 1200000,
    sparklineData: [198, 200],
    aiScore: 82,
    signals: ['High Volume'],
    trending: true,
  },
  {
    symbol: 'TSLA',
    name: 'Tesla Inc',
    price: 240,
    change: -12,
    changePercent: -5,
    volume: 2200000,
    sparklineData: [252, 240],
    aiScore: 68,
    signals: ['Price Down'],
    trending: false,
  },
  {
    symbol: 'MSFT',
    name: 'Microsoft',
    price: 430,
    change: 1,
    changePercent: 0.25,
    volume: 900000,
    sparklineData: [429, 430],
    aiScore: 91,
    signals: ['Price Up'],
    trending: true,
  },
]

describe('market dashboard utilities', () => {
  it('filters by query and dashboard mode', () => {
    expect(filterAndSortHotStocks(stocks, 'app', 'all', 'symbol').map((s) => s.symbol)).toEqual([
      'AAPL',
    ])

    const filters: Record<StockFilterKey, string[]> = {
      all: ['AAPL', 'MSFT', 'TSLA'],
      trending: ['AAPL', 'MSFT'],
      gainers: ['AAPL', 'MSFT'],
      decliners: ['TSLA'],
    }

    for (const [filter, expected] of Object.entries(filters)) {
      expect(
        filterAndSortHotStocks(stocks, '', filter as StockFilterKey, 'symbol').map(
          (s) => s.symbol
        )
      ).toEqual(expected)
    }
  })

  it('sorts by absolute move, volume, AI score, and symbol', () => {
    expect(filterAndSortHotStocks(stocks, '', 'all', 'change')[0].symbol).toBe('TSLA')
    expect(filterAndSortHotStocks(stocks, '', 'all', 'volume')[0].symbol).toBe('TSLA')
    expect(filterAndSortHotStocks(stocks, '', 'all', 'aiScore')[0].symbol).toBe('MSFT')
    expect(filterAndSortHotStocks(stocks, '', 'all', 'symbol').map((s) => s.symbol)).toEqual([
      'AAPL',
      'MSFT',
      'TSLA',
    ])
  })

  it('summarizes market stats from live stock rows', () => {
    const stats = getMarketStatsSummary(stocks)

    expect(stats.totalStocks).toBe(3)
    expect(stats.trendingCount).toBe(2)
    expect(stats.gainers).toBe(2)
    expect(stats.decliners).toBe(1)
    expect(stats.averageAiScore).toBe(80)
    expect(stats.topMover?.symbol).toBe('TSLA')
    expect(stats.highestVolume?.symbol).toBe('TSLA')
  })
})
