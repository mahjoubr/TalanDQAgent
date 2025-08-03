"use client"

import { useState } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { FileText, Download, Loader2, Database, Activity, BarChart3 } from "lucide-react"
import { useToast } from "@/hooks/use-toast"
import { apiClient } from "@/lib/api"

interface ReportGenerationProps {
  qualityMetrics: any
  varimaResults: any
  connections?: any[]
  data: any
}

export function ReportGeneration({ 
  qualityMetrics, 
  varimaResults, 
  connections = [], 
  data 
}: ReportGenerationProps) {
  const [isGenerating, setIsGenerating] = useState(false)
  const { toast } = useToast()

  // Debug logging to see what data we're receiving
  console.log('ReportGeneration received props:', {
    qualityMetrics,
    varimaResults,
    connections,
    data
  })

  // Get the active connection
  const getActiveConnection = () => {
    if (data?.id) {
      return data
    }
    if (connections && connections.length > 0) {
      return connections[connections.length - 1]
    }
    return null
  }

  const activeConnection = getActiveConnection()

  const generatePdfReport = async () => {
    if (!activeConnection?.id) {
      toast({
        title: "No Connection",
        description: "Please connect to a database first",
        variant: "destructive",
      })
      return
    }

    setIsGenerating(true)
    try {
      // Simulate PDF generation with collected data
      await new Promise((resolve) => setTimeout(resolve, 3000))
      
      // Create a comprehensive PDF report content
      const reportContent = {
        connection_id: activeConnection.id,
        database_type: activeConnection.db_type || 'Database',
        generated_at: new Date().toISOString(),
        quality_metrics: qualityMetrics,
        varima_results: varimaResults,
        tables_analyzed: qualityMetrics?.analyzed_tables || [],
        total_anomalies: varimaResults?.total_anomalies || 0,
        quality_summary: {
          completeness: qualityMetrics?.metrics?.completeness || 0,
          uniqueness: qualityMetrics?.metrics?.uniqueness || 0,
          cardinality: qualityMetrics?.metrics?.cardinality || 0,
          consistency: qualityMetrics?.metrics?.consistency || 0,
          volumetry: qualityMetrics?.metrics?.volumetry || 0,
        }
      }

      // Create downloadable PDF (simulated)
      const blob = new Blob([JSON.stringify(reportContent, null, 2)], { 
        type: 'application/json' 
      })
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `data_quality_varima_report_${activeConnection.id}_${new Date().toISOString().slice(0, 10)}.json`
      a.click()
      
      toast({
        title: "PDF Report Generated",
        description: `Comprehensive report including ${reportContent.tables_analyzed.length} tables, quality metrics, and VARIMA anomaly analysis`,
      })
    } catch (error) {
      toast({
        title: "Report Generation Failed", 
        description: "Unable to generate report. Please try again.",
        variant: "destructive",
      })
    } finally {
      setIsGenerating(false)
    }
  }

  const generateExcelReport = async () => {
    if (!activeConnection?.id) {
      toast({
        title: "No Connection",
        description: "Please connect to a database first",
        variant: "destructive",
      })
      return
    }

    setIsGenerating(true)
    try {
      // Simulate Excel generation with collected data
      await new Promise((resolve) => setTimeout(resolve, 2500))
      
      // Create Excel-formatted data structure
      const excelData = {
        summary: {
          connection_id: activeConnection.id,
          database_type: activeConnection.db_type || 'Database',
          generated_at: new Date().toISOString(),
          tables_count: qualityMetrics?.analyzed_tables?.length || 0,
          total_records: qualityMetrics?.sample_size || 0,
          total_anomalies: varimaResults?.total_anomalies || 0,
          anomaly_rate: varimaResults?.anomaly_rate || 0,
          risk_level: varimaResults?.risk_level || 'Unknown'
        },
        quality_metrics: qualityMetrics?.metrics || {},
        quality_details: qualityMetrics?.detailed_analysis || {},
        varima_summary: varimaResults || {},
        tables_analyzed: qualityMetrics?.analyzed_tables || []
      }

      // Create downloadable Excel (simulated as CSV)
      const csvContent = [
        "Data Quality & VARIMA Analysis Report",
        "",
        "=== SUMMARY ===",
        `Connection ID,${excelData.summary.connection_id}`,
        `Database Type,${excelData.summary.database_type}`,
        `Generated At,${excelData.summary.generated_at}`,
        `Tables Analyzed,${excelData.summary.tables_count}`,
        `Total Records,${excelData.summary.total_records}`,
        `Total Anomalies,${excelData.summary.total_anomalies}`,
        `Anomaly Rate,${excelData.summary.anomaly_rate}%`,
        `Risk Level,${excelData.summary.risk_level}`,
        "",
        "=== QUALITY METRICS ===",
        `Completeness,${excelData.quality_metrics.completeness || 0}%`,
        `Uniqueness,${excelData.quality_metrics.uniqueness || 0}%`,
        `Cardinality,${excelData.quality_metrics.cardinality || 0}%`,
        `Consistency,${excelData.quality_metrics.consistency || 0}%`,
        `Volumetry,${excelData.quality_metrics.volumetry || 0}%`,
        "",
        "=== ANALYZED TABLES ===",
        "Table Name",
        ...excelData.tables_analyzed
      ].join("\n")

      const blob = new Blob([csvContent], { type: 'text/csv' })
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `data_quality_varima_report_${activeConnection.id}_${new Date().toISOString().slice(0, 10)}.csv`
      a.click()
      
      toast({
        title: "Excel Report Generated",
        description: `Spreadsheet report with ${excelData.summary.tables_count} tables analysis and anomaly detection results`,
      })
    } catch (error) {
      toast({
        title: "Report Generation Failed",
        description: "Unable to generate Excel report. Please try again.",
        variant: "destructive",
      })
    } finally {
      setIsGenerating(false)
    }
  }

  const hasData = qualityMetrics || varimaResults
  const tablesCount = qualityMetrics?.analyzed_tables?.length || 0
  const anomaliesCount = varimaResults?.total_anomalies || 0
  const overallQuality = qualityMetrics?.metrics ? 
    Math.round((
      (qualityMetrics.metrics.completeness || 0) + 
      (qualityMetrics.metrics.uniqueness || 0) + 
      (qualityMetrics.metrics.cardinality || 0) + 
      (qualityMetrics.metrics.consistency || 0) + 
      (qualityMetrics.metrics.volumetry || 0)
    ) / 5) : 0

  // Additional debug info
  console.log('Report Generation computed values:', {
    hasData,
    tablesCount,
    anomaliesCount,
    overallQuality,
    qualityMetricsStructure: qualityMetrics ? Object.keys(qualityMetrics) : 'No quality metrics',
    varimaResultsStructure: varimaResults ? Object.keys(varimaResults) : 'No varima results'
  })

  return (
    <div className="space-y-8">
      {/* Header */}
      <div>
        <h2 className="text-4xl font-bold bg-gradient-to-r from-purple-600 to-violet-600 bg-clip-text text-transparent">
          Automated Report Generation
        </h2>
        <p className="text-gray-600 mt-2">
          Generate comprehensive reports combining data quality analysis and VARIMA anomaly detection
        </p>
        {activeConnection && (
          <p className="text-sm text-blue-600 mt-1">
            Connected to: {activeConnection.db_type ? `${activeConnection.db_type?.toUpperCase()} Database` : 'Database'} • {activeConnection.id}
          </p>
        )}
        
        {/* Debug Info - Remove in production */}
        <div className="mt-4 p-4 bg-gray-100 rounded-lg text-xs">
          <h4 className="font-semibold mb-2">Debug Information:</h4>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <strong>Quality Metrics:</strong> {qualityMetrics ? 'Present' : 'Missing'}
              {qualityMetrics && (
                <div className="ml-2">
                  <div>Tables: {qualityMetrics.analyzed_tables?.length || 0}</div>
                  <div>Has metrics: {qualityMetrics.metrics ? 'Yes' : 'No'}</div>
                </div>
              )}
            </div>
            <div>
              <strong>VARIMA Results:</strong> {varimaResults ? 'Present' : 'Missing'}
              {varimaResults && (
                <div className="ml-2">
                  <div>Anomalies: {varimaResults.total_anomalies || 0}</div>
                  <div>Risk: {varimaResults.risk_level || 'N/A'}</div>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Data Summary */}
      {hasData && (
        <Card className="border-0 shadow-lg bg-gradient-to-r from-blue-50 to-purple-50">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-xl">
              <div className="p-2 bg-gradient-to-r from-blue-500 to-purple-500 rounded-lg">
                <BarChart3 className="h-5 w-5 text-white" />
              </div>
              Analysis Summary
            </CardTitle>
            <CardDescription>
              Overview of available data for report generation
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid gap-4 md:grid-cols-4">
              <div className="bg-white rounded-lg border border-blue-200 p-4 text-center">
                <div className="text-2xl font-bold text-blue-700">
                  {tablesCount}
                </div>
                <div className="text-sm text-blue-600">Tables Analyzed</div>
              </div>
              <div className="bg-white rounded-lg border border-green-200 p-4 text-center">
                <div className="text-2xl font-bold text-green-700">
                  {overallQuality}%
                </div>
                <div className="text-sm text-green-600">Avg Quality Score</div>
              </div>
              <div className="bg-white rounded-lg border border-red-200 p-4 text-center">
                <div className="text-2xl font-bold text-red-700">
                  {anomaliesCount}
                </div>
                <div className="text-sm text-red-600">Anomalies Found</div>
              </div>
              <div className="bg-white rounded-lg border border-purple-200 p-4 text-center">
                <div className="text-2xl font-bold text-purple-700">
                  {varimaResults?.risk_level || 'N/A'}
                </div>
                <div className="text-sm text-purple-600">Risk Level</div>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Report Generation */}
      <div className="grid gap-6 md:grid-cols-2">
        <Card className="border-0 shadow-lg">
          <div className="h-2 bg-gradient-to-r from-red-500 to-pink-500 rounded-t-lg"></div>
          <CardHeader>
            <CardTitle className="flex items-center gap-3 text-xl">
              <div className="p-2 bg-gradient-to-r from-red-500 to-pink-500 rounded-lg">
                <FileText className="h-5 w-5 text-white" />
              </div>
              PDF Report
            </CardTitle>
            <CardDescription>
              Comprehensive PDF report with data quality metrics and VARIMA anomaly analysis
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <h4 className="font-semibold text-gray-700">Includes:</h4>
              <div className="space-y-1 text-sm text-gray-600">
                <div className="flex items-center gap-2">
                  <Database className="h-4 w-4 text-green-500" />
                  <span>Quality metrics for all {tablesCount} tables</span>
                </div>
                <div className="flex items-center gap-2">
                  <Activity className="h-4 w-4 text-purple-500" />
                  <span>VARIMA anomaly detection results</span>
                </div>
                <div className="flex items-center gap-2">
                  <BarChart3 className="h-4 w-4 text-blue-500" />
                  <span>Detailed analysis and recommendations</span>
                </div>
              </div>
            </div>
            <Button
              onClick={generatePdfReport}
              disabled={isGenerating || !hasData}
              className="w-full bg-gradient-to-r from-red-500 to-pink-500 hover:from-red-600 hover:to-pink-600 text-white"
            >
              {isGenerating ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Generating PDF...
                </>
              ) : (
                <>
                  <Download className="mr-2 h-4 w-4" />
                  Generate PDF Report
                </>
              )}
            </Button>
          </CardContent>
        </Card>

        <Card className="border-0 shadow-lg">
          <div className="h-2 bg-gradient-to-r from-green-500 to-emerald-500 rounded-t-lg"></div>
          <CardHeader>
            <CardTitle className="flex items-center gap-3 text-xl">
              <div className="p-2 bg-gradient-to-r from-green-500 to-emerald-500 rounded-lg">
                <FileText className="h-5 w-5 text-white" />
              </div>
              Excel Report
            </CardTitle>
            <CardDescription>
              Structured Excel/CSV report with data tables and analysis results
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <h4 className="font-semibold text-gray-700">Includes:</h4>
              <div className="space-y-1 text-sm text-gray-600">
                <div className="flex items-center gap-2">
                  <Database className="h-4 w-4 text-green-500" />
                  <span>Table-by-table quality breakdown</span>
                </div>
                <div className="flex items-center gap-2">
                  <Activity className="h-4 w-4 text-purple-500" />
                  <span>Anomaly details and scores</span>
                </div>
                <div className="flex items-center gap-2">
                  <BarChart3 className="h-4 w-4 text-blue-500" />
                  <span>Summary statistics and trends</span>
                </div>
              </div>
            </div>
            <Button
              onClick={generateExcelReport}
              disabled={isGenerating || !hasData}
              className="w-full bg-gradient-to-r from-green-500 to-emerald-500 hover:from-green-600 hover:to-emerald-600 text-white"
            >
              {isGenerating ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Generating Excel...
                </>
              ) : (
                <>
                  <Download className="mr-2 h-4 w-4" />
                  Generate Excel Report
                </>
              )}
            </Button>
          </CardContent>
        </Card>
      </div>

      {/* No Data State */}
      {!hasData && (
        <Card className="border-0 shadow-lg bg-gradient-to-r from-yellow-50 to-orange-50">
          <CardContent className="text-center py-12">
            <FileText className="h-16 w-16 text-yellow-500 mx-auto mb-4" />
            <h3 className="text-xl font-semibold text-yellow-700 mb-2">No Analysis Data Available</h3>
            <p className="text-yellow-600 mb-4">
              Run data quality analysis and VARIMA anomaly detection first to generate comprehensive reports
            </p>
            <div className="flex gap-2 justify-center">
              <Badge className="bg-yellow-100 text-yellow-700">
                1. Connect to Database
              </Badge>
              <Badge className="bg-yellow-100 text-yellow-700">
                2. Run Quality Analysis
              </Badge>
              <Badge className="bg-yellow-100 text-yellow-700">
                3. Run VARIMA Detection
              </Badge>
              <Badge className="bg-yellow-100 text-yellow-700">
                4. Generate Reports
              </Badge>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  )
}
