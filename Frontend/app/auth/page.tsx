'use client'

import { useState, useRef, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { motion, AnimatePresence } from 'framer-motion'
import {
  Eye, EyeOff, Sparkles, ArrowRight, User, Mail, Lock, AlertCircle, Github,
} from 'lucide-react'
import { useAuth } from '@/providers/auth-provider'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Button } from '@/components/ui/button'
import { cn } from '@/lib/utils'

// ── Google icon (SVG, lucide doesn't have it) ─────────────────────────────────
const GoogleIcon = () => (
  <svg className="h-4 w-4" viewBox="0 0 24 24" fill="none">
    <path d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" fill="#4285F4"/>
    <path d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" fill="#34A853"/>
    <path d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l3.66-2.84z" fill="#FBBC05"/>
    <path d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" fill="#EA4335"/>
  </svg>
)

export default function AuthPage() {
  const { login, register, loginAsGuest, isReady } = useAuth()
  const router = useRouter()

  const [tab, setTab] = useState<'login' | 'register'>('login')
  const [email, setEmail] = useState('')
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [showPassword, setShowPassword] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)
  const [oauthNote, setOauthNote] = useState<string | null>(null)

  // ── Rising particles (exact from design) ─────────────────────────────────
  const canvasRef = useRef<HTMLCanvasElement | null>(null)
  useEffect(() => {
    const canvas = canvasRef.current
    const ctx = canvas?.getContext('2d')
    if (!canvas || !ctx) return

    const setSize = () => {
      canvas.width = window.innerWidth
      canvas.height = window.innerHeight
    }
    setSize()

    type P = { x: number; y: number; v: number; o: number }
    let ps: P[] = []
    let raf = 0

    const make = (): P => ({
      x: Math.random() * canvas.width,
      y: Math.random() * canvas.height,
      v: Math.random() * 0.25 + 0.05,
      o: Math.random() * 0.35 + 0.15,
    })

    const init = () => {
      ps = []
      const count = Math.floor((canvas.width * canvas.height) / 9000)
      for (let i = 0; i < count; i++) ps.push(make())
    }

    const draw = () => {
      ctx.clearRect(0, 0, canvas.width, canvas.height)
      ps.forEach((p) => {
        p.y -= p.v
        if (p.y < 0) {
          p.x = Math.random() * canvas.width
          p.y = canvas.height + Math.random() * 40
          p.v = Math.random() * 0.25 + 0.05
          p.o = Math.random() * 0.35 + 0.15
        }
        ctx.fillStyle = `rgba(250,250,250,${p.o})`
        ctx.fillRect(p.x, p.y, 0.7, 2.2)
      })
      raf = requestAnimationFrame(draw)
    }

    const onResize = () => { setSize(); init() }
    window.addEventListener('resize', onResize)
    init()
    raf = requestAnimationFrame(draw)
    return () => {
      window.removeEventListener('resize', onResize)
      cancelAnimationFrame(raf)
    }
  }, [])

  // ── Auth handlers ─────────────────────────────────────────────────────────
  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    setError(null)
    setOauthNote(null)
    setLoading(true)
    try {
      if (tab === 'login') {
        await login(email, password)
      } else {
        await register(email, username, password)
      }
      router.push('/')
    } catch (err: unknown) {
      const raw = (err as Error).message || ''
      const [statusStr, ...rest] = raw.split(':')
      const status = parseInt(statusStr, 10)
      const detail = rest.join(':').trim()

      if (status === 409 || detail.toLowerCase().includes('already') || detail.toLowerCase().includes('taken')) {
        setError('An account with this email or username already exists.')
      } else if (status === 401) {
        setError('Invalid email or password.')
      } else if (status === 422) {
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

  function handleOAuth(provider: 'github' | 'google') {
    setError(null)
    setOauthNote(`${provider === 'github' ? 'GitHub' : 'Google'} login coming soon.`)
    setTimeout(() => setOauthNote(null), 3000)
  }

  async function handleGuest() {
    setLoading(true)
    setError(null)
    try {
      await loginAsGuest()
      router.push('/')
    } catch {
      setError('Unable to start guest session. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <section className="fixed inset-0 bg-black text-white">
      {/* ── CSS animations (exact from design) ── */}
      <style>{`
        .accent-lines{position:absolute;inset:0;pointer-events:none;opacity:.7}
        .hline,.vline{position:absolute;background:#1e3a5f;will-change:transform,opacity}
        .hline{left:0;right:0;height:1px;transform:scaleX(0);transform-origin:50% 50%;animation:drawX .8s cubic-bezier(.22,.61,.36,1) forwards}
        .vline{top:0;bottom:0;width:1px;transform:scaleY(0);transform-origin:50% 0%;animation:drawY .9s cubic-bezier(.22,.61,.36,1) forwards}
        .hline:nth-child(1){top:18%;animation-delay:.12s}
        .hline:nth-child(2){top:50%;animation-delay:.22s}
        .hline:nth-child(3){top:82%;animation-delay:.32s}
        .vline:nth-child(4){left:22%;animation-delay:.42s}
        .vline:nth-child(5){left:50%;animation-delay:.54s}
        .vline:nth-child(6){left:78%;animation-delay:.66s}
        .hline::after,.vline::after{content:"";position:absolute;inset:0;background:linear-gradient(90deg,transparent,rgba(59,130,246,.2),transparent);opacity:0;animation:shimmer .9s ease-out forwards}
        .hline:nth-child(1)::after{animation-delay:.12s}
        .hline:nth-child(2)::after{animation-delay:.22s}
        .hline:nth-child(3)::after{animation-delay:.32s}
        .vline:nth-child(4)::after{animation-delay:.42s}
        .vline:nth-child(5)::after{animation-delay:.54s}
        .vline:nth-child(6)::after{animation-delay:.66s}
        @keyframes drawX{0%{transform:scaleX(0);opacity:0}60%{opacity:.95}100%{transform:scaleX(1);opacity:.7}}
        @keyframes drawY{0%{transform:scaleY(0);opacity:0}60%{opacity:.95}100%{transform:scaleY(1);opacity:.7}}
        @keyframes shimmer{0%{opacity:0}35%{opacity:.25}100%{opacity:0}}
        .card-animate{opacity:0;transform:translateY(20px);animation:fadeUp .8s cubic-bezier(.22,.61,.36,1) .4s forwards}
        @keyframes fadeUp{to{opacity:1;transform:translateY(0)}}
      `}</style>

      {/* ── Vignette ── */}
      <div className="absolute inset-0 pointer-events-none [background:radial-gradient(80%_60%_at_50%_30%,rgba(59,130,246,0.08),transparent_60%)]" />

      {/* ── Animated accent lines ── */}
      <div className="accent-lines">
        <div className="hline" />
        <div className="hline" />
        <div className="hline" />
        <div className="vline" />
        <div className="vline" />
        <div className="vline" />
      </div>

      {/* ── Particles ── */}
      <canvas
        ref={canvasRef}
        className="absolute inset-0 w-full h-full opacity-50 mix-blend-screen pointer-events-none"
      />

      {/* ── Header ── */}
      <header className="absolute left-0 right-0 top-0 z-10 flex items-center justify-between px-6 py-4 border-b border-white/8">
        <div className="flex items-center gap-2.5">
          <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-gradient-to-br from-[#7c6ff7] to-[#0ea5e9]">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" className="text-white">
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
          <span className="text-xs tracking-[0.14em] uppercase text-white/40">Option Oracle</span>
        </div>
        <Button
          variant="outline"
          size="sm"
          className="h-9 rounded-lg border-white/10 bg-white/5 text-white hover:bg-white/10"
        >
          <span className="mr-2 text-sm">Contact</span>
          <ArrowRight className="h-3.5 w-3.5" />
        </Button>
      </header>

      {/* ── Centered card ── */}
      <div className="h-full w-full grid place-items-center px-4">
        <div className="card-animate w-full max-w-sm">

          {/* Tab toggle above card */}
          <div className="mb-4 flex rounded-xl border border-white/10 bg-white/5 p-1">
            {(['login', 'register'] as const).map((t) => (
              <button
                key={t}
                onClick={() => { setTab(t); setError(null); setOauthNote(null) }}
                className={cn(
                  'relative flex-1 rounded-lg py-2 text-sm font-medium transition-all duration-200',
                  tab === t
                    ? 'bg-white/10 text-white shadow-sm'
                    : 'text-white/40 hover:text-white/70'
                )}
              >
                {t === 'login' ? 'Sign In' : 'Create Account'}
              </button>
            ))}
          </div>

          {/* Main card */}
          <div className="rounded-2xl border border-white/10 bg-white/5 backdrop-blur supports-[backdrop-filter]:bg-black/60 overflow-hidden">
            <div className="px-6 pt-6 pb-2">
              <AnimatePresence mode="wait">
                <motion.div
                  key={tab}
                  initial={{ opacity: 0, y: 6 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -6 }}
                  transition={{ duration: 0.15 }}
                >
                  <h2 className="text-2xl font-semibold text-white">
                    {tab === 'login' ? 'Welcome back' : 'Create account'}
                  </h2>
                  <p className="mt-1 text-sm text-white/40">
                    {tab === 'login'
                      ? 'Sign in to your Option Oracle account'
                      : 'Start trading with AI precision today'}
                  </p>
                </motion.div>
              </AnimatePresence>
            </div>

            <div className="px-6 pb-6 pt-4 grid gap-5">
              <AnimatePresence mode="wait">
                <motion.form
                  key={tab}
                  initial={{ opacity: 0, x: tab === 'login' ? -10 : 10 }}
                  animate={{ opacity: 1, x: 0 }}
                  exit={{ opacity: 0, x: tab === 'login' ? 10 : -10 }}
                  transition={{ duration: 0.16 }}
                  onSubmit={handleSubmit}
                  className="grid gap-4"
                >
                  {/* Email */}
                  <div className="grid gap-2">
                    <Label htmlFor="email" className="text-white/60">Email</Label>
                    <div className="relative">
                      <Mail className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-white/30" />
                      <Input
                        id="email"
                        type="email"
                        required
                        value={email}
                        onChange={(e) => setEmail(e.target.value)}
                        placeholder="you@example.com"
                        autoComplete="email"
                        className="pl-10 bg-white/5 border-white/10 text-white placeholder:text-white/25 focus-visible:border-blue-500/50 focus-visible:ring-blue-500/15"
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
                        className="grid gap-2 overflow-hidden"
                      >
                        <Label htmlFor="username" className="text-white/60">Username</Label>
                        <div className="relative">
                          <User className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-white/30" />
                          <Input
                            id="username"
                            type="text"
                            required={tab === 'register'}
                            value={username}
                            onChange={(e) => setUsername(e.target.value)}
                            placeholder="your_username"
                            autoComplete="username"
                            minLength={3}
                            maxLength={50}
                            pattern="[a-zA-Z0-9_]+"
                            className="pl-10 bg-white/5 border-white/10 text-white placeholder:text-white/25 focus-visible:border-blue-500/50 focus-visible:ring-blue-500/15"
                          />
                        </div>
                        <p className="text-xs text-white/25">Letters, numbers, and underscores only</p>
                      </motion.div>
                    )}
                  </AnimatePresence>

                  {/* Password */}
                  <div className="grid gap-2">
                    <div className="flex items-center justify-between">
                      <Label htmlFor="password" className="text-white/60">Password</Label>
                      {tab === 'login' && (
                        <a href="#" className="text-sm text-white/40 hover:text-white/70 transition-colors">
                          Forgot password?
                        </a>
                      )}
                    </div>
                    <div className="relative">
                      <Lock className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-white/30" />
                      <Input
                        id="password"
                        type={showPassword ? 'text' : 'password'}
                        required
                        value={password}
                        onChange={(e) => setPassword(e.target.value)}
                        placeholder="••••••••"
                        minLength={8}
                        autoComplete={tab === 'login' ? 'current-password' : 'new-password'}
                        className="pl-10 pr-10 bg-white/5 border-white/10 text-white placeholder:text-white/25 focus-visible:border-blue-500/50 focus-visible:ring-blue-500/15"
                      />
                      <button
                        type="button"
                        aria-label={showPassword ? 'Hide password' : 'Show password'}
                        className="absolute right-2 top-1/2 -translate-y-1/2 p-2 rounded-md text-white/40 hover:text-white/70 transition-colors"
                        onClick={() => setShowPassword((v) => !v)}
                      >
                        {showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                      </button>
                    </div>
                  </div>

                  {/* Error */}
                  <AnimatePresence>
                    {error && (
                      <motion.div
                        initial={{ opacity: 0, y: -6 }}
                        animate={{ opacity: 1, y: 0 }}
                        exit={{ opacity: 0, y: -6 }}
                        className="flex items-start gap-2 rounded-lg border border-red-900/40 bg-red-950/30 px-3 py-2.5"
                      >
                        <AlertCircle className="h-4 w-4 mt-0.5 shrink-0 text-red-400" />
                        <p className="text-sm text-red-400">{error}</p>
                      </motion.div>
                    )}
                  </AnimatePresence>

                  {/* Submit */}
                  <Button
                    type="submit"
                    disabled={loading}
                    className="w-full h-10 rounded-lg bg-white text-black hover:bg-white/90 font-medium"
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
                      tab === 'login' ? 'Continue' : 'Create Account'
                    )}
                  </Button>
                </motion.form>
              </AnimatePresence>

              {/* Divider */}
              <div className="relative">
                <div className="absolute inset-0 flex items-center">
                  <div className="w-full border-t border-white/10" />
                </div>
                <div className="relative flex justify-center">
                  <span className="bg-black/60 px-2 text-[11px] uppercase tracking-widest text-white/30">or</span>
                </div>
              </div>

              {/* Social login */}
              <div className="grid grid-cols-2 gap-3">
                <Button
                  type="button"
                  variant="outline"
                  onClick={() => handleOAuth('github')}
                  className="h-10 rounded-lg border-white/10 bg-white/5 text-white hover:bg-white/10 hover:text-white"
                >
                  <Github className="h-4 w-4 mr-2" />
                  GitHub
                </Button>
                <Button
                  type="button"
                  variant="outline"
                  onClick={() => handleOAuth('google')}
                  className="h-10 rounded-lg border-white/10 bg-white/5 text-white hover:bg-white/10 hover:text-white"
                >
                  <GoogleIcon />
                  <span className="ml-2">Google</span>
                </Button>
              </div>

              {/* OAuth coming soon note */}
              <AnimatePresence>
                {oauthNote && (
                  <motion.p
                    initial={{ opacity: 0, y: -4 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0 }}
                    className="text-center text-xs text-white/30"
                  >
                    {oauthNote}
                  </motion.p>
                )}
              </AnimatePresence>

              {/* Guest */}
              <button
                type="button"
                onClick={handleGuest}
                disabled={!isReady}
                className="flex w-full items-center justify-center gap-2 rounded-lg border border-white/10 bg-transparent py-2.5 text-sm text-white/40 transition-colors hover:border-white/20 hover:text-white/70 disabled:opacity-40"
              >
                <Sparkles className="h-3.5 w-3.5" />
                Continue as Guest
              </button>
            </div>

            {/* Footer */}
            <div className="flex items-center justify-center px-6 pb-5 text-sm text-white/40">
              {tab === 'login' ? (
                <>
                  Don&apos;t have an account?{' '}
                  <button
                    onClick={() => { setTab('register'); setError(null) }}
                    className="ml-1 text-white/70 hover:underline"
                  >
                    Create one
                  </button>
                </>
              ) : (
                <>
                  Already have an account?{' '}
                  <button
                    onClick={() => { setTab('login'); setError(null) }}
                    className="ml-1 text-white/70 hover:underline"
                  >
                    Sign in
                  </button>
                </>
              )}
            </div>
          </div>

          <p className="mt-4 text-center text-[10px] uppercase tracking-widest text-white/20">
            AI-powered analysis · Paper trading only · Not financial advice
          </p>
        </div>
      </div>
    </section>
  )
}
