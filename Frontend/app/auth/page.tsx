'use client'

import { useState, useRef, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { motion, AnimatePresence } from 'framer-motion'
import {
  Eye, EyeOff, Sparkles, ArrowRight, User, Mail, Lock, AlertCircle,
} from 'lucide-react'
import { useAuth } from '@/providers/auth-provider'
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

  // ── Rising particle canvas ────────────────────────────────────────────────
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
      v: Math.random() * 0.3 + 0.05,
      o: Math.random() * 0.3 + 0.1,
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
          p.v = Math.random() * 0.3 + 0.05
          p.o = Math.random() * 0.3 + 0.1
        }
        ctx.fillStyle = `rgba(124,111,247,${p.o})`
        ctx.fillRect(p.x, p.y, 0.8, 2.4)
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

  async function handleGuest() {
    router.push('/')
  }

  return (
    <section className="fixed inset-0 bg-[#0a0a0f] text-white overflow-hidden">
      {/* ── Inline CSS animations ── */}
      <style>{`
        .accent-wrap{position:absolute;inset:0;pointer-events:none}
        .hline,.vline{position:absolute;background:#7c6ff7;will-change:transform,opacity}
        .hline{left:0;right:0;height:1px;transform:scaleX(0);transform-origin:50%;animation:drawX .9s cubic-bezier(.22,.61,.36,1) forwards}
        .vline{top:0;bottom:0;width:1px;transform:scaleY(0);transform-origin:50% 0;animation:drawY 1s cubic-bezier(.22,.61,.36,1) forwards}
        .hline:nth-child(1){top:18%;animation-delay:.1s}
        .hline:nth-child(2){top:50%;animation-delay:.22s}
        .hline:nth-child(3){top:82%;animation-delay:.34s}
        .vline:nth-child(4){left:22%;animation-delay:.44s}
        .vline:nth-child(5){left:50%;animation-delay:.56s}
        .vline:nth-child(6){left:78%;animation-delay:.68s}
        @keyframes drawX{0%{transform:scaleX(0);opacity:0}60%{opacity:.14}100%{transform:scaleX(1);opacity:.08}}
        @keyframes drawY{0%{transform:scaleY(0);opacity:0}60%{opacity:.14}100%{transform:scaleY(1);opacity:.08}}
        .card-animate{opacity:0;transform:translateY(20px);animation:fadeUp .8s cubic-bezier(.22,.61,.36,1) .3s forwards}
        @keyframes fadeUp{to{opacity:1;transform:translateY(0)}}
      `}</style>

      {/* ── Ambient vignette ── */}
      <div className="absolute inset-0 pointer-events-none [background:radial-gradient(70%_50%_at_50%_30%,rgba(124,111,247,0.07),transparent_65%)]" />

      {/* ── Animated accent grid ── */}
      <div className="accent-wrap">
        <div className="hline" />
        <div className="hline" />
        <div className="hline" />
        <div className="vline" />
        <div className="vline" />
        <div className="vline" />
      </div>

      {/* ── Particle canvas ── */}
      <canvas
        ref={canvasRef}
        className="absolute inset-0 w-full h-full opacity-60 mix-blend-screen pointer-events-none"
      />

      {/* ── Top header bar ── */}
      <header className="absolute left-0 right-0 top-0 z-10 flex items-center justify-between px-6 py-4 border-b border-[#7c6ff7]/10">
        <div className="flex items-center gap-2.5">
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-gradient-to-br from-[#7c6ff7] to-[#0ea5e9]">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" className="text-white">
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
          <span className="text-sm font-semibold tracking-tight">
            Option <span className="text-[#7c6ff7]">Oracle</span>
          </span>
        </div>
        <button className="h-8 rounded-lg border border-[#7c6ff7]/20 bg-transparent px-4 text-xs text-white/40 transition hover:border-[#7c6ff7]/40 hover:text-white/70">
          Contact
        </button>
      </header>

      {/* ── Centered card ── */}
      <div className="h-full w-full grid place-items-center px-4">
        <div className="card-animate w-full max-w-sm">
          <div className="overflow-hidden rounded-2xl border border-[#7c6ff7]/15 bg-[#111118]/70 shadow-2xl shadow-purple-950/40 backdrop-blur-xl supports-[backdrop-filter]:bg-[#111118]/60">

            {/* Tab strip */}
            <div className="flex border-b border-white/5">
              {(['login', 'register'] as const).map((t) => (
                <button
                  key={t}
                  onClick={() => { setTab(t); setError(null) }}
                  className={cn(
                    'relative flex-1 py-4 text-sm font-medium transition-colors',
                    tab === t ? 'text-white' : 'text-white/35 hover:text-white/65'
                  )}
                >
                  {t === 'login' ? 'Sign In' : 'Create Account'}
                  {tab === t && (
                    <motion.div
                      layoutId="auth-tab-indicator"
                      className="absolute bottom-0 left-0 right-0 h-0.5"
                      style={{ background: 'linear-gradient(135deg, #7c6ff7 0%, #4f46e5 50%, #0ea5e9 100%)' }}
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
                  initial={{ opacity: 0, x: tab === 'login' ? -12 : 12 }}
                  animate={{ opacity: 1, x: 0 }}
                  exit={{ opacity: 0, x: tab === 'login' ? 12 : -12 }}
                  transition={{ duration: 0.18 }}
                  onSubmit={handleSubmit}
                  className="space-y-4"
                >
                  {/* Email */}
                  <div className="space-y-1.5">
                    <Label htmlFor="email" className="text-[10px] font-semibold uppercase tracking-widest text-white/30">
                      Email
                    </Label>
                    <div className="relative">
                      <Mail className="absolute left-3 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-white/25" />
                      <Input
                        id="email"
                        type="email"
                        required
                        value={email}
                        onChange={(e) => setEmail(e.target.value)}
                        placeholder="you@example.com"
                        autoComplete="email"
                        className="h-10 pl-9 bg-white/5 border-white/8 text-white placeholder:text-white/20 focus-visible:border-[#7c6ff7]/60 focus-visible:ring-[#7c6ff7]/15 rounded-xl"
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
                        <Label htmlFor="username" className="text-[10px] font-semibold uppercase tracking-widest text-white/30">
                          Username
                        </Label>
                        <div className="relative">
                          <User className="absolute left-3 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-white/25" />
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
                            className="h-10 pl-9 bg-white/5 border-white/8 text-white placeholder:text-white/20 focus-visible:border-[#7c6ff7]/60 focus-visible:ring-[#7c6ff7]/15 rounded-xl"
                          />
                        </div>
                        <p className="text-[10px] text-white/20">Letters, numbers, and underscores only</p>
                      </motion.div>
                    )}
                  </AnimatePresence>

                  {/* Password */}
                  <div className="space-y-1.5">
                    <div className="flex items-center justify-between">
                      <Label htmlFor="password" className="text-[10px] font-semibold uppercase tracking-widest text-white/30">
                        Password
                      </Label>
                      <span className="text-[10px] text-white/20">Min. 8 characters</span>
                    </div>
                    <div className="relative">
                      <Lock className="absolute left-3 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-white/25" />
                      <Input
                        id="password"
                        type={showPassword ? 'text' : 'password'}
                        required
                        value={password}
                        onChange={(e) => setPassword(e.target.value)}
                        placeholder="••••••••"
                        minLength={8}
                        autoComplete={tab === 'login' ? 'current-password' : 'new-password'}
                        className="h-10 pl-9 pr-10 bg-white/5 border-white/8 text-white placeholder:text-white/20 focus-visible:border-[#7c6ff7]/60 focus-visible:ring-[#7c6ff7]/15 rounded-xl"
                      />
                      <button
                        type="button"
                        onClick={() => setShowPassword(!showPassword)}
                        className="absolute right-3 top-1/2 -translate-y-1/2 text-white/25 hover:text-white/60 transition-colors"
                      >
                        {showPassword ? <EyeOff className="h-3.5 w-3.5" /> : <Eye className="h-3.5 w-3.5" />}
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
                        className="flex items-start gap-2 rounded-xl border border-red-500/20 bg-red-500/8 px-3 py-2.5"
                      >
                        <AlertCircle className="h-3.5 w-3.5 mt-0.5 shrink-0 text-red-400" />
                        <p className="text-xs leading-relaxed text-red-400">{error}</p>
                      </motion.div>
                    )}
                  </AnimatePresence>

                  {/* Submit */}
                  <button
                    type="submit"
                    disabled={loading}
                    className="flex w-full items-center justify-center gap-2 rounded-xl py-2.5 text-sm font-medium text-white shadow-lg shadow-purple-900/30 transition-opacity hover:opacity-90 disabled:opacity-60"
                    style={{ background: 'linear-gradient(135deg, #7c6ff7 0%, #4f46e5 50%, #0ea5e9 100%)' }}
                  >
                    {loading ? (
                      <>
                        <svg className="h-4 w-4 animate-spin" viewBox="0 0 24 24" fill="none">
                          <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                          <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                        </svg>
                        {tab === 'login' ? 'Signing in…' : 'Creating account…'}
                      </>
                    ) : (
                      <>
                        {tab === 'login' ? 'Sign In' : 'Create Account'}
                        <ArrowRight className="h-4 w-4" />
                      </>
                    )}
                  </button>
                </motion.form>
              </AnimatePresence>

              {/* Divider */}
              <div className="relative my-5">
                <div className="absolute inset-0 flex items-center">
                  <div className="w-full border-t border-white/6" />
                </div>
                <div className="relative flex justify-center text-[10px]">
                  <span className="bg-[#111118] px-3 uppercase tracking-widest text-white/20">or</span>
                </div>
              </div>

              {/* Guest */}
              <button
                type="button"
                onClick={handleGuest}
                disabled={!isReady}
                className="flex w-full items-center justify-center gap-2 rounded-xl border border-white/8 bg-white/3 py-2.5 text-sm text-white/35 transition-all hover:border-[#7c6ff7]/25 hover:bg-white/5 hover:text-white/65 disabled:opacity-40"
              >
                <Sparkles className="h-3.5 w-3.5" />
                Continue as Guest
              </button>
            </div>
          </div>

          {/* Footer */}
          <p className="mt-5 text-center text-[10px] uppercase tracking-widest text-white/15">
            AI-powered analysis · Paper trading only · Not financial advice
          </p>
        </div>
      </div>
    </section>
  )
}
