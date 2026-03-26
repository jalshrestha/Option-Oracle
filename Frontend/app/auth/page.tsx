'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import { motion, AnimatePresence } from 'framer-motion'
import { Eye, EyeOff, Sparkles, ArrowRight, User, Mail, Lock, AlertCircle } from 'lucide-react'
import { useAuth } from '@/providers/auth-provider'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { cn } from '@/lib/utils'

export default function AuthPage() {
  const { login, register, isReady } = useAuth()
  const router = useRouter()

  const [tab, setTab] = useState<'login' | 'register'>('login')
  const [email, setEmail] = useState('')
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [showPassword, setShowPassword] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    setError(null)
    setLoading(true)
    try {
      if (tab === 'login') {
        await login(email, password)
      } else {
        await register(email, username, password)
      }
      router.push('/')
    } catch (err: any) {
      const raw = err.message || ''
      const [statusStr, ...rest] = raw.split(':')
      const status = parseInt(statusStr, 10)
      const detail = rest.join(':').trim()

      if (status === 409 || detail.toLowerCase().includes('already') || detail.toLowerCase().includes('taken')) {
        setError('An account with this email or username already exists.')
      } else if (status === 401) {
        setError('Invalid email or password.')
      } else if (status === 422) {
        // FastAPI validation — clean up the message
        const clean = detail
          .replace(/Value error,\s*/gi, '')
          .replace(/String should have at least (\d+) character[s]*/gi, 'Password must be at least $1 characters')
          .replace(/value is not a valid email address[^;]*/gi, 'Enter a valid email address')
        setError(clean || 'Please check your input and try again.')
      } else if (status === 429) {
        setError('Too many attempts. Please wait a minute and try again.')
      } else {
        setError(detail || 'Something went wrong. Please try again.')
      }
    } finally {
      setLoading(false)
    }
  }

  async function handleGuest() {
    router.push('/')
  }

  return (
    <div className="relative min-h-screen flex items-center justify-center bg-background overflow-hidden">
      {/* Ambient background glows */}
      <div className="pointer-events-none absolute inset-0 overflow-hidden">
        <div className="absolute -top-40 -left-40 h-96 w-96 rounded-full bg-primary/10 blur-3xl" />
        <div className="absolute -bottom-40 -right-40 h-96 w-96 rounded-full bg-blue-500/10 blur-3xl" />
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 h-[600px] w-[600px] rounded-full bg-primary/5 blur-3xl" />
      </div>

      {/* Grid pattern overlay */}
      <div
        className="pointer-events-none absolute inset-0 opacity-[0.03]"
        style={{
          backgroundImage: 'linear-gradient(to right, #7c6ff7 1px, transparent 1px), linear-gradient(to bottom, #7c6ff7 1px, transparent 1px)',
          backgroundSize: '48px 48px',
        }}
      />

      <motion.div
        initial={{ opacity: 0, y: 24 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.4, ease: 'easeOut' }}
        className="relative z-10 w-full max-w-md px-4"
      >
        {/* Logo / Brand */}
        <div className="mb-8 flex flex-col items-center gap-3">
          <div className="flex h-14 w-14 items-center justify-center rounded-2xl brand-gradient shadow-lg shadow-primary/25">
            <svg
              width="28"
              height="28"
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
          <div className="text-center">
            <h1 className="text-2xl font-bold tracking-tight">
              Option <span className="text-primary">Oracle</span>
            </h1>
            <p className="mt-1 text-sm text-muted-foreground">
              AI-powered options trading intelligence
            </p>
          </div>
        </div>

        {/* Card */}
        <div className="rounded-2xl border border-border bg-card shadow-xl shadow-black/20">
          {/* Tabs */}
          <div className="flex border-b border-border">
            {(['login', 'register'] as const).map((t) => (
              <button
                key={t}
                onClick={() => { setTab(t); setError(null) }}
                className={cn(
                  'relative flex-1 py-4 text-sm font-medium transition-colors',
                  tab === t ? 'text-foreground' : 'text-muted-foreground hover:text-foreground'
                )}
              >
                {t === 'login' ? 'Sign In' : 'Create Account'}
                {tab === t && (
                  <motion.div
                    layoutId="auth-tab-indicator"
                    className="absolute bottom-0 left-0 right-0 h-0.5 brand-gradient"
                  />
                )}
              </button>
            ))}
          </div>

          {/* Form */}
          <div className="p-6">
            <AnimatePresence mode="wait">
              <motion.form
                key={tab}
                initial={{ opacity: 0, x: tab === 'login' ? -16 : 16 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: tab === 'login' ? 16 : -16 }}
                transition={{ duration: 0.2 }}
                onSubmit={handleSubmit}
                className="space-y-4"
              >
                {/* Email */}
                <div className="space-y-1.5">
                  <Label htmlFor="email" className="text-xs font-medium text-muted-foreground uppercase tracking-wide">
                    Email
                  </Label>
                  <div className="relative">
                    <Mail className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                    <Input
                      id="email"
                      type="email"
                      required
                      value={email}
                      onChange={(e) => setEmail(e.target.value)}
                      placeholder="you@example.com"
                      className="pl-9 bg-background/50 border-border focus:border-primary"
                      autoComplete="email"
                    />
                  </div>
                </div>

                {/* Username (register only) */}
                <AnimatePresence>
                  {tab === 'register' && (
                    <motion.div
                      initial={{ opacity: 0, height: 0 }}
                      animate={{ opacity: 1, height: 'auto' }}
                      exit={{ opacity: 0, height: 0 }}
                      transition={{ duration: 0.2 }}
                      className="space-y-1.5 overflow-hidden"
                    >
                      <Label htmlFor="username" className="text-xs font-medium text-muted-foreground uppercase tracking-wide">
                        Username
                      </Label>
                      <div className="relative">
                        <User className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                        <Input
                          id="username"
                          type="text"
                          required={tab === 'register'}
                          value={username}
                          onChange={(e) => setUsername(e.target.value)}
                          placeholder="your_username"
                          className="pl-9 bg-background/50 border-border focus:border-primary"
                          minLength={3}
                          maxLength={50}
                          pattern="[a-zA-Z0-9_]+"
                          autoComplete="username"
                        />
                      </div>
                      <p className="text-xs text-muted-foreground">Letters, numbers, and underscores only</p>
                    </motion.div>
                  )}
                </AnimatePresence>

                {/* Password */}
                <div className="space-y-1.5">
                  <div className="flex items-center justify-between">
                    <Label htmlFor="password" className="text-xs font-medium text-muted-foreground uppercase tracking-wide">
                      Password
                    </Label>
                    <span className="text-xs text-muted-foreground">
                      Min. 8 characters
                    </span>
                  </div>
                  <div className="relative">
                    <Lock className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                    <Input
                      id="password"
                      type={showPassword ? 'text' : 'password'}
                      required
                      value={password}
                      onChange={(e) => setPassword(e.target.value)}
                      placeholder="••••••••"
                      className="pl-9 pr-10 bg-background/50 border-border focus:border-primary"
                      minLength={8}
                      autoComplete={tab === 'login' ? 'current-password' : 'new-password'}
                    />
                    <button
                      type="button"
                      onClick={() => setShowPassword(!showPassword)}
                      className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground transition-colors"
                    >
                      {showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                    </button>
                  </div>
                </div>

                {/* Error */}
                <AnimatePresence>
                  {error && (
                    <motion.div
                      initial={{ opacity: 0, y: -8 }}
                      animate={{ opacity: 1, y: 0 }}
                      exit={{ opacity: 0, y: -8 }}
                      className="flex items-center gap-2 rounded-lg border border-destructive/30 bg-destructive/10 px-3 py-2.5"
                    >
                      <AlertCircle className="h-4 w-4 shrink-0 text-destructive" />
                      <p className="text-sm text-destructive">{error}</p>
                    </motion.div>
                  )}
                </AnimatePresence>

                {/* Submit */}
                <Button
                  type="submit"
                  disabled={loading}
                  className="w-full brand-gradient text-white font-medium shadow-md shadow-primary/20 hover:opacity-90 transition-opacity"
                >
                  {loading ? (
                    <span className="flex items-center gap-2">
                      <svg className="h-4 w-4 animate-spin" viewBox="0 0 24 24" fill="none">
                        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                      </svg>
                      {tab === 'login' ? 'Signing in…' : 'Creating account…'}
                    </span>
                  ) : (
                    <span className="flex items-center gap-2">
                      {tab === 'login' ? 'Sign In' : 'Create Account'}
                      <ArrowRight className="h-4 w-4" />
                    </span>
                  )}
                </Button>
              </motion.form>
            </AnimatePresence>

            {/* Divider */}
            <div className="relative my-5">
              <div className="absolute inset-0 flex items-center">
                <div className="w-full border-t border-border" />
              </div>
              <div className="relative flex justify-center text-xs">
                <span className="bg-card px-3 text-muted-foreground">or</span>
              </div>
            </div>

            {/* Guest */}
            <button
              type="button"
              onClick={handleGuest}
              disabled={!isReady}
              className="flex w-full items-center justify-center gap-2 rounded-lg border border-border bg-muted/30 py-2.5 text-sm text-muted-foreground transition-colors hover:border-primary/30 hover:bg-muted/50 hover:text-foreground disabled:opacity-50"
            >
              <Sparkles className="h-4 w-4" />
              Continue as Guest
            </button>
          </div>
        </div>

        {/* Footer note */}
        <p className="mt-5 text-center text-xs text-muted-foreground">
          AI-powered analysis. Paper trading only. Not financial advice.
        </p>
      </motion.div>
    </div>
  )
}
