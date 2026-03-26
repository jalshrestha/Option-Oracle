'use client'

import { useRef, useEffect, useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import Link from 'next/link'
import { ArrowRight, TrendingUp, Zap, Shield, Activity } from 'lucide-react'

// ─── WebGL Lightning ──────────────────────────────────────────────────────────

const Lightning: React.FC<{
  hue?: number
  xOffset?: number
  speed?: number
  intensity?: number
  size?: number
}> = ({ hue = 260, xOffset = 0, speed = 1.4, intensity = 0.5, size = 2 }) => {
  const canvasRef = useRef<HTMLCanvasElement>(null)

  useEffect(() => {
    const canvas = canvasRef.current
    if (!canvas) return
    const resizeCanvas = () => {
      canvas.width = canvas.clientWidth
      canvas.height = canvas.clientHeight
    }
    resizeCanvas()
    window.addEventListener('resize', resizeCanvas)
    const gl = canvas.getContext('webgl')
    if (!gl) return

    const vertSrc = `attribute vec2 aPosition;void main(){gl_Position=vec4(aPosition,0.0,1.0);}`
    const fragSrc = `precision mediump float;uniform vec2 iResolution;uniform float iTime;uniform float uHue;uniform float uXOffset;uniform float uSpeed;uniform float uIntensity;uniform float uSize;#define OCTAVE_COUNT 10\nvec3 hsv2rgb(vec3 c){vec3 rgb=clamp(abs(mod(c.x*6.0+vec3(0.0,4.0,2.0),6.0)-3.0)-1.0,0.0,1.0);return c.z*mix(vec3(1.0),rgb,c.y);}float hash11(float p){p=fract(p*.1031);p*=p+33.33;p*=p+p;return fract(p);}float hash12(vec2 p){vec3 p3=fract(vec3(p.xyx)*.1031);p3+=dot(p3,p3.yzx+33.33);return fract((p3.x+p3.y)*p3.z);}mat2 rotate2d(float theta){float c=cos(theta);float s=sin(theta);return mat2(c,-s,s,c);}float noise(vec2 p){vec2 ip=floor(p);vec2 fp=fract(p);float a=hash12(ip);float b=hash12(ip+vec2(1.0,0.0));float c2=hash12(ip+vec2(0.0,1.0));float d=hash12(ip+vec2(1.0,1.0));vec2 t=smoothstep(0.0,1.0,fp);return mix(mix(a,b,t.x),mix(c2,d,t.x),t.y);}float fbm(vec2 p){float value=0.0;float amplitude=0.5;for(int i=0;i<OCTAVE_COUNT;++i){value+=amplitude*noise(p);p*=rotate2d(0.45);p*=2.0;amplitude*=0.5;}return value;}void mainImage(out vec4 fragColor,in vec2 fragCoord){vec2 uv=fragCoord/iResolution.xy;uv=2.0*uv-1.0;uv.x*=iResolution.x/iResolution.y;uv.x+=uXOffset;uv+=2.0*fbm(uv*uSize+0.8*iTime*uSpeed)-1.0;float dist=abs(uv.x);vec3 baseColor=hsv2rgb(vec3(uHue/360.0,0.7,0.8));vec3 col=baseColor*pow(mix(0.0,0.07,hash11(iTime*uSpeed))/dist,1.0)*uIntensity;fragColor=vec4(col,1.0);}void main(){mainImage(gl_FragColor,gl_FragCoord.xy);}`

    const compile = (src: string, type: number) => {
      const s = gl.createShader(type)!
      gl.shaderSource(s, src)
      gl.compileShader(s)
      return s
    }
    const vs = compile(vertSrc, gl.VERTEX_SHADER)
    const fs = compile(fragSrc, gl.FRAGMENT_SHADER)
    const prog = gl.createProgram()!
    gl.attachShader(prog, vs)
    gl.attachShader(prog, fs)
    gl.linkProgram(prog)
    gl.useProgram(prog)

    const verts = new Float32Array([-1, -1, 1, -1, -1, 1, -1, 1, 1, -1, 1, 1])
    const buf = gl.createBuffer()
    gl.bindBuffer(gl.ARRAY_BUFFER, buf)
    gl.bufferData(gl.ARRAY_BUFFER, verts, gl.STATIC_DRAW)
    const aPos = gl.getAttribLocation(prog, 'aPosition')
    gl.enableVertexAttribArray(aPos)
    gl.vertexAttribPointer(aPos, 2, gl.FLOAT, false, 0, 0)

    const uRes = gl.getUniformLocation(prog, 'iResolution')
    const uTime = gl.getUniformLocation(prog, 'iTime')
    const uHueLoc = gl.getUniformLocation(prog, 'uHue')
    const uXOff = gl.getUniformLocation(prog, 'uXOffset')
    const uSpd = gl.getUniformLocation(prog, 'uSpeed')
    const uInt = gl.getUniformLocation(prog, 'uIntensity')
    const uSz = gl.getUniformLocation(prog, 'uSize')

    const start = performance.now()
    let raf = 0
    const render = () => {
      resizeCanvas()
      gl.viewport(0, 0, canvas.width, canvas.height)
      gl.uniform2f(uRes, canvas.width, canvas.height)
      gl.uniform1f(uTime, (performance.now() - start) / 1000)
      gl.uniform1f(uHueLoc, hue)
      gl.uniform1f(uXOff, xOffset)
      gl.uniform1f(uSpd, speed)
      gl.uniform1f(uInt, intensity)
      gl.uniform1f(uSz, size)
      gl.drawArrays(gl.TRIANGLES, 0, 6)
      raf = requestAnimationFrame(render)
    }
    raf = requestAnimationFrame(render)
    return () => {
      window.removeEventListener('resize', resizeCanvas)
      cancelAnimationFrame(raf)
    }
  }, [hue, xOffset, speed, intensity, size])

  return <canvas ref={canvasRef} className="w-full h-full" />
}

// ─── Feature Chip ─────────────────────────────────────────────────────────────

interface FeatureChipProps {
  icon: React.ReactNode
  name: string
  value: string
  position: string
  delay?: number
}

const FeatureChip: React.FC<FeatureChipProps> = ({ icon, name, value, position, delay = 0 }) => (
  <motion.div
    className={`absolute ${position} z-10`}
    initial={{ opacity: 0, scale: 0.8 }}
    animate={{ opacity: 1, scale: 1 }}
    transition={{ duration: 0.6, delay, ease: 'easeOut' }}
  >
    <div className="group flex items-center gap-2.5 rounded-full border border-white/10 bg-white/5 px-3 py-2 backdrop-blur-md transition-all duration-300 hover:border-purple-400/30 hover:bg-white/10">
      <div className="flex h-6 w-6 items-center justify-center rounded-full bg-purple-500/20 text-purple-300">
        {icon}
      </div>
      <div>
        <div className="text-xs font-semibold text-white">{name}</div>
        <div className="text-[10px] text-white/50">{value}</div>
      </div>
      <div className="h-1.5 w-1.5 rounded-full bg-emerald-400 shadow-[0_0_6px_2px_rgba(52,211,153,0.5)]" />
    </div>
  </motion.div>
)

// ─── Stat Item ────────────────────────────────────────────────────────────────

const StatItem: React.FC<{ value: string; label: string; delay: number }> = ({ value, label, delay }) => (
  <motion.div
    initial={{ opacity: 0, y: 12 }}
    animate={{ opacity: 1, y: 0 }}
    transition={{ duration: 0.5, delay }}
    className="flex flex-col items-center gap-1"
  >
    <span className="font-mono text-xl font-bold text-white">{value}</span>
    <span className="text-xs text-white/40 tracking-wide">{label}</span>
  </motion.div>
)

// ─── Landing Page ─────────────────────────────────────────────────────────────

export default function LandingPage() {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false)

  return (
    <div className="relative w-full min-h-screen bg-black text-white overflow-hidden">
      {/* ── Navigation ── */}
      <motion.nav
        initial={{ y: -20, opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
        transition={{ duration: 0.5 }}
        className="absolute top-0 left-0 right-0 z-50 flex items-center justify-between px-6 py-5 lg:px-12"
      >
        {/* Brand */}
        <Link href="/landing" className="flex items-center gap-2.5 group">
          <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-gradient-to-br from-[#7c6ff7] to-[#0ea5e9] shadow-lg shadow-purple-500/25">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" className="text-white">
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
          <span className="text-base font-semibold tracking-tight text-white">
            Option <span className="text-purple-400">Oracle</span>
          </span>
        </Link>

        {/* Desktop nav */}
        <div className="hidden md:flex items-center gap-3">
          <Link
            href="/auth"
            className="px-4 py-2 text-sm text-white/70 hover:text-white transition-colors"
          >
            Sign In
          </Link>
          <Link
            href="/auth"
            className="flex items-center gap-1.5 rounded-full bg-gradient-to-r from-[#7c6ff7] to-[#0ea5e9] px-5 py-2 text-sm font-medium text-white shadow-lg shadow-purple-500/25 transition-all hover:opacity-90 hover:shadow-purple-500/40"
          >
            Get Started
            <ArrowRight className="h-3.5 w-3.5" />
          </Link>
        </div>

        {/* Mobile menu button */}
        <button
          className="md:hidden p-2 text-white/70"
          onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
        >
          <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            {mobileMenuOpen
              ? <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              : <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
            }
          </svg>
        </button>
      </motion.nav>

      {/* Mobile menu */}
      <AnimatePresence>
        {mobileMenuOpen && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 z-40 flex flex-col items-center justify-center gap-6 bg-black/95 backdrop-blur-xl text-lg"
          >
            <Link href="/auth" onClick={() => setMobileMenuOpen(false)} className="text-white/70 hover:text-white">Sign In</Link>
            <Link href="/auth" onClick={() => setMobileMenuOpen(false)} className="rounded-full bg-gradient-to-r from-[#7c6ff7] to-[#0ea5e9] px-8 py-3 text-white font-medium">Get Started</Link>
          </motion.div>
        )}
      </AnimatePresence>

      {/* ── Hero Content ── */}
      <div className="relative z-20 flex h-screen flex-col items-center justify-center px-4 text-center">

        {/* Feature chips — floating around hero */}
        <div className="relative w-full max-w-4xl mx-auto">
          <FeatureChip
            icon={<Zap className="h-3 w-3" />}
            name="AI Analysis"
            value="GPT-4 powered"
            position="left-0 sm:left-4 top-[-120px] sm:top-[-140px]"
            delay={0.6}
          />
          <FeatureChip
            icon={<Activity className="h-3 w-3" />}
            name="Real-time Data"
            value="Live market feed"
            position="right-0 sm:right-4 top-[-120px] sm:top-[-140px]"
            delay={0.75}
          />
          <FeatureChip
            icon={<TrendingUp className="h-3 w-3" />}
            name="Options Flow"
            value="Smart money tracker"
            position="left-0 sm:left-4 bottom-[-120px] sm:bottom-[-140px]"
            delay={0.9}
          />
          <FeatureChip
            icon={<Shield className="h-3 w-3" />}
            name="Risk Engine"
            value="Auto position sizing"
            position="right-0 sm:right-4 bottom-[-120px] sm:bottom-[-140px]"
            delay={1.05}
          />

          {/* Badge */}
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.2 }}
            className="mb-6 inline-flex items-center gap-2 rounded-full border border-purple-500/20 bg-purple-500/10 px-4 py-1.5 text-xs text-purple-300"
          >
            <span className="h-1.5 w-1.5 rounded-full bg-purple-400 animate-pulse" />
            AI-Powered Options Intelligence
          </motion.div>

          {/* Headline */}
          <motion.h1
            initial={{ opacity: 0, y: 16 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.3 }}
            className="text-6xl sm:text-7xl md:text-8xl font-light tracking-tight mb-3"
          >
            Option Oracle
          </motion.h1>

          <motion.h2
            initial={{ opacity: 0, y: 16 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.42 }}
            className="text-3xl sm:text-4xl md:text-5xl font-light pb-2"
            style={{
              background: 'linear-gradient(135deg, #7c6ff7 0%, #4f46e5 50%, #0ea5e9 100%)',
              WebkitBackgroundClip: 'text',
              WebkitTextFillColor: 'transparent',
              backgroundClip: 'text',
            }}
          >
            Trade with AI Precision
          </motion.h2>

          {/* Body */}
          <motion.p
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.54 }}
            className="mx-auto mt-4 max-w-xl text-base text-white/50 leading-relaxed"
          >
            Real-time AI analysis of options flow, technicals, and market sentiment.
            Make smarter trades — not more of them.
          </motion.p>

          {/* CTAs */}
          <motion.div
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.66 }}
            className="mt-8 flex flex-col sm:flex-row items-center justify-center gap-3"
          >
            <Link
              href="/auth"
              className="flex items-center gap-2 rounded-full bg-white px-7 py-3 text-sm font-semibold text-black shadow-lg transition-all hover:bg-white/90 hover:shadow-white/20"
            >
              Start Trading Free
              <ArrowRight className="h-4 w-4" />
            </Link>
            <button className="flex items-center gap-2 rounded-full border border-white/15 bg-white/5 px-7 py-3 text-sm text-white/70 backdrop-blur transition-all hover:border-white/25 hover:bg-white/10 hover:text-white">
              Watch Demo
            </button>
          </motion.div>

          {/* Stats */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ duration: 0.6, delay: 0.85 }}
            className="mt-10 flex items-center justify-center gap-10"
          >
            <StatItem value="12K+" label="Traders" delay={0.9} />
            <div className="h-8 w-px bg-white/10" />
            <StatItem value="94.2%" label="Signal Accuracy" delay={1.0} />
            <div className="h-8 w-px bg-white/10" />
            <StatItem value="<50ms" label="Latency" delay={1.1} />
          </motion.div>
        </div>
      </div>

      {/* ── Background ── */}
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ duration: 1.2 }}
        className="absolute inset-0 z-0"
      >
        {/* Dark overlay */}
        <div className="absolute inset-0 bg-black/75" />

        {/* Ambient glow */}
        <div className="absolute top-[55%] left-1/2 -translate-x-1/2 -translate-y-1/2 h-[700px] w-[700px] rounded-full bg-gradient-to-b from-purple-600/15 to-indigo-600/8 blur-3xl" />

        {/* Lightning beam */}
        <div className="absolute top-0 left-1/2 -translate-x-1/2 w-full h-full">
          <Lightning hue={260} xOffset={0} speed={1.4} intensity={0.5} size={2} />
        </div>

        {/* Sphere */}
        <div className="absolute top-[55%] left-1/2 -translate-x-1/2 -translate-y-1/2 h-[500px] w-[500px] rounded-full backdrop-blur-3xl"
          style={{
            background: 'radial-gradient(circle at 25% 90%, #1e1b4b 15%, #000000de 70%, #000000ed 100%)',
          }}
        />

        {/* Edge vignette */}
        <div className="absolute inset-0 [background:radial-gradient(ellipse_80%_60%_at_50%_30%,transparent_40%,rgba(0,0,0,0.7)_100%)]" />
      </motion.div>
    </div>
  )
}
