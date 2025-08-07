"use client"

import { useState } from "react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { ArrowLeft, Home, BarChart3, Database, Activity, Settings, TrendingUp } from "lucide-react"
import { DataConnector } from "@/components/data-connector"

interface DashboardPageProps {
  connections: any[]
    userData: any

  analysisResults: any
  onDataConnected: (data: any) => void
  onBack?: () => void
  onNavigateTo?: (view: "welcome" | "auth" | "guided" | "dashboard") => void
  canGoBack?: boolean
}

export function DashboardPage({
  connections,
  analysisResults,
  onDataConnected,
  
  onBack,
  onNavigateTo,
  canGoBack,
}: DashboardPageProps) {
  const [activeTab, setActiveTab] = useState("overview")
  const [isLoading, setIsLoading] = useState(false)

  const stats = [
    {
      title: "Active Connections",
      value: connections.length.toString(),
      icon: Database,
      color: "from-blue-500 to-cyan-500",
    },
    {
      title: "Data Quality Score",
      value: "94.2%",
      icon: BarChart3,
      color: "from-green-500 to-emerald-500",
    },
    {
      title: "Anomalies Detected",
      value: "12",
      icon: Activity,
      color: "from-red-500 to-pink-500",
    },
    {
      title: "Reports Generated",
      value: "8",
      icon: TrendingUp,
      color: "from-violet-500 to-purple-500",
    },
  ]

  const tabs = [
    { id: "overview", label: "Overview", icon: BarChart3 },
    { id: "analytics", label: "Analytics", icon: TrendingUp },
    { id: "realtime", label: "Real-time", icon: Activity },
    { id: "connections", label: "Data Sources", icon: Database },
    { id: "settings", label: "Settings", icon: Settings },
  ]

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-50">
      

      {/* Header */}
      <div className="bg-white border-b border-gray-200 shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <div className="flex items-center gap-4">
              {onBack && (
                <>
                  {canGoBack ? (
                    <Button
                      onClick={onBack}
                      variant="outline"
                      size="sm"
                      className="border-gray-300 hover:bg-gray-50 bg-transparent"
                    >
                      <ArrowLeft className="mr-2 h-4 w-4" />
                      Back
                    </Button>
                  ) : (
                    <Button
                      onClick={onBack}
                      variant="outline"
                      size="sm"
                      className="border-gray-300 hover:bg-gray-50 bg-transparent"
                    >
                      <Home className="mr-2 h-4 w-4" />
                      Home
                    </Button>
                  )}
                </>
              )}

              <div className="flex items-center gap-3">
                <div className="p-2 bg-gradient-to-r from-blue-500 to-purple-500 rounded-lg">
                  <BarChart3 className="h-5 w-5 text-white" />
                </div>
                <div>
                  <h1 className="text-lg font-bold text-gray-900">Interactive Dashboard</h1>
                  <p className="text-sm text-gray-500">Power BI Analytics & Monitoring</p>
                </div>
              </div>
            </div>

            <div className="flex items-center gap-4">
              <Badge variant="secondary" className="bg-green-100 text-green-700">
                Live Data
              </Badge>

              {onNavigateTo && (
                <Button
                  onClick={() => onNavigateTo("guided")}
                  variant="outline"
                  size="sm"
                  className="border-violet-300 text-violet-600 hover:bg-violet-50"
                >
                  <Settings className="mr-2 h-4 w-4" />
                  Setup Guide
                </Button>
              )}
            </div>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Stats Overview */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          {stats.map((stat, index) => (
            <Card key={index} className="border-0 shadow-lg hover:shadow-xl transition-shadow">
              <CardContent className="p-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium text-gray-600">{stat.title}</p>
                    <p className="text-3xl font-bold text-gray-900 mt-2">{stat.value}</p>
                  </div>
                  <div className={`p-3 rounded-xl bg-gradient-to-r ${stat.color}`}>
                    <stat.icon className="h-6 w-6 text-white" />
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>

        {/* Navigation Tabs */}
        <Card className="border-0 shadow-lg mb-8">
          <CardContent className="p-0">
            <div className="flex overflow-x-auto">
              {tabs.map((tab) => (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={`flex items-center gap-2 px-6 py-4 text-sm font-medium border-b-2 transition-colors whitespace-nowrap ${
                    activeTab === tab.id
                      ? "border-blue-500 text-blue-600 bg-blue-50"
                      : "border-transparent text-gray-500 hover:text-gray-700 hover:bg-gray-50"
                  }`}
                >
                  <tab.icon className="h-4 w-4" />
                  {tab.label}
                </button>
              ))}
            </div>
          </CardContent>
        </Card>

        {/* Tab Content */}
        <div className="space-y-6">
          {activeTab === "overview" && (
            <div className="grid gap-6">
              <Card className="border-0 shadow-lg">
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <BarChart3 className="h-5 w-5" />
                    Dashboard Overview
                  </CardTitle>
                  <CardDescription>
                    Comprehensive view of your data quality metrics and system performance
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="grid gap-6 md:grid-cols-2">
                    <div className="space-y-4">
                      <h3 className="font-semibold text-gray-900">Recent Activity</h3>
                      <div className="space-y-3">
                        <div className="flex items-center gap-3 p-3 bg-blue-50 rounded-lg">
                          <div className="w-2 h-2 bg-blue-500 rounded-full"></div>
                          <span className="text-sm text-gray-700">Data quality analysis completed</span>
                          <span className="text-xs text-gray-500 ml-auto">2 min ago</span>
                        </div>
                        <div className="flex items-center gap-3 p-3 bg-green-50 rounded-lg">
                          <div className="w-2 h-2 bg-green-500 rounded-full"></div>
                          <span className="text-sm text-gray-700">New data source connected</span>
                          <span className="text-xs text-gray-500 ml-auto">5 min ago</span>
                        </div>
                        <div className="flex items-center gap-3 p-3 bg-yellow-50 rounded-lg">
                          <div className="w-2 h-2 bg-yellow-500 rounded-full"></div>
                          <span className="text-sm text-gray-700">Anomaly detected in dataset</span>
                          <span className="text-xs text-gray-500 ml-auto">12 min ago</span>
                        </div>
                      </div>
                    </div>
                    <div className="space-y-4">
                      <h3 className="font-semibold text-gray-900">System Status</h3>
                      <div className="space-y-3">
                        <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                          <span className="text-sm text-gray-700">Data Pipeline</span>
                          <Badge className="bg-green-100 text-green-700">Healthy</Badge>
                        </div>
                        <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                          <span className="text-sm text-gray-700">API Status</span>
                          <Badge className="bg-green-100 text-green-700">Online</Badge>
                        </div>
                        <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                          <span className="text-sm text-gray-700">Last Backup</span>
                          <Badge className="bg-blue-100 text-blue-700">1 hour ago</Badge>
                        </div>
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </div>
          )}

          {activeTab === "dashboard" && (
            <div className="space-y-6">
              <Card className="border-0 shadow-lg">
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Database className="h-5 w-5" />
                    Data Source Management
                  </CardTitle>
                  <CardDescription>Connect and manage your data sources</CardDescription>
                </CardHeader>
              </Card>
              <DataConnector onDataConnected={onDataConnected} setIsLoading={setIsLoading} />
            </div>
          )}

          {activeTab === "settings" && (
            <Card className="border-0 shadow-lg">
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Settings className="h-5 w-5" />
                  Dashboard Settings
                </CardTitle>
                <CardDescription>Configure your dashboard preferences and system settings</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-6">
                  <div className="grid gap-6 md:grid-cols-2">
                    <div className="space-y-4">
                      <h3 className="font-semibold text-gray-900">Display Settings</h3>
                      <div className="space-y-3">
                        <div className="flex items-center justify-between">
                          <span className="text-sm text-gray-700">Dark Mode</span>
                          <Button variant="outline" size="sm">
                            Toggle
                          </Button>
                        </div>
                        <div className="flex items-center justify-between">
                          <span className="text-sm text-gray-700">Auto Refresh</span>
                          <Button variant="outline" size="sm">
                            Enable
                          </Button>
                        </div>
                        <div className="flex items-center justify-between">
                          <span className="text-sm text-gray-700">Notifications</span>
                          <Button variant="outline" size="sm">
                            Configure
                          </Button>
                        </div>
                      </div>
                    </div>
                    <div className="space-y-4">
                      <h3 className="font-semibold text-gray-900">Data Settings</h3>
                      <div className="space-y-3">
                        <div className="flex items-center justify-between">
                          <span className="text-sm text-gray-700">Cache Duration</span>
                          <Button variant="outline" size="sm">
                            5 minutes
                          </Button>
                        </div>
                        <div className="flex items-center justify-between">
                          <span className="text-sm text-gray-700">Export Format</span>
                          <Button variant="outline" size="sm">
                            CSV
                          </Button>
                        </div>
                        <div className="flex items-center justify-between">
                          <span className="text-sm text-gray-700">Backup Schedule</span>
                          <Button variant="outline" size="sm">
                            Daily
                          </Button>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          )}
        </div>
      </div>
    </div>
  )
}
