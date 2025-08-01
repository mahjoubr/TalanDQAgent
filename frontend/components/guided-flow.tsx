"use client"

import { useState, useEffect } from "react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Progress } from "@/components/ui/progress"
import { Badge } from "@/components/ui/badge"
import { DataConnector } from "./data-connector"
import { DataQualityEngine } from "./data-quality-engine"
import { AnomalyDetection } from "./anomaly-detection"
import { ReportGeneration } from "./report-generation"
import {
  ArrowLeft,
  ArrowRight,
  Home,
  Database,
  Shield,
  Activity,
  FileText,
  CheckCircle2,
  BarChart3,
} from "lucide-react"
import { useToast } from "@/hooks/use-toast"

interface GuidedFlowProps {
  onBack?: () => void
  onNavigateTo?: (view: "welcome" | "auth" | "guided" | "dashboard") => void
  canGoBack?: boolean
  userData?: any
  onComplete?: () => void
  onViewDashboard: () => void
}

export function GuidedFlow({ onBack, onNavigateTo, canGoBack, userData, onComplete, onViewDashboard }: GuidedFlowProps) {
  const [currentStep, setCurrentStep] = useState(0)
  const [completedSteps, setCompletedSteps] = useState<number[]>([])
  const [stepData, setStepData] = useState<any>({})
  const [isLoading, setIsLoading] = useState(false)
  const { toast } = useToast()

  // Show notification when reaching quality analysis step with connected data
  useEffect(() => {
    if (currentStep === 1 && stepData[0]?.id) {
      toast({
        title: "Quality Analysis Starting",
        description: "Automatically analyzing your connected database for quality metrics...",
      })
    }
  }, [currentStep, stepData[0]?.id])

  const steps = [
    {
      id: 0,
      title: "Data Connection",
      description: "Connect your data sources",
      icon: Database,
      component: DataConnector,
      color: "from-blue-500 to-cyan-500",
    },
    {
      id: 1,
      title: "Quality Analysis",
      description: "Analyze data quality metrics",
      icon: Shield,
      component: DataQualityEngine,
      color: "from-violet-500 to-purple-500",
    },
    {
      id: 2,
      title: "Anomaly Detection",
      description: "AI-powered anomaly detection",
      icon: Activity,
      component: AnomalyDetection,
      color: "from-pink-500 to-rose-500",
    },
    {
      id: 3,
      title: "Report Generation",
      description: "Generate comprehensive reports",
      icon: FileText,
      component: ReportGeneration,
      color: "from-green-500 to-emerald-500",
    },
  ]

  const currentStepData = steps[currentStep]
  const progress = ((currentStep + 1) / steps.length) * 100
  const isStepCompleted = completedSteps.includes(currentStep)
  const canProceed = isStepCompleted || currentStep === 0

  const handleStepComplete = (data: any) => {
    setStepData((prev: any) => ({ ...prev, [currentStep]: data }))
    if (!completedSteps.includes(currentStep)) {
      setCompletedSteps((prev) => [...prev, currentStep])
    }
  }

  const handleDataConnected = (data: any) => {
    console.log('Data connected in guided flow:', data)
    handleStepComplete(data)
  }

  const handleMetricsCalculated = (metrics: any) => {
    console.log('Metrics calculated in guided flow:', metrics)
    handleStepComplete(metrics)
    
    // Show completion message and auto-advance to next step after a delay
    if (currentStep === 1) {
      toast({
        title: "Quality Analysis Complete!",
        description: "Your data quality metrics have been calculated. Moving to anomaly detection...",
      })
      
      setTimeout(() => {
        setCurrentStep(2)
      }, 3000) // 3 second delay to show results
    }
  }

  const handleNext = () => {
    if (currentStep < steps.length - 1) {
      setCurrentStep(currentStep + 1)
    } else if (onComplete) {
      onComplete()
    }
  }

  const handlePrevious = () => {
    if (currentStep > 0) {
      setCurrentStep(currentStep - 1)
    }
  }

  const handleStepClick = (stepIndex: number) => {
    if (stepIndex <= Math.max(...completedSteps) + 1) {
      setCurrentStep(stepIndex)
    }
  }

  const CurrentComponent = currentStepData.component

  // Prepare props based on the current step
  const getComponentProps = (): any => {
    const baseProps = {
      onComplete: handleStepComplete,
      isCompleted: isStepCompleted,
      setIsLoading,
    }

    switch (currentStep) {
      case 0: // DataConnector
        return {
          ...baseProps,
          data: stepData[currentStep],
          onDataConnected: handleDataConnected,
        }
      case 1: // DataQualityEngine
        return {
          ...baseProps,
          data: stepData[0], // Pass the connected data from step 0
          onMetricsCalculated: handleMetricsCalculated,
          qualityMetrics: stepData[currentStep]?.metrics,
          connections: stepData[0] ? [stepData[0]] : [], // Pass connections from step 0
          onDataConnected: handleDataConnected, // Required by DataConnector interface
        }
      case 2: // AnomalyDetection
        return {
          ...baseProps,
          data: stepData[0], // Pass the connected data from step 0
          qualityMetrics: stepData[1]?.metrics,
          connections: stepData[0] ? [stepData[0]] : [],
          onDataConnected: handleDataConnected, // Required by DataConnector interface
          onMetricsCalculated: handleMetricsCalculated, // Required by DataQualityEngine interface
        }
      case 3: // ReportGeneration
        return {
          ...baseProps,
          data: stepData[0], // Pass the connected data from step 0
          qualityMetrics: stepData[1]?.metrics,
          anomalyResults: stepData[2],
          connections: stepData[0] ? [stepData[0]] : [],
          onDataConnected: handleDataConnected, // Required by DataConnector interface
          onMetricsCalculated: handleMetricsCalculated, // Required by DataQualityEngine interface
        }
      default:
        return {
          ...baseProps,
          onDataConnected: handleDataConnected,
          onMetricsCalculated: handleMetricsCalculated,
        }
    }
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-50">
      {/* Header */}
      <div className="bg-white border-b border-gray-200 shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <div className="flex items-center gap-4">
              {canGoBack && onBack ? (
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

              <div className="flex items-center gap-3">
                <div className="p-2 bg-gradient-to-r from-blue-500 to-purple-500 rounded-lg">
                  <Database className="h-5 w-5 text-white" />
                </div>
                <div>
                  <h1 className="text-lg font-bold text-gray-900">Guided Setup</h1>
                  <p className="text-sm text-gray-500">Power BI Dashboard Configuration</p>
                </div>
              </div>
            </div>

            <div className="flex items-center gap-4">
              <Badge variant="secondary" className="bg-blue-100 text-blue-700">
                Step {currentStep + 1} of {steps.length}
              </Badge>

              {onNavigateTo && (
                <Button
                  onClick={() => onNavigateTo("dashboard")}
                  variant="outline"
                  size="sm"
                  className="border-blue-300 text-blue-600 hover:bg-blue-50"
                >
                  <BarChart3 className="mr-2 h-4 w-4" />
                  View Dashboard
                </Button>
              )}
            </div>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-4 gap-8">
          {/* Sidebar - Step Navigation */}
          <div className="lg:col-span-1">
            <Card className="sticky top-8">
              <CardHeader>
                <CardTitle className="text-lg">Setup Progress</CardTitle>
                <Progress value={progress} className="w-full" />
                <p className="text-sm text-gray-600">{Math.round(progress)}% Complete</p>
              </CardHeader>
              <CardContent className="space-y-2">
                {steps.map((step, index) => {
                  const isCompleted = completedSteps.includes(index)
                  const isCurrent = index === currentStep
                  const isAccessible = index <= Math.max(...completedSteps) + 1

                  return (
                    <Button
                      key={step.id}
                      onClick={() => handleStepClick(index)}
                      variant={isCurrent ? "default" : "ghost"}
                      className={`w-full justify-start p-3 h-auto ${
                        !isAccessible ? "opacity-50 cursor-not-allowed" : ""
                      }`}
                      disabled={!isAccessible}
                    >
                      <div className="flex items-center gap-3 w-full">
                        <div
                          className={`p-2 rounded-lg bg-gradient-to-r ${step.color} ${
                            isCurrent ? "text-white" : "text-white opacity-80"
                          }`}
                        >
                          <step.icon className="h-4 w-4" />
                        </div>
                        <div className="flex-1 text-left">
                          <div className="flex items-center gap-2">
                            <span className="font-medium">{step.title}</span>
                            {isCompleted && <CheckCircle2 className="h-4 w-4 text-green-500" />}
                          </div>
                          <p className="text-xs text-gray-500 mt-1">{step.description}</p>
                        </div>
                      </div>
                    </Button>
                  )
                })}
              </CardContent>
            </Card>
          </div>

          {/* Main Content */}
          <div className="lg:col-span-3">
            <Card>
              <CardHeader>
                <div className="flex items-center gap-3">
                  <div className={`p-3 rounded-xl bg-gradient-to-r ${currentStepData.color}`}>
                    <currentStepData.icon className="h-6 w-6 text-white" />
                  </div>
                  <div>
                    <CardTitle className="text-2xl">{currentStepData.title}</CardTitle>
                    <CardDescription className="text-base">{currentStepData.description}</CardDescription>
                  </div>
                </div>
              </CardHeader>
              <CardContent>
                {isLoading && (
                  <div className="flex items-center justify-center py-8">
                    <div className="w-8 h-8 border-4 border-blue-500 border-t-transparent rounded-full animate-spin"></div>
                    <span className="ml-3 text-gray-600">Processing...</span>
                  </div>
                )}
                <CurrentComponent {...getComponentProps()} />
              </CardContent>
            </Card>

            {/* Navigation Footer */}
            <div className="flex items-center justify-between mt-6">
              <Button
                onClick={handlePrevious}
                variant="outline"
                disabled={currentStep === 0}
                className="flex items-center gap-2 bg-transparent"
              >
                <ArrowLeft className="h-4 w-4" />
                Previous
              </Button>

              <div className="flex items-center gap-2">
                {steps.map((_, index) => (
                  <div
                    key={index}
                    className={`w-2 h-2 rounded-full transition-colors ${
                      index === currentStep
                        ? "bg-blue-500"
                        : completedSteps.includes(index)
                          ? "bg-green-500"
                          : "bg-gray-300"
                    }`}
                  />
                ))}
              </div>

              <Button
                onClick={handleNext}
                disabled={currentStep === steps.length - 1 ? false : !canProceed}
                className="flex items-center gap-2 bg-gradient-to-r from-blue-500 to-purple-500 hover:from-blue-600 hover:to-purple-600"
              >
                {currentStep === steps.length - 1 ? "Complete" : "Next"}
                <ArrowRight className="h-4 w-4" />
              </Button>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}