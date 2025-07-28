"use client"

import { BarChart3, Activity, Home } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"

const navigationItems = [
  {
    title: "Dashboard",
    url: "dashboard",
    icon: BarChart3,
    description: "Interactive analytics dashboard",
  },
  {
    title: "Guided Flow",
    url: "guided",
    icon: Activity,
    description: "Step-by-step data analysis",
  },
  {
    title: "Welcome",
    url: "welcome",
    icon: Home,
    description: "Back to welcome screen",
  },
]

export function AppSidebar({ onNavigate, currentView }) {
  return (
    <div className="w-64 bg-white border-r border-gray-200 shadow-lg">
      <div className="p-4">
        <div className="flex items-center gap-3 mb-6">
          <div className="p-2 bg-gradient-to-r from-blue-500 to-purple-500 rounded-lg">
            <BarChart3 className="h-6 w-6 text-white" />
          </div>
          <div>
            <h2 className="text-lg font-bold bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">
              Power BI Dashboard
            </h2>
            <p className="text-xs text-gray-500">Data Quality Platform</p>
          </div>
        </div>

        <Card className="mb-6">
          <CardHeader>
            <CardTitle className="text-sm">Navigation</CardTitle>
          </CardHeader>
          <CardContent className="space-y-2">
            {navigationItems.map((item) => (
              <Button
                key={item.title}
                onClick={() => onNavigate(item.url)}
                variant={currentView === item.url ? "default" : "ghost"}
                className="w-full justify-start"
              >
                <item.icon className="h-4 w-4 mr-2" />
                <div className="flex flex-col items-start">
                  <span className="font-medium">{item.title}</span>
                  <span className="text-xs text-gray-500">{item.description}</span>
                </div>
              </Button>
            ))}
          </CardContent>
        </Card>

        <div className="text-center">
          <p className="text-xs text-gray-500">Power BI Dashboard v1.0</p>
          <p className="text-xs text-gray-400">Data Quality Platform</p>
        </div>
      </div>
    </div>
  )
}
