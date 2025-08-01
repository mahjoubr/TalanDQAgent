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
import { Database, Upload, FileText, CheckCircle, Zap, Server, Trash2, Cloud } from "lucide-react"
import { useToast } from "@/hooks/use-toast"
import { apiClient, type DatabaseConnectionRequest } from "@/lib/api"

// Base connection interface
interface BaseConnection {
  id: string
  status: string
  createdAt: string
}

// Database connection interface matching backend Pydantic model
interface DatabaseConnection extends BaseConnection {
  db_type: string
  connection_string: string
  username?: string
  password?: string
  host: string
  port?: number
  database_name: string
  additional_params?: Record<string, any>
}

// File connection interface
interface FileConnection extends BaseConnection {
  type: "file"
  fileName: string
  fileSize: number
  recordCount?: number
  columns?: string[]
}

// Stored connection interface (from Redis/backend)
interface StoredConnection {
  connection_id: string
  created_at: string
  connection_preview: string
}

// Union type for all connection types
type Connection = DatabaseConnection | FileConnection

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
  const [username, setUsername] = useState("aa")
  const [password, setPassword] = useState("aa")
  const [host, setHost] = useState("aa")
  const [port, setPort] = useState("aa")
  const [databaseName, setDatabaseName] = useState("aa")
  const [isConnecting, setIsConnecting] = useState(false)
  const [uploadedFile, setUploadedFile] = useState<File | null>(null)
  const [connections, setConnections] = useState<Connection[]>([])
  const [storedConnections, setStoredConnections] = useState<StoredConnection[]>([])
  const [hasNotifiedParent, setHasNotifiedParent] = useState(false)
  const [isLoadingStored, setIsLoadingStored] = useState(false)
  const { toast } = useToast()

  // Get user email from localStorage
  const getUserEmail = () => {
    const savedDataString = localStorage.getItem("signInData")
    const savedData = savedDataString ? JSON.parse(savedDataString) : null
    return savedData?.email || null
  }

  // Memoize the onDataConnected callback to prevent unnecessary re-renders
  const stableOnDataConnected = useCallback((data: any) => {
    if (onDataConnected) {
      onDataConnected(data)
    }
  }, [onDataConnected])

  // Load stored connections from backend
  const loadStoredConnections = async () => {
    const email = getUserEmail()
    if (!email) return

    setIsLoadingStored(true)
    try {
      const response = await apiClient.getStoredConnections(email)
      if (response.success && response.data) {
        setStoredConnections(response.data.connections || [])
      }
    } catch (error) {
      console.error("Failed to load stored connections:", error)
    } finally {
      setIsLoadingStored(false)
    }
  }

  // Load saved connections on component mount
  useEffect(() => {
    const savedConnections = loadConnections()
    setConnections(savedConnections)
    
    // Load stored connections from backend
    loadStoredConnections()
    
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
    if (!dbType || !host || !databaseName) {
      toast({
        title: "Missing Information",
        description: "Please fill in database type, host, and database name",
        variant: "destructive",
      })
      return
    }

    setIsConnecting(true)
    setIsLoading?.(true)
    console.log("Connecting to database:", { dbType, host, databaseName, username })
    
    try {
      // Auto-generate connection string if not provided
      let finalConnectionString = connectionString
      if (!finalConnectionString && host && databaseName) {
        const portPart = port ? `:${port}` : ''
        const authPart = username && password ? `${username}:${password}@` : ''
        
        switch (dbType) {
          case 'postgresql':
            finalConnectionString = `postgresql://${authPart}${host}${portPart}/${databaseName}`
            break
          case 'mysql':
            finalConnectionString = `mysql+pymysql://${authPart}${host}${portPart}/${databaseName}`
            break
          case 'sqlserver':
            finalConnectionString = `mssql+pyodbc://${authPart}${host}${portPart}/${databaseName}?driver=ODBC+Driver+17+for+SQL+Server`
            break
          case 'oracle':
            finalConnectionString = `oracle+cx_oracle://${authPart}${host}${portPart}/?service_name=${databaseName}`
            break
          case 'sqlite':
            finalConnectionString = `sqlite:///${databaseName}`
            break
          default:
            finalConnectionString = `${dbType}://${authPart}${host}${portPart}/${databaseName}`
        }
      }

      // Create the request object matching backend Pydantic model
      const connectionRequest = {
        db_type: dbType,
        connection_string: finalConnectionString,
        username: username || undefined,
        password: password || undefined,
        host,
        port: port ? parseInt(port) : undefined,
        database_name: databaseName,
        additional_params: {},
      }
      
      const response = await apiClient.connectDatabase(connectionRequest)

      if (response.success && response.data) {
        const newConnection: DatabaseConnection = {
          id: response.data.connection_id || `db-${Date.now()}`,
          db_type: dbType,
          connection_string: finalConnectionString,
          username: username || undefined,
          password: password || undefined,
          host,
          port: port ? parseInt(port) : undefined,
          database_name: databaseName,
          additional_params: {},
          status: "connected",
          createdAt: new Date().toISOString()
        }

        setConnections((prev) => {
          const updated = [...prev, newConnection]
          addConnection(newConnection)
          return updated
        })

        stableOnDataConnected(newConnection)
        
        // Store connection string in backend
        const email = getUserEmail()
        if (email) {
          await apiClient.storeConnectionString(email, finalConnectionString)
          // Reload stored connections to show the new one
          loadStoredConnections()
        }

        toast({
          title: "Database Connected Successfully",
          description: response.data.message || "Connection established",
        })

        // Clear form after successful connection
        setConnectionString("")
        setDbType("")
        setUsername("")
        setPassword("")
        setHost("")
        setPort("")
        setDatabaseName("")
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
        const newConnection: FileConnection = {
          id: response.data.connection_id,
          type: "file",
          fileName: response.data.details.filename || file.name,
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
        // Handle API failure
        toast({
          title: "Upload Failed",
          description: response.error || "Failed to upload file",
          variant: "destructive",
        })
      }
    } catch (error) {
      toast({
        title: "Upload Failed",
        description: "Failed to upload file: " + String(error),
        variant: "destructive",
      })
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

  const handleDeleteStoredConnection = async (connectionId: string) => {
    const email = getUserEmail()
    if (!email) {
      toast({
        title: "Error",
        description: "No user email found",
        variant: "destructive",
      })
      return
    }

    try {
      const response = await apiClient.deleteConnectionString(email, connectionId)
      if (response.success) {
        // Remove from local state
        setStoredConnections(prev => prev.filter(conn => conn.connection_id !== connectionId))
        
        toast({
          title: "Connection Deleted",
          description:  "Connection deleted successfully",
        })
      } else {
        toast({
          title: "Delete Failed",
          description: response.message || "Failed to delete connection",
          variant: "destructive",
        })
      }
    } catch (error) {
      toast({
        title: "Delete Failed",
        description: error instanceof Error ? error.message : "Unknown error occurred",
        variant: "destructive",
      })
    }
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

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="host" className="text-sm font-semibold text-gray-700">
                    Host <span className="text-red-500">*</span>
                  </Label>
                  <Input
                    id="host"
                    placeholder="localhost or IP address"
                    value={host}
                    onChange={(e) => setHost(e.target.value)}
                    className="border-blue-200 focus:border-blue-400"
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="port" className="text-sm font-semibold text-gray-700">
                    Port
                  </Label>
                  <Input
                    id="port"
                    placeholder="5432"
                    value={port}
                    onChange={(e) => setPort(e.target.value)}
                    className="border-blue-200 focus:border-blue-400"
                  />
                </div>
              </div>

              <div className="space-y-2">
                <Label htmlFor="database-name" className="text-sm font-semibold text-gray-700">
                  Database Name <span className="text-red-500">*</span>
                </Label>
                <Input
                  id="database-name"
                  placeholder="Enter database name"
                  value={databaseName}
                  onChange={(e) => setDatabaseName(e.target.value)}
                  className="border-blue-200 focus:border-blue-400"
                />
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="username" className="text-sm font-semibold text-gray-700">
                    Username
                  </Label>
                  <Input
                    id="username"
                    placeholder="Database username"
                    value={username}
                    onChange={(e) => setUsername(e.target.value)}
                    className="border-blue-200 focus:border-blue-400"
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="password" className="text-sm font-semibold text-gray-700">
                    Password
                  </Label>
                  <Input
                    id="password"
                    type="password"
                    placeholder="Database password"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    className="border-blue-200 focus:border-blue-400"
                  />
                </div>
              </div>

              <div className="space-y-2">
                <Label htmlFor="connection-string" className="text-sm font-semibold text-gray-700">
                  Connection String (Optional)
                </Label>
                <Textarea
                  id="connection-string"
                  placeholder="postgresql://username:password@host:port/database"
                  value={connectionString}
                  onChange={(e) => setConnectionString(e.target.value)}
                  rows={3}
                  className="border-blue-200 focus:border-blue-400 font-mono text-sm"
                />
                <p className="text-xs text-gray-500">Override the individual fields above with a complete connection string</p>
              </div>

              <Button
                onClick={handleDatabaseConnect}
                disabled={!dbType || !host || !databaseName || isConnecting}
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

      {/* Active Connections */}
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
                    <div className="flex-1">
                      <div className="flex items-center justify-between">
                        <span className="font-semibold text-gray-800">
                          {connection.id}
                        </span>
                      </div>
                      <div className="flex items-center gap-4 mt-1 text-sm text-gray-600">
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

      {/* Stored Connections from Backend */}
      <Card className="border-0 shadow-lg">
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-xl">
            <div className="p-2 bg-gradient-to-r from-orange-500 to-red-500 rounded-lg">
              <Cloud className="h-5 w-5 text-white" />
            </div>
            Stored Connections ({storedConnections.length})
          </CardTitle>
          <CardDescription>Previously saved database connections from your account</CardDescription>
        </CardHeader>
        <CardContent>
          {isLoadingStored ? (
            <div className="text-center py-8">
              <div className="w-8 h-8 border-2 border-orange-500 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
              <p className="text-gray-500">Loading stored connections...</p>
            </div>
          ) : storedConnections.length === 0 ? (
            <div className="text-center py-8">
              <Cloud className="h-12 w-12 text-gray-300 mx-auto mb-4" />
              <p className="text-gray-500">No stored connections found</p>
              <p className="text-sm text-gray-400">Connect to a database to save connection strings</p>
            </div>
          ) : (
            <div className="space-y-3">
              {storedConnections.map((connection) => (
                <div
                  key={connection.connection_id}
                  className="flex items-center justify-between p-4 bg-gradient-to-r from-white to-orange-50 rounded-xl border border-orange-100"
                >
                  <div className="flex items-center gap-3 flex-1">
                    <div className="p-2 bg-gradient-to-r from-orange-500 to-red-500 rounded-lg">
                      <Database className="h-4 w-4 text-white" />
                    </div>
                    <div className="flex-1">
                      <div className="flex items-center justify-between">
                        <span className="font-semibold text-gray-800">
                          {connection.connection_id}
                        </span>
                      </div>
                      <div className="flex items-center gap-4 mt-1 text-sm text-gray-600">
                        <span className="font-mono text-xs bg-gray-100 px-2 py-1 rounded">
                          {connection.connection_preview}
                        </span>
                        <span className="text-xs">• {formatDate(connection.created_at)}</span>
                      </div>
                    </div>
                  </div>
                  <div className="flex items-center gap-3">
                    <div className="flex items-center gap-2">
                      <Cloud className="h-5 w-5 text-orange-500" />
                      <span className="text-sm font-medium text-orange-600">Stored</span>
                    </div>
                    <Button
                      onClick={() => handleDeleteStoredConnection(connection.connection_id)}
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