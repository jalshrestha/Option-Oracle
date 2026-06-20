'use client'

import { useMemo, useState } from 'react'
import { AlertCircle } from 'lucide-react'
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert'
import { HotStocksGrid } from './hot-stocks-grid'
import { MarketStats } from './market-stats'
import { StockFilters } from './stock-filters'
import {
  filterAndSortHotStocks,
  getMarketStatsSummary,
  type StockFilterKey,
  type StockSortKey,
} from './market-dashboard-utils'
import { useHotStocks } from '@/lib/hooks/use-api'

export function MarketDashboard() {
  const [searchQuery, setSearchQuery] = useState('')
  const [sortBy, setSortBy] = useState<StockSortKey>('change')
  const [filterBy, setFilterBy] = useState<StockFilterKey>('all')
  const { data: stocks = [], isLoading, error, mutate } = useHotStocks()

  const visibleStocks = useMemo(
    () => filterAndSortHotStocks(stocks, searchQuery, filterBy, sortBy),
    [filterBy, searchQuery, sortBy, stocks]
  )

  const stats = useMemo(() => getMarketStatsSummary(stocks), [stocks])

  return (
    <section className="space-y-4">
      <StockFilters
        searchQuery={searchQuery}
        onSearchChange={setSearchQuery}
        sortBy={sortBy}
        onSortChange={setSortBy}
        filterBy={filterBy}
        onFilterChange={setFilterBy}
        totalStocks={stocks.length}
        visibleStocks={visibleStocks.length}
        trendingCount={stats.trendingCount}
      />

      <MarketStats stats={stats} isLoading={isLoading} />

      {error ? (
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertTitle>Market data unavailable</AlertTitle>
          <AlertDescription>
            The dashboard could not load hot stocks from the backend. Use retry after the
            API is reachable.
            <button
              type="button"
              onClick={() => void mutate()}
              className="ml-2 underline underline-offset-4"
            >
              Retry
            </button>
          </AlertDescription>
        </Alert>
      ) : null}

      <HotStocksGrid
        stocks={visibleStocks}
        isLoading={isLoading}
        hasActiveFilters={Boolean(searchQuery.trim()) || filterBy !== 'all'}
      />
    </section>
  )
}
