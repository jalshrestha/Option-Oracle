"use client";

import { useState } from "react";
import { motion } from "framer-motion";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import {
  Search,
  TrendingUp,
  TrendingDown,
  Activity,
  Zap,
  Calendar,
  Filter,
  ArrowUpRight,
  ArrowDownRight,
  Eye,
  Bell,
} from "lucide-react";
import { formatCurrency, formatPercent } from "@/lib/utils/format";

// Mock options chain data
const generateOptionsChain = (basePrice: number, expiry: string) => {
  const strikes = [];
  const atmStrike = Math.round(basePrice / 5) * 5;
  
  for (let i = -10; i <= 10; i++) {
    const strike = atmStrike + i * 5;
    const isITM = strike < basePrice;
    const distance = Math.abs(strike - basePrice);
    const iv = 0.25 + Math.random() * 0.15;
    
    strikes.push({
      strike,
      isITM,
      isATM: distance < 2.5,
      call: {
        bid: Math.max(0, (basePrice - strike + 5) * (1 - distance / 100) + Math.random() * 2),
        ask: Math.max(0, (basePrice - strike + 5) * (1 - distance / 100) + Math.random() * 2 + 0.1),
        last: Math.max(0, (basePrice - strike + 5) * (1 - distance / 100) + Math.random() * 2),
        change: (Math.random() - 0.5) * 2,
        volume: Math.floor(Math.random() * 5000),
        openInterest: Math.floor(Math.random() * 20000),
        iv,
        delta: Math.max(0, Math.min(1, 0.5 + (basePrice - strike) / 50)),
        gamma: 0.02 + Math.random() * 0.03,
        theta: -(0.01 + Math.random() * 0.05),
        vega: 0.1 + Math.random() * 0.2,
      },
      put: {
        bid: Math.max(0, (strike - basePrice + 5) * (1 - distance / 100) + Math.random() * 2),
        ask: Math.max(0, (strike - basePrice + 5) * (1 - distance / 100) + Math.random() * 2 + 0.1),
        last: Math.max(0, (strike - basePrice + 5) * (1 - distance / 100) + Math.random() * 2),
        change: (Math.random() - 0.5) * 2,
        volume: Math.floor(Math.random() * 5000),
        openInterest: Math.floor(Math.random() * 20000),
        iv,
        delta: Math.min(0, Math.max(-1, -0.5 + (basePrice - strike) / 50)),
        gamma: 0.02 + Math.random() * 0.03,
        theta: -(0.01 + Math.random() * 0.05),
        vega: 0.1 + Math.random() * 0.2,
      },
    });
  }
  return strikes;
};

const expirations = [
  { label: "Feb 28, 2024", value: "2024-02-28", daysToExpiry: 7 },
  { label: "Mar 15, 2024", value: "2024-03-15", daysToExpiry: 22 },
  { label: "Mar 22, 2024", value: "2024-03-22", daysToExpiry: 29 },
  { label: "Apr 19, 2024", value: "2024-04-19", daysToExpiry: 57 },
  { label: "May 17, 2024", value: "2024-05-17", daysToExpiry: 85 },
];

const stockData = {
  symbol: "AAPL",
  name: "Apple Inc.",
  price: 178.25,
  change: 2.35,
  changePercent: 0.0134,
  volume: 45678900,
  avgVolume: 52345678,
};

