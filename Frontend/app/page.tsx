'use client'

import { motion } from 'framer-motion'
import { MarketPulseCard } from '@/components/dashboard/market-pulse-card'
import { ActiveSessionCard } from '@/components/dashboard/active-session-card'
import { MarketDashboard } from '@/components/dashboard/market-dashboard'
import { RecentSignals } from '@/components/dashboard/recent-signals'
import { QuickAnalyze } from '@/components/dashboard/quick-analyze'

const containerVariants = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: { staggerChildren: 0.05 },
  },
}

const itemVariants = {
  hidden: { opacity: 0, y: 16 },
  visible: { opacity: 1, y: 0 },
}

export default function Dashboard() {
  return (
    <motion.div
      variants={containerVariants}
      initial="hidden"
      animate="visible"
      className="space-y-6"
    >
      <motion.section
        variants={itemVariants}
        className="grid gap-4 md:grid-cols-2 lg:grid-cols-3"
      >
        <MarketPulseCard />
        <ActiveSessionCard />
      </motion.section>

      <motion.section variants={itemVariants}>
        <MarketDashboard />
      </motion.section>

      <motion.section
        variants={itemVariants}
        className="grid gap-6 lg:grid-cols-5"
      >
        <div className="lg:col-span-3">
          <RecentSignals />
        </div>
        <div className="lg:col-span-2">
          <QuickAnalyze />
        </div>
      </motion.section>
    </motion.div>
  )
}
