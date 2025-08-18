"use client"

import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { BarChart3, Database, Activity, Zap, Shield, Clock, ArrowRight } from "lucide-react"

interface WelcomeScreenProps {
  onGetStarted: () => void
}

export function WelcomeScreen({ onGetStarted }: WelcomeScreenProps) {
  const features = [
    {
      icon: Database,
      title: "Multi-Source Connectivity",
      description: "Connect to Power BI, databases, and file uploads seamlessly",
      gradient: "from-blue-500 to-cyan-500",
    },
    {
      icon: BarChart3,
      title: "Advanced Analytics",
      description: "5-dimensional quality metrics with real-time insights",
      gradient: "from-violet-500 to-purple-500",
    },
    {
      icon: Activity,
      title: "AI-Powered Detection",
      description: "VARIMA models for multivariate anomaly detection",
      gradient: "from-pink-500 to-rose-500",
    },
  ]

  const benefits = [
    { icon: Zap, text: "Lightning-fast analysis", color: "text-yellow-600" },
    { icon: Shield, text: "Enterprise-grade security", color: "text-green-600" },
    { icon: Clock, text: "Real-time monitoring", color: "text-blue-600" },
  ]

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-purple-50 to-cyan-50 flex items-center justify-center p-4">
      <div className="max-w-6xl mx-auto space-y-12">
        {/* Hero Section */}
        <div className="text-center space-y-6">
          <div className="flex justify-center mb-6">
            <div className="p-4 bg-gradient-to-r from-blue-500 to-purple-500 rounded-2xl shadow-2xl">
              <BarChart3 className="h-16 w-16 text-white" />
            </div>
          </div>

          <h1 className="text-6xl font-bold bg-gradient-to-r from-blue-600 via-purple-600 to-cyan-600 bg-clip-text text-transparent leading-tight">
            Data Quality Agent Setup
          </h1>

          <p className="text-xl text-gray-600 max-w-3xl mx-auto leading-relaxed">
            Transform your data quality management with AI-powered analytics, real-time monitoring, and seamless Power
            BI integration. Experience enterprise-grade data insights like never before.
          </p>

          <div className="flex items-center justify-center gap-4 flex-wrap">
            {benefits.map((benefit, index) => (
              <div
                key={index}
                className="flex items-center gap-2 bg-white/80 backdrop-blur-sm px-4 py-2 rounded-full shadow-lg"
              >
                <benefit.icon className={`h-5 w-5 ${benefit.color}`} />
                <span className="text-sm font-medium text-gray-700">{benefit.text}</span>
              </div>
            ))}
          </div>
        </div>

        {/* Features Grid */}
        <div className="grid gap-8 md:grid-cols-2 lg:grid-cols-3">
          {features.map((feature, index) => (
            <Card
              key={index}
              className="border-0 shadow-xl hover:shadow-2xl transition-all duration-300 hover:scale-105 bg-white/80 backdrop-blur-sm"
            >
              <div className={`h-2 bg-gradient-to-r ${feature.gradient} rounded-t-lg`}></div>
              <CardHeader className="text-center pb-4">
                <div className={`w-16 h-16 mx-auto mb-4 p-3 bg-gradient-to-r ${feature.gradient} rounded-xl shadow-lg`}>
                  <feature.icon className="h-10 w-10 text-white" />
                </div>
                <CardTitle className="text-lg font-bold text-gray-800">{feature.title}</CardTitle>
              </CardHeader>
              <CardContent>
                <CardDescription className="text-center text-gray-600 leading-relaxed">
                  {feature.description}
                </CardDescription>
              </CardContent>
            </Card>
          ))}
        </div>

        {/* CTA Section */}
        <div className="text-center space-y-8">
          <Card className="border-0 shadow-2xl bg-gradient-to-r from-blue-500 via-purple-500 to-cyan-500 text-white max-w-4xl mx-auto">
            <CardContent className="p-8">
              <h2 className="text-3xl font-bold mb-4">Ready to Transform Your Data Quality?</h2>
              

              <div className="flex flex-col sm:flex-row gap-4 justify-center items-center">
                <Button
                  onClick={onGetStarted}
                  size="lg"
                  className="bg-white text-blue-600 hover:bg-blue-50 font-semibold px-8 py-4 text-lg shadow-xl hover:shadow-2xl transition-all duration-300"
                >
                  <Zap className="mr-2 h-5 w-5" />
                  Start Guided Setup
                  <ArrowRight className="ml-2 h-5 w-5" />
                </Button>

            
              </div>
            </CardContent>
          </Card>

      

          
        </div>
      </div>
    </div>
  )
}
