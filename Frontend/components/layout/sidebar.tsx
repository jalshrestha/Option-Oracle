'use client'

import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { motion, AnimatePresence } from 'framer-motion'
import {
  Home,
  Sparkles,
  BarChart3,
  Briefcase,
  Grid3X3,
  GraduationCap,
  Settings,
  ChevronLeft,
  ChevronRight,
} from 'lucide-react'
import { cn } from '@/lib/utils'
import { Button } from '@/components/ui/button'
import { useLLMProvider } from '@/lib/hooks/use-api'

const navItems = [
  { href: '/', icon: Home, label: 'Dashboard' },
  { href: '/chat', icon: Sparkles, label: 'Oracle Chat' },
  { href: '/analyze', icon: BarChart3, label: 'Analyze' },
  { href: '/portfolio', icon: Briefcase, label: 'Portfolio' },
  { href: '/options', icon: Grid3X3, label: 'Options Chain' },
  { href: '/education', icon: GraduationCap, label: 'Education' },
  { href: '/system', icon: Settings, label: 'System' },
]

interface SidebarProps {
  collapsed: boolean
  onToggle: () => void
}

export function Sidebar({ collapsed, onToggle }: SidebarProps) {
  const pathname = usePathname()
  const { data: llmProvider } = useLLMProvider()

  return (
    <motion.aside
      initial={false}
      animate={{ width: collapsed ? 64 : 240 }}
      transition={{ duration: 0.2, ease: 'easeInOut' }}
      className="fixed left-0 top-0 z-40 h-screen border-r border-border bg-sidebar flex flex-col"
    >
      {/* Logo */}
      <div className="flex h-16 items-center gap-3 border-b border-border px-4">
        <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg brand-gradient">
          <svg
            width="20"
            height="20"
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
            <line x1="12" y1="6" x2="12" y2="9" stroke="currentColor" strokeWidth="1.5" opacity="0.4" />
            <line x1="12" y1="15" x2="12" y2="18" stroke="currentColor" strokeWidth="1.5" opacity="0.4" />
            <line x1="6" y1="12" x2="9" y2="12" stroke="currentColor" strokeWidth="1.5" opacity="0.4" />
            <line x1="15" y1="12" x2="18" y2="12" stroke="currentColor" strokeWidth="1.5" opacity="0.4" />
          </svg>
        </div>
        <AnimatePresence>
          {!collapsed && (
            <motion.div
              initial={{ opacity: 0, x: -10 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: -10 }}
              transition={{ duration: 0.15 }}
              className="flex flex-col"
            >
              <span className="text-sm font-semibold tracking-tight text-foreground">
                Option <span className="text-primary">Oracle</span>
              </span>
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      {/* Navigation */}
      <nav className="flex-1 space-y-1 p-2">
        {navItems.map((item) => {
          const isActive = pathname === item.href || 
            (item.href !== '/' && pathname.startsWith(item.href))
          
          return (
            <Link key={item.href} href={item.href}>
              <div
                className={cn(
                  'group flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-all duration-200',
                  isActive
                    ? 'bg-primary/10 text-primary'
                    : 'text-muted-foreground hover:bg-accent hover:text-foreground'
                )}
              >
                <item.icon
                  className={cn(
                    'h-5 w-5 shrink-0 transition-colors',
                    isActive ? 'text-primary' : 'text-muted-foreground group-hover:text-foreground'
                  )}
                />
                <AnimatePresence>
                  {!collapsed && (
                    <motion.span
                      initial={{ opacity: 0, x: -10 }}
                      animate={{ opacity: 1, x: 0 }}
                      exit={{ opacity: 0, x: -10 }}
                      transition={{ duration: 0.15 }}
                    >
                      {item.label}
                    </motion.span>
                  )}
                </AnimatePresence>
              </div>
            </Link>
          )
        })}
      </nav>

      {/* Footer - LLM Provider */}
      <div className="border-t border-border p-3">
        <AnimatePresence>
          {!collapsed ? (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="flex items-center gap-2 rounded-lg bg-accent/50 px-3 py-2"
            >
              <div className="h-2 w-2 rounded-full bg-green-500" />
              <span className="text-xs font-medium text-muted-foreground">
                {llmProvider?.provider || 'GPT-4o'}
              </span>
            </motion.div>
          ) : (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="flex justify-center"
            >
              <div className="h-2 w-2 rounded-full bg-green-500" />
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      {/* Toggle Button */}
      <Button
        variant="ghost"
        size="icon"
        onClick={onToggle}
        className="absolute -right-3 top-20 h-6 w-6 rounded-full border border-border bg-background shadow-sm"
      >
        {collapsed ? (
          <ChevronRight className="h-3 w-3" />
        ) : (
          <ChevronLeft className="h-3 w-3" />
        )}
      </Button>
    </motion.aside>
  )
}
