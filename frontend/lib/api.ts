const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"

export interface ApiResponse<T = any> {
  success: boolean
  message?: string
  data?: T
  error?: string
}
export interface DbStore {
  email: string
  connectionString: string
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

export interface DetailedQualityMetric {
  score: number
  issues: string[]
  recommendations: string[]
  trend?: string
}

export interface QualityAnalysisResult {
  metrics: QualityMetrics
  detailed_analysis: {
    completeness: DetailedQualityMetric & {
      total_missing: number
      missing_by_column: Record<string, number>
    }
    uniqueness: DetailedQualityMetric & {
      duplicate_rows: number
      uniqueness_by_column: Record<string, number>
    }
    cardinality: DetailedQualityMetric & {
      column_cardinalities: Record<string, number>
    }
    consistency: DetailedQualityMetric & {
      data_types: Record<string, string>
    }
    volumetry: DetailedQualityMetric & {
      total_rows: number
      total_columns: number
      data_size_mb: number
    }
  }
  sample_size: number
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

export interface DatabaseConnectionRequest {
  db_type: string
  connection_string: string
  username?: string
  password?: string
  host: string
  port?: number
  database_name: string
  additional_params?: Record<string, any>
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

  public get apiBaseUrl(): string {
    return this.baseUrl
  }

  private async request<T>(endpoint: string, options: RequestInit = {}): Promise<ApiResponse<T>> {
    try {
      //  Use of HeadersInit type which is more flexible
      const headers: HeadersInit = {
        ...options.headers,
      }

      // Only set Content-Type for non-FormData requests
      if (!(options.body instanceof FormData)) {
        (headers as Record<string, string>)["Content-Type"] = "application/json"
      }

      // Add session ID for Power BI requests
      if (this.sessionId && endpoint.includes("/powerbi/")) {
        (headers as Record<string, string>)["X-Session-ID"] = this.sessionId
      }

      // First, try to connect to the real backend
      const controller = new AbortController()
      const timeoutId = setTimeout(() => controller.abort(), 300000) // 5 minutes for VARIMA analysis

      try {
        const response = await fetch(`${this.baseUrl}${endpoint}`, {
          ...options,
          headers,
          signal: controller.signal,
        })

        clearTimeout(timeoutId)

        if (!response.ok) {
          const errorData = await response.json().catch(() => ({}))
          throw new Error(errorData.detail || `HTTP error! status: ${response.status}`)
        }

        const data = await response.json()
        console.log(" Backend connected successfully")
        return { success: true, data }
      } catch (fetchError) {
        clearTimeout(timeoutId)
        console.error(" Backend unavailable:", fetchError)
        return { success: false, error: "Backend unavailable", message: String(fetchError) }
      }
    } catch (error) {
      console.error("API request failed:", error)
      return { success: false, error: "API request failed", message: String(error) }
    }
  }

