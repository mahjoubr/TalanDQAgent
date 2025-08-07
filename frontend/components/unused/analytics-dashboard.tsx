"use client"

import { useState, useEffect } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Progress } from "@/components/ui/progress"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import {
  BarChart3,
  TrendingUp,
  TrendingDown,
  AlertTriangle,
  CheckCircle,
  Activity,
  Database,
  RefreshCw,
  Download,
  Eye,
  Calendar,
  Zap,
} from "lucide-react"
import { useToast } from "@/hooks/use-toast"

interface AnalyticsDashboardProps {
  connections: any[]
  analysisResults: any
  onRefresh?: () => void
}

export function AnalyticsDashboard({ connections, analysisResults, onRefresh }: AnalyticsDashboardProps) {
  const [selectedConnection, setSelectedConnection] = useState("")
  const [isRefreshing, setIsRefreshing] = useState(false)
  const [timeRange, setTimeRange] = useState("7d")
  const [dashboardData, setDashboardData] = useState({
    overview: {
      totalConnections: 0,
      activeAnalyses: 0,
      anomaliesDetected: 0,
      avgQualityScore: 0,
    },
    qualityTrends: [],
    anomalyTrends: [],
    connectionHealth: [],
  })
  const { toast } = useToast()

  useEffect(() => {
    updateDashboardData()
  }, [connections, analysisResults])

  const updateDashboardData = () => {
    // Calculate overview metrics
    const totalConnections = connections.length
    const activeAnalyses = Object.keys(analysisResults || {}).length

    let totalAnomalies = 0
    const qualityScores = []

    Object.values(analysisResults || {}).forEach((result: any) => {
      if (result.analysis_type === "anomaly_detection") {
        totalAnomalies += result.anomalies_detected || 0
      }
      if (result.analysis_type === "quality_metrics" && result.metrics) {
        const avgScore = Object.values(result.metrics).reduce((a: any, b: any) => a + b, 0) / 5
        qualityScores.push(avgScore)
      }
    })

    const avgQualityScore =
      qualityScores.length > 0 ? qualityScores.reduce((a, b) => a + b, 0) / qualityScores.length : 0

    // Generate mock trend data (in real app, this would come from historical data)
    const qualityTrends = generateMockTrendData("quality")
    const anomalyTrends = generateMockTrendData("anomaly")
    const connectionHealth = connections.map((conn) => ({
      id: conn.id,
      name: conn.type === "database" ? `${conn.dbType} DB` : conn.fileName || "Unknown",
      status: conn.status || "connected",
      lastUpdated: new Date().toISOString(),
      health: Math.random() > 0.2 ? "healthy" : "warning",
    }))

    setDashboardData({
      overview: {
        totalConnections,
        activeAnalyses,
        anomaliesDetected: totalAnomalies,
        avgQualityScore: Math.round(avgQualityScore),
      },
      qualityTrends,
      anomalyTrends,
      connectionHealth,
    })
  }

  const generateMockTrendData = (type: string) => {
    const days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    return days.map((day) => ({
      day,
      value: type === "quality" ? Math.floor(Math.random() * 20) + 80 : Math.floor(Math.random() * 10) + 2,
    }))
  }

  const handleRefresh = async () => {
    setIsRefreshing(true)
    try {
      if (onRefresh) {
        await onRefresh()
      }
      updateDashboardData()
      toast({
        title: "Dashboard Refreshed",
        description: "All data has been updated successfully",
      })
    } catch (error) {
      toast({
        title: "Refresh Failed",
        description: "Could not refresh dashboard data",
        variant: "destructive",
      })
    } finally {
      setIsRefreshing(false)
    }
  }

  const exportDashboard = () => {
    const exportData = {
      timestamp: new Date().toISOString(),
      overview: dashboardData.overview,
      connections: connections.length,
      analysisResults: Object.keys(analysisResults || {}).length,
    }

    const blob = new Blob([JSON.stringify(exportData, null, 2)], { type: "application/json" })
    const url = URL.createObjectURL(blob)
    const a = document.createElement("a")
    a.href = url
    a.download = `dashboard-export-${new Date().toISOString().split("T")[0]}.json`
    a.click()

    toast({
      title: "Dashboard Exported",
      description: "Dashboard data exported successfully",
    })
  }

  const getHealthColor = (health: string) => {
    switch (health) {
      case "healthy":
        return "text-green-600 bg-green-100"
      case "warning":
        return "text-yellow-600 bg-yellow-100"
      case "error":
        return "text-red-600 bg-red-100"
      default:
        return "text-gray-600 bg-gray-100"
    }
  }

  const getQualityScoreColor = (score: number) => {
    if (score >= 90) return "text-green-600"
    if (score >= 70) return "text-yellow-600"
    return "text-red-600"
  }

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-4xl font-bold bg-gradient-to-r from-blue-600 via-purple-600 to-cyan-600 bg-clip-text text-transparent">
            Analytics Dashboard
          </h1>
          <p className="text-gray-600 mt-2">Real-time insights into your data quality and anomaly detection</p>
        </div>
        <div className="flex gap-3">
          <Select value={timeRange} onValueChange={setTimeRange}>
            <SelectTrigger className="w-32">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="1d">Last 24h</SelectItem>
              <SelectItem value="7d">Last 7 days</SelectItem>
              <SelectItem value="30d">Last 30 days</SelectItem>
              <SelectItem value="90d">Last 90 days</SelectItem>
            </SelectContent>
          </Select>
          <Button
            onClick={exportDashboard}
            variant="outline"
            className="border-blue-200 hover:bg-blue-50 bg-transparent"
          >
            <Download className="mr-2 h-4 w-4" />
            Export
          </Button>
          <Button
            onClick={handleRefresh}
            disabled={isRefreshing}
            className="bg-gradient-to-r from-blue-500 to-purple-500 hover:from-blue-600 hover:to-purple-600 text-white"
          >
            {isRefreshing ? (
              <RefreshCw className="mr-2 h-4 w-4 animate-spin" />
            ) : (
              <RefreshCw className="mr-2 h-4 w-4" />
            )}
            Refresh
          </Button>
        </div>
      </div>

      {/* Overview Cards */}
      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-4">
        <Card className="border-0 shadow-lg hover:shadow-xl transition-all duration-300">
          <div className="h-2 bg-gradient-to-r from-blue-500 to-cyan-500 rounded-t-lg"></div>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium text-gray-600">Total Connections</CardTitle>
            <Database className="h-4 w-4 text-blue-500" />
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold text-blue-600">{dashboardData.overview.totalConnections}</div>
            <div className="flex items-center mt-2">
              <TrendingUp className="h-3 w-3 text-green-500 mr-1" />
              <span className="text-xs text-green-600">+2 this week</span>
            </div>
          </CardContent>
        </Card>

        <Card className="border-0 shadow-lg hover:shadow-xl transition-all duration-300">
          <div className="h-2 bg-gradient-to-r from-violet-500 to-purple-500 rounded-t-lg"></div>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium text-gray-600">Active Analyses</CardTitle>
            <Activity className="h-4 w-4 text-violet-500" />
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold text-violet-600">{dashboardData.overview.activeAnalyses}</div>
            <div className="flex items-center mt-2">
              <TrendingUp className="h-3 w-3 text-green-500 mr-1" />
              <span className="text-xs text-green-600">+5 today</span>
            </div>
          </CardContent>
        </Card>

        <Card className="border-0 shadow-lg hover:shadow-xl transition-all duration-300">
          <div className="h-2 bg-gradient-to-r from-pink-500 to-rose-500 rounded-t-lg"></div>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium text-gray-600">Anomalies Detected</CardTitle>
            <AlertTriangle className="h-4 w-4 text-pink-500" />
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold text-pink-600">{dashboardData.overview.anomaliesDetected}</div>
            <div className="flex items-center mt-2">
              <TrendingDown className="h-3 w-3 text-green-500 mr-1" />
              <span className="text-xs text-green-600">-3 from yesterday</span>
            </div>
          </CardContent>
        </Card>

        <Card className="border-0 shadow-lg hover:shadow-xl transition-all duration-300">
          <div className="h-2 bg-gradient-to-r from-green-500 to-emerald-500 rounded-t-lg"></div>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium text-gray-600">Avg Quality Score</CardTitle>
            <BarChart3 className="h-4 w-4 text-green-500" />
          </CardHeader>
          <CardContent>
            <div className={`text-3xl font-bold ${getQualityScoreColor(dashboardData.overview.avgQualityScore)}`}>
              {dashboardData.overview.avgQualityScore}%
            </div>
            <div className="flex items-center mt-2">
              <TrendingUp className="h-3 w-3 text-green-500 mr-1" />
              <span className="text-xs text-green-600">+2.3% this month</span>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Main Dashboard Content */}
      <Tabs defaultValue="overview" className="space-y-6">
        <TabsList className="grid w-full grid-cols-4 bg-gray-50 p-1 rounded-xl">
          <TabsTrigger value="overview" className="data-[state=active]:bg-white data-[state=active]:shadow-sm">
            Overview
          </TabsTrigger>
          <TabsTrigger value="quality" className="data-[state=active]:bg-white data-[state=active]:shadow-sm">
            Quality Metrics
          </TabsTrigger>
          <TabsTrigger value="anomalies" className="data-[state=active]:bg-white data-[state=active]:shadow-sm">
            Anomaly Detection
          </TabsTrigger>
          <TabsTrigger value="connections" className="data-[state=active]:bg-white data-[state=active]:shadow-sm">
            Connections
          </TabsTrigger>
        </TabsList>

        <TabsContent value="overview">
          <div className="grid gap-6 lg:grid-cols-2">
            {/* Quality Trends Chart */}
            <Card className="border-0 shadow-lg">
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <div className="p-2 bg-gradient-to-r from-blue-500 to-cyan-500 rounded-lg">
                    <TrendingUp className="h-4 w-4 text-white" />
                  </div>
                  Quality Score Trends
                </CardTitle>
                <CardDescription>Data quality metrics over time</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {dashboardData.qualityTrends.map((trend, index) => (
                    <div key={trend.day} className="flex items-center justify-between">
                      <span className="text-sm font-medium text-gray-600">{trend.day}</span>
                      <div className="flex items-center gap-3 flex-1 mx-4">
                        <Progress value={trend.value} className="flex-1" />
                        <span className={`text-sm font-bold ${getQualityScoreColor(trend.value)}`}>{trend.value}%</span>
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>

            {/* Anomaly Detection Chart */}
            <Card className="border-0 shadow-lg">
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <div className="p-2 bg-gradient-to-r from-pink-500 to-rose-500 rounded-lg">
                    <AlertTriangle className="h-4 w-4 text-white" />
                  </div>
                  Anomaly Detection Trends
                </CardTitle>
                <CardDescription>Anomalies detected over time</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {dashboardData.anomalyTrends.map((trend, index) => (
                    <div key={trend.day} className="flex items-center justify-between">
                      <span className="text-sm font-medium text-gray-600">{trend.day}</span>
                      <div className="flex items-center gap-3">
                        <div className="w-32 bg-gray-200 rounded-full h-2">
                          <div
                            className="bg-gradient-to-r from-pink-500 to-rose-500 h-2 rounded-full transition-all duration-300"
                            style={{ width: `${(trend.value / 15) * 100}%` }}
                          ></div>
                        </div>
                        <span className="text-sm font-bold text-pink-600 w-8">{trend.value}</span>
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        <TabsContent value="quality">
          <div className="grid gap-6">
            {/* Quality Metrics Breakdown */}
            <Card className="border-0 shadow-lg">
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <div className="p-2 bg-gradient-to-r from-indigo-500 to-blue-500 rounded-lg">
                    <BarChart3 className="h-4 w-4 text-white" />
                  </div>
                  Quality Metrics Breakdown
                </CardTitle>
                <CardDescription>Detailed analysis of data quality indicators</CardDescription>
              </CardHeader>
              <CardContent>
                {Object.entries(analysisResults || {}).map(([key, result]: [string, any]) => {
                  if (result.analysis_type !== "quality_metrics" || !result.metrics) return null

                  return (
                    <div key={key} className="space-y-4 p-4 bg-gradient-to-r from-blue-50 to-indigo-50 rounded-lg mb-4">
                      <h4 className="font-semibold text-blue-900">Connection: {result.connection_id}</h4>
                      <div className="grid gap-4 md:grid-cols-5">
                        {Object.entries(result.metrics).map(([metric, value]: [string, any]) => (
                          <div key={metric} className="text-center">
                            <div className={`text-2xl font-bold ${getQualityScoreColor(value)}`}>{value}%</div>
                            <div className="text-xs text-gray-600 capitalize">{metric}</div>
                            <Progress value={value} className="mt-2 h-2" />
                          </div>
                        ))}
                      </div>
                    </div>
                  )
                })}
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        <TabsContent value="anomalies">
          <div className="grid gap-6">
            {/* Anomaly Detection Results */}
            <Card className="border-0 shadow-lg">
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <div className="p-2 bg-gradient-to-r from-pink-500 to-rose-500 rounded-lg">
                    <Zap className="h-4 w-4 text-white" />
                  </div>
                  Anomaly Detection Results
                </CardTitle>
                <CardDescription>AI-powered anomaly detection insights</CardDescription>
              </CardHeader>
              <CardContent>
                {Object.entries(analysisResults || {}).map(([key, result]: [string, any]) => {
                  if (result.analysis_type !== "anomaly_detection") return null

                  return (
                    <div key={key} className="space-y-4 p-4 bg-gradient-to-r from-pink-50 to-rose-50 rounded-lg mb-4">
                      <div className="flex items-center justify-between">
                        <h4 className="font-semibold text-pink-900">
                          {result.model_type} Detection - {result.connection_id}
                        </h4>
                        <Badge className="bg-gradient-to-r from-pink-500 to-rose-500 text-white">
                          {result.anomalies_detected} anomalies
                        </Badge>
                      </div>

                      <div className="grid gap-4 md:grid-cols-3">
                        <div className="text-center">
                          <div className="text-2xl font-bold text-pink-600">{result.anomalies_detected}</div>
                          <div className="text-xs text-gray-600">Anomalies Found</div>
                        </div>
                        <div className="text-center">
                          <div className="text-2xl font-bold text-pink-600">{result.total_records}</div>
                          <div className="text-xs text-gray-600">Total Records</div>
                        </div>
                        <div className="text-center">
                          <div className="text-2xl font-bold text-pink-600">
                            {((result.anomalies_detected / result.total_records) * 100).toFixed(1)}%
                          </div>
                          <div className="text-xs text-gray-600">Anomaly Rate</div>
                        </div>
                      </div>

                      {result.anomaly_details && result.anomaly_details.length > 0 && (
                        <div className="mt-4">
                          <h5 className="font-medium text-pink-800 mb-2">Recent Anomalies:</h5>
                          <div className="space-y-2">
                            {result.anomaly_details.slice(0, 3).map((anomaly: any, index: number) => (
                              <div
                                key={index}
                                className="flex items-center justify-between p-2 bg-white rounded border border-pink-200"
                              >
                                <span className="text-sm text-gray-700">
                                  Index {anomaly.index}: Score {anomaly.anomaly_score.toFixed(2)}
                                </span>
                                <Badge variant="outline" className="border-pink-300 text-pink-700">
                                  {anomaly.components_affected.join(", ")}
                                </Badge>
                              </div>
                            ))}
                          </div>
                        </div>
                      )}
                    </div>
                  )
                })}
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        <TabsContent value="connections">
          <div className="grid gap-6">
            {/* Connection Health Status */}
            <Card className="border-0 shadow-lg">
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <div className="p-2 bg-gradient-to-r from-green-500 to-emerald-500 rounded-lg">
                    <Database className="h-4 w-4 text-white" />
                  </div>
                  Connection Health Status
                </CardTitle>
                <CardDescription>Monitor the health and status of all data connections</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {dashboardData.connectionHealth.map((connection) => (
                    <div
                      key={connection.id}
                      className="flex items-center justify-between p-4 border border-gray-200 rounded-xl bg-gradient-to-r from-white to-gray-50"
                    >
                      <div className="flex items-center gap-4">
                        <div className="p-2 bg-gradient-to-r from-blue-500 to-cyan-500 rounded-lg">
                          <Database className="h-4 w-4 text-white" />
                        </div>
                        <div>
                          <h4 className="font-semibold text-gray-800">{connection.name}</h4>
                          <div className="flex items-center gap-2 mt-1">
                            <Calendar className="h-3 w-3 text-gray-400" />
                            <span className="text-xs text-gray-500">
                              Last updated: {new Date(connection.lastUpdated).toLocaleString()}
                            </span>
                          </div>
                        </div>
                      </div>
                      <div className="flex items-center gap-3">
                        <Badge className={getHealthColor(connection.health)}>
                          {connection.health === "healthy" ? (
                            <CheckCircle className="h-3 w-3 mr-1" />
                          ) : (
                            <AlertTriangle className="h-3 w-3 mr-1" />
                          )}
                          {connection.health}
                        </Badge>
                        <Button size="sm" variant="outline" className="border-gray-200 bg-transparent">
                          <Eye className="h-3 w-3 mr-1" />
                          View
                        </Button>
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>
      </Tabs>
    </div>
  )
}
