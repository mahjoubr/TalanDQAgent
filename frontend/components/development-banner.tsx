"use client"

import { Alert, AlertDescription } from "@/components/ui/alert"
import { AlertTriangle } from "lucide-react"

export function DevelopmentBanner() {
  if (process.env.NODE_ENV !== "development") {
    return null
  }

  return (
    <Alert className="border-yellow-200 bg-yellow-50 text-yellow-800 mb-4">
      <AlertTriangle className="h-4 w-4" />
      <AlertDescription>
        <strong>Development Mode:</strong> Backend service not detected. Using mock data for demonstration purposes. All
        features are fully functional with sample data.
      </AlertDescription>
    </Alert>
  )
}