export default function OptionsChainPage() {
  const [searchSymbol, setSearchSymbol] = useState("AAPL");
  const [selectedExpiry, setSelectedExpiry] = useState(expirations[1].value);
  const [showGreeks, setShowGreeks] = useState(false);
  const [highlightVolume, setHighlightVolume] = useState(true);

  const optionsChain = generateOptionsChain(stockData.price, selectedExpiry);
  const selectedExpiration = expirations.find((e) => e.value === selectedExpiry);

  return (
    <div className="space-y-6 p-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Options Chain</h1>
          <p className="text-muted-foreground">
            Real-time options data with AI-powered analysis
          </p>
        </div>
      </div>

      {/* Symbol Search & Stock Info */}
      <div className="grid gap-4 lg:grid-cols-4">
        <Card className="border-border/50 bg-card/50 backdrop-blur lg:col-span-1">
          <CardContent className="p-4">
            <div className="flex gap-2">
              <div className="relative flex-1">
                <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
                <Input
                  value={searchSymbol}
                  onChange={(e) => setSearchSymbol(e.target.value.toUpperCase())}
                  placeholder="Symbol"
                  className="pl-9"
                />
              </div>
              <Button className="bg-accent text-accent-foreground hover:bg-accent/90">
                <Search className="h-4 w-4" />
              </Button>
            </div>
          </CardContent>
        </Card>

        <Card className="border-accent/30 bg-gradient-to-br from-accent/10 to-transparent lg:col-span-3">
          <CardContent className="flex items-center justify-between p-4">
            <div className="flex items-center gap-6">
              <div>
                <div className="flex items-center gap-2">
                  <span className="text-2xl font-bold">{stockData.symbol}</span>
                  <Badge variant="outline">{stockData.name}</Badge>
                </div>
                <div className="flex items-center gap-2">
                  <span className="text-xl font-semibold">{formatCurrency(stockData.price)}</span>
                  <span className={`flex items-center text-sm ${stockData.change >= 0 ? "text-success" : "text-destructive"}`}>
                    {stockData.change >= 0 ? <ArrowUpRight className="h-4 w-4" /> : <ArrowDownRight className="h-4 w-4" />}
                    {formatCurrency(Math.abs(stockData.change))} ({formatPercent(Math.abs(stockData.changePercent))})
                  </span>
                </div>
              </div>
              <div className="h-10 border-l border-border" />
              <div>
                <div className="text-sm text-muted-foreground">Volume</div>
                <div className="font-semibold">{(stockData.volume / 1000000).toFixed(1)}M</div>
              </div>
              <div>
                <div className="text-sm text-muted-foreground">Avg Volume</div>
                <div className="font-semibold">{(stockData.avgVolume / 1000000).toFixed(1)}M</div>
              </div>
            </div>
            <div className="flex gap-2">
              <Button variant="outline" size="sm">
                <Bell className="mr-2 h-4 w-4" />
                Alert
              </Button>
              <Button variant="outline" size="sm">
                <Eye className="mr-2 h-4 w-4" />
                Watch
              </Button>
              <Button size="sm" className="bg-accent text-accent-foreground hover:bg-accent/90">
                <Zap className="mr-2 h-4 w-4" />
                Analyze
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Controls */}
      <Card className="border-border/50 bg-card/50 backdrop-blur">
        <CardContent className="flex flex-wrap items-center justify-between gap-4 p-4">
          <div className="flex items-center gap-4">
            <div className="flex items-center gap-2">
              <Calendar className="h-4 w-4 text-muted-foreground" />
              <span className="text-sm font-medium">Expiration:</span>
            </div>
            <div className="flex gap-2">
              {expirations.slice(0, 4).map((exp) => (
                <Button
                  key={exp.value}
                  variant={selectedExpiry === exp.value ? "default" : "outline"}
                  size="sm"
                  onClick={() => setSelectedExpiry(exp.value)}
                  className={selectedExpiry === exp.value ? "bg-accent text-accent-foreground" : ""}
                >
                  {exp.label}
                  <Badge variant="secondary" className="ml-2 text-xs">
                    {exp.daysToExpiry}d
                  </Badge>
                </Button>
              ))}
            </div>
          </div>
          <div className="flex items-center gap-4">
            <Button
              variant={showGreeks ? "default" : "outline"}
              size="sm"
              onClick={() => setShowGreeks(!showGreeks)}
              className={showGreeks ? "bg-accent text-accent-foreground" : ""}
            >
              Greeks
            </Button>
            <Button
              variant={highlightVolume ? "default" : "outline"}
              size="sm"
              onClick={() => setHighlightVolume(!highlightVolume)}
              className={highlightVolume ? "bg-accent text-accent-foreground" : ""}
            >
              Volume Heat
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Options Chain Table */}
      <Card className="border-border/50 bg-card/50 backdrop-blur">
        <CardHeader className="pb-2">
          <CardTitle className="flex items-center justify-between">
            <span className="flex items-center gap-2">
              <Activity className="h-5 w-5 text-accent" />
              Options Chain - {selectedExpiration?.label}
            </span>
            <Badge variant="outline">{selectedExpiration?.daysToExpiry} days to expiry</Badge>
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-border/50">
                  <th colSpan={showGreeks ? 8 : 5} className="bg-success/10 px-4 py-3 text-center font-medium text-success">
                    CALLS
                  </th>
                  <th className="border-x border-border/50 bg-muted/50 px-4 py-3 text-center font-medium">
                    Strike
                  </th>
                  <th colSpan={showGreeks ? 8 : 5} className="bg-destructive/10 px-4 py-3 text-center font-medium text-destructive">
                    PUTS
                  </th>
                </tr>
                <tr className="border-b border-border/50 text-xs text-muted-foreground">
                  <th className="px-2 py-2 text-right">Last</th>
                  <th className="px-2 py-2 text-right">Chg</th>
                  <th className="px-2 py-2 text-right">Bid</th>
                  <th className="px-2 py-2 text-right">Ask</th>
                  <th className="px-2 py-2 text-right">Vol</th>
                  {showGreeks && (
                    <>
                      <th className="px-2 py-2 text-right">IV</th>
                      <th className="px-2 py-2 text-right">Delta</th>
                      <th className="px-2 py-2 text-right">Gamma</th>
                    </>
                  )}
                  <th className="border-x border-border/50 bg-muted/30 px-4 py-2 text-center font-medium">$</th>
                  <th className="px-2 py-2 text-right">Last</th>
                  <th className="px-2 py-2 text-right">Chg</th>
                  <th className="px-2 py-2 text-right">Bid</th>
                  <th className="px-2 py-2 text-right">Ask</th>
                  <th className="px-2 py-2 text-right">Vol</th>
                  {showGreeks && (
                    <>
                      <th className="px-2 py-2 text-right">IV</th>
                      <th className="px-2 py-2 text-right">Delta</th>
                      <th className="px-2 py-2 text-right">Gamma</th>
                    </>
                  )}
                </tr>
              </thead>
              <tbody>
                {optionsChain.map((row, i) => {
                  const callVolHighlight = highlightVolume && row.call.volume > 2000;
                  const putVolHighlight = highlightVolume && row.put.volume > 2000;

                  return (
                    <motion.tr
                      key={row.strike}
                      initial={{ opacity: 0 }}
                      animate={{ opacity: 1 }}
                      transition={{ delay: i * 0.02 }}
                      className={`border-b border-border/30 transition-colors hover:bg-muted/30 ${
                        row.isATM ? "bg-accent/10" : row.isITM ? "bg-success/5" : ""
                      }`}
                    >
                      <td className={`px-2 py-2 text-right ${callVolHighlight ? "bg-success/20 font-semibold" : ""}`}>
                        {row.call.last.toFixed(2)}
                      </td>
                      <td className={`px-2 py-2 text-right ${row.call.change >= 0 ? "text-success" : "text-destructive"}`}>
                        {row.call.change >= 0 ? "+" : ""}{row.call.change.toFixed(2)}
                      </td>
                      <td className="px-2 py-2 text-right">{row.call.bid.toFixed(2)}</td>
                      <td className="px-2 py-2 text-right">{row.call.ask.toFixed(2)}</td>
                      <td className={`px-2 py-2 text-right ${callVolHighlight ? "font-semibold text-success" : ""}`}>
                        {row.call.volume.toLocaleString()}
                      </td>
                      {showGreeks && (
                        <>
                          <td className="px-2 py-2 text-right">{formatPercent(row.call.iv)}</td>
                          <td className="px-2 py-2 text-right">{row.call.delta.toFixed(2)}</td>
                          <td className="px-2 py-2 text-right">{row.call.gamma.toFixed(3)}</td>
                        </>
                      )}
                      <td className={`border-x border-border/50 px-4 py-2 text-center font-semibold ${
                        row.isATM ? "bg-accent/20 text-accent" : "bg-muted/30"
                      }`}>
                        ${row.strike}
                      </td>
                      <td className={`px-2 py-2 text-right ${putVolHighlight ? "bg-destructive/20 font-semibold" : ""}`}>
                        {row.put.last.toFixed(2)}
                      </td>
                      <td className={`px-2 py-2 text-right ${row.put.change >= 0 ? "text-success" : "text-destructive"}`}>
                        {row.put.change >= 0 ? "+" : ""}{row.put.change.toFixed(2)}
                      </td>
                      <td className="px-2 py-2 text-right">{row.put.bid.toFixed(2)}</td>
                      <td className="px-2 py-2 text-right">{row.put.ask.toFixed(2)}</td>
                      <td className={`px-2 py-2 text-right ${putVolHighlight ? "font-semibold text-destructive" : ""}`}>
                        {row.put.volume.toLocaleString()}
                      </td>
                      {showGreeks && (
                        <>
                          <td className="px-2 py-2 text-right">{formatPercent(row.put.iv)}</td>
                          <td className="px-2 py-2 text-right">{row.put.delta.toFixed(2)}</td>
                          <td className="px-2 py-2 text-right">{row.put.gamma.toFixed(3)}</td>
                        </>
                      )}
                    </motion.tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>

      {/* AI Insights */}
      <Card className="border-accent/30 bg-gradient-to-br from-accent/5 to-transparent">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Zap className="h-5 w-5 text-accent" />
            AI Options Insights
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid gap-4 md:grid-cols-3">
            <div className="rounded-lg border border-border/50 bg-background/50 p-4">
              <h4 className="mb-2 font-semibold">Unusual Activity Detected</h4>
              <p className="text-sm text-muted-foreground">
                Heavy call volume at $180 strike suggests bullish institutional positioning. Volume is 3x the average open interest.
              </p>
              <Badge className="mt-2 bg-success/20 text-success">Bullish Signal</Badge>
            </div>
            <div className="rounded-lg border border-border/50 bg-background/50 p-4">
              <h4 className="mb-2 font-semibold">IV Analysis</h4>
              <p className="text-sm text-muted-foreground">
                Implied volatility is elevated at 28.5%, sitting at the 72nd percentile of the past year. Options are relatively expensive.
              </p>
              <Badge className="mt-2 bg-warning/20 text-warning">IV Rich</Badge>
            </div>
            <div className="rounded-lg border border-border/50 bg-background/50 p-4">
              <h4 className="mb-2 font-semibold">Recommended Strategy</h4>
              <p className="text-sm text-muted-foreground">
                Consider a bull call spread ($175/$185) to reduce cost basis while maintaining upside exposure.
              </p>
              <Button size="sm" className="mt-2 bg-accent text-accent-foreground hover:bg-accent/90">
                View Strategy
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
