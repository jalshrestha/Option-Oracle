import type { HotStock } from '@/lib/api/types'

export type StockSortKey = 'change' | 'volume' | 'aiScore' | 'symbol'
export type StockFilterKey = 'all' | 'trending' | 'gainers' | 'decliners'

export interface MarketStatsSummary {
  totalStocks: number
  trendingCount: number
  gainers: number
  decliners: number
  averageAiScore: number
  topMover?: HotStock
  highestVolume?: HotStock
}

export function filterAndSortHotStocks(
  stocks: HotStock[],
  searchQuery: string,
  filterBy: StockFilterKey,
  sortBy: StockSortKey
): HotStock[] {
  const query = searchQuery.trim().toLowerCase()

  return stocks
    .filter((stock) => {
      const matchesQuery =
        !query ||
        stock.symbol.toLowerCase().includes(query) ||
        stock.name.toLowerCase().includes(query)

      if (!matchesQuery) return false

      if (filterBy === 'trending') return stock.trending
      if (filterBy === 'gainers') return stock.changePercent > 0
      if (filterBy === 'decliners') return stock.changePercent < 0
      return true
    })
    .sort((a, b) => {
      if (sortBy === 'change') return Math.abs(b.changePercent) - Math.abs(a.changePercent)
      if (sortBy === 'volume') return b.volume - a.volume
      if (sortBy === 'aiScore') return b.aiScore - a.aiScore
      return a.symbol.localeCompare(b.symbol)
    })
}

export function getMarketStatsSummary(stocks: HotStock[]): MarketStatsSummary {
  const totalStocks = stocks.length
  const trendingCount = stocks.filter((stock) => stock.trending).length
  const gainers = stocks.filter((stock) => stock.changePercent > 0).length
  const decliners = stocks.filter((stock) => stock.changePercent < 0).length
  const averageAiScore = totalStocks
    ? Math.round(stocks.reduce((sum, stock) => sum + stock.aiScore, 0) / totalStocks)
    : 0

  const topMover = stocks.reduce<HotStock | undefined>((best, stock) => {
    if (!best) return stock
    return Math.abs(stock.changePercent) > Math.abs(best.changePercent) ? stock : best
  }, undefined)

  const highestVolume = stocks.reduce<HotStock | undefined>((best, stock) => {
    if (!best) return stock
    return stock.volume > best.volume ? stock : best
  }, undefined)

  return {
    totalStocks,
    trendingCount,
    gainers,
    decliners,
    averageAiScore,
    topMover,
    highestVolume,
  }
}
