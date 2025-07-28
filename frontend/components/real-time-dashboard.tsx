"use client"

import { useState, useEffect, useRef } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Switch } from "@/components/ui/switch"
import { Label } from "@/components/ui/label"
import { Activity, Wifi, WifiOff, Pause, Play, RotateCcw, TrendingUp, AlertCircle, CheckCircle } from "lucide-react"

interface RealTimeDashboardProps {
  isConnected: boolean
  onToggleConnection: (connected: boolean) => void
}

export function RealTimeDashboard({ isConnected, onToggleConnection }: RealTimeDashboardProps) {
  const [isLive, setIsLive] = useState(false)
  const [metrics, setMetrics] = useState({
    dataPoints: 0,
    anomaliesFound: 0,
    qualityScore: 85,
    processingRate: 0,
  })
  const [activityLog, setActivityLog] = useState<
    Array<{
      id: string
      timestamp: Date
      type: "info" | "warning" | "error" | "success"
      message: string
    }>
  >([])
  const [chartData, setChartData] = useState<
    Array<{
      time: string
      quality: number
      anomalies: number
    }>
  >([])

  const intervalRef = useRef<NodeJS.Timeout | null>(null)

  useEffect(() => {
    if (isLive && isConnected) {
      startRealTimeUpdates()
    } else {
      stopRealTimeUpdates()
    }

    return () => stopRealTimeUpdates()
  }, [isLive, isConnected])

  const startRealTimeUpdates = () => {
    intervalRef.current = setInterval(() => {
      updateMetrics()
      updateChartData()
      addActivityLogEntry()
    }, 2000) // Update every 2 seconds
  }

  const stopRealTimeUpdates = () => {
    if (intervalRef.current) {
      clearInterval(intervalRef.current)
      intervalRef.current = null
    }
  }

  const updateMetrics = () => {
    setMetrics((prev) => ({
      dataPoints: prev.dataPoints + Math.floor(Math.random() * 10) + 1,
      anomaliesFound: prev.anomaliesFound + (Math.random() > 0.8 ? 1 : 0),
      qualityScore: Math.max(70, Math.min(100, prev.qualityScore + (Math.random() - 0.5) * 4)),
      processingRate: Math.floor(Math.random() * 50) + 20,
    }))
  }

  const updateChartData = () => {
    const now = new Date()
    const timeString = now.toLocaleTimeString()

    setChartData((prev) => {
      const newData = [
        ...prev,
        {
          time: timeString,
          quality: Math.floor(Math.random() * 20) + 80,
          anomalies: Math.floor(Math.random() * 5),
        },
      ]

      // Keep only last 20 data points
      return newData.slice(-20)
    })
  }

  const addActivityLogEntry = () => {
    const activities = [
      { type: "info" as const, message: "Processing new data batch" },
      { type: "success" as const, message: "Quality analysis completed" },
      { type: "warning" as const, message: "Anomaly detected in dataset" },
      { type: "info" as const, message: "VARIMA model updated" },
      { type: "success" as const, message: "Data validation passed" },
    ]

    const randomActivity = activities[Math.floor(Math.random() * activities.length)]

    setActivityLog((prev) => {
      const newEntry = {
        id: Date.now().toString(),
        timestamp: new Date(),
        ...randomActivity,
      }

      // Keep only last 10 entries
      return [newEntry, ...prev.slice(0, 9)]
    })
  }

  const resetMetrics = () => {
    setMetrics({
      dataPoints: 0,
      anomaliesFound: 0,
      qualityScore: 85,
      processingRate: 0,
    })
    setChartData([])
    setActivityLog([])
  }

  const getActivityIcon = (type: string) => {
    switch (type) {
      case "success":
        return <CheckCircle className="h-4 w-4 text-green-500" />
      case "warning":
        return <AlertCircle className="h-4 w-4 text-yellow-500" />
      case "error":
        return <AlertCircle className="h-4 w-4 text-red-500" />
      default:
        return <Activity className="h-4 w-4 text-blue-500" />
    }
  }

  const getActivityColor = (type: string) => {
    switch (type) {
      case "success":
        return "border-green-200 bg-green-50"
      case "warning":
        return "border-yellow-200 bg-yellow-50"
      case "error":
        return "border-red-200 bg-red-50"
      default:
        return "border-blue-200 bg-blue-50"
    }
  }

  return (
    <div className="space-y-6">
      {/* Real-time Controls */}
      <Card className="border-0 shadow-lg">
        <CardHeader>
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-gradient-to-r from-green-500 to-emerald-500 rounded-lg">
                <Activity className="h-5 w-5 text-white" />
              </div>
              <div>
                <CardTitle className="text-xl">Real-Time Monitoring</CardTitle>
                <CardDescription>Live data processing and analysis updates</CardDescription>
              </div>
            </div>
            <div className="flex items-center gap-4">
              <div className="flex items-center gap-2">
                {isConnected ? (
                  <Wifi className="h-4 w-4 text-green-500" />
                ) : (
                  <WifiOff className="h-4 w-4 text-red-500" />
                )}
                <Badge className={isConnected ? "bg-green-100 text-green-800" : "bg-red-100 text-red-800"}>
                  {isConnected ? "Connected" : "Disconnected"}
                </Badge>
              </div>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-6">
              <div className="flex items-center space-x-2">
                <Switch id="live-mode" checked={isLive} onCheckedChange={setIsLive} disabled={!isConnected} />
                <Label htmlFor="live-mode" className="flex items-center gap-2">
                  {isLive ? <Play className="h-4 w-4 text-green-500" /> : <Pause className="h-4 w-4 text-gray-500" />}
                  Live Updates
                </Label>
              </div>

              <div className="flex items-center space-x-2">
                <Switch id="connection" checked={isConnected} onCheckedChange={onToggleConnection} />
                <Label htmlFor="connection">Data Connection</Label>
              </div>
            </div>

            <Button
              onClick={resetMetrics}
              variant="outline"
              size="sm"
              className="border-gray-200 hover:bg-gray-50 bg-transparent"
            >
              <RotateCcw className="h-4 w-4 mr-2" />
              Reset
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Real-time Metrics */}
      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-4">
        <Card className="border-0 shadow-lg">
          <div className="h-2 bg-gradient-to-r from-blue-500 to-cyan-500 rounded-t-lg"></div>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Data Points</p>
                <p className="text-3xl font-bold text-blue-600">{metrics.dataPoints.toLocaleString()}</p>
              </div>
              <Activity className="h-8 w-8 text-blue-500" />
            </div>
            {isLive && (
              <div className="mt-2 flex items-center">
                <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse mr-2"></div>
                <span className="text-xs text-green-600">Live</span>
              </div>
            )}
          </CardContent>
        </Card>

        <Card className="border-0 shadow-lg">
          <div className="h-2 bg-gradient-to-r from-pink-500 to-rose-500 rounded-t-lg"></div>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Anomalies</p>
                <p className="text-3xl font-bold text-pink-600">{metrics.anomaliesFound}</p>
              </div>
              <AlertCircle className="h-8 w-8 text-pink-500" />
            </div>
            {isLive && (
              <div className="mt-2 flex items-center">
                <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse mr-2"></div>
                <span className="text-xs text-green-600">Monitoring</span>
              </div>
            )}
          </CardContent>
        </Card>

        <Card className="border-0 shadow-lg">
          <div className="h-2 bg-gradient-to-r from-green-500 to-emerald-500 rounded-t-lg"></div>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Quality Score</p>
                <p className="text-3xl font-bold text-green-600">{Math.round(metrics.qualityScore)}%</p>
              </div>
              <TrendingUp className="h-8 w-8 text-green-500" />
            </div>
            {isLive && (
              <div className="mt-2 flex items-center">
                <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse mr-2"></div>
                <span className="text-xs text-green-600">Updating</span>
              </div>
            )}
          </CardContent>
        </Card>

        <Card className="border-0 shadow-lg">
          <div className="h-2 bg-gradient-to-r from-violet-500 to-purple-500 rounded-t-lg"></div>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Processing Rate</p>
                <p className="text-3xl font-bold text-violet-600">{metrics.processingRate}/s</p>
              </div>
              <Activity className="h-8 w-8 text-violet-500" />
            </div>
            {isLive && (
              <div className="mt-2 flex items-center">
                <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse mr-2"></div>
                <span className="text-xs text-green-600">Active</span>
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Real-time Charts and Activity */}
      <div className="grid gap-6 lg:grid-cols-2">
        {/* Live Chart */}
        <Card className="border-0 shadow-lg">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <div className="p-2 bg-gradient-to-r from-blue-500 to-purple-500 rounded-lg">
                <TrendingUp className="h-4 w-4 text-white" />
              </div>
              Live Metrics Chart
            </CardTitle>
            <CardDescription>Real-time quality and anomaly trends</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="h-64 flex items-end justify-between gap-1 p-4 bg-gradient-to-t from-gray-50 to-white rounded-lg">
              {chartData.map((data, index) => (
                <div key={index} className="flex flex-col items-center gap-1 flex-1">
                  <div className="flex flex-col gap-1 w-full">
                    <div
                      className="bg-gradient-to-t from-blue-500 to-cyan-500 rounded-t transition-all duration-300"
                      style={{ height: `${(data.quality / 100) * 120}px` }}
                    ></div>
                    <div
                      className="bg-gradient-to-t from-pink-500 to-rose-500 rounded-t transition-all duration-300"
                      style={{ height: `${(data.anomalies / 10) * 40}px` }}
                    ></div>
                  </div>
                  <span className="text-xs text-gray-500 transform -rotate-45 origin-left">
                    {data.time.split(":").slice(0, 2).join(":")}
                  </span>
                </div>
              ))}
            </div>
            <div className="flex items-center justify-center gap-6 mt-4">
              <div className="flex items-center gap-2">
                <div className="w-3 h-3 bg-gradient-to-r from-blue-500 to-cyan-500 rounded"></div>
                <span className="text-xs text-gray-600">Quality Score</span>
              </div>
              <div className="flex items-center gap-2">
                <div className="w-3 h-3 bg-gradient-to-r from-pink-500 to-rose-500 rounded"></div>
                <span className="text-xs text-gray-600">Anomalies</span>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Activity Log */}
        <Card className="border-0 shadow-lg">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <div className="p-2 bg-gradient-to-r from-green-500 to-emerald-500 rounded-lg">
                <Activity className="h-4 w-4 text-white" />
              </div>
              Activity Log
            </CardTitle>
            <CardDescription>Real-time processing events</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-3 max-h-64 overflow-y-auto">
              {activityLog.map((entry) => (
                <div
                  key={entry.id}
                  className={`flex items-start gap-3 p-3 rounded-lg border ${getActivityColor(entry.type)}`}
                >
                  {getActivityIcon(entry.type)}
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium text-gray-900">{entry.message}</p>
                    <p className="text-xs text-gray-500">{entry.timestamp.toLocaleTimeString()}</p>
                  </div>
                </div>
              ))}
              {activityLog.length === 0 && (
                <div className="text-center py-8 text-gray-500">
                  <Activity className="h-8 w-8 mx-auto mb-2 opacity-50" />
                  <p className="text-sm">No activity yet. Enable live updates to see real-time events.</p>
                </div>
              )}
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
