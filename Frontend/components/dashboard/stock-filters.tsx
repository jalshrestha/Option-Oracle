'use client'

import { Filter, Flame, Search } from 'lucide-react'
import { Badge } from '@/components/ui/badge'
import { Input } from '@/components/ui/input'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import type { StockFilterKey, StockSortKey } from './market-dashboard-utils'

interface StockFiltersProps {
  searchQuery: string
  onSearchChange: (value: string) => void
  sortBy: StockSortKey
  onSortChange: (value: StockSortKey) => void
  filterBy: StockFilterKey
  onFilterChange: (value: StockFilterKey) => void
  totalStocks: number
  visibleStocks: number
  trendingCount: number
}

export function StockFilters({
  searchQuery,
  onSearchChange,
  sortBy,
  onSortChange,
  filterBy,
  onFilterChange,
  totalStocks,
  visibleStocks,
  trendingCount,
}: StockFiltersProps) {
  return (
    <div className="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
      <div className="space-y-2">
        <div className="flex flex-wrap items-center gap-2">
          <h2 className="flex items-center gap-2 text-lg font-semibold">
            <Flame className="h-5 w-5 text-amber-500" />
            Hot Stocks
          </h2>
          <Badge variant="secondary">{trendingCount} trending</Badge>
        </div>
        <p className="text-sm text-muted-foreground">
          Showing {visibleStocks} of {totalStocks} symbols from the market data feed.
        </p>
      </div>

      <div className="grid gap-3 sm:grid-cols-[minmax(220px,1fr)_160px_180px] lg:min-w-[640px]">
        <div className="relative">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
          <Input
            value={searchQuery}
            onChange={(event) => onSearchChange(event.target.value)}
            placeholder="Search symbol or company"
            className="pl-9"
          />
        </div>

        <Select value={filterBy} onValueChange={(value) => onFilterChange(value as StockFilterKey)}>
          <SelectTrigger aria-label="Filter stocks">
            <Filter className="mr-2 h-4 w-4 text-muted-foreground" />
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All stocks</SelectItem>
            <SelectItem value="trending">Trending</SelectItem>
            <SelectItem value="gainers">Gainers</SelectItem>
            <SelectItem value="decliners">Decliners</SelectItem>
          </SelectContent>
        </Select>

        <Select value={sortBy} onValueChange={(value) => onSortChange(value as StockSortKey)}>
          <SelectTrigger aria-label="Sort stocks">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="change">Largest move</SelectItem>
            <SelectItem value="volume">Volume</SelectItem>
            <SelectItem value="aiScore">AI score</SelectItem>
            <SelectItem value="symbol">Symbol</SelectItem>
          </SelectContent>
        </Select>
      </div>
    </div>
  )
}
