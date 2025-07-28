"use client"

import type React from "react"

import { useState } from "react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Database, Shield, Sparkles, ArrowLeft, Home } from "lucide-react"

interface LoginFormProps {
  onLogin: () => void
  onBack?: () => void
  canGoBack?: boolean
}

export function LoginForm({ onLogin, onBack, canGoBack }: LoginFormProps) {
  const [credentials, setCredentials] = useState({
    username: "",
    password: "",
  })
  const [isLoading, setIsLoading] = useState(false)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (credentials.username && credentials.password) {
      setIsLoading(true)
      // Simulate authentication
      setTimeout(() => {
        setIsLoading(false)
        onLogin()
      }, 1500)
    }
  }

  return (
    <div className="w-full max-w-md relative z-10">
      {/* Navigation Header */}
      <div className="flex items-center justify-between mb-6">
        {canGoBack && onBack ? (
          <Button
            onClick={onBack}
            variant="outline"
            size="sm"
            className="bg-white/80 backdrop-blur-sm border-violet-200 hover:bg-violet-50"
          >
            <ArrowLeft className="mr-2 h-4 w-4" />
            Back
          </Button>
        ) : (
          <Button
            onClick={onBack}
            variant="outline"
            size="sm"
            className="bg-white/80 backdrop-blur-sm border-violet-200 hover:bg-violet-50"
          >
            <Home className="mr-2 h-4 w-4" />
            Home
          </Button>
        )}
        <div className="text-center">
          <p className="text-sm text-violet-600 font-medium">Step 1 of 3</p>
        </div>
        <div className="w-16"></div> {/* Spacer */}
      </div>

      <Card className="backdrop-blur-sm bg-white/90 shadow-2xl border-0">
        <CardHeader className="text-center pb-8">
          <div className="mx-auto mb-6 relative">
            <div className="w-16 h-16 bg-gradient-to-r from-violet-500 to-blue-500 rounded-2xl flex items-center justify-center shadow-lg">
              <Database className="h-8 w-8 text-white" />
            </div>
            <div className="absolute -top-1 -right-1 w-6 h-6 bg-gradient-to-r from-pink-400 to-violet-400 rounded-full flex items-center justify-center">
              <Sparkles className="w-3 h-3 text-white" />
            </div>
          </div>
          <CardTitle className="text-3xl font-bold bg-gradient-to-r from-violet-600 to-blue-600 bg-clip-text text-transparent">
            Data Quality Pipeline
          </CardTitle>
          <CardDescription className="text-gray-600 mt-2">AI-powered data quality management system</CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-6">
            <div className="space-y-2">
              <Label htmlFor="username" className="text-gray-700 font-medium">
                Username
              </Label>
              <Input
                id="username"
                type="text"
                placeholder="Enter your username"
                value={credentials.username}
                onChange={(e) => setCredentials((prev) => ({ ...prev, username: e.target.value }))}
                className="border-violet-200 focus:border-violet-400 focus:ring-violet-400"
                required
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="password" className="text-gray-700 font-medium">
                Password
              </Label>
              <Input
                id="password"
                type="password"
                placeholder="Enter your password"
                value={credentials.password}
                onChange={(e) => setCredentials((prev) => ({ ...prev, password: e.target.value }))}
                className="border-violet-200 focus:border-violet-400 focus:ring-violet-400"
                required
              />
            </div>
            <Button
              type="submit"
              className="w-full bg-gradient-to-r from-violet-500 to-blue-500 hover:from-violet-600 hover:to-blue-600 text-white font-semibold py-3 rounded-lg shadow-lg transition-all duration-300 hover:scale-105"
              disabled={isLoading}
            >
              {isLoading ? (
                <div className="flex items-center gap-2">
                  <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                  Signing In...
                </div>
              ) : (
                <>
                  <Shield className="mr-2 h-4 w-4" />
                  Sign In & Continue
                </>
              )}
            </Button>
          </form>
        </CardContent>
      </Card>
    </div>
  )
}