  // Connection endpoints
  async connectDatabase(data: DatabaseConnectionRequest): Promise<ApiResponse<ConnectionResponse>> {
    const connection = {
      db_type: data.db_type,
      connection_string: data.connection_string,
      username: data.username,
      password: data.password,
      host: data.host,
      port: data.port,
      database_name: data.database_name,
      additional_params: data.additional_params || {},
    }
    console.log(connection)
    return this.request<ConnectionResponse>("/api/connect/database", {
      method: "POST",
      body: JSON.stringify(connection),
    })
  }
  async storeConnectionString(email: string, connectionString: string): Promise<ApiResponse<DbStore>> {
    return this.request<DbStore>("/api/store/db-connection", {
      method: "POST",
      body: JSON.stringify({ email, connection_string: connectionString }),
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

  async getConnectionSample(connectionId: string, limit: number = 100, tableName?: string): Promise<ApiResponse<{
    connection_id: string
    filename?: string
    table_name?: string
    total_rows: number
    sample_rows: number
    columns: string[]
    sample_data: Record<string, any>[]
  }>> {
    const params = new URLSearchParams({ limit: limit.toString() })
    if (tableName) {
      params.append('table_name', tableName)
    }
    return this.request(`/api/connections/${connectionId}/sample?${params.toString()}`)
  }

  async getTableStatistics(connectionId: string): Promise<ApiResponse<{
    table_statistics: Record<string, {
      table_name: string
      row_count: number
      column_count: number
      columns: Array<{
        name: string
        data_type: string
        non_null_count: number
        sample_values: string[]
      }>
      sample_data: Record<string, any>[]
      error?: string
    }>
  }>> {
    return this.request(`/api/connections/${connectionId}/tables`)
  }

  async getAnalyzedTableStatistics(connectionId: string): Promise<ApiResponse<{
    table_statistics: Record<string, {
      table_name: string
      row_count: number
      column_count: number
      columns: Array<{
        name: string
        data_type: string
        non_null_count: number
        sample_values: string[]
      }>
      sample_data: Record<string, any>[]
      error?: string
    }>
    analyzed_tables: string[]
  }>> {
    return this.request(`/api/connections/${connectionId}/analyzed-tables`)
  }

  async getAnalyzedSample(connectionId: string, limit: number = 100): Promise<ApiResponse<{
    sample: {
      columns: string[]
      data: Record<string, any>[]
      total_rows: number
      data_types: Record<string, string>
      is_analyzed_data?: boolean
    }
  }>> {
    return this.request(`/api/connections/${connectionId}/analyzed-sample?limit=${limit}`)
  }

  async getTablePreview(connectionId: string, tableName: string, limit: number = 20): Promise<ApiResponse<{
    table_preview: {
      table_name: string
      total_rows: number
      columns: string[]
      data_types: Record<string, string>
      preview_data: Record<string, any>[]
      preview_rows: number
      column_stats: Record<string, {
        non_null_count: number
        null_count: number
        unique_count: number
        data_type: string
        min?: number
        max?: number
        mean?: number
      }>
    }
  }>> {
    return this.request(`/api/connections/${connectionId}/tables/${tableName}/preview?limit=${limit}`)
  }

  // Analysis endpoints
  async runQualityAnalysis(connectionId: string, selectedTables?: string[]): Promise<ApiResponse<QualityAnalysisResult>> {
    const params = new URLSearchParams({ connection_id: connectionId })
    if (selectedTables && selectedTables.length > 0) {
      selectedTables.forEach(table => params.append('tables', table))
    }
    
    return this.request(`/api/analysis/quality-metrics?${params.toString()}`, {
      method: "POST",
    })
  }

  async runAutoQualityAnalysisAllTables(connectionId: string): Promise<ApiResponse<QualityAnalysisResult & {
    table_count: number
    analyzed_tables: string[]
  }>> {
    const params = new URLSearchParams({ connection_id: connectionId })
    
    return this.request(`/api/analysis/auto-quality-all-tables?${params.toString()}`, {
      method: "POST",
    })
  }

  async getCachedAnalysisResults(connectionId: string): Promise<ApiResponse<{
    combined_results: QualityAnalysisResult & {
      table_count: number
      analyzed_tables: string[]
    }
    table_results: Record<string, QualityAnalysisResult & {
      table_name: string
      table_stats: {
        row_count: number
        column_count: number
        columns: Array<{
          name: string
          data_type: string
          non_null_count: number
          sample_values: string[]
        }>
        sample_data: Record<string, any>[]
      }
    }>
    analyzed_tables: string[]
  }>> {
    return this.request(`/api/analysis/cached-results/${connectionId}`)
  }

  async runAnomalyDetection(
    connectionId: string,
    modelType = "VARIMA",
    threshold = 2.0,
    maxComponents = 5,
    selectedTables?: string[]
  ): Promise<ApiResponse<AnomalyDetectionResult>> {
    return this.request("/api/analysis/anomaly-detection", {
      method: "POST",
      body: JSON.stringify({
        connection_id: connectionId,
        model_type: modelType,
        threshold,
        max_components: maxComponents,
        selected_tables: selectedTables,
      }),
    })
  }

  async runAutoVarimaAllTables(connectionId: string): Promise<ApiResponse<any>> {
    return this.request("/api/analysis/auto-varima-all-tables", {
      method: "POST",
      body: JSON.stringify({
        connection_id: connectionId
      }),
    })
  }

  async getCachedVarimaResults(connectionId: string): Promise<ApiResponse<any>> {
    return this.request(`/api/analysis/cached-varima-results/${connectionId}`)
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

async deleteConnectionString(email: string, connectionId: string): Promise<ApiResponse<{ remaining_connections: number }>> {
  return this.request<{ remaining_connections: number }>(`/api/delete/db-connection/${email}/${connectionId}`, {
    method: "DELETE",
  })
}

async getStoredConnections(email: string): Promise<ApiResponse<{
  data: {
    email: string
    connections: Array<{
      connection_id: string
      created_at: string
      connection_preview: string
    }>
    total_connections: number
    last_updated: string
  }
}>> {
  return this.request(`/api/get/db-connections/${email}`)
}

async exportCleanedData(connectionId: string): Promise<ApiResponse<{
  success: boolean
  files: Array<{
    table_name: string
    csv_data: string
    original_records: number
    cleaned_records: number
    removed_records: number
    cleaning_efficiency: number
    columns: string[]
  }>
  export_timestamp: string
}>> {
  return this.request(`/api/analysis/export-cleaned-data`, {
    method: "POST",
    body: JSON.stringify({ connection_id: connectionId }),
    headers: {
      'Content-Type': 'application/json'
    }
  })
}

async exportCleanedTable(connectionId: string, tableName: string): Promise<ApiResponse<{
  success: boolean
  table_name: string
  csv_data: string
  original_records: number
  cleaned_records: number
  removed_records: number
  cleaning_efficiency: number
  columns: string[]
}>> {
  return this.request(`/api/analysis/export-cleaned-table`, {
    method: "POST",
    body: JSON.stringify({ connection_id: connectionId, table_name: tableName }),
    headers: {
      'Content-Type': 'application/json'
    }
  })
}

async exportAnalysisStatistics(connectionId: string): Promise<ApiResponse<{
  success: boolean
  csv_data: string
  summary: {
    total_tables: number
    analyzed_tables: number
    overall_quality_score: number
    total_records: number
    anomalies_detected: number
    anomaly_percentage: number
  }
  message: string
}>> {
  return this.request(`/api/analysis/export-statistics`, {
    method: "POST",
    body: JSON.stringify({ connection_id: connectionId }),
    headers: {
      'Content-Type': 'application/json'
    }
  })
}

async checkPowerBIInstallation(): Promise<ApiResponse<{
  installed: boolean
  paths: string[]
  primary_path: string | null
  message: string
  download_url?: string
  instructions?: string[]
}>> {
  return this.request("/api/powerbi/check-installation")
}

async openPowerBIDesktop(connectionId: string): Promise<ApiResponse<{
  success: boolean
  message: string
  download_url?: string
  package_path?: string
  csv_path: string
  template_path?: string | null
  pbix_path?: string | null
  instructions_path?: string
  temp_directory: string
  powerbi_url?: string
  template_available: boolean
  pbix_available: boolean
  package_contents?: {
    csv_data: string
    template?: string | null
    dashboard?: string | null
    setup_guide: string
  }
  quick_actions?: string[]
  recommended_workflow?: string
  data_summary?: {
    total_tables: number
    overall_score: number
    risk_level: string
    anomalies: number
  }
}>> {
  return this.request(`/api/powerbi/open-online`, {
    method: "POST",
    body: JSON.stringify({ connection_id: connectionId }),
    headers: {
      'Content-Type': 'application/json'
    }
  })
}

async createPowerBITemplate(connectionId: string): Promise<ApiResponse<{
  success: boolean
  message: string
  template_directory: string
  files: {
    csv_data: string
    config: string
    instructions: string
  }
  template_config: any
  next_steps: string[]
}>> {
  return this.request(`/api/powerbi/create-template?connection_id=${connectionId}`, {
    method: "POST",
  })
}

async updateRowData(connectionId: string, rowIndex: number, updatedData: Record<string, any>): Promise<ApiResponse<{
  success: boolean
  message: string
  updated_columns: string[]
  row_index: number
}>> {
  return this.request(`/api/connections/${connectionId}/update-row`, {
    method: "PUT",
    body: JSON.stringify({
      row_index: rowIndex,
      updated_data: updatedData
    }),
    headers: {
      'Content-Type': 'application/json'
    }
  })
}

  // Data Cleaning endpoints
  async getCleaningOptions(connectionId: string, tableName?: string): Promise<ApiResponse> {
    return this.request("/api/data-cleaning/preview-options", {
      method: "POST",
      body: JSON.stringify({
        connection_id: connectionId,
        table_name: tableName
      })
    })
  }

  async cleanData(connectionId: string, cleaningOptions: any, tableName?: string): Promise<ApiResponse> {
    return this.request("/api/data-cleaning/clean-data", {
      method: "POST",
      body: JSON.stringify({
        connection_id: connectionId,
        table_name: tableName,
        cleaning_options: cleaningOptions
      })
    })
  }

  async downloadCleanedData(filename: string): Promise<Response> {
    return fetch(`${this.baseUrl}/api/data-cleaning/download/${filename}`)
  }
}

export const apiClient = new ApiClient()