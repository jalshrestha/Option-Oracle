"use client";

import { useState, useMemo } from "react";
import { motion } from "framer-motion";
import useSWR from "swr";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import {
  Briefcase,
  TrendingUp,
  TrendingDown,
  PieChart,
  Activity,
  DollarSign,
  Target,
  AlertTriangle,
  Plus,
  Filter,
  ArrowUpRight,
  ArrowDownRight,
  Clock,
  Zap,
} from "lucide-react";
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  PieChart as RechartsPieChart,
  Pie,
  Cell,
} from "recharts";
import { formatCurrency, formatPercent } from "@/lib/utils/format";
import { getPortfolioSummary, getPositions } from "@/lib/api/client";

const ALLOCATION_COLORS = [
  "hsl(var(--accent))",
  "hsl(var(--success))",
  "hsl(var(--warning))",
  "#3b82f6",
  "#8b5cf6",
  "#06b6d4",
];

const performanceHistory = Array.from({ length: 30 }, (_, i) => ({
  date: new Date(Date.now() - (29 - i) * 24 * 60 * 60 * 1000).toLocaleDateString(),
  value: 100000 + i * 500,
}));

export default function PortfolioPage() {
  const [filterType, setFilterType] = useState("all");

  const { data: portfolio, isLoading: portfolioLoading } = useSWR(
    "portfolio-summary",
    getPortfolioSummary,
    { refreshInterval: 30000 }
  );

  const { data: positions = [], isLoading: positionsLoading } = useSWR(
    "positions",
    getPositions,
    { refreshInterval: 30000 }
  );

  const totalGain = portfolio
    ? (portfolio.unrealized_pnl ?? 0) + (portfolio.realized_pnl ?? 0)
    : 0;

  const allocationData = useMemo(() => {
    if (portfolio?.allocation?.length) {
      return portfolio.allocation.map((a, i) => ({
        name: a.symbol,
        value: a.percentage ?? (a.value / (portfolio.total_value || 1)) * 100,
        color: ALLOCATION_COLORS[i % ALLOCATION_COLORS.length],
      }));
    }
    return [];
  }, [portfolio]);

  const filteredPositions = positions.filter((p) => {
    if (filterType === "all") return true;
    if (filterType === "option") return !!p.option_type;
    return !p.option_type;
  });

  const riskMetrics = portfolio?.risk_metrics;
  const sharpeRatio = riskMetrics?.sharpe_ratio ?? 0;
  const beta = riskMetrics?.beta ?? 0;
  const maxDrawdown = riskMetrics?.max_drawdown ?? 0;

  return (
    <div className="space-y-6 p-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Portfolio</h1>
          <p className="text-muted-foreground">
            Track and manage your investments
          </p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline">
            <Filter className="mr-2 h-4 w-4" />
            Filter
          </Button>
          <Button className="bg-accent text-accent-foreground hover:bg-accent/90">
            <Plus className="mr-2 h-4 w-4" />
            Add Position
          </Button>
        </div>
      </div>

      {/* Portfolio Overview Cards */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }}>
          <Card className="border-accent/30 bg-gradient-to-br from-accent/10 to-transparent">
            <CardContent className="p-6">
              <div className="flex items-center gap-3">
                <div className="rounded-lg bg-accent/20 p-2">
                  <Briefcase className="h-5 w-5 text-accent" />
                </div>
                <div>
                  <p className="text-sm text-muted-foreground">Total Value</p>
                  {portfolioLoading ? (
                    <div className="h-8 w-32 animate-pulse rounded bg-muted" />
                  ) : (
                    <p className="text-2xl font-bold">
                      {formatCurrency(portfolio?.total_value ?? 0)}
                    </p>
                  )}
                </div>
              </div>
            </CardContent>
          </Card>
        </motion.div>

        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.1 }}>
          <Card className={`border-${totalGain >= 0 ? "success" : "destructive"}/30 bg-gradient-to-br from-${totalGain >= 0 ? "success" : "destructive"}/10 to-transparent`}>
            <CardContent className="p-6">
              <div className="flex items-center gap-3">
                <div className={`rounded-lg bg-${totalGain >= 0 ? "success" : "destructive"}/20 p-2`}>
                  {totalGain >= 0 ? (
                    <TrendingUp className="h-5 w-5 text-success" />
                  ) : (
                    <TrendingDown className="h-5 w-5 text-destructive" />
                  )}
                </div>
                <div>
                  <p className="text-sm text-muted-foreground">Unrealized P&L</p>
                  {portfolioLoading ? (
                    <div className="h-8 w-32 animate-pulse rounded bg-muted" />
                  ) : (
                    <>
                      <p className={`text-2xl font-bold ${totalGain >= 0 ? "text-success" : "text-destructive"}`}>
                        {totalGain >= 0 ? "+" : ""}{formatCurrency(portfolio?.unrealized_pnl ?? 0)}
                      </p>
                      <p className={`text-sm ${(portfolio?.total_return_pct ?? 0) >= 0 ? "text-success" : "text-destructive"}`}>
                        {(portfolio?.total_return_pct ?? 0) >= 0 ? "+" : ""}{formatPercent(portfolio?.total_return_pct ?? 0)}
                      </p>
                    </>
                  )}
                </div>
              </div>
            </CardContent>
          </Card>
        </motion.div>

        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.2 }}>
          <Card className="border-border/50 bg-card/50">
            <CardContent className="p-6">
              <div className="flex items-center gap-3">
                <div className="rounded-lg bg-muted p-2">
                  <Activity className="h-5 w-5 text-muted-foreground" />
                </div>
                <div>
                  <p className="text-sm text-muted-foreground">Realized P&L</p>
                  {portfolioLoading ? (
                    <div className="h-8 w-32 animate-pulse rounded bg-muted" />
                  ) : (
                    <p className={`text-2xl font-bold ${(portfolio?.realized_pnl ?? 0) >= 0 ? "text-success" : "text-destructive"}`}>
                      {(portfolio?.realized_pnl ?? 0) >= 0 ? "+" : ""}{formatCurrency(portfolio?.realized_pnl ?? 0)}
                    </p>
                  )}
                </div>
              </div>
            </CardContent>
          </Card>
        </motion.div>

        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.3 }}>
          <Card className="border-border/50 bg-card/50">
            <CardContent className="p-6">
              <div className="flex items-center gap-3">
                <div className="rounded-lg bg-muted p-2">
                  <Target className="h-5 w-5 text-muted-foreground" />
                </div>
                <div>
                  <p className="text-sm text-muted-foreground">Sharpe Ratio</p>
                  {portfolioLoading ? (
                    <div className="h-8 w-16 animate-pulse rounded bg-muted" />
                  ) : (
                    <p className="text-2xl font-bold">{sharpeRatio.toFixed(2)}</p>
                  )}
                  <p className="text-sm text-muted-foreground">Risk-adjusted</p>
                </div>
              </div>
            </CardContent>
          </Card>
        </motion.div>
      </div>

      {/* Chart and Allocation */}
      <div className="grid gap-6 lg:grid-cols-3">
        <Card className="border-border/50 bg-card/50 backdrop-blur lg:col-span-2">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Activity className="h-5 w-5 text-accent" />
              Portfolio Performance
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="h-80">
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={performanceHistory}>
                  <defs>
                    <linearGradient id="portfolioGradient" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="0%" stopColor="hsl(var(--accent))" stopOpacity={0.3} />
                      <stop offset="100%" stopColor="hsl(var(--accent))" stopOpacity={0} />
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" opacity={0.3} />
                  <XAxis dataKey="date" tick={{ fill: "hsl(var(--muted-foreground))", fontSize: 12 }} tickLine={{ stroke: "hsl(var(--border))" }} />
                  <YAxis tick={{ fill: "hsl(var(--muted-foreground))", fontSize: 12 }} tickLine={{ stroke: "hsl(var(--border))" }} tickFormatter={(v) => `$${(v / 1000).toFixed(0)}k`} />
                  <Tooltip
                    contentStyle={{ backgroundColor: "hsl(var(--card))", border: "1px solid hsl(var(--border))", borderRadius: "8px" }}
                    formatter={(value: number) => [formatCurrency(value), "Value"]}
                  />
                  <Area type="monotone" dataKey="value" stroke="hsl(var(--accent))" fill="url(#portfolioGradient)" strokeWidth={2} />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          </CardContent>
        </Card>

        <Card className="border-border/50 bg-card/50 backdrop-blur">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <PieChart className="h-5 w-5 text-accent" />
              Allocation
            </CardTitle>
          </CardHeader>
          <CardContent>
            {portfolioLoading ? (
              <div className="h-48 animate-pulse rounded bg-muted" />
            ) : allocationData.length > 0 ? (
              <>
                <div className="h-48">
                  <ResponsiveContainer width="100%" height="100%">
                    <RechartsPieChart>
                      <Pie data={allocationData} cx="50%" cy="50%" innerRadius={50} outerRadius={80} paddingAngle={2} dataKey="value">
                        {allocationData.map((entry, index) => (
                          <Cell key={index} fill={entry.color} />
                        ))}
                      </Pie>
                    </RechartsPieChart>
                  </ResponsiveContainer>
                </div>
                <div className="mt-4 space-y-2">
                  {allocationData.map((item) => (
                    <div key={item.name} className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <div className="h-3 w-3 rounded-full" style={{ backgroundColor: item.color }} />
                        <span className="text-sm">{item.name}</span>
                      </div>
                      <span className="text-sm font-medium">{item.value.toFixed(1)}%</span>
                    </div>
                  ))}
                </div>
              </>
            ) : (
              <div className="flex h-48 items-center justify-center text-sm text-muted-foreground">
                No positions yet
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Positions */}
      <Card className="border-border/50 bg-card/50 backdrop-blur">
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle className="flex items-center gap-2">
              <DollarSign className="h-5 w-5 text-accent" />
              Positions ({portfolio?.open_positions ?? positions.length})
            </CardTitle>
            <div className="flex gap-2">
              {["all", "option", "stock"].map((type) => (
                <Button
                  key={type}
                  variant={filterType === type ? "default" : "outline"}
                  size="sm"
                  onClick={() => setFilterType(type)}
                  className={filterType === type ? "bg-accent text-accent-foreground" : ""}
                >
                  {type === "all" ? "All" : type.charAt(0).toUpperCase() + type.slice(1)}s
                </Button>
              ))}
            </div>
          </div>
        </CardHeader>
        <CardContent>
          {positionsLoading ? (
            <div className="space-y-3">
              {[1, 2, 3].map((i) => (
                <div key={i} className="h-16 animate-pulse rounded-lg bg-muted" />
              ))}
            </div>
          ) : filteredPositions.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-12 text-muted-foreground">
              <Briefcase className="mb-3 h-10 w-10 opacity-30" />
              <p className="text-sm">No positions yet. Run an analysis to get trade recommendations.</p>
            </div>
          ) : (
            <div className="space-y-3">
              {filteredPositions.map((position, i) => {
                const posType = position.option_type ? "option" : "stock";
                const posValue = position.current_price * position.quantity;
                const posGain = position.unrealized_pnl;
                const posGainPct = posGain / (position.entry_price * position.quantity || 1);
                return (
                  <motion.div
                    key={position.id}
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: i * 0.05 }}
                    className="flex items-center justify-between rounded-lg border border-border/50 bg-background/50 p-4 transition-colors hover:bg-muted/30"
                  >
                    <div className="flex items-center gap-4">
                      <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-accent/10">
                        <span className="text-sm font-bold text-accent">
                          {position.symbol.slice(0, 2)}
                        </span>
                      </div>
                      <div>
                        <div className="flex items-center gap-2">
                          <span className="font-semibold">{position.symbol}</span>
                          <Badge variant="outline" className="text-xs">{posType}</Badge>
                          {position.option_type && (
                            <Badge variant="secondary" className="text-xs capitalize">
                              {position.option_type}
                            </Badge>
                          )}
                          {position.expiry_date && (
                            <Badge variant="secondary" className="text-xs">
                              <Clock className="mr-1 h-3 w-3" />
                              {position.expiry_date}
                            </Badge>
                          )}
                        </div>
                        {position.strike_price && (
                          <div className="text-sm text-muted-foreground">
                            Strike: {formatCurrency(position.strike_price)}
                          </div>
                        )}
                      </div>
                    </div>
                    <div className="flex items-center gap-8">
                      <div className="text-right">
                        <div className="text-sm text-muted-foreground">
                          {position.quantity} {posType === "option" ? "contracts" : "shares"}
                        </div>
                        <div className="text-sm text-muted-foreground">
                          Avg: {formatCurrency(position.entry_price)}
                        </div>
                      </div>
                      <div className="text-right">
                        <div className="font-semibold">{formatCurrency(position.current_price)}</div>
                      </div>
                      <div className="w-28 text-right">
                        <div className="font-semibold">{formatCurrency(posValue)}</div>
                        <div className={`flex items-center justify-end text-sm ${posGain >= 0 ? "text-success" : "text-destructive"}`}>
                          {posGain >= 0 ? <ArrowUpRight className="h-3 w-3" /> : <ArrowDownRight className="h-3 w-3" />}
                          {posGain >= 0 ? "+" : ""}{formatCurrency(posGain)} ({formatPercent(Math.abs(posGainPct))})
                        </div>
                      </div>
                      <Button size="sm" variant="ghost">
                        <Zap className="h-4 w-4" />
                      </Button>
                    </div>
                  </motion.div>
                );
              })}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Risk Metrics */}
      <div className="grid gap-4 md:grid-cols-4">
        <Card className="border-border/50 bg-card/50">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <span className="text-sm text-muted-foreground">Beta</span>
              <span className="font-semibold">{portfolioLoading ? "—" : beta.toFixed(2)}</span>
            </div>
            <Progress value={Math.min(beta * 50, 100)} className="mt-2 h-1" />
          </CardContent>
        </Card>
        <Card className="border-border/50 bg-card/50">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <span className="text-sm text-muted-foreground">Sharpe Ratio</span>
              <span className="font-semibold">{portfolioLoading ? "—" : sharpeRatio.toFixed(2)}</span>
            </div>
            <Progress value={Math.min(sharpeRatio * 25, 100)} className="mt-2 h-1" />
          </CardContent>
        </Card>
        <Card className="border-border/50 bg-card/50">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <span className="text-sm text-muted-foreground">Max Drawdown</span>
              <span className="font-semibold text-destructive">
                {portfolioLoading ? "—" : formatPercent(maxDrawdown)}
              </span>
            </div>
            <Progress value={Math.min(Math.abs(maxDrawdown) * 200, 100)} className="mt-2 h-1" />
          </CardContent>
        </Card>
        <Card className="border-warning/30 bg-warning/5">
          <CardContent className="flex items-center gap-3 p-4">
            <AlertTriangle className="h-5 w-5 text-warning" />
            <div className="text-sm">
              <span className="font-medium">{portfolio?.open_positions ?? 0} open</span>
              <span className="text-muted-foreground"> positions tracked</span>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
