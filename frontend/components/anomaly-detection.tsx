"use client"

import { useState } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Slider } from "@/components/ui/slider"
import { AlertTriangle, Download, Edit, Play, Activity, Zap, Loader2 } from "lucide-react"
import { useToast } from "@/hooks/use-toast"
import { apiClient } from "@/lib/api"

interface AnomalyDetectionProps {
  data: any
  qualityMetrics: any
  setIsLoading: (loading: boolean) => void
}

export function AnomalyDetection({ data, qualityMetrics, setIsLoading }: AnomalyDetectionProps) {
  const [selectedModel, setSelectedModel] = useState("")
  const [isRunning, setIsRunning] = useState(false)
  const [varimaThreshold, setVarimaThreshold] = useState([2.0])
  const [anomalies, setAnomalies] = useState([
    {
      id: 4,
      model: "VARIMA",
      field: "time_series_pattern",
      value: "irregular",
      score: 1.8,
      severity: "medium",
      description: "Irregular time series pattern detected in multivariate financial data",
      confidence: 82,
    },
  ])
  const [varimaResults, setVarimaResults] = useState<any>(null)
  const [editingAnomaly, setEditingAnomaly] = useState<number | null>(null)
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

  const runAnomalyDetection = async () => {
    if (!selectedModel) {
      toast({
        title: "Model Selection Required",
        description: "Please select an anomaly detection model first",
        variant: "destructive",
      })
      return
    }

    if (!data?.id) {
      toast({
        title: "No Data Connection",
        description: "Please connect to a data source first",
        variant: "destructive",
      })
      return
    }

    setIsRunning(true)
    setIsLoading(true)

    if (selectedModel === "VARIMA") {
      await runVarimaDetection()
    }
  }

  const runVarimaDetection = async () => {
    if (!data?.id) {
      toast({
        title: "No Data Connection",
        description: "Please connect to a data source first",
        variant: "destructive",
      })
      return
    }

    try {
      const response = await apiClient.runAnomalyDetection(data.id, "VARIMA", varimaThreshold[0], 5)

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

        toast({
          title: "VARIMA Detection Complete",
          description: `Detected ${response.data.anomalies_detected} anomalies in ${response.data.total_records} records`,
        })
      } else {
        // Handle API failure with mock data
        const mockResults = {
          anomalies_detected: 15,
          total_records: 10000,
          anomaly_details: [
            {
              index: 1234,
              anomaly_score: 2.8,
              components_affected: ["value1", "value2"],
            },
            {
              index: 5678,
              anomaly_score: 3.2,
              components_affected: ["value2", "value3"],
            },
          ],
        }

        setVarimaResults(mockResults)

        const mockAnomalies = mockResults.anomaly_details.map((detail: any, index: number) => ({
          id: Date.now() + index,
          model: "VARIMA",
          field: "multivariate_pattern",
          value: `Pattern ${detail.index}`,
          score: detail.anomaly_score,
          severity: detail.anomaly_score > 3 ? "high" : detail.anomaly_score > 2 ? "medium" : "low",
          description: `Multivariate anomaly detected in components: ${detail.components_affected.join(", ")}`,
          confidence: Math.min(95, Math.round(detail.anomaly_score * 30)),
        }))

        setAnomalies((prev) => [...prev.filter((a) => a.model !== "VARIMA"), ...mockAnomalies])

        toast({
          title: "Mock VARIMA Detection",
          description: "Using mock anomaly detection - backend service unavailable",
        })
      }
    } catch (error) {
      // Fallback to mock data in development
      if (process.env.NODE_ENV === "development") {
        const mockResults = {
          anomalies_detected: 15,
          total_records: 10000,
          anomaly_details: [
            {
              index: 1234,
              anomaly_score: 2.8,
              components_affected: ["value1", "value2"],
            },
            {
              index: 5678,
              anomaly_score: 3.2,
              components_affected: ["value2", "value3"],
            },
          ],
        }

        setVarimaResults(mockResults)

        const mockAnomalies = mockResults.anomaly_details.map((detail: any, index: number) => ({
          id: Date.now() + index,
          model: "VARIMA",
          field: "multivariate_pattern",
          value: `Pattern ${detail.index}`,
          score: detail.anomaly_score,
          severity: detail.anomaly_score > 3 ? "high" : detail.anomaly_score > 2 ? "medium" : "low",
          description: `Multivariate anomaly detected in components: ${detail.components_affected.join(", ")}`,
          confidence: Math.min(95, Math.round(detail.anomaly_score * 30)),
        }))

        setAnomalies((prev) => [...prev.filter((a) => a.model !== "VARIMA"), ...mockAnomalies])

        toast({
          title: "Development Mode",
          description: "Using mock VARIMA detection for development",
        })
      } else {
        toast({
          title: "Detection Failed",
          description: error instanceof Error ? error.message : "Unknown error occurred",
          variant: "destructive",
        })
      }
    } finally {
      setIsRunning(false)
      setIsLoading(false)
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

  const exportData = () => {
    const csvContent = [
      "ID,Model,Field,Value,Score,Severity,Confidence,Description",
      ...anomalies.map(
        (a) => `${a.id},${a.model},${a.field},${a.value},${a.score},${a.severity},${a.confidence}%,"${a.description}"`,
      ),
    ].join("\n")

    const blob = new Blob([csvContent], { type: "text/csv" })
    const url = window.URL.createObjectURL(blob)
    const a = document.createElement("a")
    a.href = url
    a.download = "anomaly_detection_results.csv"
    a.click()

    toast({
      title: "Export Successful",
      description: "Anomaly detection results exported to CSV file",
    })
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

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-4xl font-bold bg-gradient-to-r from-violet-600 to-pink-600 bg-clip-text text-transparent">
            AI Anomaly Detection
          </h2>
          <p className="text-gray-600 mt-2">Advanced ML models for outlier detection and data cleaning</p>
        </div>
        <div className="flex gap-3">
          <Button
            onClick={exportData}
            variant="outline"
            className="border-violet-200 hover:bg-violet-50 bg-transparent"
          >
            <Download className="mr-2 h-4 w-4" />
            Export Results
          </Button>
          <Button
            onClick={runAnomalyDetection}
            disabled={!selectedModel || isRunning}
            className="bg-gradient-to-r from-violet-500 to-pink-500 hover:from-violet-600 hover:to-pink-600 text-white shadow-lg"
          >
            {isRunning ? (
              <div className="flex items-center gap-2">
                <Loader2 className="h-4 w-4 animate-spin" />
                Analyzing...
              </div>
            ) : (
              <>
                <Play className="mr-2 h-4 w-4" />
                Run Detection
              </>
            )}
          </Button>
        </div>
      </div>

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
                        {((varimaResults.anomalies_detected / varimaResults.total_records) * 100).toFixed(1)}%
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
                </CardTitle>
                <CardDescription>Review, edit, and validate anomalous data points</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
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
    </div>
  )
}
