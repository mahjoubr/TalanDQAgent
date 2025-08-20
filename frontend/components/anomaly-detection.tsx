"use client"

import { useState, useEffect } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Slider } from "@/components/ui/slider"
import { AlertTriangle, Edit, Play, Activity, Zap, Loader2, Database, Save, X, Check } from "lucide-react"
import { useToast } from "@/hooks/use-toast"
import { apiClient } from "@/lib/api"

interface AnomalyDetectionProps {
  data: any
  qualityMetrics: any
  setIsLoading?: (loading: boolean) => void
  connections?: any[]
  onDataConnected?: (data: any) => void
  onMetricsCalculated?: (metrics: any) => void
}

export function AnomalyDetection({ 
  data, 
  qualityMetrics, 
  setIsLoading,
  connections = [],
  onDataConnected,
  onMetricsCalculated 
}: AnomalyDetectionProps) {
  console.log('AnomalyDetection received data:', data)
  console.log('AnomalyDetection received connections:', connections)
  const [selectedModel, setSelectedModel] = useState("VARIMA") // Auto-select VARIMA model
  const [isRunning, setIsRunning] = useState(false)
  const [hasRunAnalysis, setHasRunAnalysis] = useState(false)
  const [isLoadingResults, setIsLoadingResults] = useState(false)
  const [analyzedTables, setAnalyzedTables] = useState<string[]>([])
  const [tableResults, setTableResults] = useState<Record<string, any>>({})
  const [selectedTableForView, setSelectedTableForView] = useState<string>("")
  const [varimaThreshold, setVarimaThreshold] = useState([2.0])
  const [anomalies, setAnomalies] = useState<any[]>([]) // Remove mock data
  const [varimaResults, setVarimaResults] = useState<any>(null)
  const [combinedResults, setCombinedResults] = useState<any>(null)
  const [editingAnomaly, setEditingAnomaly] = useState<number | null>(null)
  const [editingAnomalyData, setEditingAnomalyData] = useState<Record<string, any>>({})
  const [savingEdit, setSavingEdit] = useState(false)
  const { toast } = useToast()

  const models = [
    {
      name: "VARIMA",
      description: "Vector AutoRegressive Integrated Moving Average for multivariate time series",
      bestFor: "Multivariate time series, financial data with interdependencies",
      icon: Activity,
      gradient: "from-pink-500 to-rose-500",
      cleaningStrategy: "Advanced interpolation + PCA + stationarity testing for complex patterns",
    },
  ]

  // Get the active connection (prioritize the direct data prop, then latest connection)
  const getActiveConnection = () => {
    // If data prop has an ID, use it
    if (data?.id) {
      console.log('Using data prop connection:', data.id)
      return data
    }
    
    // Otherwise, use the latest connection from connections array
    if (connections && connections.length > 0) {
      const latest = connections[connections.length - 1]
      console.log('Using latest connection from array:', latest.id)
      return latest
    }
    
    console.log('No active connection found')
    return null
  }

  const activeConnection = getActiveConnection()

  // Auto-load cached results when connection becomes available - CONSERVATIVE APPROACH
  useEffect(() => {
    const connection = getActiveConnection()
    
    // Only load if we have a connection, aren't already loading/running, and don't have results yet
    if (connection?.id && !isRunning && !isLoadingResults && !hasRunAnalysis) {
      console.log('Connection available, loading cached VARIMA results:', connection.id)
      loadCachedVarimaResults(connection.id)
    }
  }, [data?.id]) // Only depend on data.id to avoid constant re-triggering

  // Load cached VARIMA analysis results from Redis
  const loadCachedVarimaResults = async (connectionId: string) => {
    setIsLoadingResults(true)
    try {
      const response = await apiClient.getCachedVarimaResults(connectionId)
      
      if (response.success && response.data) {
        const { combined_results, table_results, analyzed_tables } = response.data
        
        // Set combined results
        if (combined_results) {
          setCombinedResults(combined_results)
          setHasRunAnalysis(true)
          
          // Notify parent component
          onMetricsCalculated?.({
            anomaly_rate: combined_results.anomaly_rate,
            risk_level: combined_results.risk_level,
            total_anomalies: combined_results.total_anomalies,
            total_records: combined_results.total_records,
            connection_id: connectionId,
            analyzed_tables: analyzed_tables,
            tables_count: combined_results.tables_analyzed,
            // Add the full analysis data for report generation
            combined_results: combined_results,
            table_results: table_results
          })
        }
        
        // Set table-specific results
        setTableResults(table_results || {})
        setAnalyzedTables(analyzed_tables || [])
        
        console.log('Cached VARIMA results loaded:', {
          tables: analyzed_tables?.length || 0,
          anomalies: combined_results?.total_anomalies || 0
        })
        
      } else {
        // No cached results found - show ready state
        console.log('No cached VARIMA results found for connection:', connectionId)
        setHasRunAnalysis(false)
        setCombinedResults(null)
        setTableResults({})
        setAnalyzedTables([])
      }
    } catch (error) {
      console.error('Failed to load cached VARIMA results:', error)
      // Show ready state if no cache available
      setHasRunAnalysis(false)
    } finally {
      setIsLoadingResults(false)
    }
  }

  // REMOVED: Auto-run anomaly detection - now user must click button manually

  // Reset analysis state when connection changes - CONSERVATIVE APPROACH
  useEffect(() => {
    const connection = getActiveConnection()
    const currentConnectionId = connection?.id
    
    // Only reset if connection ID actually changes (not just props update)
    if (currentConnectionId && data?.id && currentConnectionId !== data?.id) {
      console.log('Connection changed, resetting VARIMA analysis state:', currentConnectionId)
      setHasRunAnalysis(false)
      setAnomalies([])
      setVarimaResults(null)
      setCombinedResults(null)
      setTableResults({})
      setAnalyzedTables([])
    }
  }, [data?.id]) // Only depend on data.id to avoid excessive re-runs

  const runAutoVarimaAnalysis = async () => {
    const connection = getActiveConnection()
    
    if (!connection?.id) {
      console.log('No connection available for VARIMA analysis')
      toast({
        title: "No Data Connection",
        description: "Please connect to a data source first",
        variant: "destructive",
      })
      return
    }

    console.log('Starting VARIMA analysis for connection:', connection.id)
    setIsRunning(true)
    setIsLoading?.(true)

    try {
      // Show starting notification
      toast({
        title: "Starting VARIMA Analysis",
        description: "Analyzing all tables for anomalies and caching results...",
      })

      console.log('Running auto VARIMA analysis for connection:', connection.id)
      
      const response = await apiClient.runAutoVarimaAllTables(connection.id)
      console.log('VARIMA API response:', response)

      if (response.success && response.data) {
        const analysisData = response.data
        
        console.log('Auto VARIMA analysis results:', analysisData)
        
        setCombinedResults(analysisData.combined_results)
        setTableResults(analysisData.table_results || {})
        setAnalyzedTables(analysisData.analyzed_tables || [])
        setHasRunAnalysis(true)
        
        // Notify parent component with the results
        onMetricsCalculated?.({
          anomaly_rate: analysisData.combined_results.anomaly_rate,
          risk_level: analysisData.combined_results.risk_level,
          total_anomalies: analysisData.combined_results.total_anomalies,
          total_records: analysisData.combined_results.total_records,
          connection_id: connection.id,
          analyzed_tables: analysisData.analyzed_tables,
          tables_count: analysisData.combined_results.tables_analyzed,
          // Add the full analysis data for report generation
          combined_results: analysisData.combined_results,
          table_results: analysisData.table_results
        })

        // Load the detailed cached results
        await loadCachedVarimaResults(connection.id)

        toast({
          title: "VARIMA Analysis Complete!",
          description: `Successfully analyzed ${analysisData.combined_results.tables_analyzed} tables. Found ${analysisData.combined_results.total_anomalies} anomalies in ${analysisData.combined_results.total_records} records.`,
        })

      } else {
        console.error('VARIMA API response not successful:', response)
        throw new Error(response.error || "API response was not successful")
      }
    } catch (error) {
      console.error("Auto VARIMA analysis failed:", error)
      
      toast({
        title: "VARIMA Analysis Failed",
        description: error instanceof Error ? error.message : "Unable to analyze data. Please check your connection and try again.",
        variant: "destructive",
      })
    } finally {
      setIsRunning(false)
      setIsLoading?.(false)
    }
  }

  const runAnomalyDetection = async (connectionData?: any) => {
    const connection = connectionData || getActiveConnection()
    
    if (!selectedModel) {
      toast({
        title: "Model Selection Required",
        description: "Please select an anomaly detection model first",
        variant: "destructive",
      })
      return
    }

    if (!connection?.id) {
      toast({
        title: "No Data Connection",
        description: "Please connect to a data source first",
        variant: "destructive",
      })
      return
    }

    setIsRunning(true)
    setIsLoading?.(true)

    if (selectedModel === "VARIMA") {
      await runVarimaDetection(connection)
    }
  }

  const runVarimaDetection = async (connectionData?: any) => {
    const connection = connectionData || getActiveConnection()
    
    if (!connection?.id) {
      toast({
        title: "No Data Connection",
        description: "Please connect to a data source first",
        variant: "destructive",
      })
      return
    }

    try {
      // Use all available tables automatically
      const selectedTables = connection.details?.tables || []
      console.log('Running anomaly detection on all tables:', selectedTables)
      
      const response = await apiClient.runAnomalyDetection(
        connection.id, 
        "VARIMA", 
        varimaThreshold[0], 
        5,
        selectedTables
      )

      if (response.success && response.data) {
        setVarimaResults(response.data)

        // Convert API response to frontend format
        const varimaAnomalies = response.data.anomaly_details.map((detail: any, index: number) => ({
          id: Date.now() + index,
          model: "VARIMA",
          field: "multivariate_pattern",
          value: `Pattern ${detail.index}`,
          score: detail.anomaly_score,
          severity: detail.anomaly_score > 3 ? "high" : detail.anomaly_score > 2 ? "medium" : "low",
          description: `Multivariate anomaly detected in components: ${detail.components_affected.join(", ")}`,
          confidence: Math.min(95, Math.round(detail.anomaly_score * 30)),
        }))

        // Update anomalies list
        setAnomalies((prev) => [...prev.filter((a) => a.model !== "VARIMA"), ...varimaAnomalies])

        // Mark analysis as completed
        setHasRunAnalysis(true)

        // Notify parent component if callback is provided
        if (onMetricsCalculated) {
          onMetricsCalculated({
            anomalies: varimaAnomalies,
            results: response.data,
            model: "VARIMA",
            threshold: varimaThreshold[0]
          })
        }

        toast({
          title: "VARIMA Detection Complete",
          description: `Detected ${response.data.anomalies_detected} anomalies in ${response.data.total_records} records`,
        })
      } else {
        // Handle API failure
        toast({
          title: "VARIMA Detection Failed",
          description: response.error || "Failed to run VARIMA anomaly detection",
          variant: "destructive",
        })
      }
    } catch (error) {
      toast({
        title: "Detection Failed",
        description: `Failed to run VARIMA detection: ${String(error)}`,
        variant: "destructive",
      })
    } finally {
      setIsRunning(false)
      setIsLoading?.(false)
    }
  }

  const handleEditAnomaly = (id: number, newValue: string) => {
    setAnomalies((prev) => prev.map((anomaly) => (anomaly.id === id ? { ...anomaly, value: newValue } : anomaly)))
    setEditingAnomaly(null)
    toast({
      title: "Anomaly Corrected",
      description: "Data point has been updated and will be reflected in future analyses",
    })
  }

  const startEditingAnomalyRow = async (tableName: string, rowIndex: number) => {
    const connection = getActiveConnection()
    if (!connection?.id) return

    try {
      // Get the actual row data for editing (pass table name for database connections)
      const response = await apiClient.getConnectionSample(connection.id, 1000, tableName)
      if (response.success && response.data?.sample_data) {
        const rowData = response.data.sample_data[rowIndex]
        if (rowData) {
          setEditingAnomalyData(rowData)
          setEditingAnomaly(rowIndex)
        }
      }
    } catch (error) {
      console.error('Failed to fetch row data:', error)
      toast({
        title: "Error",
        description: "Failed to load row data for editing",
        variant: "destructive",
      })
    }
  }

  const saveAnomalyEdit = async (tableName: string, rowIndex: number, updatedData: Record<string, any>) => {
    const connection = getActiveConnection()
    if (!connection?.id) return

    setSavingEdit(true)
    try {
      // Make API call to update the actual data in the file
      const response = await apiClient.updateRowData(connection.id, rowIndex, updatedData)
      
      if (response.success) {
        setEditingAnomaly(null)
        setEditingAnomalyData({})
        
        toast({
          title: "Row Updated Successfully",
          description: `Row ${rowIndex} has been updated in the dataset. The cached analysis has been cleared - re-run analysis to see updated results.`,
        })
      } else {
        throw new Error(response.error || "Update failed")
      }
    } catch (error) {
      console.error('Failed to save row edit:', error)
      toast({
        title: "Update Failed", 
        description: `Failed to update row data: ${error instanceof Error ? error.message : 'Unknown error'}`,
        variant: "destructive",
      })
    } finally {
      setSavingEdit(false)
    }
  }

  const cancelAnomalyEdit = () => {
    setEditingAnomaly(null)
    setEditingAnomalyData({})
  }

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case "high":
        return "bg-gradient-to-r from-red-500 to-pink-500 text-white"
      case "medium":
        return "bg-gradient-to-r from-yellow-500 to-orange-500 text-white"
      case "low":
        return "bg-gradient-to-r from-green-500 to-emerald-500 text-white"
      default:
        return "bg-gray-100 text-gray-800"
    }
  }

  // Check if we have any VARIMA analysis results to display
  const hasVarimaResults = hasRunAnalysis && (combinedResults || analyzedTables.length > 0)

  return (
    <div className="space-y-8">
      {/* Connection Status */}
      {activeConnection && (
        <Card className="border-0 shadow-lg bg-gradient-to-r from-green-50 to-emerald-50">
          <CardContent className="pt-6">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-gradient-to-r from-green-500 to-emerald-500 rounded-lg">
                <Database className="h-5 w-5 text-white" />
              </div>
              <div className="flex-1">
                <div className="flex items-center gap-2">
                  <h3 className="font-semibold text-green-800">
                    {activeConnection.type === 'database' ? 'Database' : 'File'} Connected
                  </h3>
                  <Badge className="bg-green-100 text-green-700 border-green-200">
                    {activeConnection.id}
                  </Badge>
                </div>
                <p className="text-sm text-green-600 mt-1">
                  {activeConnection.type === 'database' ? 
                    `${activeConnection.database_type || 'Database'} connection established` :
                    `${activeConnection.file_type || 'File'} ready for analysis`
                  }
                </p>
                {activeConnection.details?.tables && activeConnection.details.tables.length > 0 && (
                  <div className="mt-2">
                    <div className="text-xs text-green-600 mb-1">
                      Available tables ({activeConnection.details.tables.length}):
                    </div>
                    <div className="flex flex-wrap gap-1">
                      {activeConnection.details.tables.map((table: string) => (
                        <Badge 
                          key={table} 
                          variant="outline" 
                          className="text-xs border-green-300 text-green-700"
                        >
                          {table}
                        </Badge>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-4xl font-bold bg-gradient-to-r from-violet-600 to-pink-600 bg-clip-text text-transparent">
            VARIMA Anomaly Detection
          </h2>
          <p className="text-gray-600 mt-2">
            Advanced multivariate time series anomaly detection with Redis caching
          </p>
          {activeConnection && (
            <p className="text-sm text-blue-600 mt-1">
              Connected to: {activeConnection.db_type ? `${activeConnection.db_type?.toUpperCase()} Database` : activeConnection.fileName || 'Database'}
              {analyzedTables.length > 0 && ` • ${analyzedTables.length} tables analyzed`}
            </p>
          )}
        </div>
        <div className="flex gap-3">
          <Button
            onClick={() => runAutoVarimaAnalysis()}
            disabled={isRunning || !activeConnection}
            className="bg-gradient-to-r from-violet-500 to-pink-500 hover:from-violet-600 hover:to-pink-600 text-white shadow-lg"
          >
            {isRunning ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                Analyzing All Tables...
              </>
            ) : hasVarimaResults ? (
              <>
                <Play className="mr-2 h-4 w-4" />
                Re-run VARIMA Analysis
              </>
            ) : (
              <>
                <Play className="mr-2 h-4 w-4" />
                Analyze All Tables
              </>
            )}
          </Button>
        </div>
      </div>

      {/* Progress Indicator */}
      {isRunning && (
        <Card className="border-0 shadow-lg bg-gradient-to-r from-violet-50 to-pink-50">
          <CardContent className="p-6">
            <div className="space-y-4">
              <div className="flex items-center gap-4">
                <Loader2 className="h-6 w-6 text-violet-500 animate-spin" />
                <div className="flex-1">
                  <p className="font-semibold text-violet-800">
                    Running VARIMA anomaly detection on all tables...
                  </p>
                  <p className="text-sm text-violet-600">
                    Processing all available tables in the database
                  </p>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* VARIMA Results Summary */}
      {combinedResults && (
        <Card className="border-0 shadow-lg bg-gradient-to-r from-purple-50 to-violet-50">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-xl">
              <div className="p-2 bg-gradient-to-r from-purple-500 to-violet-500 rounded-lg">
                <Activity className="h-5 w-5 text-white" />
              </div>
              VARIMA Analysis Results
            </CardTitle>
            <CardDescription>
              Anomaly detection summary across all analyzed tables
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid gap-4 md:grid-cols-4">
              <div className="bg-white rounded-lg border border-purple-200 p-4 text-center">
                <div className="text-2xl font-bold text-purple-700">
                  {typeof combinedResults.anomaly_rate === 'number' ? combinedResults.anomaly_rate.toFixed(2) : combinedResults.anomaly_rate}%
                </div>
                <div className="text-sm text-purple-600">Anomaly Rate</div>
              </div>
              <div className="bg-white rounded-lg border border-purple-200 p-4 text-center">
                <div className="text-2xl font-bold text-violet-700">
                  {combinedResults.total_anomalies}
                </div>
                <div className="text-sm text-violet-600">Total Anomalies</div>
              </div>
              <div className="bg-white rounded-lg border border-purple-200 p-4 text-center">
                <div className="text-2xl font-bold text-pink-700">
                  {combinedResults.tables_analyzed}
                </div>
                <div className="text-sm text-pink-600">Tables Analyzed</div>
              </div>
              <div className="bg-white rounded-lg border border-purple-200 p-4 text-center">
                <div className={`text-2xl font-bold ${
                  combinedResults.risk_level === 'High' ? 'text-red-600' :
                  combinedResults.risk_level === 'Medium' ? 'text-yellow-600' : 'text-green-600'
                }`}>
                  {combinedResults.risk_level}
                </div>
                <div className="text-sm text-gray-600">Risk Level</div>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Table-specific VARIMA Results */}
      {activeConnection && analyzedTables.length > 0 && (
        <Card className="border-0 shadow-lg">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-xl">
              <div className="p-2 bg-gradient-to-r from-indigo-500 to-purple-500 rounded-lg">
                <Database className="h-5 w-5 text-white" />
              </div>
              Analyzed Tables ({analyzedTables.length})
            </CardTitle>
            <CardDescription>
              VARIMA anomaly detection results by table • Click to view detailed results
            </CardDescription>
          </CardHeader>
          <CardContent>
            {isLoadingResults ? (
              <div className="text-center py-8">
                <div className="w-8 h-8 border-2 border-purple-500 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
                <p className="text-gray-500">Loading cached VARIMA results...</p>
              </div>
            ) : (
              <div className="space-y-4">
                {analyzedTables.map((tableName) => {
                  const tableResult = tableResults[tableName]
                  return (
                    <Card 
                      key={tableName} 
                      className="border border-purple-300 bg-gradient-to-r from-purple-50 to-violet-50 cursor-pointer hover:shadow-md transition-all"
                      onClick={() => setSelectedTableForView(selectedTableForView === tableName ? "" : tableName)}
                    >
                      <CardHeader className="pb-3">
                        <div className="flex items-center justify-between">
                          <div className="flex items-center gap-3">
                            <div className="p-2 bg-gradient-to-r from-purple-500 to-violet-500 rounded-lg">
                              <Database className="h-4 w-4 text-white" />
                            </div>
                            <div>
                              <CardTitle className="text-lg text-purple-800">
                                {tableName}
                                <Badge className="ml-2 bg-purple-100 text-purple-700 text-xs">
                                  ✓ VARIMA Analyzed
                                </Badge>
                              </CardTitle>
                              {tableResult && (
                                <p className="text-sm text-purple-600 mt-1">
                                  {tableResult.total_observations?.toLocaleString() || 0} rows • 
                                  {tableResult.numeric_columns || 0} numeric columns • 
                                  <span className={`ml-1 ${
                                    (tableResult.anomalies_detected || 0) > 10 ? 'text-red-600' :
                                    (tableResult.anomalies_detected || 0) > 5 ? 'text-yellow-600' : 'text-green-600'
                                  }`}>
                                    {tableResult.anomalies_detected || 0} anomalies found
                                  </span>
                                </p>
                              )}
                            </div>
                          </div>
                          <div className="flex items-center gap-2">
                            {tableResult && (
                              <Badge variant="outline" className="border-purple-300 text-purple-700 bg-white">
                                {tableResult.anomalies_detected || 0} anomalies
                              </Badge>
                            )}
                            <div className={`transform transition-transform ${selectedTableForView === tableName ? 'rotate-180' : ''}`}>
                              <div className="w-2 h-2 border-r-2 border-b-2 border-purple-600 transform rotate-45"></div>
                            </div>
                          </div>
                        </div>
                      </CardHeader>
                      
                      {/* Expanded Table Details */}
                      {selectedTableForView === tableName && tableResult && (
                        <CardContent className="pt-0" onClick={(e) => e.stopPropagation()}>
                          <div className="space-y-4">
                            <div className="bg-white rounded border border-purple-200 p-4">
                              <h4 className="font-semibold text-purple-800 mb-3">Detected Anomalies</h4>
                              {tableResult && tableResult.anomaly_indices && tableResult.anomaly_indices.length > 0 ? (
                                <div className="space-y-2 max-h-96 overflow-y-auto">
                                  {tableResult.anomaly_indices.map((index: number, i: number) => (
                                    <div key={i} className="border border-purple-200 rounded-lg bg-purple-50">
                                      {/* Anomaly Header */}
                                      <div className="flex items-center justify-between p-3">
                                        <div className="flex-1">
                                          <span className="font-medium text-purple-800">Row {index}</span>
                                          <span className="text-xs text-purple-600 ml-2">
                                            Columns: {tableResult.columns_analyzed?.join(', ') || 'Multiple columns'}
                                          </span>
                                        </div>
                                        <div className="flex items-center gap-2">
                                          <div className="text-right">
                                            <div className="text-sm font-medium text-red-600">
                                              VARIMA Anomaly
                                            </div>
                                            <Badge className="text-xs bg-red-100 text-red-700">
                                              high
                                            </Badge>
                                          </div>
                                          <Button
                                            size="sm"
                                            variant="outline"
                                            onClick={() => startEditingAnomalyRow(tableName, index)}
                                            disabled={editingAnomaly === index}
                                            className="border-purple-300 hover:bg-purple-100 text-purple-700"
                                          >
                                            <Edit className="h-4 w-4" />
                                          </Button>
                                        </div>
                                      </div>

                                      {/* Editable Row Data */}
                                      {editingAnomaly === index && editingAnomalyData && Object.keys(editingAnomalyData).length > 0 && (
                                        <div className="border-t border-purple-200 bg-white p-4">
                                          <h5 className="font-semibold text-purple-800 mb-3">Edit Row {index} Values</h5>
                                          <div className="grid gap-3 md:grid-cols-2 lg:grid-cols-3 max-h-64 overflow-y-auto">
                                            {Object.entries(editingAnomalyData).map(([column, value]) => {
                                              // Skip non-editable columns like IDs
                                              if (column.toLowerCase().includes('id') && typeof value === 'number') {
                                                return (
                                                  <div key={column} className="space-y-1">
                                                    <Label className="text-sm font-medium text-gray-600">
                                                      {column} (read-only)
                                                    </Label>
                                                    <Input
                                                      value={String(value)}
                                                      disabled
                                                      className="bg-gray-50 text-gray-500"
                                                    />
                                                  </div>
                                                )
                                              }

                                              return (
                                                <div key={column} className="space-y-1">
                                                  <Label className="text-sm font-medium text-purple-700">
                                                    {column}
                                                    {tableResult.columns_analyzed?.includes(column) && (
                                                      <Badge className="ml-1 text-xs bg-red-100 text-red-600">
                                                        anomalous
                                                      </Badge>
                                                    )}
                                                  </Label>
                                                  <Input
                                                    type={typeof value === 'number' ? 'number' : 'text'}
                                                    value={String(value)}
                                                    onChange={(e) => {
                                                      const newValue = typeof value === 'number' 
                                                        ? parseFloat(e.target.value) || 0
                                                        : e.target.value
                                                      setEditingAnomalyData(prev => ({
                                                        ...prev,
                                                        [column]: newValue
                                                      }))
                                                    }}
                                                    className={`border-purple-200 focus:border-purple-400 ${
                                                      tableResult.columns_analyzed?.includes(column) 
                                                        ? 'bg-red-50 border-red-300' 
                                                        : ''
                                                    }`}
                                                  />
                                                </div>
                                              )
                                            })}
                                          </div>
                                          
                                          {/* Edit Actions */}
                                          <div className="flex items-center gap-3 mt-4 pt-3 border-t border-purple-200">
                                            <Button
                                              onClick={() => saveAnomalyEdit(tableName, index, editingAnomalyData)}
                                              disabled={savingEdit}
                                              className="bg-gradient-to-r from-green-500 to-emerald-500 hover:from-green-600 hover:to-emerald-600 text-white"
                                            >
                                              {savingEdit ? (
                                                <>
                                                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                                                  Saving...
                                                </>
                                              ) : (
                                                <>
                                                  <Save className="mr-2 h-4 w-4" />
                                                  Save Changes
                                                </>
                                              )}
                                            </Button>
                                            <Button
                                              onClick={cancelAnomalyEdit}
                                              variant="outline"
                                              disabled={savingEdit}
                                              className="border-gray-300 hover:bg-gray-50"
                                            >
                                              Cancel
                                            </Button>
                                            <div className="text-xs text-gray-500 ml-auto">
                                              * Red highlighted fields were flagged as anomalous
                                            </div>
                                          </div>
                                        </div>
                                      )}
                                    </div>
                                  ))}
                                </div>
                              ) : (
                                <div className="text-center py-4 text-gray-500">
                                  No anomalies detected in this table
                                </div>
                              )}
                              
                              {/* VARIMA Summary */}
                              {tableResult && (
                                <div className="mt-4 pt-4 border-t border-purple-200">
                                  <div className="grid grid-cols-2 gap-4 text-sm">
                                    <div>
                                      <span className="text-purple-600">Anomaly Rate:</span>
                                      <span className="font-semibold ml-1 text-purple-800">
                                        {tableResult.anomaly_percentage?.toFixed(2) || '0.00'}%
                                      </span>
                                    </div>
                                    <div>
                                      <span className="text-purple-600">Total Records:</span>
                                      <span className="font-semibold ml-1 text-purple-800">
                                        {tableResult.total_observations?.toLocaleString() || 0}
                                      </span>
                                    </div>
                                    <div>
                                      <span className="text-purple-600">Anomalies Found:</span>
                                      <span className="font-semibold ml-1 text-purple-800">
                                        {tableResult.anomalies_detected || 0}
                                      </span>
                                    </div>
                                    <div>
                                      <span className="text-purple-600">Numeric Columns:</span>
                                      <span className="font-semibold ml-1 text-purple-800">
                                        {tableResult.numeric_columns || 0}
                                      </span>
                                    </div>
                                  </div>
                                  
                                  {/* Analyzed Columns */}
                                  {tableResult.columns_analyzed && tableResult.columns_analyzed.length > 0 && (
                                    <div className="mt-3">
                                      <span className="text-sm text-purple-600">Analyzed columns:</span>
                                      <div className="flex flex-wrap gap-1 mt-1">
                                        {tableResult.columns_analyzed.map((col: string) => (
                                          <Badge 
                                            key={col} 
                                            variant="outline" 
                                            className="text-xs border-purple-300 text-purple-700 bg-purple-50"
                                          >
                                            {col}
                                          </Badge>
                                        ))}
                                      </div>
                                    </div>
                                  )}
                                  
                                  {/* Timestamp */}
                                  {tableResult.timestamp && (
                                    <div className="mt-2 text-xs text-purple-500">
                                      Analysis completed: {new Date(tableResult.timestamp).toLocaleString()}
                                    </div>
                                  )}
                                </div>
                              )}
                            </div>
                          </div>
                        </CardContent>
                      )}
                    </Card>
                  )
                })}
              </div>
            )}
          </CardContent>
        </Card>
      )}

      <Tabs defaultValue="models" className="space-y-6">
        <TabsList className="grid w-full grid-cols-3 bg-violet-50 p-1 rounded-xl">
          <TabsTrigger value="models" className="data-[state=active]:bg-white data-[state=active]:shadow-sm">
            Model Selection
          </TabsTrigger>
          <TabsTrigger value="results" className="data-[state=active]:bg-white data-[state=active]:shadow-sm">
            Detection Results
          </TabsTrigger>
          <TabsTrigger value="cleaning" className="data-[state=active]:bg-white data-[state=active]:shadow-sm">
            Data Cleaning
          </TabsTrigger>
        </TabsList>

        <TabsContent value="models">
          <div className="grid gap-6 md:grid-cols-2">
            {models.map((model) => (
              <Card
                key={model.name}
                className={`cursor-pointer transition-all duration-300 hover:scale-105 border-0 shadow-lg ${
                  selectedModel === model.name ? "ring-2 ring-violet-400 shadow-xl" : "hover:shadow-xl"
                }`}
                onClick={() => setSelectedModel(model.name)}
              >
                <div className={`h-2 bg-gradient-to-r ${model.gradient} rounded-t-lg`}></div>
                <CardHeader>
                  <CardTitle className="flex items-center gap-3">
                    <div className={`p-2 bg-gradient-to-r ${model.gradient} rounded-lg`}>
                      <model.icon className="h-5 w-5 text-white" />
                    </div>
                    <div>
                      <span className="text-lg">{model.name}</span>
                      {selectedModel === model.name && (
                        <Badge className="ml-2 bg-gradient-to-r from-violet-500 to-purple-500 text-white">
                          Selected
                        </Badge>
                      )}
                    </div>
                  </CardTitle>
                  <CardDescription className="text-gray-600">{model.description}</CardDescription>
                </CardHeader>
                <CardContent className="space-y-3">
                  <div>
                    <p className="text-sm font-medium text-gray-700 mb-1">Best for:</p>
                    <p className="text-sm text-gray-600">{model.bestFor}</p>
                  </div>
                  <div>
                    <p className="text-sm font-medium text-gray-700 mb-1">Data Cleaning:</p>
                    <p className="text-xs text-gray-500 bg-gray-50 p-2 rounded">{model.cleaningStrategy}</p>
                  </div>
                  {model.name === "VARIMA" && selectedModel === "VARIMA" && (
                    <div className="space-y-3 pt-3 border-t">
                      <div>
                        <Label className="text-sm font-medium text-gray-700">
                          Anomaly Threshold: {varimaThreshold[0]}
                        </Label>
                        <Slider
                          value={varimaThreshold}
                          onValueChange={setVarimaThreshold}
                          max={5}
                          min={1}
                          step={0.1}
                          className="mt-2"
                        />
                        <p className="text-xs text-gray-500 mt-1">Higher values = fewer, more significant anomalies</p>
                      </div>
                    </div>
                  )}
                </CardContent>
              </Card>
            ))}
          </div>
        </TabsContent>

        <TabsContent value="results">
          <div className="space-y-6">
            {/* VARIMA Results Summary */}
            {varimaResults && (
              <Card className="border-0 shadow-lg bg-gradient-to-r from-pink-50 to-rose-50">
                <CardHeader>
                  <CardTitle className="flex items-center gap-2 text-xl">
                    <div className="p-2 bg-gradient-to-r from-pink-500 to-rose-500 rounded-lg">
                      <Activity className="h-5 w-5 text-white" />
                    </div>
                    VARIMA Detection Results
                  </CardTitle>
                  <CardDescription>Multivariate time series anomaly detection summary</CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="grid gap-4 md:grid-cols-3">
                    <div className="text-center">
                      <div className="text-2xl font-bold text-pink-600">{varimaResults.anomalies_detected}</div>
                      <div className="text-sm text-gray-600">Anomalies Detected</div>
                    </div>
                    <div className="text-center">
                      <div className="text-2xl font-bold text-pink-600">{varimaResults.total_records}</div>
                      <div className="text-sm text-gray-600">Total Records</div>
                    </div>
                    <div className="text-center">
                      <div className="text-2xl font-bold text-pink-600">
                        {((varimaResults.anomalies_detected / varimaResults.total_records) * 100).toFixed(2)}%
                      </div>
                      <div className="text-sm text-gray-600">Anomaly Rate</div>
                    </div>
                  </div>
                </CardContent>
              </Card>
            )}

            {/* Anomalies List */}
            <Card className="border-0 shadow-lg">
              <CardHeader>
                <CardTitle className="flex items-center gap-2 text-xl">
                  <div className="p-2 bg-gradient-to-r from-red-500 to-pink-500 rounded-lg">
                    <AlertTriangle className="h-5 w-5 text-white" />
                  </div>
                  Detected Anomalies
                  {combinedResults && (
                    <Badge className="bg-gradient-to-r from-red-500 to-pink-500 text-white ml-2">
                      {combinedResults.total_anomalies} found
                    </Badge>
                  )}
                </CardTitle>
                <CardDescription>
                  Review, edit, and validate anomalous data points • Click edit to modify row values
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {/* Add dynamic anomalies from VARIMA results */}
                  {combinedResults && tableResults && Object.keys(tableResults).length > 0 && (
                    <>
                      {Object.entries(tableResults).map(([tableName, tableResult]: [string, any]) => {
                        if (!tableResult.anomaly_indices || tableResult.anomaly_indices.length === 0) return null
                        
                        return tableResult.anomaly_indices.slice(0, 5).map((index: number, i: number) => {
                          const anomalyId = `${tableName}-${index}`
                          return (
                            <div
                              key={anomalyId}
                              className="border border-violet-100 rounded-xl p-6 bg-gradient-to-r from-white to-violet-50 hover:shadow-md transition-all duration-300"
                            >
                              <div className="flex items-center justify-between mb-4">
                                <div className="flex items-center gap-3">
                                  <div className="p-2 bg-gradient-to-r from-violet-500 to-purple-500 rounded-lg">
                                    <Zap className="h-4 w-4 text-white" />
                                  </div>
                                  <div className="flex items-center gap-2">
                                    <Badge variant="outline" className="border-violet-200">
                                      VARIMA
                                    </Badge>
                                    <Badge className="bg-gradient-to-r from-red-500 to-pink-500 text-white">
                                      high
                                    </Badge>
                                    <Badge variant="outline" className="border-green-200 text-green-700">
                                      95% confidence
                                    </Badge>
                                  </div>
                                </div>
                                <div className="flex items-center gap-2">
                                  <Button
                                    size="sm"
                                    variant="outline"
                                    onClick={() => startEditingAnomalyRow(tableName, index)}
                                    className="border-violet-200 hover:bg-violet-50"
                                  >
                                    <Edit className="h-4 w-4" />
                                  </Button>
                                </div>
                              </div>

                              <div className="grid gap-4 md:grid-cols-3 mb-4">
                                <div>
                                  <Label className="text-sm font-semibold text-gray-700">Table</Label>
                                  <p className="text-sm text-gray-600 mt-1">{tableName}</p>
                                </div>
                                <div>
                                  <Label className="text-sm font-semibold text-gray-700">Row Index</Label>
                                  <p className="text-sm text-gray-600 mt-1 font-mono bg-gray-100 px-2 py-1 rounded">
                                    {index}
                                  </p>
                                </div>
                                <div>
                                  <Label className="text-sm font-semibold text-gray-700">Affected Columns</Label>
                                  <p className="text-sm text-violet-600 font-bold mt-1">
                                    {tableResult.columns_analyzed?.length || 0} columns
                                  </p>
                                </div>
                              </div>

                              <div className="bg-white/50 p-3 rounded-lg">
                                <p className="text-sm text-gray-700">
                                  Multivariate anomaly detected in {tableName} at row {index}. 
                                  Affected columns: {tableResult.columns_analyzed?.join(', ') || 'Multiple columns'}
                                </p>
                              </div>

                              {/* Editing Panel for this specific anomaly */}
                              {editingAnomaly === index && editingAnomalyData && Object.keys(editingAnomalyData).length > 0 && (
                                <div className="mt-4 border-t border-violet-200 pt-4">
                                  <div className="bg-white rounded-lg border border-violet-200 p-4">
                                    <h5 className="font-semibold text-violet-800 mb-3">
                                      Edit Row {index} in {tableName}
                                    </h5>
                                    <div className="grid gap-3 md:grid-cols-2 lg:grid-cols-3 max-h-64 overflow-y-auto">
                                      {Object.entries(editingAnomalyData).slice(0, 12).map(([column, value]) => (
                                        <div key={column} className="space-y-1">
                                          <Label className="text-sm font-medium text-violet-700">
                                            {column}
                                            {tableResult.columns_analyzed?.includes(column) && (
                                              <Badge className="ml-1 text-xs bg-red-100 text-red-600">
                                                anomalous
                                              </Badge>
                                            )}
                                          </Label>
                                          <Input
                                            type={typeof value === 'number' ? 'number' : 'text'}
                                            value={String(value)}
                                            onChange={(e) => {
                                              const newValue = typeof value === 'number' 
                                                ? parseFloat(e.target.value) || 0
                                                : e.target.value
                                              setEditingAnomalyData(prev => ({
                                                ...prev,
                                                [column]: newValue
                                              }))
                                            }}
                                            className={`border-violet-200 focus:border-violet-400 ${
                                              tableResult.columns_analyzed?.includes(column) 
                                                ? 'bg-red-50 border-red-300' 
                                                : ''
                                            }`}
                                          />
                                        </div>
                                      ))}
                                    </div>
                                    
                                    <div className="flex items-center gap-3 mt-4 pt-3 border-t border-violet-200">
                                      <Button
                                        onClick={() => saveAnomalyEdit(tableName, index, editingAnomalyData)}
                                        disabled={savingEdit}
                                        className="bg-gradient-to-r from-green-500 to-emerald-500 hover:from-green-600 hover:to-emerald-600 text-white"
                                      >
                                        {savingEdit ? (
                                          <>
                                            <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                                            Saving...
                                          </>
                                        ) : (
                                          <>
                                            <Save className="mr-2 h-4 w-4" />
                                            Save Changes
                                          </>
                                        )}
                                      </Button>
                                      <Button
                                        onClick={cancelAnomalyEdit}
                                        variant="outline"
                                        disabled={savingEdit}
                                        className="border-gray-300 hover:bg-gray-50"
                                      >
                                        <X className="mr-2 h-4 w-4" />
                                        Cancel
                                      </Button>
                                    </div>
                                  </div>
                                </div>
                              )}
                            </div>
                          )
                        })
                      })}
                    </>
                  )}

                  {/* Original static anomalies */}
                  {anomalies.map((anomaly) => (
                    <div
                      key={anomaly.id}
                      className="border border-violet-100 rounded-xl p-6 bg-gradient-to-r from-white to-violet-50 hover:shadow-md transition-all duration-300"
                    >
                      <div className="flex items-center justify-between mb-4">
                        <div className="flex items-center gap-3">
                          <div className="p-2 bg-gradient-to-r from-violet-500 to-purple-500 rounded-lg">
                            <Zap className="h-4 w-4 text-white" />
                          </div>
                          <div className="flex items-center gap-2">
                            <Badge variant="outline" className="border-violet-200">
                              {anomaly.model}
                            </Badge>
                            <Badge className={getSeverityColor(anomaly.severity)}>{anomaly.severity}</Badge>
                            <Badge variant="outline" className="border-green-200 text-green-700">
                              {anomaly.confidence}% confidence
                            </Badge>
                          </div>
                        </div>
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={() => setEditingAnomaly(anomaly.id)}
                          className="border-violet-200 hover:bg-violet-50"
                        >
                          <Edit className="h-4 w-4" />
                        </Button>
                      </div>

                      <div className="grid gap-4 md:grid-cols-3 mb-4">
                        <div>
                          <Label className="text-sm font-semibold text-gray-700">Field</Label>
                          <p className="text-sm text-gray-600 mt-1">{anomaly.field}</p>
                        </div>
                        <div>
                          <Label className="text-sm font-semibold text-gray-700">Value</Label>
                          {editingAnomaly === anomaly.id ? (
                            <Input
                              type="text"
                              defaultValue={anomaly.value}
                              onBlur={(e) => handleEditAnomaly(anomaly.id, e.target.value)}
                              className="h-8 mt-1 border-violet-200 focus:border-violet-400"
                            />
                          ) : (
                            <p className="text-sm text-gray-600 mt-1 font-mono bg-gray-100 px-2 py-1 rounded">
                              {anomaly.value}
                            </p>
                          )}
                        </div>
                        <div>
                          <Label className="text-sm font-semibold text-gray-700">Anomaly Score</Label>
                          <p className="text-sm text-violet-600 font-bold mt-1">{anomaly.score}</p>
                        </div>
                      </div>

                      <div className="bg-white/50 p-3 rounded-lg">
                        <p className="text-sm text-gray-700">{anomaly.description}</p>
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        <TabsContent value="cleaning">
          <div className="grid gap-6 md:grid-cols-2">
            <Card className="border-0 shadow-lg">
              <CardHeader>
                <CardTitle className="text-xl">Data Cleaning Strategies</CardTitle>
                <CardDescription>Model-specific approaches for handling missing values and noise</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                {models.map((model) => (
                  <div
                    key={model.name}
                    className="border border-violet-100 rounded-lg p-4 bg-gradient-to-r from-white to-violet-50"
                  >
                    <div className="flex items-center gap-3 mb-2">
                      <div className={`p-1.5 bg-gradient-to-r ${model.gradient} rounded`}>
                        <model.icon className="h-4 w-4 text-white" />
                      </div>
                      <h4 className="font-semibold text-gray-800">{model.name}</h4>
                    </div>
                    <p className="text-sm text-gray-600 mb-2">{model.cleaningStrategy}</p>
                  </div>
                ))}
              </CardContent>
            </Card>

            <Card className="border-0 shadow-lg">
              <CardHeader>
                <CardTitle className="text-xl">Selection Guidelines</CardTitle>
                <CardDescription>Choose the right model for your data characteristics</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div className="bg-gradient-to-r from-blue-50 to-cyan-50 p-4 rounded-lg border border-blue-200">
                    <h4 className="font-semibold text-blue-800 mb-2">Data Type Recommendations</h4>
                    <ul className="text-sm text-blue-700 space-y-2">
                      <li className="flex items-start gap-2">
                        <span className="w-2 h-2 bg-pink-500 rounded-full mt-1.5 flex-shrink-0"></span>
                        <span>
                          <strong>Multivariate time series:</strong> Use VARIMA for interdependent variables
                        </span>
                      </li>
                    </ul>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>
      </Tabs>

      {/* No Data State */}
      {!activeConnection && (
        <Card className="border-0 shadow-lg">
          <CardContent className="text-center py-12">
            <Activity className="h-16 w-16 text-gray-300 mx-auto mb-4" />
            <h3 className="text-xl font-semibold text-gray-700 mb-2">No Data Source Connected</h3>
            <p className="text-gray-500 mb-4">Connect to a database to start VARIMA anomaly detection</p>
            <p className="text-sm text-gray-400">All tables will be analyzed with multivariate time series analysis when you click the button</p>
          </CardContent>
        </Card>
      )}

      {/* Connection Available but No Analysis State */}
      {activeConnection && !hasVarimaResults && !isRunning && !isLoadingResults && (
        <Card className="border-0 shadow-lg bg-gradient-to-r from-purple-50 to-violet-50">
          <CardContent className="text-center py-12">
            <AlertTriangle className="h-16 w-16 text-purple-500 mx-auto mb-4" />
            <h3 className="text-xl font-semibold text-purple-700 mb-2">Ready for VARIMA Analysis</h3>
            <p className="text-purple-600 mb-4">
              Connection established to {activeConnection.db_type || 'database'}. Click to run VARIMA anomaly detection on all tables.
            </p>
            <Button
              onClick={() => runAutoVarimaAnalysis()}
              className="bg-gradient-to-r from-purple-500 to-violet-500 hover:from-purple-600 hover:to-violet-600 text-white"
            >
              <Play className="mr-2 h-4 w-4" />
              Start VARIMA Analysis
            </Button>
          </CardContent>
        </Card>
      )}
    </div>
  )
}
