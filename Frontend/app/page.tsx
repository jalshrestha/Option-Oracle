'use client'

import { motion } from 'framer-motion'
import { MarketPulseCard } from '@/components/dashboard/market-pulse-card'
import { ActiveSessionCard } from '@/components/dashboard/active-session-card'
import { SystemHealthCard } from '@/components/dashboard/system-health-card'
import { HotStocksGrid } from '@/components/dashboard/hot-stocks-grid'
import { RecentSignals } from '@/components/dashboard/recent-signals'
import { QuickAnalyze } from '@/components/dashboard/quick-analyze'

const containerVariants = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: {
      staggerChildren: 0.05,
    },
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
      {/* Hero Row - 3 Stat Cards */}
      <motion.section
        variants={itemVariants}
        className="grid gap-4 md:grid-cols-2 lg:grid-cols-3"
      >
        <MarketPulseCard />
        <ActiveSessionCard />
        <SystemHealthCard />
      </motion.section>

      {/* Hot Stocks Grid */}
      <motion.section variants={itemVariants}>
        <HotStocksGrid />
      </motion.section>

      {/* Two Column Split */}
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
