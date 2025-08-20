"use client"

import { useState, useEffect } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Badge } from "@/components/ui/badge"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { BarChart3, ExternalLink, CheckCircle, Loader2, Database, Upload, Eye } from "lucide-react"
import { useToast } from "@/hooks/use-toast"
import { apiClient, type PowerBIWorkspace, type PowerBIReport, type PowerBIDataset } from "@/lib/api"

interface PowerBIEmbedProps {
  onDataConnected?: (data: any) => void
}

export function PowerBIEmbed({ onDataConnected }: PowerBIEmbedProps) {
  const [authConfig, setAuthConfig] = useState({
    tenantId: "",
    clientId: "",
    clientSecret: "",
    username: "",
    password: "",
  })
  const [isAuthenticated, setIsAuthenticated] = useState(false)
  const [isLoading, setIsLoading] = useState(false)
  const [workspaces, setWorkspaces] = useState<PowerBIWorkspace[]>([])
  const [reports, setReports] = useState<PowerBIReport[]>([])
  const [datasets, setDatasets] = useState<PowerBIDataset[]>([])
  const [selectedWorkspace, setSelectedWorkspace] = useState("")
  const [selectedReport, setSelectedReport] = useState("")
  const [selectedDataset, setSelectedDataset] = useState("")
  const [embedToken, setEmbedToken] = useState("")
  const [embedUrl, setEmbedUrl] = useState("")
  const { toast } = useToast()

  const authenticatePowerBI = async () => {
    setIsLoading(true)
    try {
      const response = await apiClient.authenticatePowerBI({
        tenant_id: authConfig.tenantId,
        client_id: authConfig.clientId,
        client_secret: authConfig.clientSecret,
        username: authConfig.username || undefined,
        password: authConfig.password || undefined,
      })

      if (response.success) {
        setIsAuthenticated(true)
        toast({
          title: "Authentication Successful",
          description: "Connected to Power BI successfully",
        })
        await loadWorkspaces()
      } else {
        throw new Error(response.error || "Authentication failed")
      }
    } catch (error) {
      toast({
        title: "Authentication Failed",
        description: error instanceof Error ? error.message : "Please check your credentials",
        variant: "destructive",
      })
    } finally {
      setIsLoading(false)
    }
  }

  const loadWorkspaces = async () => {
    try {
      const response = await apiClient.getPowerBIWorkspaces()
      if (response.success && response.data) {
        setWorkspaces(response.data.workspaces)
      }
    } catch (error) {
      toast({
        title: "Failed to load workspaces",
        description: "Could not fetch Power BI workspaces",
        variant: "destructive",
      })
    }
  }

  const loadReports = async (workspaceId: string) => {
    try {
      const response = await apiClient.getPowerBIReports(workspaceId)
      if (response.success && response.data) {
        setReports(response.data.reports)
      }
    } catch (error) {
      toast({
        title: "Failed to load reports",
        description: "Could not fetch reports for this workspace",
        variant: "destructive",
      })
    }
  }

  const loadDatasets = async (workspaceId: string) => {
    try {
      const response = await apiClient.getPowerBIDatasets(workspaceId)
      if (response.success && response.data) {
        setDatasets(response.data.datasets)
      }
    } catch (error) {
      toast({
        title: "Failed to load datasets",
        description: "Could not fetch datasets for this workspace",
        variant: "destructive",
      })
    }
  }

  const handleWorkspaceChange = async (workspaceId: string) => {
    setSelectedWorkspace(workspaceId)
    setSelectedReport("")
    setSelectedDataset("")
    setReports([])
    setDatasets([])

    if (workspaceId) {
      await Promise.all([loadReports(workspaceId), loadDatasets(workspaceId)])
    }
  }

  const generateEmbedToken = async () => {
    if (!selectedWorkspace || !selectedReport) return

    setIsLoading(true)
    try {
      const response = await apiClient.getPowerBIEmbedToken(
        selectedWorkspace,
        selectedReport,
        selectedDataset || undefined,
      )

      if (response.success && response.data) {
        setEmbedToken(response.data.embed_token)
        setEmbedUrl(response.data.embed_url)
        toast({
          title: "Embed Token Generated",
          description: "Power BI report is ready to embed",
        })
      }
    } catch (error) {
      toast({
        title: "Failed to generate embed token",
        description: "Could not generate embed token for the report",
        variant: "destructive",
      })
    } finally {
      setIsLoading(false)
    }
  }

  const extractDatasetData = async () => {
    if (!selectedDataset) return

    setIsLoading(true)
    try {
      const response = await apiClient.extractPowerBIDatasetData(selectedDataset)

      if (response.success && response.data) {
        toast({
          title: "Data Extracted Successfully",
          description: `Extracted ${response.data.details.record_count} records for analysis`,
        })

        if (onDataConnected) {
          onDataConnected({
            connection_id: response.data.connection_id,
            type: "powerbi_dataset",
            details: response.data.details,
          })
        }
      }
    } catch (error) {
      toast({
        title: "Failed to extract data",
        description: "Could not extract data from the dataset",
        variant: "destructive",
      })
    } finally {
      setIsLoading(false)
    }
  }

  // Power BI embed script
  useEffect(() => {
    if (embedToken && embedUrl) {
      const script = document.createElement("script")
      script.src = "https://cdn.jsdelivr.net/npm/powerbi-client@2.22.0/dist/powerbi.min.js"
      script.onload = () => {
        // Power BI embed logic would go here
      }
      document.head.appendChild(script)

      return () => {
        document.head.removeChild(script)
      }
    }
  }, [embedToken, embedUrl])

  return (
    <Card className="border-0 shadow-lg">
      <CardHeader>
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-gradient-to-r from-yellow-500 to-orange-500 rounded-lg">
              <BarChart3 className="h-5 w-5 text-white" />
            </div>
            <div>
              <CardTitle className="text-xl">Power BI Integration</CardTitle>
              <CardDescription>Connect to your Power BI dashboards and reports</CardDescription>
            </div>
          </div>
          <div className="flex items-center gap-2">
            {isAuthenticated && (
              <Badge className="bg-gradient-to-r from-green-500 to-emerald-500 text-white">
                <CheckCircle className="h-3 w-3 mr-1" />
                Connected
              </Badge>
            )}
          </div>
        </div>
      </CardHeader>
      <CardContent>
        <Tabs defaultValue="auth" className="space-y-6">
          <TabsList className="grid w-full grid-cols-4">
            <TabsTrigger value="auth">Authentication</TabsTrigger>
            <TabsTrigger value="browse" disabled={!isAuthenticated}>
              Browse
            </TabsTrigger>
            <TabsTrigger value="embed" disabled={!embedToken}>
              Embedded View
            </TabsTrigger>
            <TabsTrigger value="data" disabled={!isAuthenticated}>
              Extract Data
            </TabsTrigger>
          </TabsList>

          <TabsContent value="auth">
            <div className="space-y-4">
              <div className="grid gap-4 md:grid-cols-2">
                <div className="space-y-2">
                  <Label htmlFor="tenant-id">Tenant ID</Label>
                  <Input
                    id="tenant-id"
                    placeholder="Enter Azure AD Tenant ID"
                    value={authConfig.tenantId}
                    onChange={(e) => setAuthConfig((prev) => ({ ...prev, tenantId: e.target.value }))}
                    className="border-yellow-200 focus:border-yellow-400"
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="client-id">Client ID</Label>
                  <Input
                    id="client-id"
                    placeholder="Enter Application Client ID"
                    value={authConfig.clientId}
                    onChange={(e) => setAuthConfig((prev) => ({ ...prev, clientId: e.target.value }))}
                    className="border-yellow-200 focus:border-yellow-400"
                  />
                </div>
              </div>
              <div className="space-y-2">
                <Label htmlFor="client-secret">Client Secret</Label>
                <Input
                  id="client-secret"
                  type="password"
                  placeholder="Enter Application Client Secret"
                  value={authConfig.clientSecret}
                  onChange={(e) => setAuthConfig((prev) => ({ ...prev, clientSecret: e.target.value }))}
                  className="border-yellow-200 focus:border-yellow-400"
                />
              </div>
              <div className="grid gap-4 md:grid-cols-2">
                <div className="space-y-2">
                  <Label htmlFor="username">Username (Optional)</Label>
                  <Input
                    id="username"
                    placeholder="Power BI Username"
                    value={authConfig.username}
                    onChange={(e) => setAuthConfig((prev) => ({ ...prev, username: e.target.value }))}
                    className="border-yellow-200 focus:border-yellow-400"
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="password">Password (Optional)</Label>
                  <Input
                    id="password"
                    type="password"
                    placeholder="Power BI Password"
                    value={authConfig.password}
                    onChange={(e) => setAuthConfig((prev) => ({ ...prev, password: e.target.value }))}
                    className="border-yellow-200 focus:border-yellow-400"
                  />
                </div>
              </div>
              <Button
                onClick={authenticatePowerBI}
                disabled={isLoading || !authConfig.tenantId || !authConfig.clientId || !authConfig.clientSecret}
                className="w-full bg-gradient-to-r from-yellow-500 to-orange-500 hover:from-yellow-600 hover:to-orange-600 text-white"
              >
                {isLoading ? (
                  <div className="flex items-center gap-2">
                    <Loader2 className="h-4 w-4 animate-spin" />
                    Authenticating...
                  </div>
                ) : (
                  <>
                    <ExternalLink className="mr-2 h-4 w-4" />
                    Connect to Power BI
                  </>
                )}
              </Button>
            </div>
          </TabsContent>

          <TabsContent value="browse">
            <div className="space-y-4">
              <div className="space-y-2">
                <Label>Select Workspace</Label>
                <Select value={selectedWorkspace} onValueChange={handleWorkspaceChange}>
                  <SelectTrigger>
                    <SelectValue placeholder="Choose a workspace" />
                  </SelectTrigger>
                  <SelectContent>
                    {workspaces.map((workspace) => (
                      <SelectItem key={workspace.id} value={workspace.id}>
                        {workspace.name}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              {selectedWorkspace && (
                <div className="grid gap-4 md:grid-cols-2">
                  <div className="space-y-2">
                    <Label>Select Report</Label>
                    <Select value={selectedReport} onValueChange={setSelectedReport}>
                      <SelectTrigger>
                        <SelectValue placeholder="Choose a report" />
                      </SelectTrigger>
                      <SelectContent>
                        {reports.map((report) => (
                          <SelectItem key={report.id} value={report.id}>
                            {report.name}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>

                  <div className="space-y-2">
                    <Label>Select Dataset (Optional)</Label>
                    <Select value={selectedDataset} onValueChange={setSelectedDataset}>
                      <SelectTrigger>
                        <SelectValue placeholder="Choose a dataset" />
                      </SelectTrigger>
                      <SelectContent>
                        {datasets.map((dataset) => (
                          <SelectItem key={dataset.id} value={dataset.id}>
                            {dataset.name}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                </div>
              )}

              {selectedReport && (
                <Button
                  onClick={generateEmbedToken}
                  disabled={isLoading}
                  className="w-full bg-gradient-to-r from-violet-500 to-purple-500 hover:from-violet-600 hover:to-purple-600 text-white"
                >
                  {isLoading ? (
                    <div className="flex items-center gap-2">
                      <Loader2 className="h-4 w-4 animate-spin" />
                      Generating Token...
                    </div>
                  ) : (
                    <>
                      <Eye className="mr-2 h-4 w-4" />
                      Generate Embed Token
                    </>
                  )}
                </Button>
              )}
            </div>
          </TabsContent>

          <TabsContent value="embed">
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <h3 className="text-lg font-semibold">Embedded Power BI Report</h3>
                <Button
                  size="sm"
                  className="bg-gradient-to-r from-violet-500 to-purple-500 hover:from-violet-600 hover:to-purple-600 text-white"
                  onClick={() => window.open(embedUrl, "_blank")}
                >
                  <ExternalLink className="h-4 w-4 mr-1" />
                  Open in Power BI
                </Button>
              </div>
              <div className="w-full h-96 border rounded-lg bg-gray-50 flex items-center justify-center">
                <div className="text-center">
                  <BarChart3 className="h-12 w-12 text-gray-300 mx-auto mb-4" />
                  <p className="text-gray-500">Power BI report will be embedded here</p>
                  <p className="text-xs text-gray-400 mt-2">Embed URL: {embedUrl ? "Ready" : "Not generated"}</p>
                </div>
              </div>
            </div>
          </TabsContent>

          <TabsContent value="data">
            <div className="space-y-4">
              <div className="text-center">
                <Database className="h-12 w-12 text-blue-500 mx-auto mb-4" />
                <h3 className="text-lg font-semibold mb-2">Extract Dataset Data</h3>
                <p className="text-gray-600 mb-4">
                  Extract data from Power BI datasets for quality analysis and anomaly detection
                </p>
              </div>

              {selectedDataset && (
                <div className="p-4 bg-blue-50 rounded-lg">
                  <h4 className="font-medium text-blue-900 mb-2">Selected Dataset</h4>
                  <p className="text-blue-700">
                    {datasets.find((d) => d.id === selectedDataset)?.name || selectedDataset}
                  </p>
                </div>
              )}

              <Button
                onClick={extractDatasetData}
                disabled={!selectedDataset || isLoading}
                className="w-full bg-gradient-to-r from-blue-500 to-cyan-500 hover:from-blue-600 hover:to-cyan-600 text-white"
              >
                {isLoading ? (
                  <div className="flex items-center gap-2">
                    <Loader2 className="h-4 w-4 animate-spin" />
                    Extracting Data...
                  </div>
                ) : (
                  <>
                    <Upload className="mr-2 h-4 w-4" />
                    Extract Data for Analysis
                  </>
                )}
              </Button>
            </div>
          </TabsContent>
        </Tabs>
      </CardContent>
    </Card>
  )
}
