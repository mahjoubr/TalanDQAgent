"use client"

import { useState, useEffect } from "react"
import { Badge } from "@/components/ui/badge"
import { CheckCircle, XCircle, AlertCircle } from "lucide-react"

export function BackendStatus() {
  const [status, setStatus] = useState<"checking" | "connected" | "disconnected" | "mock">("checking")

  useEffect(() => {
    checkBackendStatus()
  }, [])

  const checkBackendStatus = async () => {
    try {
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}/health`, {
        method: "GET",
        timeout: 5000,
      })

      if (response.ok) {
        setStatus("connected")
      } else {
        setStatus("disconnected")
      }
    } catch (error) {
      // In development, show mock status
      if (process.env.NODE_ENV === "development") {
        setStatus("mock")
      } else {
        setStatus("disconnected")
      }
    }
  }

  const getStatusConfig = () => {
    switch (status) {
      case "connected":
        return {
          icon: CheckCircle,
          text: "Backend Connected",
          className: "bg-green-100 text-green-800 border-green-200",
        }
      case "mock":
        return {
          icon: AlertCircle,
          text: "Using Mock Data",
          className: "bg-yellow-100 text-yellow-800 border-yellow-200",
        }
      case "disconnected":
        return {
          icon: XCircle,
          text: "Backend Offline",
          className: "bg-red-100 text-red-800 border-red-200",
        }
      default:
        return {
          icon: AlertCircle,
          text: "Checking...",
          className: "bg-gray-100 text-gray-800 border-gray-200",
        }
    }
  }

  const config = getStatusConfig()
  const Icon = config.icon

  return (
    <Badge className={`${config.className} border flex items-center gap-1`}>
      <Icon className="h-3 w-3" />
      {config.text}
    </Badge>
  )
}
