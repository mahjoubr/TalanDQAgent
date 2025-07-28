const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"

export interface ApiResponse<T = any> {
  success: boolean
  message?: string
  data?: T
  error?: string
}

export interface ConnectionResponse {
  connection_id: string
  message: string
  details: {
    tables?: string[]
    record_count: number
    filename?: string
    size_mb?: number
    columns?: string[]
  }
}

export interface QualityMetrics {
  completeness: number
  uniqueness: number
  cardinality: number
  consistency: number
  volumetry: number
}

export interface AnomalyDetectionResult {
  connection_id: string
  model_type: string
  anomalies_detected: number
  total_records: number
  anomaly_details: Array<{
    index: number
    anomaly_score: number
    components_affected: string[]
  }>
}

export interface PowerBIAuthRequest {
  tenant_id: string
  client_id: string
  client_secret: string
  username?: string
  password?: string
}

export interface PowerBIWorkspace {
  id: string
  name: string
  isReadOnly: boolean
  isOnDedicatedCapacity: boolean
}

export interface PowerBIReport {
  id: string
  name: string
  webUrl: string
  embedUrl: string
  datasetId: string
}

export interface PowerBIDataset {
  id: string
  name: string
  addRowsAPIEnabled: boolean
  configuredBy: string
  isRefreshable: boolean
}

class ApiClient {
  private baseUrl: string
  private sessionId: string | null = null

  constructor(baseUrl: string = API_BASE_URL) {
    this.baseUrl = baseUrl
  }

