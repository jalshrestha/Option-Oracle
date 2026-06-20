import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { TradeWorkflow } from './trade-workflow'
import {
  analyzeBuyRecommendation,
  executeRecommendation,
  getBuyRecommendations,
} from '@/lib/api/client'
import type { TradeRecommendationResponse } from '@/lib/api/types'

vi.mock('@/lib/api/client', () => ({
  analyzeBuyRecommendation: vi.fn(),
  executeTrade: vi.fn(),
  executeRecommendation: vi.fn(),
  getBuyRecommendations: vi.fn(),
}))

const baseRecommendation: TradeRecommendationResponse = {
  id: 'rec-1',
  symbol: 'AAPL',
  strategy: 'long_call',
  action: 'buy',
  status: 'draft',
  mode: 'paper',
  legs: [
    {
      asset_type: 'option',
      action: 'buy',
      quantity: 1,
      option_type: 'call',
      strike: 100,
      expiry: '2026-07-17',
      estimated_price: 2.5,
    },
  ],
  rationale: 'Rule-based recommendation',
  source: 'rule_based',
  estimated_cost: 250,
  max_loss: 250,
  confidence: 0.5,
  risk_score: 0.01,
  expires_at: new Date(Date.now() + 30 * 60 * 1000).toISOString(),
}

describe('TradeWorkflow', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    vi.mocked(getBuyRecommendations).mockResolvedValue([])
  })

  it('renders an empty recommendation state after loading', async () => {
    render(<TradeWorkflow symbol="AAPL" latestSignal="BUY" />)

    expect(await screen.findByText('No recommendations yet.')).toBeInTheDocument()
    expect(getBuyRecommendations).toHaveBeenCalledWith('AAPL')
  })

  it('creates and displays a draft recommendation', async () => {
    vi.mocked(analyzeBuyRecommendation).mockResolvedValue(baseRecommendation)

    render(<TradeWorkflow symbol="AAPL" latestSignal="BUY" />)
    await screen.findByText('No recommendations yet.')

    fireEvent.click(screen.getByRole('button', { name: /Analyze Buy/i }))

    expect(await screen.findByText('Recommendation saved as a draft.')).toBeInTheDocument()
    expect(screen.getByText('Rule-based recommendation')).toBeInTheDocument()
    expect(analyzeBuyRecommendation).toHaveBeenCalledWith(
      expect.objectContaining({
        symbol: 'AAPL',
        risk_profile: expect.objectContaining({
          account_balance: 50000,
          max_position_size: 0.05,
        }),
      })
    )
  })

  it('confirms and executes a saved paper recommendation', async () => {
    vi.mocked(getBuyRecommendations).mockResolvedValue([baseRecommendation])
    vi.mocked(executeRecommendation).mockResolvedValue({
      trade_id: 'trade-1',
      status: 'executed',
      position_id: 'pos-1',
      execution_price: 2.5,
      message: 'Paper trade executed for AAPL',
    })

    render(<TradeWorkflow symbol="AAPL" latestSignal="BUY" />)

    fireEvent.click(await screen.findByRole('button', { name: /Execute Paper Recommendation/i }))
    fireEvent.click(screen.getByRole('button', { name: /^Confirm$/i }))

    expect(await screen.findByText('Paper trade executed for AAPL')).toBeInTheDocument()
    expect(executeRecommendation).toHaveBeenCalledWith({
      recommendation_id: 'rec-1',
      mode: 'paper',
      confirmed: true,
    })
  })

  it('keeps direct option orders disabled until required fields are present', async () => {
    render(<TradeWorkflow symbol="AAPL" latestSignal="BUY" />)
    await screen.findByText('No recommendations yet.')

    expect(
      screen.getByRole('button', { name: /Execute Direct Paper Order/i })
    ).toBeDisabled()
  })
})
