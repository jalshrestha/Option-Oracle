"use client";

import { motion } from "framer-motion";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { TrendingUp, TrendingDown, Target, Zap, Calendar, DollarSign } from "lucide-react";
import type { AnalysisResult } from "@/lib/api/types";
import { formatCurrency, formatPercent } from "@/lib/utils/format";

interface OptionsTabProps {
  analysis: AnalysisResult;
}

export function OptionsTab({ analysis }: OptionsTabProps) {
  const { options_strategies } = analysis;

  return (
    <div className="space-y-6">
      {/* Strategy Recommendations */}
      <Card className="border-border/50 bg-card/50 backdrop-blur">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Zap className="h-5 w-5 text-accent" />
            AI-Recommended Strategies
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid gap-4">
            {options_strategies.recommendations.map((strategy, i) => (
              <motion.div
                key={strategy.name}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: i * 0.1 }}
                className="rounded-lg border border-border/50 bg-background/50 p-4"
              >
                <div className="flex items-start justify-between">
                  <div className="space-y-2">
                    <div className="flex items-center gap-2">
                      <h4 className="font-semibold">{strategy.name}</h4>
                      <Badge variant={strategy.risk_level === "low" ? "default" : strategy.risk_level === "medium" ? "secondary" : "destructive"}>
                        {strategy.risk_level} risk
                      </Badge>
                    </div>
                    <p className="text-sm text-muted-foreground">{strategy.description}</p>
                    <div className="flex items-center gap-4 text-sm">
                      <span className="flex items-center gap-1">
                        <Target className="h-4 w-4 text-accent" />
                        Max Profit: {formatCurrency(strategy.max_profit)}
                      </span>
                      <span className="flex items-center gap-1">
                        <TrendingDown className="h-4 w-4 text-destructive" />
                        Max Loss: {formatCurrency(strategy.max_loss)}
                      </span>
                      <span className="flex items-center gap-1">
                        <Calendar className="h-4 w-4 text-muted-foreground" />
                        {strategy.timeframe}
                      </span>
                    </div>
                  </div>
                  <div className="text-right">
                    <div className="text-2xl font-bold text-accent">
                      {formatPercent(strategy.win_probability)}
                    </div>
                    <div className="text-xs text-muted-foreground">Win Rate</div>
                  </div>
                </div>
                <div className="mt-4 flex gap-2">
                  <Button size="sm" className="bg-accent text-accent-foreground hover:bg-accent/90">
                    Execute Trade
                  </Button>
                  <Button size="sm" variant="outline">
                    View Details
                  </Button>
                </div>
              </motion.div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Options Flow */}
      <Card className="border-border/50 bg-card/50 backdrop-blur">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <DollarSign className="h-5 w-5 text-accent" />
            Unusual Options Activity
          </CardTitle>
        </CardHeader>
        <CardContent>
          <Tabs defaultValue="calls">
            <TabsList className="mb-4">
              <TabsTrigger value="calls" className="flex items-center gap-1">
                <TrendingUp className="h-4 w-4" />
                Calls
              </TabsTrigger>
              <TabsTrigger value="puts" className="flex items-center gap-1">
                <TrendingDown className="h-4 w-4" />
                Puts
              </TabsTrigger>
            </TabsList>
            <TabsContent value="calls">
              <div className="space-y-2">
                {options_strategies.unusual_activity
                  .filter((a) => a.type === "call")
                  .map((activity, i) => (
                    <div
                      key={i}
                      className="flex items-center justify-between rounded-lg border border-success/20 bg-success/5 p-3"
                    >
                      <div className="flex items-center gap-3">
                        <Badge variant="outline" className="border-success text-success">
                          CALL
                        </Badge>
                        <span className="font-medium">${activity.strike}</span>
                        <span className="text-sm text-muted-foreground">{activity.expiry}</span>
                      </div>
                      <div className="flex items-center gap-4">
                        <div className="text-right">
                          <div className="font-semibold">{activity.volume.toLocaleString()}</div>
                          <div className="text-xs text-muted-foreground">Volume</div>
                        </div>
                        <div className="text-right">
                          <div className="font-semibold">{activity.open_interest.toLocaleString()}</div>
                          <div className="text-xs text-muted-foreground">OI</div>
                        </div>
                        <Badge className="bg-success/20 text-success">
                          {activity.volume / activity.open_interest > 1 ? "Sweep" : "Block"}
                        </Badge>
                      </div>
                    </div>
                  ))}
              </div>
            </TabsContent>
            <TabsContent value="puts">
              <div className="space-y-2">
                {options_strategies.unusual_activity
                  .filter((a) => a.type === "put")
                  .map((activity, i) => (
                    <div
                      key={i}
                      className="flex items-center justify-between rounded-lg border border-destructive/20 bg-destructive/5 p-3"
                    >
                      <div className="flex items-center gap-3">
                        <Badge variant="outline" className="border-destructive text-destructive">
                          PUT
                        </Badge>
                        <span className="font-medium">${activity.strike}</span>
                        <span className="text-sm text-muted-foreground">{activity.expiry}</span>
                      </div>
                      <div className="flex items-center gap-4">
                        <div className="text-right">
                          <div className="font-semibold">{activity.volume.toLocaleString()}</div>
                          <div className="text-xs text-muted-foreground">Volume</div>
                        </div>
                        <div className="text-right">
                          <div className="font-semibold">{activity.open_interest.toLocaleString()}</div>
                          <div className="text-xs text-muted-foreground">OI</div>
                        </div>
                        <Badge className="bg-destructive/20 text-destructive">
                          {activity.volume / activity.open_interest > 1 ? "Sweep" : "Block"}
                        </Badge>
                      </div>
                    </div>
                  ))}
              </div>
            </TabsContent>
          </Tabs>
        </CardContent>
      </Card>

      {/* Greeks Summary */}
      <Card className="border-border/50 bg-card/50 backdrop-blur">
        <CardHeader>
          <CardTitle>Greeks Analysis</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 gap-4 md:grid-cols-4">
            {Object.entries(options_strategies.greeks_summary).map(([greek, value]) => (
              <div key={greek} className="rounded-lg border border-border/50 bg-background/50 p-4 text-center">
                <div className="text-2xl font-bold">{typeof value === "number" ? value.toFixed(4) : value}</div>
                <div className="text-sm capitalize text-muted-foreground">{greek}</div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
