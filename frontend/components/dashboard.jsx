"use client"

import { useState } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { BarChart3, Activity, Database, TrendingUp, Bell, Download, RefreshCw } from "lucide-react"
import { BackendStatus } from "./backend-status"

export function Dashboard({ connections = [], analysisResults = {}, onDataConnected }) {
  const [dashboardStats] = useState({
    totalAnalyses: Object.keys(analysisResults).length,
    activeConnections: connections.filter((conn) => conn.status === "connected").length,
    recentAlerts: 3,
    systemHealth: "healthy",
  })

  const getHealthColor = (health) => {
    switch (health) {
      case "healthy":
        return "bg-green-100 text-green-800"
      case "warning":
        return "bg-yellow-100 text-yellow-800"
      case "error":
        return "bg-red-100 text-red-800"
      default:
        return "bg-gray-100 text-gray-800"
    }
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 via-blue-50 to-purple-50 p-6">
      <div className="max-w-7xl mx-auto space-y-8">
        {/* Dashboard Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-4xl font-bold bg-gradient-to-r from-blue-600 via-purple-600 to-cyan-600 bg-clip-text text-transparent">
              Interactive Dashboard
            </h1>
            <p className="text-gray-600 mt-2">
              Comprehensive analytics, real-time monitoring, and Power BI integration
            </p>
          </div>
          <div className="flex items-center gap-4">
            <BackendStatus />
            <Badge className={getHealthColor(dashboardStats.systemHealth)}>System {dashboardStats.systemHealth}</Badge>
            <Button variant="outline" className="border-blue-200 hover:bg-blue-50 bg-transparent">
              <Download className="mr-2 h-4 w-4" />
              Export All
            </Button>
            <Button className="bg-gradient-to-r from-blue-500 to-purple-500 hover:from-blue-600 hover:to-purple-600 text-white">
              <RefreshCw className="mr-2 h-4 w-4" />
              Refresh All
            </Button>
          </div>
        </div>

        {/* Quick Stats */}
        <div className="grid gap-6 md:grid-cols-4">
          <Card className="border-0 shadow-lg hover:shadow-xl transition-all duration-300">
            <div className="h-2 bg-gradient-to-r from-blue-500 to-cyan-500 rounded-t-lg"></div>
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-600">Total Analyses</p>
                  <p className="text-3xl font-bold text-blue-600">{dashboardStats.totalAnalyses}</p>
                </div>
                <BarChart3 className="h-8 w-8 text-blue-500" />
              </div>
            </CardContent>
          </Card>

          <Card className="border-0 shadow-lg hover:shadow-xl transition-all duration-300">
            <div className="h-2 bg-gradient-to-r from-green-500 to-emerald-500 rounded-t-lg"></div>
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-600">Active Connections</p>
                  <p className="text-3xl font-bold text-green-600">{dashboardStats.activeConnections}</p>
                </div>
                <Database className="h-8 w-8 text-green-500" />
              </div>
            </CardContent>
          </Card>

          <Card className="border-0 shadow-lg hover:shadow-xl transition-all duration-300">
            <div className="h-2 bg-gradient-to-r from-yellow-500 to-orange-500 rounded-t-lg"></div>
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-600">Recent Alerts</p>
                  <p className="text-3xl font-bold text-yellow-600">{dashboardStats.recentAlerts}</p>
                </div>
                <Bell className="h-8 w-8 text-yellow-500" />
              </div>
            </CardContent>
          </Card>

          <Card className="border-0 shadow-lg hover:shadow-xl transition-all duration-300">
            <div className="h-2 bg-gradient-to-r from-purple-500 to-pink-500 rounded-t-lg"></div>
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-600">System Health</p>
                  <p className="text-lg font-bold text-purple-600 capitalize">{dashboardStats.systemHealth}</p>
                </div>
                <Activity className="h-8 w-8 text-purple-500" />
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Main Dashboard Content */}
        <div className="grid gap-8 lg:grid-cols-2">
          {/* Analytics Overview */}
          <Card className="border-0 shadow-lg">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <div className="p-2 bg-gradient-to-r from-blue-500 to-purple-500 rounded-lg">
                  <BarChart3 className="h-5 w-5 text-white" />
                </div>
                Analytics Overview
              </CardTitle>
              <CardDescription>Key metrics and performance indicators</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <div className="flex items-center justify-between p-4 bg-gradient-to-r from-blue-50 to-purple-50 rounded-lg">
                  <div>
                    <p className="font-semibold text-blue-900">Data Quality Score</p>
                    <p className="text-sm text-blue-700">Average across all connections</p>
                  </div>
                  <div className="text-2xl font-bold text-blue-600">87%</div>
                </div>

                <div className="flex items-center justify-between p-4 bg-gradient-to-r from-green-50 to-emerald-50 rounded-lg">
                  <div>
                    <p className="font-semibold text-green-900">Anomalies Detected</p>
                    <p className="text-sm text-green-700">Last 24 hours</p>
                  </div>
                  <div className="text-2xl font-bold text-green-600">12</div>
                </div>

                <div className="flex items-center justify-between p-4 bg-gradient-to-r from-yellow-50 to-orange-50 rounded-lg">
                  <div>
                    <p className="font-semibold text-yellow-900">Processing Rate</p>
                    <p className="text-sm text-yellow-700">Records per second</p>
                  </div>
                  <div className="text-2xl font-bold text-yellow-600">1.2K</div>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Real-time Activity */}
          <Card className="border-0 shadow-lg">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <div className="p-2 bg-gradient-to-r from-green-500 to-emerald-500 rounded-lg">
                  <Activity className="h-5 w-5 text-white" />
                </div>
                Real-time Activity
              </CardTitle>
              <CardDescription>Live system events and processing status</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                <div className="flex items-start gap-3 p-3 bg-green-50 rounded-lg border border-green-200">
                  <div className="w-2 h-2 bg-green-500 rounded-full mt-2"></div>
                  <div>
                    <p className="text-sm font-medium text-green-900">Quality analysis completed</p>
                    <p className="text-xs text-green-700">2 minutes ago</p>
                  </div>
                </div>

                <div className="flex items-start gap-3 p-3 bg-blue-50 rounded-lg border border-blue-200">
                  <div className="w-2 h-2 bg-blue-500 rounded-full mt-2"></div>
                  <div>
                    <p className="text-sm font-medium text-blue-900">New data connection established</p>
                    <p className="text-xs text-blue-700">5 minutes ago</p>
                  </div>
                </div>

                <div className="flex items-start gap-3 p-3 bg-yellow-50 rounded-lg border border-yellow-200">
                  <div className="w-2 h-2 bg-yellow-500 rounded-full mt-2"></div>
                  <div>
                    <p className="text-sm font-medium text-yellow-900">Anomaly detected in dataset</p>
                    <p className="text-xs text-yellow-700">8 minutes ago</p>
                  </div>
                </div>

                <div className="flex items-start gap-3 p-3 bg-purple-50 rounded-lg border border-purple-200">
                  <div className="w-2 h-2 bg-purple-500 rounded-full mt-2"></div>
                  <div>
                    <p className="text-sm font-medium text-purple-900">VARIMA model updated</p>
                    <p className="text-xs text-purple-700">12 minutes ago</p>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Welcome Message */}
        <Card className="border-0 shadow-lg bg-gradient-to-r from-violet-50 to-purple-50">
          <CardContent className="p-8 text-center">
            <h2 className="text-2xl font-bold text-violet-900 mb-4">Welcome to Your Interactive Dashboard!</h2>
            <p className="text-violet-700 mb-6">
              This is your central hub for data quality management, analytics, and real-time monitoring. Connect data
              sources, run analyses, and monitor your data pipeline all in one place.
            </p>
            <div className="flex justify-center gap-4">
              <Button className="bg-gradient-to-r from-violet-500 to-purple-500 hover:from-violet-600 hover:to-purple-600 text-white">
                <Database className="mr-2 h-4 w-4" />
                Connect Data Source
              </Button>
              <Button variant="outline" className="border-violet-200 hover:bg-violet-50 bg-transparent">
                <TrendingUp className="mr-2 h-4 w-4" />
                View Analytics
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
