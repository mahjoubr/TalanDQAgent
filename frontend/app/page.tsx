"use client"

import { NavigationProvider, useNavigation } from "@/components/navigation-provider"
import { WelcomeScreen } from "@/components/welcome-screen"
import { AuthPage } from "@/components/auth-page"
import { GuidedFlow } from "@/components/guided-flow"
import { ThemeProvider } from "@/components/theme-provider"

function AppContent() {
  const { currentView, navigateTo, goBack, userData, setUserData } = useNavigation()

  const handleAuthSuccess = (authData: any) => {
    setUserData(authData)
    navigateTo("guided")
  }

  const handleGuidedComplete = () => {
    // Return to welcome screen after guided setup completion
    navigateTo("welcome")
  }

  switch (currentView) {
    case "welcome":
      return <WelcomeScreen onGetStarted={() => navigateTo("auth")} />

    case "auth":
      return <AuthPage onBack={goBack} onAuthSuccess={handleAuthSuccess} />

    case "guided":
      return (
        <GuidedFlow
          onBack={goBack}
          onComplete={handleGuidedComplete}
          userData={userData}
        />
      )

    default:
      return <WelcomeScreen onGetStarted={() => navigateTo("auth")} />
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