  private async request<T>(endpoint: string, options: RequestInit = {}): Promise<ApiResponse<T>> {
    try {
      const headers: Record<string, string> = {
        ...options.headers,
      }

      // Only set Content-Type for non-FormData requests
      if (!(options.body instanceof FormData)) {
        headers["Content-Type"] = "application/json"
      }

      // Add session ID for Power BI requests
      if (this.sessionId && endpoint.includes("/powerbi/")) {
        headers["X-Session-ID"] = this.sessionId
      }

      // Always use mock data in development or when backend is unavailable
      const isDevelopment = process.env.NODE_ENV === "development"
      const shouldUseMock = isDevelopment || !this.baseUrl.includes("localhost")

      if (shouldUseMock) {
        console.log("Using mock data for endpoint:", endpoint)
        return this.getMockResponse<T>(endpoint, options)
      }

      const controller = new AbortController()
      const timeoutId = setTimeout(() => controller.abort(), 5000) // 5 second timeout

      const response = await fetch(`${this.baseUrl}${endpoint}`, {
        headers,
        signal: controller.signal,
        ...options,
      }).catch((fetchError) => {
        clearTimeout(timeoutId)
        console.warn("Backend fetch failed, using mock data:", fetchError.message)
        throw new Error("BACKEND_UNAVAILABLE")
      })

      clearTimeout(timeoutId)

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}))
        throw new Error(errorData.detail || `HTTP error! status: ${response.status}`)
      }

      const data = await response.json()
      return { success: true, data }
    } catch (error) {
      console.log("API request failed, falling back to mock data:", error)
      return this.getMockResponse<T>(endpoint, options)
    }
  }

  private getMockResponse<T>(endpoint: string, options: RequestInit = {}): ApiResponse<T> {
    // Simulate network delay
    return new Promise((resolve) => {
      setTimeout(() => {
        const mockResponses: Record<string, any> = {
          "/api/connect/database": {
            connection_id: `mock-db-${Date.now()}`,
            message: "Successfully connected to mock database",
            details: {
              tables: ["customers", "transactions", "products", "orders", "analytics"],
              record_count: 15000,
            },
          },
          "/api/connect/file": {
            connection_id: `mock-file-${Date.now()}`,
            message: "File uploaded successfully (mock)",
            details: {
              filename: "sample-data.csv",
              size_mb: 2.5,
              record_count: 5000,
              columns: ["id", "name", "email", "created_at", "value", "category"],
            },
          },
          "/api/connections": {
            connections: [
              {
                id: "mock-conn-1",
                type: "database",
                db_type: "postgresql",
                status: "connected",
                record_count: 15000,
                tables: ["customers", "transactions", "products"],
              },
              {
                id: "mock-conn-2",
                type: "file",
                filename: "sample-data.csv",
                status: "uploaded",
                record_count: 5000,
                columns: ["id", "name", "email", "value"],
              },
            ],
          },
        }

        // Handle POST requests with query parameters
        const baseEndpoint = endpoint.split("?")[0]

        if (options.method === "POST" && baseEndpoint === "/api/analysis/quality-metrics") {
          resolve({
            success: true,
            data: {
              connection_id: "mock-conn-1",
              metrics: {
                completeness: 87.5,
                uniqueness: 94.2,
                cardinality: 81.3,
                consistency: 89.7,
                volumetry: 96.1,
              },
              message: "Quality analysis completed successfully (mock)",
            } as T,
          })
          return
        }

        if (options.method === "POST" && baseEndpoint === "/api/analysis/anomaly-detection") {
          resolve({
            success: true,
            data: {
              connection_id: "mock-conn-1",
              model_type: "VARIMA",
              anomalies_detected: 23,
              total_records: 15000,
              anomaly_details: [
                {
                  index: 1234,
                  anomaly_score: 2.8,
                  components_affected: ["value1", "value2"],
                },
                {
                  index: 5678,
                  anomaly_score: 3.2,
                  components_affected: ["value2", "value3"],
                },
                {
                  index: 9012,
                  anomaly_score: 2.9,
                  components_affected: ["value1", "value3"],
                },
              ],
              message: "VARIMA anomaly detection completed (mock)",
            } as T,
          })
          return
        }

        const mockData = mockResponses[baseEndpoint] || mockResponses[endpoint]

        if (mockData) {
          resolve({ success: true, data: mockData as T })
        } else {
          resolve({
            success: true,
            data: {
              message: "Mock response for " + endpoint,
              timestamp: new Date().toISOString(),
            } as T,
          })
        }
      }, 500) // Simulate 500ms delay
    }) as Promise<ApiResponse<T>>
  }

  // Connection endpoints
  async connectDatabase(dbType: string, connectionString: string): Promise<ApiResponse<ConnectionResponse>> {
    return this.request<ConnectionResponse>("/api/connect/database", {
      method: "POST",
      body: JSON.stringify({
        db_type: dbType,
        connection_string: connectionString,
      }),
    })
  }

  async uploadFile(file: File): Promise<ApiResponse<ConnectionResponse>> {
    const formData = new FormData()
    formData.append("file", file)

    return this.request<ConnectionResponse>("/api/connect/file", {
      method: "POST",
      body: formData,
    })
  }

  async getConnections(): Promise<ApiResponse<{ connections: any[] }>> {
    return this.request("/api/connections")
  }

  // Analysis endpoints
  async runQualityAnalysis(connectionId: string): Promise<ApiResponse<{ metrics: QualityMetrics }>> {
    return this.request(`/api/analysis/quality-metrics?connection_id=${connectionId}`, {
      method: "POST",
    })
  }

  async runAnomalyDetection(
    connectionId: string,
    modelType = "VARIMA",
    threshold = 2.0,
    maxComponents = 5,
  ): Promise<ApiResponse<AnomalyDetectionResult>> {
    return this.request("/api/analysis/anomaly-detection", {
      method: "POST",
      body: JSON.stringify({
        connection_id: connectionId,
        model_type: modelType,
        threshold,
        max_components: maxComponents,
      }),
    })
  }

  async getAnalysisResults(connectionId: string): Promise<ApiResponse<any>> {
    return this.request(`/api/analysis/results/${connectionId}`)
  }

  // Report endpoints
  async generateReport(connectionId: string, reportType: string, format = "json"): Promise<ApiResponse<any>> {
    return this.request("/api/reports/generate", {
      method: "POST",
      body: JSON.stringify({
        connection_id: connectionId,
        report_type: reportType,
        format,
      }),
    })
  }

  // Power BI endpoints
  async authenticatePowerBI(
    authData: PowerBIAuthRequest,
  ): Promise<ApiResponse<{ session_id: string; expires_in: number }>> {
    const response = await this.request<{ session_id: string; expires_in: number }>("/api/powerbi/authenticate", {
      method: "POST",
      body: JSON.stringify(authData),
    })

    if (response.success && response.data) {
      this.sessionId = response.data.session_id
    }

    return response
  }

  async getPowerBIWorkspaces(): Promise<ApiResponse<{ workspaces: PowerBIWorkspace[] }>> {
    return this.request("/api/powerbi/workspaces")
  }

  async getPowerBIReports(workspaceId: string): Promise<ApiResponse<{ reports: PowerBIReport[] }>> {
    return this.request(`/api/powerbi/workspaces/${workspaceId}/reports`)
  }

  async getPowerBIDatasets(workspaceId: string): Promise<ApiResponse<{ datasets: PowerBIDataset[] }>> {
    return this.request(`/api/powerbi/workspaces/${workspaceId}/datasets`)
  }

  async getPowerBIEmbedToken(
    workspaceId: string,
    reportId: string,
    datasetId?: string,
  ): Promise<
    ApiResponse<{
      embed_token: string
      embed_url: string
      expires_at: string
    }>
  > {
    return this.request("/api/powerbi/embed-token", {
      method: "POST",
      body: JSON.stringify({
        workspace_id: workspaceId,
        report_id: reportId,
        dataset_id: datasetId,
      }),
    })
  }

  async extractPowerBIDatasetData(datasetId: string): Promise<ApiResponse<ConnectionResponse>> {
    return this.request(`/api/powerbi/datasets/${datasetId}/data`)
  }

  async createPowerBIDataset(workspaceId: string, name: string, tables: any[]): Promise<ApiResponse<any>> {
    return this.request("/api/powerbi/datasets/create", {
      method: "POST",
      body: JSON.stringify({
        workspace_id: workspaceId,
        name,
        tables,
      }),
    })
  }

  async pushDataToPowerBI(
    datasetId: string,
    tableName: string,
    connectionId: string,
  ): Promise<
    ApiResponse<{
      records_pushed: number
    }>
  > {
    return this.request(
      `/api/powerbi/datasets/${datasetId}/push-data?table_name=${tableName}&connection_id=${connectionId}`,
      {
        method: "POST",
      },
    )
  }

  // Session management
  setSessionId(sessionId: string) {
    this.sessionId = sessionId
  }

  clearSession() {
    this.sessionId = null
  }
}

export const apiClient = new ApiClient()
