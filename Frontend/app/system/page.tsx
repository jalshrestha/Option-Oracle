"use client";

import { useState, useEffect } from "react";
import { motion } from "framer-motion";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Switch } from "@/components/ui/switch";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Progress } from "@/components/ui/progress";
import { Label } from "@/components/ui/label";
import {
  Activity,
  Cpu,
  Database,
  Wifi,
  Clock,
  CheckCircle,
  AlertCircle,
  RefreshCw,
  Settings,
  Shield,
  Zap,
  Server,
  HardDrive,
  MemoryStick,
  TrendingUp,
  Globe,
  Lock,
  Key,
  Bell,
  Moon,
  Sun,
  Palette,
} from "lucide-react";
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from "recharts";

// Mock system data
const systemMetrics = {
  cpu: 42,
  memory: 68,
  storage: 35,
  network: 99.9,
  apiLatency: 45,
  uptime: 99.97,
};

const agents = [
  { id: "technical", name: "Technical Analyst", status: "online", latency: 32, requests: 15234, accuracy: 0.92 },
  { id: "fundamental", name: "Fundamental Analyst", status: "online", latency: 45, requests: 12456, accuracy: 0.88 },
  { id: "sentiment", name: "Sentiment Analyst", status: "online", latency: 28, requests: 18934, accuracy: 0.85 },
  { id: "options", name: "Options Strategist", status: "online", latency: 38, requests: 9876, accuracy: 0.91 },
  { id: "risk", name: "Risk Manager", status: "online", latency: 22, requests: 8765, accuracy: 0.94 },
  { id: "macro", name: "Macro Analyst", status: "maintenance", latency: 0, requests: 7654, accuracy: 0.87 },
];

const apiLogs = [
  { time: "14:32:15", endpoint: "/api/analyze", status: 200, duration: 234, method: "POST" },
  { time: "14:32:10", endpoint: "/api/chat", status: 200, duration: 156, method: "POST" },
  { time: "14:32:05", endpoint: "/api/portfolio", status: 200, duration: 45, method: "GET" },
  { time: "14:31:58", endpoint: "/api/market-data", status: 200, duration: 23, method: "GET" },
  { time: "14:31:52", endpoint: "/api/options-chain", status: 200, duration: 78, method: "GET" },
  { time: "14:31:45", endpoint: "/api/analyze", status: 200, duration: 312, method: "POST" },
  { time: "14:31:40", endpoint: "/api/signals", status: 200, duration: 67, method: "GET" },
  { time: "14:31:35", endpoint: "/api/user", status: 401, duration: 12, method: "GET" },
];

const performanceHistory = Array.from({ length: 24 }, (_, i) => ({
  hour: `${i}:00`,
  cpu: 30 + Math.random() * 30,
  memory: 55 + Math.random() * 25,
  latency: 30 + Math.random() * 40,
}));

