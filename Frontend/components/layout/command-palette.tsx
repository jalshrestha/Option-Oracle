'use client'

import { useRouter } from 'next/navigation'
import {
  CommandDialog,
  CommandEmpty,
  CommandGroup,
  CommandInput,
  CommandItem,
  CommandList,
  CommandSeparator,
} from '@/components/ui/command'
import {
  Home,
  Sparkles,
  BarChart3,
  Briefcase,
  Grid3X3,
  TrendingUp,
} from 'lucide-react'

const popularSymbols = ['AAPL', 'GOOGL', 'MSFT', 'TSLA', 'AMZN', 'NVDA', 'META', 'NFLX']

const pages = [
  { label: 'Dashboard', icon: Home, href: '/' },
  { label: 'Oracle Chat', icon: Sparkles, href: '/chat' },
  { label: 'Analyze', icon: BarChart3, href: '/analyze' },
  { label: 'Portfolio', icon: Briefcase, href: '/portfolio' },
  { label: 'Options Chain', icon: Grid3X3, href: '/options' },
]

interface CommandPaletteProps {
  open: boolean
  onOpenChange: (open: boolean) => void
}

export function CommandPalette({ open, onOpenChange }: CommandPaletteProps) {
  const router = useRouter()

  const runCommand = (command: () => void) => {
    onOpenChange(false)
    command()
  }

  return (
    <CommandDialog open={open} onOpenChange={onOpenChange}>
      <CommandInput placeholder="Search symbols or ask Oracle..." />
      <CommandList>
        <CommandEmpty>No results found.</CommandEmpty>
        
        <CommandGroup heading="Quick Analyze">
          {popularSymbols.map((symbol) => (
            <CommandItem
              key={symbol}
              value={symbol}
              onSelect={() => runCommand(() => router.push(`/analyze/${symbol}`))}
            >
              <TrendingUp className="mr-2 h-4 w-4 text-primary" />
              <span className="font-mono font-semibold">{symbol}</span>
              <span className="ml-2 text-xs text-muted-foreground">Analyze</span>
            </CommandItem>
          ))}
        </CommandGroup>
        
        <CommandSeparator />
        
        <CommandGroup heading="Navigation">
          {pages.map((page) => (
            <CommandItem
              key={page.href}
              value={page.label}
              onSelect={() => runCommand(() => router.push(page.href))}
            >
              <page.icon className="mr-2 h-4 w-4" />
              <span>{page.label}</span>
            </CommandItem>
          ))}
        </CommandGroup>
      </CommandList>
    </CommandDialog>
  )
}
