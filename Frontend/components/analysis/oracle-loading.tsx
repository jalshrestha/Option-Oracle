'use client'

import { useEffect, useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import {
  BarChart3,
  Activity,
  TrendingUp,
  Clock,
  Shield,
} from 'lucide-react'
import { Progress } from '@/components/ui/progress'

const agents = [
  { name: 'Technical Agent', icon: BarChart3, message: 'Analyzing technical indicators...' },
  { name: 'Sentiment Agent', icon: Activity, message: 'Scanning sentiment signals...' },
  { name: 'Flow Agent', icon: TrendingUp, message: 'Evaluating options flow...' },
  { name: 'Historical Agent', icon: Clock, message: 'Reviewing historical patterns...' },
  { name: 'Risk Agent', icon: Shield, message: 'Assessing risk profile...' },
]

interface OracleLoadingProps {
  symbol?: string
}

export function OracleLoading({ symbol }: OracleLoadingProps) {
  const [currentAgent, setCurrentAgent] = useState(0)
  const [progress, setProgress] = useState(0)

  useEffect(() => {
    const agentInterval = setInterval(() => {
      setCurrentAgent((prev) => (prev < agents.length - 1 ? prev + 1 : prev))
    }, 5500)

    const progressInterval = setInterval(() => {
      setProgress((prev) => (prev < 100 ? prev + 0.5 : prev))
    }, 175)

    return () => {
      clearInterval(agentInterval)
      clearInterval(progressInterval)
    }
  }, [])

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-background/80 backdrop-blur-md">
      <div className="w-full max-w-md space-y-8 p-8">
        {/* Animated Neural Network Icon */}
        <div className="flex justify-center">
          <motion.div
            animate={{
              scale: [1, 1.1, 1],
              opacity: [0.8, 1, 0.8],
            }}
            transition={{
              duration: 2,
              repeat: Infinity,
              ease: 'easeInOut',
            }}
            className="flex h-24 w-24 items-center justify-center rounded-full brand-gradient"
          >
            <svg
              width="48"
              height="48"
              viewBox="0 0 24 24"
              fill="none"
              xmlns="http://www.w3.org/2000/svg"
              className="text-white"
            >
              <motion.circle
                cx="12"
                cy="12"
                r="3"
                fill="currentColor"
                animate={{ scale: [1, 1.2, 1] }}
                transition={{ duration: 1.5, repeat: Infinity }}
              />
              <motion.circle
                cx="12"
                cy="4"
                r="2"
                fill="currentColor"
                animate={{ opacity: [0.4, 1, 0.4] }}
                transition={{ duration: 1.2, repeat: Infinity, delay: 0 }}
              />
              <motion.circle
                cx="12"
                cy="20"
                r="2"
                fill="currentColor"
                animate={{ opacity: [0.4, 1, 0.4] }}
                transition={{ duration: 1.2, repeat: Infinity, delay: 0.2 }}
              />
              <motion.circle
                cx="4"
                cy="12"
                r="2"
                fill="currentColor"
                animate={{ opacity: [0.4, 1, 0.4] }}
                transition={{ duration: 1.2, repeat: Infinity, delay: 0.4 }}
              />
              <motion.circle
                cx="20"
                cy="12"
                r="2"
                fill="currentColor"
                animate={{ opacity: [0.4, 1, 0.4] }}
                transition={{ duration: 1.2, repeat: Infinity, delay: 0.6 }}
              />
              <motion.circle
                cx="6"
                cy="6"
                r="1.5"
                fill="currentColor"
                animate={{ opacity: [0.3, 0.8, 0.3] }}
                transition={{ duration: 1.2, repeat: Infinity, delay: 0.1 }}
              />
              <motion.circle
                cx="18"
                cy="6"
                r="1.5"
                fill="currentColor"
                animate={{ opacity: [0.3, 0.8, 0.3] }}
                transition={{ duration: 1.2, repeat: Infinity, delay: 0.3 }}
              />
              <motion.circle
                cx="6"
                cy="18"
                r="1.5"
                fill="currentColor"
                animate={{ opacity: [0.3, 0.8, 0.3] }}
                transition={{ duration: 1.2, repeat: Infinity, delay: 0.5 }}
              />
              <motion.circle
                cx="18"
                cy="18"
                r="1.5"
                fill="currentColor"
                animate={{ opacity: [0.3, 0.8, 0.3] }}
                transition={{ duration: 1.2, repeat: Infinity, delay: 0.7 }}
              />
            </svg>
          </motion.div>
        </div>

        {/* Title */}
        <div className="text-center">
          <h2 className="text-xl font-semibold text-foreground">
            Oracle is thinking
            <motion.span
              animate={{ opacity: [0, 1, 0] }}
              transition={{ duration: 1.5, repeat: Infinity }}
            >
              ...
            </motion.span>
          </h2>
          {symbol && (
            <p className="mt-1 font-mono text-sm text-muted-foreground">
              Analyzing {symbol}
            </p>
          )}
        </div>

        {/* Agent Progress */}
        <div className="space-y-4">
          <div className="flex flex-wrap justify-center gap-2">
            {agents.map((agent, index) => {
              const isActive = index === currentAgent
              const isComplete = index < currentAgent
              const Icon = agent.icon

              return (
                <motion.div
                  key={agent.name}
                  initial={{ scale: 0.8, opacity: 0 }}
                  animate={{
                    scale: isActive ? 1.1 : 1,
                    opacity: isComplete ? 1 : isActive ? 1 : 0.4,
                  }}
                  className={`flex h-10 w-10 items-center justify-center rounded-full ${
                    isComplete
                      ? 'bg-green-500/20 text-green-500'
                      : isActive
                        ? 'bg-primary/20 text-primary glow-accent'
                        : 'bg-muted text-muted-foreground'
                  }`}
                >
                  <Icon className="h-5 w-5" />
                </motion.div>
              )
            })}
          </div>

          {/* Current Status Text */}
          <AnimatePresence mode="wait">
            <motion.p
              key={currentAgent}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -10 }}
              className="text-center text-sm text-muted-foreground"
            >
              {agents[currentAgent].message}
            </motion.p>
          </AnimatePresence>
        </div>

        {/* Progress Bar */}
        <div className="space-y-2">
          <Progress value={progress} className="h-2" />
          <p className="text-center text-xs text-muted-foreground">
            {Math.round(progress)}% complete
          </p>
        </div>
      </div>
    </div>
  )
}