export default function SystemPage() {
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [autoRefresh, setAutoRefresh] = useState(true);
  const [metrics, setMetrics] = useState(systemMetrics);

  useEffect(() => {
    if (!autoRefresh) return;
    const interval = setInterval(() => {
      setMetrics({
        cpu: 35 + Math.random() * 20,
        memory: 60 + Math.random() * 15,
        storage: 35,
        network: 99.5 + Math.random() * 0.5,
        apiLatency: 35 + Math.random() * 25,
        uptime: 99.97,
      });
    }, 3000);
    return () => clearInterval(interval);
  }, [autoRefresh]);

  const handleRefresh = async () => {
    setIsRefreshing(true);
    await new Promise((resolve) => setTimeout(resolve, 1000));
    setIsRefreshing(false);
  };

  return (
    <div className="space-y-6 p-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">System Status</h1>
          <p className="text-muted-foreground">
            Monitor AI agents, API health, and system performance
          </p>
        </div>
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2">
            <Switch
              id="auto-refresh"
              checked={autoRefresh}
              onCheckedChange={setAutoRefresh}
            />
            <Label htmlFor="auto-refresh" className="text-sm">Auto-refresh</Label>
          </div>
          <Button
            variant="outline"
            onClick={handleRefresh}
            disabled={isRefreshing}
          >
            <RefreshCw className={`mr-2 h-4 w-4 ${isRefreshing ? "animate-spin" : ""}`} />
            Refresh
          </Button>
        </div>
      </div>

      {/* System Health Overview */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
        >
          <Card className="border-success/30 bg-gradient-to-br from-success/10 to-transparent">
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className="rounded-lg bg-success/20 p-2">
                    <CheckCircle className="h-5 w-5 text-success" />
                  </div>
                  <div>
                    <p className="text-sm text-muted-foreground">System Status</p>
                    <p className="text-xl font-bold text-success">Operational</p>
                  </div>
                </div>
                <div className="text-right">
                  <p className="text-2xl font-bold">{metrics.uptime}%</p>
                  <p className="text-xs text-muted-foreground">Uptime</p>
                </div>
              </div>
            </CardContent>
          </Card>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
        >
          <Card className="border-border/50 bg-card/50">
            <CardContent className="p-6">
              <div className="flex items-center gap-3">
                <div className="rounded-lg bg-muted p-2">
                  <Cpu className="h-5 w-5 text-muted-foreground" />
                </div>
                <div className="flex-1">
                  <p className="text-sm text-muted-foreground">CPU Usage</p>
                  <p className="text-xl font-bold">{metrics.cpu.toFixed(1)}%</p>
                  <Progress value={metrics.cpu} className="mt-2 h-1.5" />
                </div>
              </div>
            </CardContent>
          </Card>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
        >
          <Card className="border-border/50 bg-card/50">
            <CardContent className="p-6">
              <div className="flex items-center gap-3">
                <div className="rounded-lg bg-muted p-2">
                  <MemoryStick className="h-5 w-5 text-muted-foreground" />
                </div>
                <div className="flex-1">
                  <p className="text-sm text-muted-foreground">Memory</p>
                  <p className="text-xl font-bold">{metrics.memory.toFixed(1)}%</p>
                  <Progress value={metrics.memory} className="mt-2 h-1.5" />
                </div>
              </div>
            </CardContent>
          </Card>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3 }}
        >
          <Card className="border-border/50 bg-card/50">
            <CardContent className="p-6">
              <div className="flex items-center gap-3">
                <div className="rounded-lg bg-muted p-2">
                  <Activity className="h-5 w-5 text-accent" />
                </div>
                <div>
                  <p className="text-sm text-muted-foreground">API Latency</p>
                  <p className="text-xl font-bold">{metrics.apiLatency.toFixed(0)}ms</p>
                  <p className="text-xs text-muted-foreground">Avg response time</p>
                </div>
              </div>
            </CardContent>
          </Card>
        </motion.div>
      </div>

      <Tabs defaultValue="agents" className="space-y-6">
        <TabsList>
          <TabsTrigger value="agents" className="flex items-center gap-2">
            <Zap className="h-4 w-4" />
            AI Agents
          </TabsTrigger>
          <TabsTrigger value="api" className="flex items-center gap-2">
            <Server className="h-4 w-4" />
            API Health
          </TabsTrigger>
          <TabsTrigger value="performance" className="flex items-center gap-2">
            <TrendingUp className="h-4 w-4" />
            Performance
          </TabsTrigger>
          <TabsTrigger value="settings" className="flex items-center gap-2">
            <Settings className="h-4 w-4" />
            Settings
          </TabsTrigger>
        </TabsList>

        <TabsContent value="agents" className="space-y-4">
          <Card className="border-border/50 bg-card/50 backdrop-blur">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Zap className="h-5 w-5 text-accent" />
                AI Agent Status
              </CardTitle>
              <CardDescription>
                Real-time status of all AI analysis agents
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {agents.map((agent, i) => (
                  <motion.div
                    key={agent.id}
                    initial={{ opacity: 0, x: -20 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: i * 0.1 }}
                    className="flex items-center justify-between rounded-lg border border-border/50 bg-background/50 p-4"
                  >
                    <div className="flex items-center gap-4">
                      <div className={`h-3 w-3 rounded-full ${
                        agent.status === "online" ? "bg-success animate-pulse" : "bg-warning"
                      }`} />
                      <div>
                        <div className="font-medium">{agent.name}</div>
                        <div className="text-sm text-muted-foreground">
                          {agent.requests.toLocaleString()} requests
                        </div>
                      </div>
                    </div>
                    <div className="flex items-center gap-6">
                      <div className="text-right">
                        <div className="text-sm font-medium">
                          {agent.status === "online" ? `${agent.latency}ms` : "N/A"}
                        </div>
                        <div className="text-xs text-muted-foreground">Latency</div>
                      </div>
                      <div className="text-right">
                        <div className="text-sm font-medium">
                          {(agent.accuracy * 100).toFixed(0)}%
                        </div>
                        <div className="text-xs text-muted-foreground">Accuracy</div>
                      </div>
                      <Badge variant={agent.status === "online" ? "default" : "secondary"} className={
                        agent.status === "online" ? "bg-success/20 text-success" : ""
                      }>
                        {agent.status}
                      </Badge>
                    </div>
                  </motion.div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="api" className="space-y-4">
          <div className="grid gap-4 lg:grid-cols-2">
            <Card className="border-border/50 bg-card/50 backdrop-blur">
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Server className="h-5 w-5 text-accent" />
                  Recent API Requests
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-2">
                  {apiLogs.map((log, i) => (
                    <motion.div
                      key={i}
                      initial={{ opacity: 0 }}
                      animate={{ opacity: 1 }}
                      transition={{ delay: i * 0.05 }}
                      className="flex items-center justify-between rounded-lg border border-border/30 bg-background/30 p-3 font-mono text-sm"
                    >
                      <div className="flex items-center gap-3">
                        <span className="text-muted-foreground">{log.time}</span>
                        <Badge variant="outline" className="text-xs">
                          {log.method}
                        </Badge>
                        <span>{log.endpoint}</span>
                      </div>
                      <div className="flex items-center gap-3">
                        <span className="text-muted-foreground">{log.duration}ms</span>
                        <Badge variant={log.status === 200 ? "default" : "destructive"} className={
                          log.status === 200 ? "bg-success/20 text-success" : ""
                        }>
                          {log.status}
                        </Badge>
                      </div>
                    </motion.div>
                  ))}
                </div>
              </CardContent>
            </Card>

            <Card className="border-border/50 bg-card/50 backdrop-blur">
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Globe className="h-5 w-5 text-accent" />
                  Endpoint Health
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {[
                    { name: "/api/analyze", status: "healthy", latency: 234, uptime: 99.9 },
                    { name: "/api/chat", status: "healthy", latency: 156, uptime: 99.95 },
                    { name: "/api/portfolio", status: "healthy", latency: 45, uptime: 100 },
                    { name: "/api/market-data", status: "healthy", latency: 23, uptime: 99.99 },
                    { name: "/api/options-chain", status: "healthy", latency: 78, uptime: 99.8 },
                  ].map((endpoint, i) => (
                    <div key={i} className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <div className="h-2 w-2 rounded-full bg-success" />
                        <span className="font-mono text-sm">{endpoint.name}</span>
                      </div>
                      <div className="flex items-center gap-4 text-sm">
                        <span className="text-muted-foreground">{endpoint.latency}ms</span>
                        <span className="text-success">{endpoint.uptime}%</span>
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        <TabsContent value="performance" className="space-y-4">
          <Card className="border-border/50 bg-card/50 backdrop-blur">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <TrendingUp className="h-5 w-5 text-accent" />
                24-Hour Performance
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="h-80">
                <ResponsiveContainer width="100%" height="100%">
                  <AreaChart data={performanceHistory}>
                    <defs>
                      <linearGradient id="cpuGradient" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="0%" stopColor="hsl(var(--accent))" stopOpacity={0.3} />
                        <stop offset="100%" stopColor="hsl(var(--accent))" stopOpacity={0} />
                      </linearGradient>
                      <linearGradient id="memoryGradient" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="0%" stopColor="hsl(var(--success))" stopOpacity={0.3} />
                        <stop offset="100%" stopColor="hsl(var(--success))" stopOpacity={0} />
                      </linearGradient>
                    </defs>
                    <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" opacity={0.3} />
                    <XAxis 
                      dataKey="hour" 
                      tick={{ fill: "hsl(var(--muted-foreground))", fontSize: 12 }}
                    />
                    <YAxis 
                      tick={{ fill: "hsl(var(--muted-foreground))", fontSize: 12 }}
                      tickFormatter={(value) => `${value}%`}
                    />
                    <Tooltip
                      contentStyle={{
                        backgroundColor: "hsl(var(--card))",
                        border: "1px solid hsl(var(--border))",
                        borderRadius: "8px",
                      }}
                    />
                    <Area
                      type="monotone"
                      dataKey="cpu"
                      name="CPU"
                      stroke="hsl(var(--accent))"
                      fill="url(#cpuGradient)"
                      strokeWidth={2}
                    />
                    <Area
                      type="monotone"
                      dataKey="memory"
                      name="Memory"
                      stroke="hsl(var(--success))"
                      fill="url(#memoryGradient)"
                      strokeWidth={2}
                    />
                  </AreaChart>
                </ResponsiveContainer>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="settings" className="space-y-4">
          <div className="grid gap-6 lg:grid-cols-2">
            <Card className="border-border/50 bg-card/50 backdrop-blur">
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Palette className="h-5 w-5 text-accent" />
                  Appearance
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <Moon className="h-4 w-4" />
                    <Label>Dark Mode</Label>
                  </div>
                  <Switch defaultChecked />
                </div>
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <Sun className="h-4 w-4" />
                    <Label>Reduce Motion</Label>
                  </div>
                  <Switch />
                </div>
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <Activity className="h-4 w-4" />
                    <Label>Live Data Updates</Label>
                  </div>
                  <Switch defaultChecked />
                </div>
              </CardContent>
            </Card>

            <Card className="border-border/50 bg-card/50 backdrop-blur">
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Bell className="h-5 w-5 text-accent" />
                  Notifications
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="flex items-center justify-between">
                  <Label>Signal Alerts</Label>
                  <Switch defaultChecked />
                </div>
                <div className="flex items-center justify-between">
                  <Label>Price Alerts</Label>
                  <Switch defaultChecked />
                </div>
                <div className="flex items-center justify-between">
                  <Label>System Notifications</Label>
                  <Switch />
                </div>
                <div className="flex items-center justify-between">
                  <Label>Email Digest</Label>
                  <Switch />
                </div>
              </CardContent>
            </Card>

            <Card className="border-border/50 bg-card/50 backdrop-blur">
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Shield className="h-5 w-5 text-accent" />
                  Security
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <Lock className="h-4 w-4" />
                    <Label>Two-Factor Auth</Label>
                  </div>
                  <Switch defaultChecked />
                </div>
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <Key className="h-4 w-4" />
                    <Label>API Key Access</Label>
                  </div>
                  <Switch />
                </div>
                <Button variant="outline" className="w-full">
                  Manage API Keys
                </Button>
              </CardContent>
            </Card>

            <Card className="border-border/50 bg-card/50 backdrop-blur">
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Database className="h-5 w-5 text-accent" />
                  Data & Storage
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div>
                  <div className="mb-2 flex justify-between text-sm">
                    <span>Storage Used</span>
                    <span>{metrics.storage}% of 10 GB</span>
                  </div>
                  <Progress value={metrics.storage} className="h-2" />
                </div>
                <Button variant="outline" className="w-full">
                  Clear Cache
                </Button>
                <Button variant="outline" className="w-full">
                  Export Data
                </Button>
              </CardContent>
            </Card>
          </div>
        </TabsContent>
      </Tabs>
    </div>
  );
}
