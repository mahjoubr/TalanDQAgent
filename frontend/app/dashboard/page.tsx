"use client"

import { useState, useEffect } from "react"
import { DashboardPage } from "@/components/dashboard-page"
import { apiClient } from "@/lib/api"
import { useToast } from "@/hooks/use-toast"

export default function Dashboard() {
  const [connections, setConnections] = useState<any[]>([])
  const [analysisResults, setAnalysisResults] = useState({})
  const [isLoading, setIsLoading] = useState(true)
  const { toast } = useToast()

  useEffect(() => {
    loadDashboardData()
  }, [])

  const loadDashboardData = async () => {
    setIsLoading(true)
    try {
      // Load connections
      const connectionsResponse = await apiClient.getConnections()
      if (connectionsResponse.success && connectionsResponse.data) {
        setConnections(connectionsResponse.data.connections)

        // Load analysis results for each connection
        const results: any = {}
        for (const connection of connectionsResponse.data.connections) {
          try {
            const analysisResponse = await apiClient.getAnalysisResults(connection.id)
            if (analysisResponse.success && analysisResponse.data) {
              results[connection.id] = analysisResponse.data
            }
          } catch (error) {
            console.log(`No analysis results for connection ${connection.id}`)
          }
        }
        setAnalysisResults(results)
      }
    } catch (error) {
      toast({
        title: "Failed to load dashboard",
        description: "Could not load dashboard data",
        variant: "destructive",
      })
    } finally {
      setIsLoading(false)
    }
  }

  const handleDataConnected = (data: any) => {
    setConnections((prev) => [...prev, data])
    toast({
      title: "New Data Connected",
      description: "Data source has been added to the dashboard",
    })
  }

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-gray-50 via-blue-50 to-purple-50 flex items-center justify-center">
        <div className="text-center">
          <div className="w-16 h-16 border-4 border-blue-500 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
          <h2 className="text-2xl font-bold text-gray-800 mb-2">Loading Dashboard</h2>
          <p className="text-gray-600">Preparing your analytics and insights...</p>
        </div>
      </div>
    )
  }

  return (
    <DashboardPage connections={connections} analysisResults={analysisResults} onDataConnected={handleDataConnected} userData={undefined} />
  )
}
