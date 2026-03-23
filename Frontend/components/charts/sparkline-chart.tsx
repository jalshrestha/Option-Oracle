'use client'

import { Line, LineChart, ResponsiveContainer } from 'recharts'

interface SparklineChartProps {
  data: number[]
  color?: 'up' | 'down' | 'neutral'
  width?: number
  height?: number
}

const colors = {
  up: '#22c55e',
  down: '#ef4444',
  neutral: '#7c6ff7',
}

export function SparklineChart({
  data,
  color = 'neutral',
  width = 80,
  height = 32,
}: SparklineChartProps) {
  // Determine trend color based on data if not specified
  const trendColor =
    color === 'neutral'
      ? data.length > 1
        ? data[data.length - 1] >= data[0]
          ? colors.up
          : colors.down
        : colors.neutral
      : colors[color]

  const chartData = data.map((value, index) => ({ index, value }))

  return (
    <div style={{ width, height }}>
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={chartData}>
          <Line
            type="monotone"
            dataKey="value"
            stroke={trendColor}
            strokeWidth={1.5}
            dot={false}
            animationDuration={1200}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  )
}
