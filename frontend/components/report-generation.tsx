"use client"

import React, { useState, useEffect } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { FileText, Download, Loader2, Database, Activity, BarChart3 } from "lucide-react"
import { useToast } from "@/hooks/use-toast"
import { apiClient } from "@/lib/api"
import jsPDF from "jspdf"
import JSZip from "jszip"

interface ReportGenerationProps {
  qualityMetrics: any
  anomalyResults: any // Changed from varimaResults to anomalyResults to match guided flow
  connections?: any[]
  data: any
}

export function ReportGeneration({ 
  qualityMetrics, 
  anomalyResults, // Updated parameter name 
  connections = [], 
  data 
}: ReportGenerationProps) {
  const [isGenerating, setIsGenerating] = useState(false)
  const [isExportingCleanData, setIsExportingCleanData] = useState(false)
  const [isExportingStatistics, setIsExportingStatistics] = useState(false)
  const [isOpeningPowerBI, setIsOpeningPowerBI] = useState(false)
  const [powerBIInstalled, setPowerBIInstalled] = useState<boolean | null>(null)
  const { toast } = useToast()

  // Debug logging to see what data we're receiving
  console.log('ReportGeneration received props:', {
    qualityMetrics,
    anomalyResults,
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
      // Simulate processing time
      await new Promise((resolve) => setTimeout(resolve, 2000))
      
      // Create PDF document
      const pdf = new jsPDF()
      const pageWidth = pdf.internal.pageSize.getWidth()
      const margin = 20
      let yPosition = margin

      // Helper function to add text with wrapping
      const addText = (text: string, size: number = 12, style: 'normal' | 'bold' = 'normal') => {
        pdf.setFontSize(size)
        pdf.setFont('helvetica', style)
        pdf.text(text, margin, yPosition)
        yPosition += size * 0.6 + 5
      }

      // Helper function to add line
      const addLine = () => {
        pdf.line(margin, yPosition, pageWidth - margin, yPosition)
        yPosition += 10
      }

      // Header
      addText('DATA QUALITY & VARIMA ANALYSIS REPORT', 18, 'bold')
      addText(`Generated: ${new Date().toLocaleDateString()} ${new Date().toLocaleTimeString()}`, 10)
      addText(`Connection: ${activeConnection.db_type || 'Database'} • ${activeConnection.id}`, 10)
      addLine()

      // Executive Summary
      addText('EXECUTIVE SUMMARY', 16, 'bold')
      addText(`Tables Analyzed: ${tablesCount}`)
      addText(`Overall Quality Score: ${overallQuality}%`)
      addText(`Total Anomalies Found: ${anomaliesCount}`)
      addText(`Risk Level: ${anomalyResults?.risk_level || 'N/A'}`)
      addLine()

      // Data Quality Metrics
      addText('DATA QUALITY METRICS', 16, 'bold')
      if (qualityMetrics?.metrics) {
        addText(`Completeness: ${qualityMetrics.metrics.completeness || 0}%`)
        addText(`Uniqueness: ${qualityMetrics.metrics.uniqueness || 0}%`)
        addText(`Cardinality: ${qualityMetrics.metrics.cardinality || 0}%`)
        addText(`Consistency: ${qualityMetrics.metrics.consistency || 0}%`)
        addText(`Volumetry: ${qualityMetrics.metrics.volumetry || 0}%`)
      } else {
        addText('No quality metrics available')
      }
      addLine()

      // VARIMA Analysis
      addText('ANOMALY DETECTION (VARIMA)', 16, 'bold')
      if (anomalyResults) {
        addText(`Anomaly Rate: ${anomalyResults.anomaly_rate || 0}%`)
        addText(`Total Anomalies: ${anomalyResults.total_anomalies || 0}`)
        addText(`Total Records: ${anomalyResults.total_records || 0}`)
        addText(`Risk Assessment: ${anomalyResults.risk_level || 'Unknown'}`)
      } else {
        addText('No VARIMA analysis results available')
      }
      addLine()

      // Tables Analyzed
      addText('TABLES ANALYZED', 16, 'bold')
      const tables = qualityMetrics?.analyzed_tables || []
      if (tables.length > 0) {
        tables.forEach((table: string, index: number) => {
          addText(`${index + 1}. ${table}`)
        })
      } else {
        addText('No tables found')
      }

      // Check if we need a new page
      if (yPosition > 250) {
        pdf.addPage()
        yPosition = margin
      }
      
      addLine()
      addText('RECOMMENDATIONS', 16, 'bold')
      
      if (overallQuality < 70) {
        addText('• Focus on data quality improvement - overall score is below acceptable threshold')
      }
      if (anomaliesCount > 0) {
        addText('• Investigate anomalies found by VARIMA analysis for potential data issues')
      }
      if (qualityMetrics?.metrics) {
        if (qualityMetrics.metrics.completeness < 90) {
          addText('• Address missing data to improve completeness score')
        }
        if (qualityMetrics.metrics.uniqueness < 95) {
          addText('• Review duplicate records to improve uniqueness')
        }
      }
      
      // Footer
      yPosition = 280
      pdf.setFontSize(8)
      pdf.text('Generated by Data Quality Agent - Automated Analysis Report', margin, yPosition)

      // Save the PDF
      const fileName = `data_quality_varima_report_${activeConnection.id}_${new Date().toISOString().slice(0, 10)}.pdf`
      pdf.save(fileName)
      
      toast({
        title: "PDF Report Generated",
        description: `Comprehensive PDF report downloaded: ${fileName}`,
      })
    } catch (error) {
      console.error('PDF generation error:', error)
      toast({
        title: "Report Generation Failed", 
        description: "Unable to generate PDF report. Please try again.",
        variant: "destructive",
      })
    } finally {
      setIsGenerating(false)
    }
  }

  const exportCleanedData = async () => {
    if (!activeConnection?.id) {
      toast({
        title: "No Connection",
        description: "Please connect to a database first",
        variant: "destructive",
      })
      return
    }

    setIsExportingCleanData(true)
    try {
      // Make direct fetch request to handle CSV response
      const response = await fetch(`${apiClient.apiBaseUrl}/api/analysis/export-cleaned-data`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ connection_id: activeConnection.id }),
      })

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }

      // Get the CSV data as text
      const csvData = await response.text()
      
      // Create and download the CSV file
      const blob = new Blob([csvData], { type: 'text/csv;charset=utf-8;' })
      const link = document.createElement('a')
      const url = URL.createObjectURL(blob)
      link.setAttribute('href', url)
      link.setAttribute('download', `cleaned_data_export_${activeConnection.id}_${new Date().toISOString().split('T')[0]}.csv`)
      link.style.visibility = 'hidden'
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)
      URL.revokeObjectURL(url)
      
      toast({
        title: "Clean Data Exported",
        description: "Cleaned data has been exported successfully as CSV file.",
      })
    } catch (error) {
      console.error('Export cleaned data error:', error)
      toast({
        title: "Export Failed",
        description: "Unable to export cleaned data. Please try again.",
        variant: "destructive",
      })
    } finally {
      setIsExportingCleanData(false)
    }
  }

  const exportAnalysisStatistics = async () => {
    if (!activeConnection) {
      toast({
        title: "No Connection",
        description: "Please establish a connection first.",
        variant: "destructive",
      })
      return
    }

    setIsExportingStatistics(true)
    try {
      // Make direct fetch request to handle CSV response
      const response = await fetch(`${apiClient.apiBaseUrl}/api/analysis/export-statistics`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ connection_id: activeConnection.id }),
      })

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }

      // Get the CSV data as text
      const csvData = await response.text()
      
      // Create and download the CSV file
      const blob = new Blob([csvData], { type: 'text/csv;charset=utf-8;' })
      const link = document.createElement('a')
      const url = URL.createObjectURL(blob)
      link.setAttribute('href', url)
      link.setAttribute('download', `analysis_statistics_${activeConnection.id}_${new Date().toISOString().split('T')[0]}.csv`)
      link.style.visibility = 'hidden'
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)
      URL.revokeObjectURL(url)
      
      toast({
        title: "Statistics Exported Successfully",
        description: "Analysis statistics have been exported successfully as CSV file.",
      })
    } catch (error) {
      console.error("Export statistics error:", error)
      toast({
        title: "Export Failed",
        description: "Unable to export analysis statistics. Please try again.",
        variant: "destructive",
      })
    } finally {
      setIsExportingStatistics(false)
    }
  }

  // Check Power BI installation on component mount
  useEffect(() => {
    const checkPowerBI = async () => {
      try {
        const response = await apiClient.checkPowerBIInstallation()
        if (response.success && response.data) {
          setPowerBIInstalled(response.data.installed)
        }
      } catch (error) {
        console.error("Error checking Power BI installation:", error)
        setPowerBIInstalled(false)
      }
    }
    
    checkPowerBI()
  }, [])

  const openPowerBIVisualization = async () => {
    if (!activeConnection) {
      toast({
        title: "No Connection",
        description: "Please establish a connection first.",
        variant: "destructive",
      })
      return
    }

    setIsOpeningPowerBI(true)
    try {
      // Step 1: Create the PowerBI package
      const response = await fetch(`${apiClient.apiBaseUrl}/api/powerbi/open-online`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ connection_id: activeConnection.id }),
      })

      if (!response.ok) {
        throw new Error(`Failed to create PowerBI package: ${response.status}`)
      }

      const packageResponse = await response.json()
      
      if (packageResponse.success) {
        // Show success message
        const packageContents = []
        if (packageResponse.package_contents?.template) {
          packageContents.push("🎯 Custom Power BI template (.pbit)")
        }
        if (packageResponse.package_contents?.dashboard) {
          packageContents.push("📈 Pre-built dashboard (.pbix)")
        }
        packageContents.push("📊 Analysis data (CSV)")
        packageContents.push("📖 Setup instructions")
        
        toast({
          title: "Power BI Package Ready!",
          description: `Package includes: ${packageContents.join(", ")}. Download will start automatically.`,
        })
        
        // Step 2: Download the package file
        if (packageResponse.download_url) {
          const downloadUrl = `${apiClient.apiBaseUrl}${packageResponse.download_url}`
          
          try {
            const downloadResponse = await fetch(downloadUrl)
            if (!downloadResponse.ok) {
              throw new Error(`Download failed: ${downloadResponse.status}`)
            }
            
            // Get the ZIP file as blob
            const blob = await downloadResponse.blob()
            
            // Create and trigger download
            const link = document.createElement('a')
            const url = URL.createObjectURL(blob)
            link.href = url
            link.download = `PowerBI_DataQuality_Package_${activeConnection.id}.zip`
            link.style.visibility = 'hidden'
            document.body.appendChild(link)
            link.click()
            document.body.removeChild(link)
            URL.revokeObjectURL(url)
            
            // Show additional instructions after a delay
            setTimeout(() => {
              const workflowMessage = packageResponse.package_contents?.template 
                ? "📁 Extract the ZIP → Open .pbit template → Connect to CSV data → Dashboard ready!"
                : "📁 Extract the ZIP → Import CSV to Power BI → Create visualizations"
                
              toast({
                title: "Next Steps",
                description: workflowMessage,
              })
            }, 2000)
          } catch (downloadError) {
            console.error('Download error:', downloadError)
            toast({
              title: "Download Failed",
              description: "Package was created but download failed. Please try again.",
              variant: "destructive",
            })
          }
        }
        
      } else {
        throw new Error(packageResponse.message || "Failed to create Power BI package")
      }
    } catch (error) {
      console.error("Power BI visualization error:", error)
      
      toast({
        title: "Package Creation Failed",
        description: "Unable to create Power BI package. Please ensure the backend is running and try again.",
        variant: "destructive",
      })
    } finally {
      setIsOpeningPowerBI(false)
    }
  }

  const hasData = qualityMetrics || anomalyResults
  const tablesCount = qualityMetrics?.analyzed_tables?.length || 0
  const anomaliesCount = anomalyResults?.total_anomalies || 0
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
    varimaResultsStructure: anomalyResults ? Object.keys(anomalyResults) : 'No varima results'
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
              <strong>VARIMA Results:</strong> {anomalyResults ? 'Present' : 'Missing'}
              {anomalyResults && (
                <div className="ml-2">
                  <div>Anomalies: {anomalyResults.total_anomalies || 0}</div>
                  <div>Risk: {anomalyResults.risk_level || 'N/A'}</div>
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
                  {anomalyResults?.risk_level || 'N/A'}
                </div>
                <div className="text-sm text-purple-600">Risk Level</div>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Report Generation */}
      <div className="grid gap-6 md:grid-cols-3">
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
          <div className="h-2 bg-gradient-to-r from-blue-500 to-cyan-500 rounded-t-lg"></div>
          <CardHeader>
            <CardTitle className="flex items-center gap-3 text-xl">
              <div className="p-2 bg-gradient-to-r from-blue-500 to-cyan-500 rounded-lg">
                <Database className="h-5 w-5 text-white" />
              </div>
              Clean Data Export
            </CardTitle>
            <CardDescription>
              Export cleaned data after quality analysis and VARIMA anomaly removal
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <h4 className="font-semibold text-gray-700">Cleaning Process:</h4>
              <div className="space-y-1 text-sm text-gray-600">
                <div className="flex items-center gap-2">
                  <Database className="h-4 w-4 text-green-500" />
                  <span>Remove null records & duplicates</span>
                </div>
                <div className="flex items-center gap-2">
                  <Activity className="h-4 w-4 text-purple-500" />
                  <span>VARIMA-based anomaly removal</span>
                </div>
                <div className="flex items-center gap-2">
                  <BarChart3 className="h-4 w-4 text-blue-500" />
                  <span>Statistical outlier filtering</span>
                </div>
              </div>
            </div>
            <Button
              onClick={exportCleanedData}
              disabled={isExportingCleanData || !activeConnection}
              className="w-full bg-gradient-to-r from-blue-500 to-cyan-500 hover:from-blue-600 hover:to-cyan-600 text-white"
            >
              {isExportingCleanData ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Exporting Clean Data...
                </>
              ) : (
                <>
                  <Download className="mr-2 h-4 w-4" />
                  Export Clean Data
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
                <BarChart3 className="h-5 w-5 text-white" />
              </div>
              Analysis Statistics Export
            </CardTitle>
            <CardDescription>
              Export comprehensive statistics including quality metrics, anomaly detection results, and risk assessment
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <h4 className="font-semibold text-gray-700">Statistics Include:</h4>
              <div className="space-y-1 text-sm text-gray-600">
                <div className="flex items-center gap-2">
                  <BarChart3 className="h-4 w-4 text-green-500" />
                  <span>Quality metrics (5 indicators)</span>
                </div>
                <div className="flex items-center gap-2">
                  <Activity className="h-4 w-4 text-purple-500" />
                  <span>VARIMA anomaly detection results</span>
                </div>
                <div className="flex items-center gap-2">
                  <Database className="h-4 w-4 text-blue-500" />
                  <span>Data source information & risk assessment</span>
                </div>
              </div>
            </div>
            <Button
              onClick={exportAnalysisStatistics}
              disabled={isExportingStatistics || !activeConnection}
              className="w-full bg-gradient-to-r from-green-500 to-emerald-500 hover:from-green-600 hover:to-emerald-600 text-white"
            >
              {isExportingStatistics ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Exporting Statistics...
                </>
              ) : (
                <>
                  <Download className="mr-2 h-4 w-4" />
                  Export Analysis Statistics
                </>
              )}
            </Button>
          </CardContent>
        </Card>

        <Card className="border-0 shadow-lg">
          <div className="h-2 bg-gradient-to-r from-orange-500 to-red-500 rounded-t-lg"></div>
          <CardHeader>
            <CardTitle className="flex items-center gap-3 text-xl">
              <div className="p-2 bg-gradient-to-r from-orange-500 to-red-500 rounded-lg">
                <BarChart3 className="h-5 w-5 text-white" />
              </div>
              Power BI Package Download
            </CardTitle>
            <CardDescription>
              Download a complete package with your analysis data, custom template, and setup instructions for Power BI visualization
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <h4 className="font-semibold text-gray-700">Power BI Features:</h4>
              <div className="space-y-1 text-sm text-gray-600">
                <div className="flex items-center gap-2">
                  <BarChart3 className="h-4 w-4 text-orange-500" />
                  <span>Interactive dashboards & charts</span>
                </div>
                <div className="flex items-center gap-2">
                  <Activity className="h-4 w-4 text-purple-500" />
                  <span>Advanced data analysis tools</span>
                </div>
                <div className="flex items-center gap-2">
                  <Database className="h-4 w-4 text-blue-500" />
                  <span>Professional reporting capabilities</span>
                </div>
              </div>
              {powerBIInstalled === false && (
                <div className="p-3 bg-orange-50 border border-orange-200 rounded-lg">
                  <p className="text-sm text-orange-800">
                    <strong>Power BI Desktop not detected.</strong> Download it from Microsoft to use this feature.
                  </p>
                </div>
              )}
            </div>
            <Button
              onClick={openPowerBIVisualization}
              disabled={isOpeningPowerBI || !activeConnection || powerBIInstalled === false}
              className="w-full bg-gradient-to-r from-orange-500 to-red-500 hover:from-orange-600 hover:to-red-600 text-white"
            >
              {isOpeningPowerBI ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Creating Package...
                </>
              ) : (
                <>
                  <Download className="mr-2 h-4 w-4" />
                  Download Power BI Package
                </>
              )}
            </Button>
            {powerBIInstalled === false && (
              <Button
                onClick={() => window.open('https://powerbi.microsoft.com/desktop/', '_blank')}
                variant="outline"
                className="w-full border-orange-300 text-orange-600 hover:bg-orange-50"
              >
                <Download className="mr-2 h-4 w-4" />
                Download Power BI Desktop
              </Button>
            )}
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
