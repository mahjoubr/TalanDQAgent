"use client"

import { useState } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Label } from "@/components/ui/label"
import { Textarea } from "@/components/ui/textarea"
import { FileText, Download, Mail, Bell, Calendar, Send } from "lucide-react"
import { useToast } from "@/hooks/use-toast"

interface ReportGenerationProps {
  qualityMetrics: any
}

export function ReportGeneration({ qualityMetrics }: ReportGenerationProps) {
  const [reportType, setReportType] = useState("")
  const [emailRecipients, setEmailRecipients] = useState("")
  const [reportSchedule, setReportSchedule] = useState("")
  const [isGenerating, setIsGenerating] = useState(false)
  const { toast } = useToast()

  const generateReport = async (format: string) => {
    setIsGenerating(true)
    // Simulate report generation
    setTimeout(() => {
      setIsGenerating(false)
      toast({
        title: "Report Generated Successfully",
        description: `${format.toUpperCase()} report has been generated and is ready for download`,
      })
    }, 2000)
  }

  const sendNotification = () => {
    toast({
      title: "Notifications Sent",
      description: "Alert notifications have been sent to all specified recipients",
    })
  }

  const mockAlerts = [
    {
      id: 1,
      type: "Data Quality",
      severity: "high",
      message: "Completeness score dropped below 80% threshold",
      timestamp: "2024-01-22 14:30:00",
      status: "active",
    },
    {
      id: 2,
      type: "Anomaly Detection",
      severity: "medium",
      message: "VARIMA model detected 15 new anomalies in financial data",
      timestamp: "2024-01-22 13:45:00",
      status: "acknowledged",
    },
  ]

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
      <div>
        <h2 className="text-4xl font-bold bg-gradient-to-r from-purple-600 to-violet-600 bg-clip-text text-transparent">
          Reports & Alert System
        </h2>
        <p className="text-gray-600 mt-2">Generate comprehensive reports and manage notification systems</p>
      </div>

      <div className="grid gap-8 lg:grid-cols-2">
        {/* Report Generation */}
        <Card className="border-0 shadow-lg">
          <div className="h-2 bg-gradient-to-r from-blue-500 to-cyan-500 rounded-t-lg"></div>
          <CardHeader>
            <CardTitle className="flex items-center gap-3 text-xl">
              <div className="p-2 bg-gradient-to-r from-blue-500 to-cyan-500 rounded-lg">
                <FileText className="h-5 w-5 text-white" />
              </div>
              Report Generation
            </CardTitle>
            <CardDescription>Create detailed data quality and anomaly reports</CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">
            <div className="space-y-2">
              <Label className="text-sm font-semibold text-gray-700">Report Type</Label>
              <Select value={reportType} onValueChange={setReportType}>
                <SelectTrigger className="border-blue-200 focus:border-blue-400">
                  <SelectValue placeholder="Select report type" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="executive">📊 Executive Summary</SelectItem>
                  <SelectItem value="detailed">📈 Detailed Analysis</SelectItem>
                  <SelectItem value="anomalies">🚨 Anomaly Report</SelectItem>
                  <SelectItem value="trends">📉 Trend Analysis</SelectItem>
                  <SelectItem value="compliance">✅ Compliance Report</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div className="grid gap-3 md:grid-cols-2">
              <Button
                onClick={() => generateReport("pdf")}
                disabled={isGenerating}
                className="bg-gradient-to-r from-red-500 to-pink-500 hover:from-red-600 hover:to-pink-600 text-white"
              >
                {isGenerating ? (
                  <div className="flex items-center gap-2">
                    <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                    Generating...
                  </div>
                ) : (
                  <>
                    <Download className="mr-2 h-4 w-4" />
                    PDF Report
                  </>
                )}
              </Button>
              <Button
                onClick={() => generateReport("excel")}
                disabled={isGenerating}
                className="bg-gradient-to-r from-green-500 to-emerald-500 hover:from-green-600 hover:to-emerald-600 text-white"
              >
                <Download className="mr-2 h-4 w-4" />
                Excel Report
              </Button>
            </div>

            <div className="space-y-2">
              <Label className="text-sm font-semibold text-gray-700">Schedule Reports</Label>
              <Select value={reportSchedule} onValueChange={setReportSchedule}>
                <SelectTrigger className="border-blue-200 focus:border-blue-400">
                  <SelectValue placeholder="Select schedule frequency" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="daily">📅 Daily</SelectItem>
                  <SelectItem value="weekly">📅 Weekly</SelectItem>
                  <SelectItem value="monthly">📅 Monthly</SelectItem>
                  <SelectItem value="quarterly">📅 Quarterly</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </CardContent>
        </Card>

        {/* Notification System */}
        <Card className="border-0 shadow-lg">
          <div className="h-2 bg-gradient-to-r from-violet-500 to-purple-500 rounded-t-lg"></div>
          <CardHeader>
            <CardTitle className="flex items-center gap-3 text-xl">
              <div className="p-2 bg-gradient-to-r from-violet-500 to-purple-500 rounded-lg">
                <Mail className="h-5 w-5 text-white" />
              </div>
              Notification System
            </CardTitle>
            <CardDescription>Configure alerts and email notifications</CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">
            <div className="space-y-2">
              <Label className="text-sm font-semibold text-gray-700">Email Recipients</Label>
              <Textarea
                placeholder="Enter email addresses separated by commas"
                value={emailRecipients}
                onChange={(e) => setEmailRecipients(e.target.value)}
                rows={3}
                className="border-violet-200 focus:border-violet-400"
              />
            </div>

            <Button
              onClick={sendNotification}
              className="w-full bg-gradient-to-r from-violet-500 to-purple-500 hover:from-violet-600 hover:to-purple-600 text-white"
            >
              <Send className="mr-2 h-4 w-4" />
              Send Test Notification
            </Button>
          </CardContent>
        </Card>
      </div>

      {/* Recent Alerts */}
      <Card className="border-0 shadow-lg">
        <CardHeader>
          <CardTitle className="flex items-center gap-3 text-xl">
            <div className="p-2 bg-gradient-to-r from-orange-500 to-red-500 rounded-lg">
              <Bell className="h-5 w-5 text-white" />
            </div>
            Recent Alerts & Notifications
          </CardTitle>
          <CardDescription>Monitor system alerts and notification history</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {mockAlerts.map((alert) => (
              <div
                key={alert.id}
                className="flex items-start justify-between p-4 border border-gray-200 rounded-xl bg-gradient-to-r from-white to-gray-50 hover:shadow-md transition-all duration-300"
              >
                <div className="flex items-start gap-4">
                  <div className="p-2 bg-gradient-to-r from-orange-500 to-red-500 rounded-lg">
                    <Bell className="h-4 w-4 text-white" />
                  </div>
                  <div className="flex-1">
                    <div className="flex items-center gap-3 mb-2">
                      <span className="font-semibold text-gray-800">{alert.type}</span>
                      <Badge className={getSeverityColor(alert.severity)}>{alert.severity}</Badge>
                    </div>
                    <p className="text-sm text-gray-700 mb-2">{alert.message}</p>
                    <div className="flex items-center gap-2 text-xs text-gray-500">
                      <Calendar className="h-3 w-3" />
                      <span>{alert.timestamp}</span>
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
