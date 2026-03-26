'use client'

import { useEffect, useState, type ReactNode } from 'react'
import { usePathname, useRouter } from 'next/navigation'
import { motion } from 'framer-motion'
import { useAuth } from '@/providers/auth-provider'
import { Sidebar } from './sidebar'
import { Header } from './header'

interface AppShellProps {
  children: ReactNode
}

const FULL_SCREEN_ROUTES = ['/auth', '/landing']

export function AppShell({ children }: AppShellProps) {
  const pathname = usePathname()
  const router = useRouter()
  const { isReady, user } = useAuth()
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false)

  const isFullScreen = FULL_SCREEN_ROUTES.some((r) => pathname.startsWith(r))

  // Redirect unauthenticated (no user at all) to landing after auth resolves
  useEffect(() => {
    if (isFullScreen || !isReady) return
    if (!user) {
      router.replace('/landing')
    }
  }, [isReady, user, isFullScreen, router])

  // Full-screen routes (landing, auth) — no sidebar or header
  if (isFullScreen) {
    return <>{children}</>
  }

  // Block all dashboard rendering until auth resolves — eliminates the flash
  if (!isReady || !user) {
    return null
  }

  return (
    <div className="min-h-screen bg-background">
      <Sidebar
        collapsed={sidebarCollapsed}
        onToggle={() => setSidebarCollapsed(!sidebarCollapsed)}
      />
      <motion.div
        initial={false}
        animate={{ marginLeft: sidebarCollapsed ? 64 : 240 }}
        transition={{ duration: 0.2, ease: 'easeInOut' }}
        className="flex min-h-screen flex-col"
      >
        <Header />
        <main className="flex-1 p-6">
          <motion.div
            initial={{ opacity: 0, y: 16 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.35, ease: 'easeOut' }}
          >
            {children}
          </motion.div>
        </main>
      </motion.div>
    </div>
  )
}
