'use client'

import { useRef, useEffect, useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import Link from 'next/link'

// ── WebGL Lightning (exact from design, hue=220 blue) ────────────────────────
const Lightning: React.FC<{
  hue?: number
  xOffset?: number
  speed?: number
  intensity?: number
  size?: number
}> = ({ hue = 220, xOffset = 0, speed = 1.6, intensity = 0.6, size = 2 }) => {
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

  return <canvas ref={canvasRef} className="w-full h-full relative" />
}

// ── Feature Item (exact structure from design) ────────────────────────────────
interface FeatureItemProps {
  name: string
  value: string
  position: string
}

const FeatureItem: React.FC<FeatureItemProps> = ({ name, value, position }) => (
  <div className={`absolute ${position} z-10 group transition-all duration-300 hover:scale-110`}>
    <div className="flex items-center gap-2 relative">
      <div className="relative">
        <div className="w-2 h-2 bg-white rounded-full group-hover:animate-pulse" />
        <div className="absolute -inset-1 bg-white/20 rounded-full blur-sm opacity-70 group-hover:opacity-100 transition-opacity duration-300" />
      </div>
      <div className="text-white relative">
        <div className="font-medium group-hover:text-white transition-colors duration-300">{name}</div>
        <div className="text-white/70 text-sm group-hover:text-white/70 transition-colors duration-300">{value}</div>
        <div className="absolute -inset-2 bg-white/10 rounded-lg blur-md opacity-70 group-hover:opacity-100 transition-opacity duration-300 -z-10" />
      </div>
    </div>
  </div>
)

// ── Landing Page ──────────────────────────────────────────────────────────────
export default function LandingPage() {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false)

  const containerVariants = {
    hidden: { opacity: 0 },
    visible: {
      opacity: 1,
      transition: { staggerChildren: 0.3, delayChildren: 0.2 },
    },
  }

  const itemVariants = {
    hidden: { y: 20, opacity: 0 },
    visible: {
      y: 0,
      opacity: 1,
      transition: { duration: 0.5, ease: 'easeOut' },
    },
  }

  return (
    <div className="relative w-full bg-black text-white overflow-hidden">
      <div className="relative z-20 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6 h-screen">

        {/* ── Navigation (exact from design) ── */}
        <motion.div
          initial={{ y: -20, opacity: 0 }}
          animate={{ y: 0, opacity: 1 }}
          transition={{ duration: 0.5 }}
          className="px-4 backdrop-blur-3xl bg-black/50 rounded-2xl py-4 flex justify-between items-center mb-12"
        >
          {/* Left: logo + nav links */}
          <div className="flex items-center">
            <div className="flex items-center gap-2.5">
              <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-gradient-to-br from-blue-500 to-purple-600">
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
              <span className="font-semibold text-sm">Option Oracle</span>
            </div>
            <div className="hidden md:flex items-center space-x-2 ml-8">
              <button className="px-4 py-2 bg-gray-800/50 hover:bg-gray-700/50 rounded-full text-sm transition-colors">
                Home
              </button>
              <button className="px-4 py-2 text-sm text-white/70 hover:text-white transition-colors">Features</button>
              <button className="px-4 py-2 text-sm text-white/70 hover:text-white transition-colors">Pricing</button>
              <button className="px-4 py-2 text-sm text-white/70 hover:text-white transition-colors">Docs</button>
            </div>
          </div>

          {/* Right: Register + Login */}
          <div className="flex items-center space-x-3">
            <Link
              href="/auth"
              className="hidden md:block px-4 py-2 text-sm text-white/70 hover:text-white transition-colors"
              onClick={() => {}}
            >
              Register
            </Link>
            <Link
              href="/auth"
              className="px-5 py-2 bg-white text-black rounded-full text-sm font-semibold hover:bg-white/90 transition-colors shadow-lg shadow-white/10"
            >
              Login
            </Link>
            {/* Mobile menu button */}
            <button
              className="md:hidden p-2"
              onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
            >
              {mobileMenuOpen ? (
                <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              ) : (
                <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
                </svg>
              )}
            </button>
          </div>
        </motion.div>

        {/* Mobile menu */}
        <AnimatePresence>
          {mobileMenuOpen && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="md:hidden fixed inset-0 z-50 bg-black/95 backdrop-blur-lg flex flex-col items-center justify-center space-y-6 text-lg"
            >
              <button
                className="absolute top-6 right-6 p-2"
                onClick={() => setMobileMenuOpen(false)}
              >
                <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
              <button className="px-6 py-3 bg-gray-800/50 rounded-full">Home</button>
              <button className="px-6 py-3 text-white/70">Features</button>
              <button className="px-6 py-3 text-white/70">Pricing</button>
              <button className="px-6 py-3 text-white/70">Docs</button>
              <Link href="/auth" onClick={() => setMobileMenuOpen(false)} className="px-6 py-3 text-white/70">Register</Link>
              <Link href="/auth" onClick={() => setMobileMenuOpen(false)} className="px-8 py-3 bg-white text-black rounded-full font-semibold">Login</Link>
            </motion.div>
          )}
        </AnimatePresence>

        {/* ── Feature items floating around hero ── */}
        <motion.div
          variants={containerVariants}
          initial="hidden"
          animate="visible"
          className="w-full z-10 top-[30%] relative"
        >
          <motion.div variants={itemVariants}>
            <FeatureItem name="AI Analysis" value="GPT-4 powered" position="left-0 sm:left-10 top-40" />
          </motion.div>
          <motion.div variants={itemVariants}>
            <FeatureItem name="Real-time Data" value="Live market feed" position="left-1/4 top-24" />
          </motion.div>
          <motion.div variants={itemVariants}>
            <FeatureItem name="Options Flow" value="Smart money tracker" position="right-1/4 top-24" />
          </motion.div>
          <motion.div variants={itemVariants}>
            <FeatureItem name="Risk Engine" value="Auto position sizing" position="right-0 sm:right-10 top-40" />
          </motion.div>
        </motion.div>

        {/* ── Main hero content ── */}
        <motion.div
          variants={containerVariants}
          initial="hidden"
          animate="visible"
          className="relative z-30 flex flex-col items-center text-center max-w-4xl mx-auto"
        >
          {/* Badge */}
          <motion.button
            variants={itemVariants}
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            className="flex items-center space-x-2 px-4 py-2 bg-white/5 hover:bg-white/10 backdrop-blur-sm rounded-full text-sm mb-6 transition-all duration-300 group"
          >
            <span>AI-powered options intelligence</span>
            <svg width="16" height="16" viewBox="0 0 16 16" fill="none" className="transform group-hover:translate-x-1 transition-transform duration-300">
              <path d="M8 3L13 8L8 13M13 8H3" stroke="white" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
            </svg>
          </motion.button>

          <motion.h1
            variants={itemVariants}
            className="text-5xl md:text-7xl font-light mb-2"
          >
            Option Oracle
          </motion.h1>

          <motion.h2
            variants={itemVariants}
            className="text-3xl md:text-5xl pb-3 font-light bg-gradient-to-r from-gray-100 via-gray-200 to-gray-300 bg-clip-text text-transparent"
          >
            Trade with AI Precision
          </motion.h2>

          <motion.p
            variants={itemVariants}
            className="text-white/50 mb-9 max-w-2xl"
          >
            Real-time AI analysis of options flow, technicals, and market sentiment.
            Make smarter trades — not more of them.
          </motion.p>

          {/* CTA */}
          <motion.div
            variants={itemVariants}
            className="mt-[60px] sm:mt-[80px] flex items-center gap-4"
          >
            <Link
              href="/auth"
              className="px-8 py-3 bg-white text-black rounded-full font-semibold hover:bg-white/90 transition-colors shadow-lg"
            >
              Get Started Free
            </Link>
            <Link
              href="/auth"
              className="px-8 py-3 bg-white/10 backdrop-blur-sm rounded-full hover:bg-white/20 transition-colors text-white"
            >
              Sign In
            </Link>
          </motion.div>

          {/* Stats */}
          <motion.div
            variants={itemVariants}
            className="mt-8 flex items-center gap-8 text-sm text-white/40"
          >
            <span><strong className="text-white font-mono">12K+</strong> Traders</span>
            <span className="h-1 w-1 rounded-full bg-white/20" />
            <span><strong className="text-white font-mono">94.2%</strong> Accuracy</span>
            <span className="h-1 w-1 rounded-full bg-white/20" />
            <span><strong className="text-white font-mono">&lt;50ms</strong> Latency</span>
          </motion.div>
        </motion.div>
      </div>

      {/* ── Background (exact from design) ── */}
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ duration: 1 }}
        className="absolute inset-0 z-0"
      >
        {/* Dark overlay */}
        <div className="absolute inset-0 bg-black/80" />

        {/* Glowing circle */}
        <div className="absolute top-[55%] left-1/2 transform -translate-x-1/2 -translate-y-1/2 w-[800px] h-[800px] rounded-full bg-gradient-to-b from-blue-500/20 to-purple-600/10 blur-3xl" />

        {/* Lightning beam */}
        <div className="absolute top-0 w-[100%] left-1/2 transform -translate-x-1/2 h-full">
          <Lightning hue={220} xOffset={0} speed={1.6} intensity={0.6} size={2} />
        </div>

        {/* Sphere (exact from design) */}
        <div
          className="z-10 absolute top-[55%] left-1/2 transform -translate-x-1/2 -translate-y-1/2 w-[600px] h-[600px] backdrop-blur-3xl rounded-full"
          style={{
            background: 'radial-gradient(circle at 25% 90%, #1e386b 15%, #000000de 70%, #000000ed 100%)',
          }}
        />
      </motion.div>
    </div>
  )
}
