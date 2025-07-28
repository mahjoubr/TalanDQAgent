"use client"

import { NavigationProvider, useNavigation } from "@/components/navigation-provider"
import { WelcomeScreen } from "@/components/welcome-screen"
import { AuthPage } from "@/components/auth-page"
import { GuidedFlow } from "@/components/guided-flow"
import { DashboardPage } from "@/components/dashboard-page"
import { ThemeProvider } from "@/components/theme-provider"

function AppContent() {
  const { currentView, navigateTo, goBack, userData, setUserData } = useNavigation()

  const handleAuthSuccess = (authData: any) => {
    setUserData(authData)
    navigateTo("guided")
  }

  const handleGuidedComplete = () => {
    navigateTo("dashboard")
  }

  switch (currentView) {
    case "welcome":
      return <WelcomeScreen onGetStarted={() => navigateTo("auth")} onViewDashboard={() => navigateTo("dashboard")} />

    case "auth":
      return <AuthPage onBack={goBack} onAuthSuccess={handleAuthSuccess} />

    case "guided":
      return (
        <GuidedFlow
          onBack={goBack}
          onComplete={handleGuidedComplete}
          onViewDashboard={() => navigateTo("dashboard")}
          userData={userData}
        />
      )

    case "dashboard":
      return <DashboardPage onBack={goBack} userData={userData} />

    default:
      return <WelcomeScreen onGetStarted={() => navigateTo("auth")} onViewDashboard={() => navigateTo("dashboard")} />
  }
}

export default function Page() {
  return (
    <ThemeProvider>
      <NavigationProvider>
        <AppContent />
      </NavigationProvider>
    </ThemeProvider>
  )
}
