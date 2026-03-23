"use client";

import { motion } from "framer-motion";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { AlertTriangle, Shield, TrendingDown, Activity, Zap, Target } from "lucide-react";
import type { AnalysisResult } from "@/lib/api/types";
import { formatPercent } from "@/lib/utils/format";
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from "recharts";

interface RiskTabProps {
  analysis: AnalysisResult;
}

export function RiskTab({ analysis }: RiskTabProps) {
  const { risk_assessment } = analysis;

  const riskColor = risk_assessment.overall_risk === "low" 
    ? "text-success" 
    : risk_assessment.overall_risk === "medium" 
    ? "text-warning" 
    : "text-destructive";

  const riskBgColor = risk_assessment.overall_risk === "low"
    ? "bg-success/10 border-success/30"
    : risk_assessment.overall_risk === "medium"
    ? "bg-warning/10 border-warning/30"
    : "bg-destructive/10 border-destructive/30";

  return (
    <div className="space-y-6">
      {/* Overall Risk */}
      <motion.div
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
      >
        <Card className={`border ${riskBgColor}`}>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-4">
                <div className={`rounded-full p-3 ${riskBgColor}`}>
                  <Shield className={`h-8 w-8 ${riskColor}`} />
                </div>
                <div>
                  <h3 className="text-lg font-semibold">Overall Risk Assessment</h3>
                  <p className="text-sm text-muted-foreground">{risk_assessment.summary}</p>
                </div>
              </div>
              <div className="text-right">
                <div className={`text-4xl font-bold capitalize ${riskColor}`}>
                  {risk_assessment.overall_risk}
                </div>
                <div className="text-sm text-muted-foreground">Risk Level</div>
              </div>
            </div>
          </CardContent>
        </Card>
      </motion.div>

      {/* Risk Metrics Grid */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        {/* Volatility */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
        >
          <Card className="border-border/50 bg-card/50 backdrop-blur">
            <CardHeader className="pb-2">
              <CardTitle className="flex items-center gap-2 text-sm font-medium">
                <Activity className="h-4 w-4 text-accent" />
                Volatility Analysis
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <div>
                  <div className="flex justify-between text-sm">
                    <span>Implied Volatility</span>
                    <span className="font-semibold">{formatPercent(risk_assessment.volatility.implied)}</span>
                  </div>
                  <Progress 
                    value={risk_assessment.volatility.implied * 100} 
                    className="mt-1 h-2"
                  />
                </div>
                <div>
                  <div className="flex justify-between text-sm">
                    <span>Historical Volatility</span>
                    <span className="font-semibold">{formatPercent(risk_assessment.volatility.historical)}</span>
                  </div>
                  <Progress 
                    value={risk_assessment.volatility.historical * 100} 
                    className="mt-1 h-2"
                  />
                </div>
                <div className="rounded-lg bg-muted/50 p-2 text-center">
                  <span className="text-sm text-muted-foreground">IV Percentile: </span>
                  <span className="font-semibold">{risk_assessment.volatility.iv_percentile}%</span>
                </div>
              </div>
            </CardContent>
          </Card>
        </motion.div>

        {/* Max Drawdown */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
        >
          <Card className="border-border/50 bg-card/50 backdrop-blur">
            <CardHeader className="pb-2">
              <CardTitle className="flex items-center gap-2 text-sm font-medium">
                <TrendingDown className="h-4 w-4 text-destructive" />
                Drawdown Analysis
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <div className="text-center">
                  <div className="text-3xl font-bold text-destructive">
                    {formatPercent(risk_assessment.max_drawdown)}
                  </div>
                  <div className="text-sm text-muted-foreground">Maximum Drawdown</div>
                </div>
                <div className="h-20">
                  <ResponsiveContainer width="100%" height="100%">
                    <AreaChart data={risk_assessment.drawdown_history}>
                      <defs>
                        <linearGradient id="drawdownGradient" x1="0" y1="0" x2="0" y2="1">
                          <stop offset="0%" stopColor="hsl(var(--destructive))" stopOpacity={0.3} />
                          <stop offset="100%" stopColor="hsl(var(--destructive))" stopOpacity={0} />
                        </linearGradient>
                      </defs>
                      <Area
                        type="monotone"
                        dataKey="value"
                        stroke="hsl(var(--destructive))"
                        fill="url(#drawdownGradient)"
                        strokeWidth={2}
                      />
                    </AreaChart>
                  </ResponsiveContainer>
                </div>
              </div>
            </CardContent>
          </Card>
        </motion.div>

        {/* VaR */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3 }}
        >
          <Card className="border-border/50 bg-card/50 backdrop-blur">
            <CardHeader className="pb-2">
              <CardTitle className="flex items-center gap-2 text-sm font-medium">
                <Target className="h-4 w-4 text-warning" />
                Value at Risk (VaR)
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <span className="text-sm">95% VaR (1-day)</span>
                  <Badge variant="outline" className="border-warning text-warning">
                    {formatPercent(risk_assessment.var_95)}
                  </Badge>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm">99% VaR (1-day)</span>
                  <Badge variant="outline" className="border-destructive text-destructive">
                    {formatPercent(risk_assessment.var_99)}
                  </Badge>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm">Expected Shortfall</span>
                  <Badge variant="outline">
                    {formatPercent(risk_assessment.expected_shortfall)}
                  </Badge>
                </div>
              </div>
            </CardContent>
          </Card>
        </motion.div>
      </div>

      {/* Risk Factors */}
      <Card className="border-border/50 bg-card/50 backdrop-blur">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <AlertTriangle className="h-5 w-5 text-warning" />
            Key Risk Factors
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            {risk_assessment.risk_factors.map((factor, i) => (
              <motion.div
                key={factor.name}
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: i * 0.1 }}
                className="flex items-center justify-between rounded-lg border border-border/50 bg-background/50 p-4"
              >
                <div className="flex items-center gap-3">
                  <div className={`h-2 w-2 rounded-full ${
                    factor.severity === "high" ? "bg-destructive" :
                    factor.severity === "medium" ? "bg-warning" : "bg-success"
                  }`} />
                  <div>
                    <div className="font-medium">{factor.name}</div>
                    <div className="text-sm text-muted-foreground">{factor.description}</div>
                  </div>
                </div>
                <Badge variant={
                  factor.severity === "high" ? "destructive" :
                  factor.severity === "medium" ? "secondary" : "default"
                }>
                  {factor.severity}
                </Badge>
              </motion.div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Scenario Analysis */}
      <Card className="border-border/50 bg-card/50 backdrop-blur">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Zap className="h-5 w-5 text-accent" />
            Scenario Analysis
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid gap-4 md:grid-cols-3">
            {risk_assessment.scenarios.map((scenario, i) => (
              <motion.div
                key={scenario.name}
                initial={{ opacity: 0, scale: 0.9 }}
                animate={{ opacity: 1, scale: 1 }}
                transition={{ delay: i * 0.1 }}
                className="rounded-lg border border-border/50 bg-background/50 p-4"
              >
                <h4 className="mb-2 font-semibold">{scenario.name}</h4>
                <p className="mb-3 text-sm text-muted-foreground">{scenario.description}</p>
                <div className="flex items-center justify-between">
                  <span className="text-sm">Expected Impact</span>
                  <span className={`font-bold ${
                    scenario.impact > 0 ? "text-success" : "text-destructive"
                  }`}>
                    {scenario.impact > 0 ? "+" : ""}{formatPercent(scenario.impact)}
                  </span>
                </div>
                <div className="mt-2 flex items-center justify-between text-sm">
                  <span className="text-muted-foreground">Probability</span>
                  <span>{formatPercent(scenario.probability)}</span>
                </div>
              </motion.div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
