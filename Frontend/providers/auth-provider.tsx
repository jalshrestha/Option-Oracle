'use client'

import {
  createContext,
  useContext,
  useEffect,
  useState,
  type ReactNode,
} from 'react'
import {
  getAccessToken,
  getRefreshToken,
  setTokens,
  clearTokens,
  register,
  login,
  logout as apiLogout,
  getMe,
} from '@/lib/api/client'
import type { UserProfile } from '@/lib/api/types'

const ANON_CREDS_KEY = 'oracle_anon_creds'

interface AnonCreds {
  email: string
  username: string
  password: string
}

function generateAnonCreds(): AnonCreds {
  const hex = Array.from(crypto.getRandomValues(new Uint8Array(8)))
    .map((b) => b.toString(16).padStart(2, '0'))
    .join('')
  // Generate a random 24-char hex token used as the anon account credential
  const token = Array.from(crypto.getRandomValues(new Uint8Array(12)))
    .map((b) => b.toString(16).padStart(2, '0'))
    .join('')
  return {
    username: `user_${hex}`,
    email: `user_${hex}@anon.example.com`,
    password: token,
  }
}

function isTokenExpired(token: string): boolean {
  try {
    const payload = JSON.parse(atob(token.split('.')[1]))
    return payload.exp * 1000 < Date.now()
  } catch {
    return true
  }
}

interface AuthContextType {
  isReady: boolean
  user: UserProfile | null
  login: (email: string, password: string) => Promise<void>
  register: (email: string, username: string, password: string) => Promise<void>
  logout: () => Promise<void>
}

const AuthContext = createContext<AuthContextType>({
  isReady: false,
  user: null,
  login: async () => {},
  register: async () => {},
  logout: async () => {},
})

export function AuthProvider({ children }: { children: ReactNode }) {
  const [isReady, setIsReady] = useState(false)
  const [user, setUser] = useState<UserProfile | null>(null)

  useEffect(() => {
    async function init() {
      const token = getAccessToken()

      if (token && !isTokenExpired(token)) {
        // Valid token — load user profile
        try {
          const profile = await getMe()
          setUser(profile)
          setIsReady(true)
          return
        } catch {
          // Token invalid, fall through to re-auth
          clearTokens()
        }
      }

      // Try refresh if we have a refresh token
      const refreshToken = getRefreshToken()
      if (refreshToken && !isTokenExpired(refreshToken)) {
        try {
          const profile = await getMe()
          setUser(profile)
          setIsReady(true)
          return
        } catch {
          clearTokens()
        }
      }

      // No valid session — auto-register or re-login as anonymous
      await initAnonUser()
    }

    init()
  }, [])

  async function initAnonUser() {
    // Check for stored anon credentials first
    let creds: AnonCreds | null = null
    try {
      const stored = localStorage.getItem(ANON_CREDS_KEY)
      if (stored) creds = JSON.parse(stored)
    } catch {}

    if (creds) {
      // Try logging in with existing anon creds
      try {
        await login(creds.email, creds.password)
        const profile = await getMe()
        setUser(profile)
        setIsReady(true)
        return
      } catch {
        // Creds invalid or user deleted — generate new ones
        localStorage.removeItem(ANON_CREDS_KEY)
        creds = null
      }
    }

    // Register a fresh anonymous user
    const newCreds = generateAnonCreds()
    try {
      await register(newCreds.email, newCreds.username, newCreds.password)
      localStorage.setItem(ANON_CREDS_KEY, JSON.stringify(newCreds))
      const profile = await getMe()
      setUser(profile)
    } catch (err) {
      // Registration failed (e.g. email conflict from a previous session) — try login
      try {
        await login(newCreds.email, newCreds.password)
        localStorage.setItem(ANON_CREDS_KEY, JSON.stringify(newCreds))
        const profile = await getMe()
        setUser(profile)
      } catch {
        // Can't auth at all — mark ready anyway so the UI doesn't hang
      }
    }

    setIsReady(true)
  }

  async function handleLogin(email: string, password: string) {
    await login(email, password)
    const profile = await getMe()
    setUser(profile)
  }

  async function handleRegister(
    email: string,
    username: string,
    password: string
  ) {
    await register(email, username, password)
    const profile = await getMe()
    setUser(profile)
  }

  async function handleLogout() {
    await apiLogout()
    setUser(null)
    // Re-init as anonymous
    await initAnonUser()
  }

  return (
    <AuthContext.Provider
      value={{
        isReady,
        user,
        login: handleLogin,
        register: handleRegister,
        logout: handleLogout,
      }}
    >
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  return useContext(AuthContext)
}
