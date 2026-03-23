'use client'

import {
  Radar,
  RadarChart as RechartsRadarChart,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  ResponsiveContainer,
} from 'recharts'
import type { AgentWeights } from '@/lib/api/types'

interface RadarChartProps {
  weights: AgentWeights
}

export function RadarChart({ weights }: RadarChartProps) {
  const data = [
    { agent: 'Technical', value: weights.technical * 100, fullMark: 100 },
    { agent: 'Sentiment', value: weights.sentiment * 100, fullMark: 100 },
    { agent: 'Flow', value: weights.flow * 100, fullMark: 100 },
    { agent: 'Historical', value: weights.historical * 100, fullMark: 100 },
  ]

  return (
    <div className="h-64 w-full">
      <ResponsiveContainer width="100%" height="100%">
        <RechartsRadarChart cx="50%" cy="50%" outerRadius="70%" data={data}>
          <PolarGrid stroke="hsl(var(--border))" />
          <PolarAngleAxis
            dataKey="agent"
            tick={{ fill: 'hsl(var(--muted-foreground))', fontSize: 12 }}
          />
          <PolarRadiusAxis
            angle={30}
            domain={[0, 100]}
            tick={{ fill: 'hsl(var(--muted-foreground))', fontSize: 10 }}
          />
          <Radar
            name="Weight"
            dataKey="value"
            stroke="hsl(var(--primary))"
            fill="hsl(var(--primary))"
            fillOpacity={0.3}
            animationDuration={1000}
          />
        </RechartsRadarChart>
      </ResponsiveContainer>
    </div>
  )
}
