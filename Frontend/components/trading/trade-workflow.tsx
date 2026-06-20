'use client'

import { useEffect, useMemo, useState } from 'react'
import {
  AlertTriangle,
  CheckCircle2,
  Clock,
  DollarSign,
  FileText,
  Loader2,
  ShieldCheck,
  ShoppingCart,
} from 'lucide-react'
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import {
  analyzeBuyRecommendation,
  executeTrade,
  executeRecommendation,
  getBuyRecommendations,
} from '@/lib/api/client'
import { formatPrice, formatPercent } from '@/lib/utils/format'
import { cn } from '@/lib/utils'
import type { TradeRecommendationResponse } from '@/lib/api/types'

type TradingMode = 'paper' | 'live'

interface TradeWorkflowProps {
  symbol: string
  latestSignal?: string
  defaultAccountBalance?: number
}

function getPrimaryLeg(recommendation: TradeRecommendationResponse) {
  return recommendation.legs[0]
}

function getErrorMessage(error: unknown) {
  return error instanceof Error ? error.message : 'Request failed'
}

export function TradeWorkflow({
  symbol,
  latestSignal,
  defaultAccountBalance = 50000,
}: TradeWorkflowProps) {
  const [mode, setMode] = useState<TradingMode>('paper')
  const [accountBalance, setAccountBalance] = useState(defaultAccountBalance.toString())
  const [maxPositionSize, setMaxPositionSize] = useState('0.05')
  const [userQuery, setUserQuery] = useState(
    latestSignal ? `Create a risk-managed options trade for ${symbol} based on ${latestSignal}` : ''
  )
  const [recommendations, setRecommendations] = useState<TradeRecommendationResponse[]>([])
  const [selectedRecommendation, setSelectedRecommendation] =
    useState<TradeRecommendationResponse | null>(null)
  const [pendingRecommendation, setPendingRecommendation] =
    useState<TradeRecommendationResponse | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [isAnalyzing, setIsAnalyzing] = useState(false)
  const [isExecuting, setIsExecuting] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [success, setSuccess] = useState<string | null>(null)
  const [directAction, setDirectAction] = useState<'buy' | 'sell'>('buy')
  const [directQuantity, setDirectQuantity] = useState('1')
  const [directOrderType, setDirectOrderType] = useState<'market' | 'limit'>('limit')
  const [directLimitPrice, setDirectLimitPrice] = useState('1.00')
  const [directAssetType, setDirectAssetType] = useState<'stock' | 'option'>('option')
  const [directOptionType, setDirectOptionType] = useState<'call' | 'put'>('call')
  const [directStrike, setDirectStrike] = useState('100')
  const [directExpiry, setDirectExpiry] = useState('')
  const [isDirectExecuting, setIsDirectExecuting] = useState(false)

  useEffect(() => {
    let active = true

    async function loadRecommendations() {
      setIsLoading(true)
      setError(null)
      try {
        const data = await getBuyRecommendations(symbol)
        if (!active) return
        setRecommendations(data)
        setSelectedRecommendation(data.find((item) => item.status === 'draft') ?? data[0] ?? null)
      } catch (err) {
        if (active) setError(getErrorMessage(err))
      } finally {
        if (active) setIsLoading(false)
      }
    }

    loadRecommendations()
    return () => {
      active = false
    }
  }, [symbol])

  const estimatedBuyingPower = useMemo(() => {
    const balance = Number.parseFloat(accountBalance) || 0
    const positionPct = Number.parseFloat(maxPositionSize) || 0
    return balance * positionPct
  }, [accountBalance, maxPositionSize])

  const canAnalyze =
    !isAnalyzing &&
    Number.parseFloat(accountBalance) > 0 &&
    Number.parseFloat(maxPositionSize) > 0
  const canExecuteDirect =
    mode === 'paper' &&
    !isDirectExecuting &&
    Number.parseInt(directQuantity, 10) > 0 &&
    (directOrderType === 'market' || Number.parseFloat(directLimitPrice) > 0) &&
    (directAssetType === 'stock' ||
      (Number.parseFloat(directStrike) > 0 && Boolean(directExpiry)))

  async function handleAnalyze() {
    if (!canAnalyze) return

    setIsAnalyzing(true)
    setError(null)
    setSuccess(null)
    try {
      const recommendation = await analyzeBuyRecommendation({
        symbol,
        user_query: userQuery || undefined,
        risk_profile: {
          account_balance: Number.parseFloat(accountBalance),
          max_position_size: Number.parseFloat(maxPositionSize),
        },
      })
      setRecommendations((current) => [recommendation, ...current])
      setSelectedRecommendation(recommendation)
      setSuccess('Recommendation saved as a draft.')
    } catch (err) {
      setError(getErrorMessage(err))
    } finally {
      setIsAnalyzing(false)
    }
  }

  async function handleExecute() {
    if (!pendingRecommendation) return

    setIsExecuting(true)
    setError(null)
    setSuccess(null)
    try {
      const response = await executeRecommendation({
        recommendation_id: pendingRecommendation.id,
        mode,
        confirmed: true,
      })
      setRecommendations((current) =>
        current.map((item) =>
          item.id === pendingRecommendation.id
            ? { ...item, status: 'executed', executed_position_id: response.position_id }
            : item
        )
      )
      setSelectedRecommendation((current) =>
        current?.id === pendingRecommendation.id
          ? { ...current, status: 'executed', executed_position_id: response.position_id }
          : current
      )
      setPendingRecommendation(null)
      setSuccess(response.message || 'Paper trade executed.')
    } catch (err) {
      setError(getErrorMessage(err))
    } finally {
      setIsExecuting(false)
    }
  }

  async function handleDirectExecute() {
    if (!canExecuteDirect) return

    setIsDirectExecuting(true)
    setError(null)
    setSuccess(null)
    try {
      const response = await executeTrade({
        symbol,
        action: directAction,
        quantity: Number.parseInt(directQuantity, 10),
        order_type: directOrderType,
        limit_price:
          directOrderType === 'limit' ? Number.parseFloat(directLimitPrice) : undefined,
        option_details:
          directAssetType === 'option'
            ? {
                option_type: directOptionType,
                strike: Number.parseFloat(directStrike),
                expiry: directExpiry,
              }
            : undefined,
      })
      setSuccess(response.message || `Paper ${directAction} order executed.`)
    } catch (err) {
      setError(getErrorMessage(err))
    } finally {
      setIsDirectExecuting(false)
    }
  }

  const selectedLeg = selectedRecommendation ? getPrimaryLeg(selectedRecommendation) : null
  const isExecutable = selectedRecommendation?.status === 'draft' || selectedRecommendation?.status === 'confirmed'

  return (
    <>
      <Card className="border-border bg-card">
        <CardHeader className="space-y-3">
          <div className="flex flex-col gap-3 lg:flex-row lg:items-center lg:justify-between">
            <CardTitle className="flex items-center gap-2 text-lg">
              <ShoppingCart className="h-5 w-5" />
              Trade Workflow
            </CardTitle>
            <Select value={mode} onValueChange={(value) => setMode(value as TradingMode)}>
              <SelectTrigger className="w-full sm:w-40">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="paper">Paper</SelectItem>
                <SelectItem value="live">Live</SelectItem>
              </SelectContent>
            </Select>
          </div>
          <Alert className={cn(mode === 'live' && 'border-destructive/50')}>
            <AlertTriangle className="h-4 w-4" />
            <AlertTitle>{mode === 'paper' ? 'Paper execution' : 'Live execution disabled by default'}</AlertTitle>
            <AlertDescription>
              {mode === 'paper'
                ? 'Recommendations execute through the backend paper trading endpoint.'
                : 'The API rejects live orders unless backend live trading is explicitly enabled.'}
            </AlertDescription>
          </Alert>
        </CardHeader>
        <CardContent className="grid gap-6 xl:grid-cols-[minmax(0,0.95fr)_minmax(0,1.25fr)]">
          <div className="space-y-4">
            <div className="grid gap-3 sm:grid-cols-2">
              <div className="space-y-2">
                <Label htmlFor="account-balance">Account balance</Label>
                <Input
                  id="account-balance"
                  type="number"
                  min="1"
                  value={accountBalance}
                  onChange={(event) => setAccountBalance(event.target.value)}
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="position-size">Max position size</Label>
                <Select value={maxPositionSize} onValueChange={setMaxPositionSize}>
                  <SelectTrigger id="position-size">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="0.01">1%</SelectItem>
                    <SelectItem value="0.03">3%</SelectItem>
                    <SelectItem value="0.05">5%</SelectItem>
                    <SelectItem value="0.10">10%</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>

            <div className="space-y-2">
              <Label htmlFor="trade-query">Trade brief</Label>
              <Input
                id="trade-query"
                value={userQuery}
                onChange={(event) => setUserQuery(event.target.value)}
                placeholder={`Risk-managed setup for ${symbol}`}
              />
            </div>

            <div className="grid gap-3 rounded-lg border border-border/70 bg-background/55 p-3 sm:grid-cols-3">
              <div>
                <p className="text-xs text-muted-foreground">Buying power cap</p>
                <p className="font-mono text-sm font-semibold">{formatPrice(estimatedBuyingPower)}</p>
              </div>
              <div>
                <p className="text-xs text-muted-foreground">Mode</p>
                <p className="font-mono text-sm font-semibold uppercase">{mode}</p>
              </div>
              <div>
                <p className="text-xs text-muted-foreground">Source</p>
                <p className="font-mono text-sm font-semibold">rule-based</p>
              </div>
            </div>

            <Button onClick={handleAnalyze} disabled={!canAnalyze} className="w-full gap-2">
              {isAnalyzing ? <Loader2 className="h-4 w-4 animate-spin" /> : <FileText className="h-4 w-4" />}
              Analyze Buy
            </Button>

            <div className="space-y-3 rounded-lg border border-border/70 bg-background/55 p-3">
              <div>
                <h3 className="text-sm font-semibold">Direct paper order</h3>
                <p className="text-xs text-muted-foreground">
                  Sends a manual paper order directly to the backend execution endpoint.
                </p>
              </div>
              <div className="grid gap-3 sm:grid-cols-2">
                <div className="space-y-2">
                  <Label htmlFor="direct-action">Action</Label>
                  <Select value={directAction} onValueChange={(value) => setDirectAction(value as 'buy' | 'sell')}>
                    <SelectTrigger id="direct-action">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="buy">Buy</SelectItem>
                      <SelectItem value="sell">Sell</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div className="space-y-2">
                  <Label htmlFor="direct-quantity">Quantity</Label>
                  <Input
                    id="direct-quantity"
                    type="number"
                    min="1"
                    value={directQuantity}
                    onChange={(event) => setDirectQuantity(event.target.value)}
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="direct-asset">Asset</Label>
                  <Select value={directAssetType} onValueChange={(value) => setDirectAssetType(value as 'stock' | 'option')}>
                    <SelectTrigger id="direct-asset">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="option">Option</SelectItem>
                      <SelectItem value="stock">Stock</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div className="space-y-2">
                  <Label htmlFor="direct-order-type">Order type</Label>
                  <Select value={directOrderType} onValueChange={(value) => setDirectOrderType(value as 'market' | 'limit')}>
                    <SelectTrigger id="direct-order-type">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="limit">Limit</SelectItem>
                      <SelectItem value="market">Market</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>

              {directOrderType === 'limit' && (
                <div className="space-y-2">
                  <Label htmlFor="direct-limit">Limit price</Label>
                  <Input
                    id="direct-limit"
                    type="number"
                    min="0.01"
                    step="0.01"
                    value={directLimitPrice}
                    onChange={(event) => setDirectLimitPrice(event.target.value)}
                  />
                </div>
              )}

              {directAssetType === 'option' && (
                <div className="grid gap-3 sm:grid-cols-3">
                  <div className="space-y-2">
                    <Label htmlFor="direct-option-type">Type</Label>
                    <Select value={directOptionType} onValueChange={(value) => setDirectOptionType(value as 'call' | 'put')}>
                      <SelectTrigger id="direct-option-type">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="call">Call</SelectItem>
                        <SelectItem value="put">Put</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="direct-strike">Strike</Label>
                    <Input
                      id="direct-strike"
                      type="number"
                      min="0.01"
                      step="0.01"
                      value={directStrike}
                      onChange={(event) => setDirectStrike(event.target.value)}
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="direct-expiry">Expiry</Label>
                    <Input
                      id="direct-expiry"
                      type="date"
                      value={directExpiry}
                      onChange={(event) => setDirectExpiry(event.target.value)}
                    />
                  </div>
                </div>
              )}

              <Button
                variant="outline"
                onClick={handleDirectExecute}
                disabled={!canExecuteDirect}
                className="w-full gap-2"
              >
                {isDirectExecuting ? <Loader2 className="h-4 w-4 animate-spin" /> : <ShoppingCart className="h-4 w-4" />}
                Execute Direct Paper Order
              </Button>
            </div>

            {error && (
              <Alert variant="destructive">
                <AlertTriangle className="h-4 w-4" />
                <AlertTitle>Trading request failed</AlertTitle>
                <AlertDescription>{error}</AlertDescription>
              </Alert>
            )}

            {success && (
              <Alert className="border-green-500/40">
                <CheckCircle2 className="h-4 w-4 text-green-600" />
                <AlertTitle>Updated</AlertTitle>
                <AlertDescription>{success}</AlertDescription>
              </Alert>
            )}
          </div>

          <div className="space-y-3">
            <div className="flex items-center justify-between gap-3">
              <div>
                <h3 className="text-sm font-semibold">Recommendations</h3>
                <p className="text-xs text-muted-foreground">Persisted snapshots for {symbol}</p>
              </div>
              {isLoading && <Loader2 className="h-4 w-4 animate-spin text-muted-foreground" />}
            </div>

            {!isLoading && recommendations.length === 0 && (
              <div className="rounded-lg border border-dashed border-border p-6 text-center text-sm text-muted-foreground">
                No recommendations yet.
              </div>
            )}

            <div className="grid gap-3">
              {recommendations.slice(0, 4).map((recommendation) => {
                const leg = getPrimaryLeg(recommendation)
                const active = selectedRecommendation?.id === recommendation.id
                return (
                  <button
                    key={recommendation.id}
                    type="button"
                    onClick={() => setSelectedRecommendation(recommendation)}
                    className={cn(
                      'rounded-lg border bg-background/55 p-3 text-left transition-colors hover:border-primary/50',
                      active ? 'border-primary/60' : 'border-border/70'
                    )}
                  >
                    <div className="flex items-start justify-between gap-3">
                      <div>
                        <div className="flex flex-wrap items-center gap-2">
                          <Badge variant={recommendation.action === 'buy' ? 'default' : 'secondary'}>
                            {recommendation.strategy.replace('_', ' ')}
                          </Badge>
                          <Badge variant="outline">{recommendation.status}</Badge>
                        </div>
                        <p className="mt-2 text-sm text-foreground">{recommendation.rationale}</p>
                      </div>
                      <div className="text-right">
                        <p className="font-mono text-sm font-semibold">
                          {formatPrice(recommendation.estimated_cost)}
                        </p>
                        <p className="text-xs text-muted-foreground">
                          {formatPercent(recommendation.confidence * 100)}
                        </p>
                      </div>
                    </div>
                    {leg && (
                      <div className="mt-3 grid gap-2 text-xs text-muted-foreground sm:grid-cols-4">
                        <span>{leg.quantity} contract</span>
                        <span>{leg.option_type?.toUpperCase() ?? leg.asset_type}</span>
                        <span>{leg.strike ? formatPrice(leg.strike) : 'Stock'}</span>
                        <span>{leg.expiry ?? 'No expiry'}</span>
                      </div>
                    )}
                  </button>
                )
              })}
            </div>

            {selectedRecommendation && selectedLeg && (
              <div className="rounded-lg border border-border bg-background/55 p-4">
                <div className="mb-3 flex items-center justify-between gap-3">
                  <div className="flex items-center gap-2">
                    <ShieldCheck className="h-4 w-4 text-primary" />
                    <span className="text-sm font-semibold">Selected order</span>
                  </div>
                  <Badge variant={isExecutable ? 'default' : 'secondary'}>{selectedRecommendation.status}</Badge>
                </div>
                <div className="grid gap-2 text-sm sm:grid-cols-2">
                  <div className="flex items-center justify-between gap-3">
                    <span className="text-muted-foreground">Max loss</span>
                    <span className="font-mono font-medium">{formatPrice(selectedRecommendation.max_loss)}</span>
                  </div>
                  <div className="flex items-center justify-between gap-3">
                    <span className="text-muted-foreground">Risk score</span>
                    <span className="font-mono font-medium">{formatPercent(selectedRecommendation.risk_score * 100)}</span>
                  </div>
                  <div className="flex items-center justify-between gap-3">
                    <span className="text-muted-foreground">Limit</span>
                    <span className="font-mono font-medium">{formatPrice(selectedLeg.estimated_price)}</span>
                  </div>
                  <div className="flex items-center justify-between gap-3">
                    <span className="text-muted-foreground">Expires</span>
                    <span className="font-mono font-medium">
                      {new Date(selectedRecommendation.expires_at).toLocaleTimeString()}
                    </span>
                  </div>
                </div>
                <Button
                  className="mt-4 w-full gap-2"
                  disabled={!isExecutable || mode === 'live'}
                  onClick={() => setPendingRecommendation(selectedRecommendation)}
                >
                  <DollarSign className="h-4 w-4" />
                  Execute Paper Recommendation
                </Button>
              </div>
            )}
          </div>
        </CardContent>
      </Card>

      <Dialog open={Boolean(pendingRecommendation)} onOpenChange={(open) => !open && setPendingRecommendation(null)}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Confirm Paper Execution</DialogTitle>
            <DialogDescription>
              This creates a paper position from the saved recommendation.
            </DialogDescription>
          </DialogHeader>
          {pendingRecommendation && (
            <div className="space-y-3 rounded-lg border border-border bg-background/55 p-4 text-sm">
              <div className="flex justify-between gap-3">
                <span className="text-muted-foreground">Symbol</span>
                <span className="font-mono font-semibold">{pendingRecommendation.symbol}</span>
              </div>
              <div className="flex justify-between gap-3">
                <span className="text-muted-foreground">Estimated cost</span>
                <span className="font-mono font-semibold">{formatPrice(pendingRecommendation.estimated_cost)}</span>
              </div>
              <div className="flex justify-between gap-3">
                <span className="text-muted-foreground">Max loss</span>
                <span className="font-mono font-semibold">{formatPrice(pendingRecommendation.max_loss)}</span>
              </div>
            </div>
          )}
          <DialogFooter>
            <Button variant="outline" onClick={() => setPendingRecommendation(null)} disabled={isExecuting}>
              Cancel
            </Button>
            <Button onClick={handleExecute} disabled={isExecuting} className="gap-2">
              {isExecuting ? <Clock className="h-4 w-4 animate-spin" /> : <ShoppingCart className="h-4 w-4" />}
              Confirm
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </>
  )
}
