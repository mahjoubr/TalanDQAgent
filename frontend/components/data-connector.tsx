"use client"

import type React from "react"

import { useState, useEffect, useCallback } from "react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Textarea } from "@/components/ui/textarea"
import { Database, Upload, FileText, CheckCircle, Zap, Server, Trash2 } from "lucide-react"
import { useToast } from "@/hooks/use-toast"
import { apiClient } from "@/lib/api"

interface Connection {
  id: string
  type: "database" | "file"
  dbType?: string
  connectionString?: string
  fileName?: string
  fileSize?: number
  status: string
  tables?: string[]
  recordCount?: number
  columns?: string[]
  createdAt: string
}

interface DataConnectorProps {
  onDataConnected: (data: any) => void
  setIsLoading?: (loading: boolean) => void
  onComplete?: (data: any) => void
  isCompleted?: boolean
}

// Key for storing connections in memory
const CONNECTIONS_KEY = 'dataConnectorConnections'

// In-memory storage for connections (persists during session)
let connectionsStorage: Connection[] = []

// Helper functions for connection management
const saveConnections = (connections: Connection[]) => {
  connectionsStorage = [...connections]
}

const loadConnections = (): Connection[] => {
  return [...connectionsStorage]
}

const addConnection = (connection: Connection) => {
  connectionsStorage = [...connectionsStorage, connection]
}

const removeConnection = (connectionId: string) => {
  connectionsStorage = connectionsStorage.filter(conn => conn.id !== connectionId)
}

