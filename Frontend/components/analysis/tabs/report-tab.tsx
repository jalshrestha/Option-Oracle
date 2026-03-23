"use client";

import { useState } from "react";
import { motion } from "framer-motion";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import { 
  FileText, 
  Download, 
  Share2, 
  Printer, 
  Calendar, 
  Clock,
  CheckCircle,
  AlertCircle,
  TrendingUp,
  TrendingDown,
  Minus
} from "lucide-react";
import type { AnalysisResult } from "@/lib/api/types";
import { formatCurrency, formatPercent, formatNumber } from "@/lib/utils/format";

interface ReportTabProps {
  analysis: AnalysisResult;
}

export function ReportTab({ analysis }: ReportTabProps) {
  const [isExporting, setIsExporting] = useState(false);

  const handleExport = async (format: string) => {
    setIsExporting(true);
    // Simulate export
    await new Promise((resolve) => setTimeout(resolve, 1500));
    setIsExporting(false);
  };

  return (
    <div className="space-y-6">
      {/* Report Header */}
      <Card className="border-accent/30 bg-gradient-to-br from-accent/5 to-transparent">
        <CardContent className="p-6">
          <div className="flex items-start justify-between">
            <div className="flex items-center gap-4">
              <div className="rounded-lg bg-accent/10 p-3">
                <FileText className="h-8 w-8 text-accent" />
              </div>
              <div>
                <h2 className="text-2xl font-bold">Analysis Report: {analysis.symbol}</h2>
                <div className="mt-1 flex items-center gap-4 text-sm text-muted-foreground">
                  <span className="flex items-center gap-1">
                    <Calendar className="h-4 w-4" />
                    {new Date(analysis.timestamp).toLocaleDateString()}
                  </span>
                  <span className="flex items-center gap-1">
                    <Clock className="h-4 w-4" />
                    {new Date(analysis.timestamp).toLocaleTimeString()}
                  </span>
                </div>
              </div>
            </div>
            <div className="flex gap-2">
              <Button variant="outline" size="sm" onClick={() => handleExport("pdf")}>
                <Download className="mr-2 h-4 w-4" />
                PDF
              </Button>
              <Button variant="outline" size="sm">
                <Share2 className="mr-2 h-4 w-4" />
                Share
              </Button>
              <Button variant="outline" size="sm">
                <Printer className="mr-2 h-4 w-4" />
                Print
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Executive Summary */}
      <Card className="border-border/50 bg-card/50 backdrop-blur">
        <CardHeader>
          <CardTitle>Executive Summary</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <p className="text-muted-foreground">{analysis.ai_summary}</p>
          
          <Separator />
          
          <div className="grid gap-4 md:grid-cols-4">
            <div className="rounded-lg bg-muted/50 p-4 text-center">
              <div className="flex items-center justify-center gap-1">
                {analysis.signal === "bullish" ? (
                  <TrendingUp className="h-5 w-5 text-success" />
                ) : analysis.signal === "bearish" ? (
                  <TrendingDown className="h-5 w-5 text-destructive" />
                ) : (
                  <Minus className="h-5 w-5 text-warning" />
                )}
                <span className={`text-xl font-bold capitalize ${
                  analysis.signal === "bullish" ? "text-success" :
                  analysis.signal === "bearish" ? "text-destructive" : "text-warning"
                }`}>
                  {analysis.signal}
                </span>
              </div>
              <div className="text-sm text-muted-foreground">Overall Signal</div>
            </div>
            <div className="rounded-lg bg-muted/50 p-4 text-center">
              <div className="text-xl font-bold text-accent">{formatPercent(analysis.confidence)}</div>
              <div className="text-sm text-muted-foreground">Confidence</div>
            </div>
            <div className="rounded-lg bg-muted/50 p-4 text-center">
              <div className={`text-xl font-bold capitalize ${
                analysis.risk_assessment.overall_risk === "low" ? "text-success" :
                analysis.risk_assessment.overall_risk === "medium" ? "text-warning" : "text-destructive"
              }`}>
                {analysis.risk_assessment.overall_risk}
              </div>
              <div className="text-sm text-muted-foreground">Risk Level</div>
            </div>
            <div className="rounded-lg bg-muted/50 p-4 text-center">
              <div className="text-xl font-bold">{formatCurrency(analysis.price_targets.target)}</div>
              <div className="text-sm text-muted-foreground">Price Target</div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Key Findings */}
      <Card className="border-border/50 bg-card/50 backdrop-blur">
        <CardHeader>
          <CardTitle>Key Findings</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {analysis.key_findings.map((finding, i) => (
              <motion.div
                key={i}
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: i * 0.1 }}
                className="flex items-start gap-3"
              >
                {finding.type === "positive" ? (
                  <CheckCircle className="mt-0.5 h-5 w-5 flex-shrink-0 text-success" />
                ) : finding.type === "negative" ? (
                  <AlertCircle className="mt-0.5 h-5 w-5 flex-shrink-0 text-destructive" />
                ) : (
                  <AlertCircle className="mt-0.5 h-5 w-5 flex-shrink-0 text-warning" />
                )}
                <div>
                  <div className="font-medium">{finding.title}</div>
                  <div className="text-sm text-muted-foreground">{finding.description}</div>
                </div>
              </motion.div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Agent Consensus */}
      <Card className="border-border/50 bg-card/50 backdrop-blur">
        <CardHeader>
          <CardTitle>AI Agent Consensus</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-border/50">
                  <th className="pb-3 text-left text-sm font-medium text-muted-foreground">Agent</th>
                  <th className="pb-3 text-center text-sm font-medium text-muted-foreground">Signal</th>
                  <th className="pb-3 text-center text-sm font-medium text-muted-foreground">Confidence</th>
                  <th className="pb-3 text-left text-sm font-medium text-muted-foreground">Key Insight</th>
                </tr>
              </thead>
              <tbody>
                {analysis.agent_analyses.map((agent) => (
                  <tr key={agent.agent_id} className="border-b border-border/30">
                    <td className="py-3">
                      <div className="flex items-center gap-2">
                        <div 
                          className="h-2 w-2 rounded-full"
                          style={{ backgroundColor: agent.color }}
                        />
                        <span className="font-medium">{agent.name}</span>
                      </div>
                    </td>
                    <td className="py-3 text-center">
                      <Badge variant={
                        agent.signal === "bullish" ? "default" :
                        agent.signal === "bearish" ? "destructive" : "secondary"
                      } className={
                        agent.signal === "bullish" ? "bg-success/20 text-success" :
                        agent.signal === "bearish" ? "bg-destructive/20 text-destructive" : ""
                      }>
                        {agent.signal}
                      </Badge>
                    </td>
                    <td className="py-3 text-center">
                      <span className="font-semibold">{formatPercent(agent.confidence)}</span>
                    </td>
                    <td className="py-3 text-sm text-muted-foreground">
                      {agent.key_points[0]}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>

      {/* Recommendations */}
      <Card className="border-border/50 bg-card/50 backdrop-blur">
        <CardHeader>
          <CardTitle>Actionable Recommendations</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {analysis.recommendations.map((rec, i) => (
              <motion.div
                key={i}
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: i * 0.1 }}
                className="rounded-lg border border-border/50 bg-background/50 p-4"
              >
                <div className="flex items-start justify-between">
                  <div>
                    <Badge className="mb-2" variant={
                      rec.priority === "high" ? "default" :
                      rec.priority === "medium" ? "secondary" : "outline"
                    }>
                      {rec.priority} priority
                    </Badge>
                    <h4 className="font-semibold">{rec.action}</h4>
                    <p className="mt-1 text-sm text-muted-foreground">{rec.rationale}</p>
                  </div>
                  <Button size="sm" className="bg-accent text-accent-foreground hover:bg-accent/90">
                    Execute
                  </Button>
                </div>
              </motion.div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Disclaimer */}
      <Card className="border-warning/30 bg-warning/5">
        <CardContent className="p-4">
          <div className="flex items-start gap-3">
            <AlertCircle className="mt-0.5 h-5 w-5 flex-shrink-0 text-warning" />
            <div className="text-sm text-muted-foreground">
              <strong className="text-foreground">Disclaimer:</strong> This report is generated by AI analysis and is for informational purposes only. 
              It does not constitute financial advice. Past performance is not indicative of future results. 
              Always consult with a qualified financial advisor before making investment decisions.
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
