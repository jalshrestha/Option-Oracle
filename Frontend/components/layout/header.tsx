'use client'

import { useState, useEffect } from 'react'
import { useTheme } from 'next-themes'
import { motion, AnimatePresence } from 'framer-motion'
import { Search, Sun, Moon, Bell, LogIn, LogOut, User } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Badge } from '@/components/ui/badge'
import { useSystemHealth } from '@/lib/hooks/use-api'
import { useAuth } from '@/providers/auth-provider'
import { cn } from '@/lib/utils'
import { CommandPalette } from './command-palette'
import Link from 'next/link'

export function Header() {
  const { theme, setTheme } = useTheme()
  const { data: health } = useSystemHealth()
  const { user, logout } = useAuth()
  const [mounted, setMounted] = useState(false)
  const [commandOpen, setCommandOpen] = useState(false)

  useEffect(() => {
    setMounted(true)
  }, [])

  useEffect(() => {
    const down = (e: KeyboardEvent) => {
      if (e.key === 'k' && (e.metaKey || e.ctrlKey)) {
        e.preventDefault()
        setCommandOpen((open) => !open)
      }
    }
    document.addEventListener('keydown', down)
    return () => document.removeEventListener('keydown', down)
  }, [])

  const toggleTheme = () => {
    setTheme(theme === 'dark' ? 'light' : 'dark')
  }

  const healthStatus = health?.overall_status || 'healthy'
  const statusColor = healthStatus === 'healthy' 
    ? 'bg-green-500' 
    : healthStatus === 'degraded' 
      ? 'bg-amber-500' 
      : 'bg-red-500'

  return (
    <>
      <header className="sticky top-0 z-30 flex h-16 items-center justify-between border-b border-border/70 bg-background/72 px-4 backdrop-blur-xl lg:px-6">
        {/* Left - Logo (mobile) */}
        <div className="flex items-center gap-4 lg:hidden">
          <div className="flex h-8 w-8 items-center justify-center rounded-lg brand-gradient">
            <svg
              width="18"
              height="18"
              viewBox="0 0 24 24"
              fill="none"
              xmlns="http://www.w3.org/2000/svg"
              className="text-white"
            >
              <circle cx="12" cy="12" r="3" fill="currentColor" />
              <circle cx="12" cy="4" r="2" fill="currentColor" opacity="0.6" />
              <circle cx="12" cy="20" r="2" fill="currentColor" opacity="0.6" />
              <circle cx="4" cy="12" r="2" fill="currentColor" opacity="0.6" />
              <circle cx="20" cy="12" r="2" fill="currentColor" opacity="0.6" />
            </svg>
          </div>
        </div>

        {/* Center - Command Search */}
        <div className="hidden flex-1 justify-center px-4 md:flex lg:px-12">
          <button
            onClick={() => setCommandOpen(true)}
            className="group flex h-10 w-full max-w-xl items-center gap-3 rounded-lg border border-border/80 bg-card/70 px-4 text-sm text-muted-foreground shadow-sm transition-colors hover:border-primary/50 hover:bg-card"
          >
            <Search className="h-4 w-4" />
            <span className="flex-1 text-left">Search symbols or ask Oracle...</span>
            <kbd className="pointer-events-none hidden h-5 select-none items-center gap-1 rounded border border-border bg-background px-1.5 font-mono text-[10px] font-medium text-muted-foreground sm:flex">
              <span className="text-xs">⌘</span>K
            </kbd>
          </button>
        </div>

        {/* Right - Actions */}
        <div className="flex items-center gap-2">
          {/* Theme Toggle */}
          {mounted && (
            <Button
              variant="ghost"
              size="icon"
              onClick={toggleTheme}
              className="relative h-9 w-9"
            >
              <AnimatePresence mode="wait" initial={false}>
                <motion.div
                  key={theme}
                  initial={{ scale: 0.5, rotate: -90, opacity: 0 }}
                  animate={{ scale: 1, rotate: 0, opacity: 1 }}
                  exit={{ scale: 0.5, rotate: 90, opacity: 0 }}
                  transition={{ duration: 0.2 }}
                >
                  {theme === 'dark' ? (
                    <Sun className="h-4 w-4" />
                  ) : (
                    <Moon className="h-4 w-4" />
                  )}
                </motion.div>
              </AnimatePresence>
            </Button>
          )}

          {/* System Status */}
          <div className="flex items-center gap-2 rounded-lg border border-border/80 bg-card/60 px-3 py-1.5">
            <div className={cn('h-2 w-2 rounded-full', statusColor)} />
            <span className="hidden text-xs font-medium text-muted-foreground sm:inline">
              {healthStatus === 'healthy' ? 'Online' : healthStatus}
            </span>
          </div>

          {/* Notifications */}
          <Button variant="ghost" size="icon" className="relative h-9 w-9 text-muted-foreground hover:text-foreground">
            <Bell className="h-4 w-4" />
          </Button>

          {/* User / Auth */}
          {user && !user.email.includes('@anon.example.com') ? (
            <div className="hidden items-center gap-2 sm:flex">
              <div className="flex items-center gap-2 rounded-lg border border-border bg-muted/50 px-3 py-1.5">
                <div className="flex h-6 w-6 items-center justify-center rounded-full brand-gradient">
                  <User className="h-3 w-3 text-white" />
                </div>
                <span className="text-xs font-medium text-muted-foreground max-w-[100px] truncate">
                  {user.username || user.email.split('@')[0]}
                </span>
              </div>
              <Button
                variant="ghost"
                size="icon"
                className="h-9 w-9 text-muted-foreground hover:text-foreground"
                onClick={() => logout()}
                title="Sign out"
              >
                <LogOut className="h-4 w-4" />
              </Button>
            </div>
          ) : (
            <Link href="/auth">
              <Button
                variant="outline"
                size="sm"
                className="hidden gap-1.5 sm:flex border-primary/30 text-primary hover:bg-primary/10"
              >
                <LogIn className="h-3.5 w-3.5" />
                Sign In
              </Button>
            </Link>
          )}
        </div>
      </header>

      <CommandPalette open={commandOpen} onOpenChange={setCommandOpen} />
    </>
  )
}