export function DataConnector({ onDataConnected, setIsLoading, onComplete, isCompleted }: DataConnectorProps) {
  const [connectionString, setConnectionString] = useState("")
  const [dbType, setDbType] = useState("")
  const [isConnecting, setIsConnecting] = useState(false)
  const [uploadedFile, setUploadedFile] = useState<File | null>(null)
  const [connections, setConnections] = useState<Connection[]>([])
  const [hasNotifiedParent, setHasNotifiedParent] = useState(false)
  const { toast } = useToast()

  // Memoize the onDataConnected callback to prevent unnecessary re-renders
  const stableOnDataConnected = useCallback((data: any) => {
    if (onDataConnected) {
      onDataConnected(data)
    }
  }, [onDataConnected])

  // Load saved connections on component mount
  useEffect(() => {
    const savedConnections = loadConnections()
    setConnections(savedConnections)
    
    // Only notify parent once and only if there are connections and we haven't notified yet
    if (savedConnections.length > 0 && !hasNotifiedParent) {
      // Notify about the most recent connection or create a summary
      const summaryData = {
        connectionCount: savedConnections.length,
        connections: savedConnections,
        lastConnection: savedConnections[savedConnections.length - 1]
      }
      stableOnDataConnected(summaryData)
      setHasNotifiedParent(true)
    }
  }, [stableOnDataConnected, hasNotifiedParent])

  // Save connections whenever they change
  useEffect(() => {
    saveConnections(connections)
  }, [connections])

  const handleDatabaseConnect = async () => {
    if (!dbType || !connectionString) {
      toast({
        title: "Missing Information",
        description: "Please select database type and enter connection string",
        variant: "destructive",
      })
      return
    }

    setIsConnecting(true)
    setIsLoading?.(true)

    try {
      const response = await apiClient.connectDatabase(dbType, connectionString)

      if (response.success && response.data) {
        const newConnection: Connection = {
          id: response.data.connection_id,
          type: "database",
          dbType,
          connectionString,
          status: "connected",
          tables: response.data.details.tables || [],
          recordCount: response.data.details.record_count,
          createdAt: new Date().toISOString(),
        }

        setConnections((prev) => {
          const updated = [...prev, newConnection]
          addConnection(newConnection)
          return updated
        })

        stableOnDataConnected(newConnection)

        toast({
          title: "Database Connected Successfully",
          description: response.data.message || "Connection established",
        })

        // Clear form after successful connection
        setConnectionString("")
        setDbType("")
      }
    } catch (error) {
      toast({
        title: "Connection Failed",
        description: error instanceof Error ? error.message : "Unknown error occurred",
        variant: "destructive",
      })
    } finally {
      setIsConnecting(false)
      setIsLoading?.(false)
    }
  }

  const handleFileUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0]
    if (!file) return

    setUploadedFile(file)
    setIsLoading?.(true)

    try {
      const response = await apiClient.uploadFile(file)

      if (response.success && response.data) {
        const newConnection: Connection = {
          id: response.data.connection_id,
          type: "file",
          fileName: response.data.details.filename,
          fileSize: (response.data.details.size_mb || 0) * 1024 * 1024,
          status: "uploaded",
          recordCount: response.data.details.record_count,
          columns: response.data.details.columns || [],
          createdAt: new Date().toISOString(),
        }

        setConnections((prev) => {
          const updated = [...prev, newConnection]
          addConnection(newConnection)
          return updated
        })

        stableOnDataConnected(newConnection)

        toast({
          title: "File Uploaded Successfully",
          description: response.data.message || "File processed successfully",
        })
      } else {
        // Handle API failure with mock data
        const mockConnection: Connection = {
          id: `mock-file-${Date.now()}`,
          type: "file",
          fileName: file.name,
          fileSize: file.size,
          status: "uploaded",
          recordCount: 5000,
          columns: ["id", "name", "email", "created_at", "value"],
          createdAt: new Date().toISOString(),
        }

        setConnections((prev) => {
          const updated = [...prev, mockConnection]
          addConnection(mockConnection)
          return updated
        })

        stableOnDataConnected(mockConnection)

        toast({
          title: "Mock File Upload",
          description: "Using mock data - backend service unavailable",
        })
      }
    } catch (error) {
      // Fallback to mock data in development
      if (process.env.NODE_ENV === "development") {
        const mockConnection: Connection = {
          id: `mock-file-${Date.now()}`,
          type: "file",
          fileName: file.name,
          fileSize: file.size,
          status: "uploaded",
          recordCount: 5000,
          columns: ["id", "name", "email", "created_at", "value"],
          createdAt: new Date().toISOString(),
        }

        setConnections((prev) => {
          const updated = [...prev, mockConnection]
          addConnection(mockConnection)
          return updated
        })

        stableOnDataConnected(mockConnection)

        toast({
          title: "Development Mode",
          description: "Using mock file upload for development",
        })
      } else {
        toast({
          title: "Upload Failed",
          description: error instanceof Error ? error.message : "Unknown error occurred",
          variant: "destructive",
        })
      }
    } finally {
      setIsLoading?.(false)
      // Clear the file input
      event.target.value = ""
      setUploadedFile(null)
    }
  }

  const handleRemoveConnection = (connectionId: string) => {
    setConnections((prev) => {
      const updated = prev.filter(conn => conn.id !== connectionId)
      removeConnection(connectionId)
      return updated
    })

    toast({
      title: "Connection Removed",
      description: "Connection has been removed from the list",
    })
  }

  const clearAllConnections = () => {
    setConnections([])
    connectionsStorage = []
    setHasNotifiedParent(false) // Reset notification flag
    toast({
      title: "All Connections Cleared",
      description: "All connections have been removed",
    })
  }

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleString()
  }

  const dbTypes = [
    { value: "postgresql", label: "PostgreSQL", icon: "🐘" },
    { value: "mysql", label: "MySQL", icon: "🐬" },
    { value: "mariadb", label: "MariaDB", icon: "🦭" },
    { value: "oracle", label: "Oracle", icon: "🔶" },
    { value: "sqlserver", label: "SQL Server", icon: "🏢" },
  ]

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex justify-between items-start">
        <div>
          <h2 className="text-4xl font-bold bg-gradient-to-r from-blue-600 to-cyan-600 bg-clip-text text-transparent">
            Data Connector Engine
          </h2>
          <p className="text-gray-600 mt-2">Connect to databases, upload files, and manage data sources</p>
          {connections.length > 0 && (
            <p className="text-sm text-green-600 mt-1">
              {connections.length} active connection{connections.length > 1 ? 's' : ''} saved
            </p>
          )}
        </div>
        {connections.length > 0 && (
          <Button
            onClick={clearAllConnections}
            variant="outline"
            size="sm"
            className="text-red-600 border-red-200 hover:bg-red-50"
          >
            <Trash2 className="w-4 h-4 mr-2" />
            Clear All
          </Button>
        )}
      </div>

      <Tabs defaultValue="database" className="space-y-6">
        <TabsList className="grid w-full grid-cols-2 bg-blue-50 p-1 rounded-xl">
          <TabsTrigger value="database" className="data-[state=active]:bg-white data-[state=active]:shadow-sm">
            <Database className="mr-2 h-4 w-4" />
            Database Connection
          </TabsTrigger>
          <TabsTrigger value="file" className="data-[state=active]:bg-white data-[state=active]:shadow-sm">
            <Upload className="mr-2 h-4 w-4" />
            File Upload
          </TabsTrigger>
        </TabsList>

        <TabsContent value="database">
          <Card className="border-0 shadow-lg">
            <div className="h-2 bg-gradient-to-r from-blue-500 to-cyan-500 rounded-t-lg"></div>
            <CardHeader>
              <CardTitle className="flex items-center gap-3 text-xl">
                <div className="p-2 bg-gradient-to-r from-blue-500 to-cyan-500 rounded-lg">
                  <Server className="h-5 w-5 text-white" />
                </div>
                Database Connection
              </CardTitle>
              <CardDescription>Connect to PostgreSQL, MySQL, and other enterprise databases</CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="space-y-2">
                <Label htmlFor="db-type" className="text-sm font-semibold text-gray-700">
                  Database Type
                </Label>
                <Select value={dbType} onValueChange={setDbType}>
                  <SelectTrigger className="border-blue-200 focus:border-blue-400">
                    <SelectValue placeholder="Select database type" />
                  </SelectTrigger>
                  <SelectContent>
                    {dbTypes.map((db) => (
                      <SelectItem key={db.value} value={db.value}>
                        <div className="flex items-center gap-2">
                          <span>{db.icon}</span>
                          <span>{db.label}</span>
                        </div>
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              <div className="space-y-2">
                <Label htmlFor="connection-string" className="text-sm font-semibold text-gray-700">
                  Connection String
                </Label>
                <Textarea
                  id="connection-string"
                  placeholder="postgresql://username:password@host:port/database"
                  value={connectionString}
                  onChange={(e) => setConnectionString(e.target.value)}
                  rows={4}
                  className="border-blue-200 focus:border-blue-400 font-mono text-sm"
                />
                <p className="text-xs text-gray-500">Example: postgresql://user:pass@localhost:5432/datawarehouse</p>
              </div>

              <Button
                onClick={handleDatabaseConnect}
                disabled={!dbType || !connectionString || isConnecting}
                className="w-full bg-gradient-to-r from-blue-500 to-cyan-500 hover:from-blue-600 hover:to-cyan-600 text-white font-semibold py-3 shadow-lg"
              >
                {isConnecting ? (
                  <div className="flex items-center gap-2">
                    <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                    Establishing Connection...
                  </div>
                ) : (
                  <>
                    <Zap className="mr-2 h-4 w-4" />
                    Connect to Database
                  </>
                )}
              </Button>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="file">
          <Card className="border-0 shadow-lg">
            <div className="h-2 bg-gradient-to-r from-green-500 to-emerald-500 rounded-t-lg"></div>
            <CardHeader>
              <CardTitle className="flex items-center gap-3 text-xl">
                <div className="p-2 bg-gradient-to-r from-green-500 to-emerald-500 rounded-lg">
                  <Upload className="h-5 w-5 text-white" />
                </div>
                File Upload
              </CardTitle>
              <CardDescription>Upload CSV, XLSX, or other data files for analysis</CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="space-y-2">
                <Label htmlFor="file-upload" className="text-sm font-semibold text-gray-700">
                  Select File
                </Label>
                <div className="border-2 border-dashed border-green-200 rounded-lg p-8 text-center hover:border-green-300 transition-colors">
                  <Upload className="h-12 w-12 text-green-400 mx-auto mb-4" />
                  <Input
                    id="file-upload"
                    type="file"
                    accept=".csv,.xlsx,.xls,.json"
                    onChange={handleFileUpload}
                    className="hidden"
                  />
                  <Label htmlFor="file-upload" className="cursor-pointer">
                    <div className="text-lg font-medium text-gray-700 mb-2">Drop files here or click to browse</div>
                    <div className="text-sm text-gray-500">Supports CSV, XLSX, XLS, JSON files up to 100MB</div>
                  </Label>
                </div>
              </div>

              {uploadedFile && (
                <div className="flex items-center gap-3 p-4 bg-gradient-to-r from-green-50 to-emerald-50 rounded-lg border border-green-200">
                  <div className="p-2 bg-gradient-to-r from-green-500 to-emerald-500 rounded-lg">
                    <CheckCircle className="h-5 w-5 text-white" />
                  </div>
                  <div className="flex-1">
                    <p className="font-semibold text-green-800">{uploadedFile.name}</p>
                    <p className="text-sm text-green-600">
                      {(uploadedFile.size / 1024 / 1024).toFixed(2)} MB • Processing...
                    </p>
                  </div>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      {/* Connection Status */}
      <Card className="border-0 shadow-lg">
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-xl">
            <div className="p-2 bg-gradient-to-r from-violet-500 to-purple-500 rounded-lg">
              <Database className="h-5 w-5 text-white" />
            </div>
            Active Connections ({connections.length})
          </CardTitle>
          <CardDescription>Manage your connected data sources - connections persist when navigating</CardDescription>
        </CardHeader>
        <CardContent>
          {connections.length === 0 ? (
            <div className="text-center py-8">
              <Database className="h-12 w-12 text-gray-300 mx-auto mb-4" />
              <p className="text-gray-500">No connections established yet</p>
              <p className="text-sm text-gray-400">Connect to a database or upload a file to get started</p>
            </div>
          ) : (
            <div className="space-y-3">
              {connections.map((connection) => (
                <div
                  key={connection.id}
                  className="flex items-center justify-between p-4 bg-gradient-to-r from-white to-violet-50 rounded-xl border border-violet-100"
                >
                  <div className="flex items-center gap-3 flex-1">
                    <div
                      className={`p-2 rounded-lg ${
                        connection.type === "database"
                          ? "bg-gradient-to-r from-blue-500 to-cyan-500"
                          : "bg-gradient-to-r from-green-500 to-emerald-500"
                      }`}
                    >
                      {connection.type === "database" ? (
                        <Database className="h-4 w-4 text-white" />
                      ) : (
                        <FileText className="h-4 w-4 text-white" />
                      )}
                    </div>
                    <div className="flex-1">
                      <div className="flex items-center justify-between">
                        <span className="font-semibold text-gray-800">
                          {connection.type === "database"
                            ? `${connection.dbType?.toUpperCase()} Database`
                            : connection.fileName}
                        </span>
                      </div>
                      <div className="flex items-center gap-4 mt-1 text-sm text-gray-600">
                        <span>{connection.recordCount?.toLocaleString()} records</span>
                        {connection.tables && <span>{connection.tables.length} tables</span>}
                        {connection.columns && <span>{connection.columns.length} columns</span>}
                        <span className="text-xs">• {formatDate(connection.createdAt)}</span>
                      </div>
                    </div>
                  </div>
                  <div className="flex items-center gap-3">
                    <div className="flex items-center gap-2">
                      <CheckCircle className="h-5 w-5 text-green-500" />
                      <span className="text-sm font-medium text-green-600">Connected</span>
                    </div>
                    <Button
                      onClick={() => handleRemoveConnection(connection.id)}
                      variant="ghost"
                      size="sm"
                      className="text-red-500 hover:text-red-700 hover:bg-red-50"
                    >
                      <Trash2 className="h-4 w-4" />
                    </Button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}