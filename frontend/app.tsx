"use client"

import { useState } from "react"
import { Toaster } from "@/components/ui/toaster"
import { WelcomeScreen } from "./components/welcome-screen"
import { GuidedFlow } from "./components/guided-flow"
import { LoginForm } from "./components/login-form"
import { DashboardPage } from "./components/dashboard-page"

export default function App() {
  const [currentView, setCurrentView] = useState<"welcome" | "login" | "guided" | "dashboard">("welcome")
  const [connections, setConnections] = useState<any[]>([])
  const [analysisResults, setAnalysisResults] = useState<any>({})

  const handleDataConnected = (data: any) => {
    setConnections((prev) => [...prev, data])
  }

  const handleViewChange = (view: "welcome" | "login" | "guided" | "dashboard") => {
    setCurrentView(view)
  }

  const renderCurrentView = () => {
    switch (currentView) {
      case "welcome":
        return (
          <WelcomeScreen
            onGetStarted={() => setCurrentView("login")}
            onViewDashboard={() => setCurrentView("dashboard")}
          />
        )
      case "login":
        return (
          <div className="min-h-screen bg-gradient-to-br from-violet-100 via-blue-100 to-cyan-100 flex items-center justify-center p-4">
            <div className="absolute inset-0 bg-gradient-to-br from-violet-500/10 via-blue-500/10 to-cyan-500/10"></div>
            <LoginForm onLogin={() => setCurrentView("guided")} />
          </div>
        )
      case "guided":
        return <GuidedFlow onBack={() => setCurrentView("welcome")} onViewDashboard={function (): void {
          throw new Error("Function not implemented.")
        } } />
      case "dashboard":
        return (
          <DashboardPage
            connections={connections}
            analysisResults={analysisResults}
            onDataConnected={handleDataConnected} userData={undefined}          />
        )
      default:
        return (
          <WelcomeScreen
            onGetStarted={() => setCurrentView("login")}
            onViewDashboard={() => setCurrentView("dashboard")}
          />
        )
    }
  }

  return (
    <div className="min-h-screen">
      {renderCurrentView()}
      <Toaster />
    </div>
  )
}
