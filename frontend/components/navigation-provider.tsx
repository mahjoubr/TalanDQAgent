"use client"

import { createContext, useContext, useState, type ReactNode } from "react"
import { Toaster } from "@/components/ui/toaster"
import { DevelopmentBanner } from "@/components/development-banner"

type ViewType = "welcome" | "auth" | "guided" | "dashboard"

interface NavigationContextType {
  currentView: ViewType
  navigationHistory: ViewType[]
  userData: any
  navigateTo: (view: ViewType) => void
  goBack: () => void
  setUserData: (data: any) => void
}

const NavigationContext = createContext<NavigationContextType | undefined>(undefined)

export function useNavigation() {
  const context = useContext(NavigationContext)
  if (!context) {
    throw new Error("useNavigation must be used within a NavigationProvider")
  }
  return context
}

interface NavigationProviderProps {
  children: ReactNode
}

export function NavigationProvider({ children }: NavigationProviderProps) {
  const [currentView, setCurrentView] = useState<ViewType>("welcome")
  const [navigationHistory, setNavigationHistory] = useState<ViewType[]>(["welcome"])
  const [userData, setUserData] = useState<any>(null)

  const navigateTo = (view: ViewType) => {
    setNavigationHistory((prev) => [...prev, view])
    setCurrentView(view)
  }

  const goBack = () => {
    if (navigationHistory.length > 1) {
      const newHistory = [...navigationHistory]
      newHistory.pop() // Remove current view
      const previousView = newHistory[newHistory.length - 1]
      setNavigationHistory(newHistory)
      setCurrentView(previousView)
    } else {
      // Fallback to welcome if no history
      setCurrentView("welcome")
      setNavigationHistory(["welcome"])
    }
  }

  const contextValue: NavigationContextType = {
    currentView,
    navigationHistory,
    userData,
    navigateTo,
    goBack,
    setUserData,
  }

  return (
    <NavigationContext.Provider value={contextValue}>
      <div className="min-h-screen">
        <DevelopmentBanner />
        {children}
        <Toaster />
      </div>
    </NavigationContext.Provider>
  )
}
