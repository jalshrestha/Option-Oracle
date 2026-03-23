'use client'

import { createContext, useContext, useEffect, useState, type ReactNode } from 'react'
import { createSession, getSessionToken } from '@/lib/api/client'

interface SessionContextType {
  isReady: boolean
  token: string | null
}

const SessionContext = createContext<SessionContextType>({
  isReady: false,
  token: null,
})

export function SessionProvider({ children }: { children: ReactNode }) {
  const [isReady, setIsReady] = useState(false)
  const [token, setToken] = useState<string | null>(null)

  useEffect(() => {
    async function init() {
      const existing = getSessionToken()
      if (!existing) {
        await createSession('moderate')
      }
      setToken(getSessionToken())
      setIsReady(true)
    }
    init()
  }, [])

  return (
    <SessionContext.Provider value={{ isReady, token }}>
      {children}
    </SessionContext.Provider>
  )
}

export function useSession() {
  return useContext(SessionContext)
}
