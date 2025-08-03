"use client"

import { useState, useEffect } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Table, Search, Database, BarChart3, Plus, X } from "lucide-react"

interface TableInfo {
  name: string
  recordCount: number | string
}

interface TableSelectorProps {
  connection: any
  onTablesSelected: (selectedTables: string[]) => void
  selectedTables?: string[]
}

export function TableSelector({ connection, onTablesSelected, selectedTables = [] }: TableSelectorProps) {
  const [tables, setTables] = useState<TableInfo[]>([])
  const [searchTerm, setSearchTerm] = useState("")
  const [currentSelectedTables, setCurrentSelectedTables] = useState<string[]>(selectedTables)

  useEffect(() => {
    if (connection?.details?.tables && connection?.details?.record_counts) {
      const tableList = connection.details.tables.map((tableName: string) => ({
        name: tableName,
        recordCount: connection.details.record_counts[tableName] || 0,
      }))
      setTables(tableList)
    }
  }, [connection])

  useEffect(() => {
    setCurrentSelectedTables(selectedTables)
  }, [selectedTables])

  const filteredTables = tables.filter(table =>
    table.name.toLowerCase().includes(searchTerm.toLowerCase())
  )

  const availableTables = filteredTables.filter(table => 
    !currentSelectedTables.includes(table.name)
  )

  const handleAddTable = (tableName: string) => {
    if (tableName && !currentSelectedTables.includes(tableName)) {
      const updatedTables = [...currentSelectedTables, tableName]
      setCurrentSelectedTables(updatedTables)
      onTablesSelected(updatedTables)
    }
  }

  const handleRemoveTable = (tableName: string) => {
    const updatedTables = currentSelectedTables.filter(name => name !== tableName)
    setCurrentSelectedTables(updatedTables)
    onTablesSelected(updatedTables)
  }

  const handleSelectAll = () => {
    const allTableNames = tables.map(table => table.name)
    setCurrentSelectedTables(allTableNames)
    onTablesSelected(allTableNames)
  }

  const handleClearAll = () => {
    setCurrentSelectedTables([])
    onTablesSelected([])
  }

  const getTableRecordCount = (tableName: string) => {
    const table = tables.find(t => t.name === tableName)
    return table?.recordCount || 0
  }

  const totalRecords = currentSelectedTables.reduce((sum, tableName) => {
    const count = getTableRecordCount(tableName)
    return sum + (typeof count === 'number' ? count : 0)
  }, 0)

  if (!connection?.details?.tables || connection.details.tables.length === 0) {
    return (
      <Card className="border-0 shadow-lg">
        <CardContent className="pt-6">
          <div className="text-center py-8">
            <Database className="h-12 w-12 text-gray-400 mx-auto mb-4" />
            <p className="text-gray-500">No tables available for this connection</p>
          </div>
        </CardContent>
      </Card>
    )
  }

  return (
    <Card className="border-0 shadow-lg">
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle className="flex items-center gap-2 text-xl">
              <div className="p-2 bg-gradient-to-r from-blue-500 to-cyan-500 rounded-lg">
                <Table className="h-5 w-5 text-white" />
              </div>
              Select Tables for Analysis
            </CardTitle>
            <CardDescription>
              Choose which tables to include in quality analysis and anomaly detection
            </CardDescription>
          </div>
          {currentSelectedTables.length > 0 && (
            <div className="text-right">
              <Badge className="bg-blue-100 text-blue-700 mb-1">
                {currentSelectedTables.length} table{currentSelectedTables.length !== 1 ? 's' : ''} selected
              </Badge>
              <div className="text-sm text-gray-600">
                {totalRecords.toLocaleString()} total records
              </div>
            </div>
          )}
        </div>
      </CardHeader>
      <CardContent className="space-y-6">
        {/* Table Selection Dropdown */}
        <div className="space-y-4">
          <div className="flex items-center gap-4">
            <div className="flex-1">
              <Label htmlFor="table-select" className="text-sm font-medium">
                Add Table to Analysis
              </Label>
              <div className="flex gap-2 mt-1">
                <Select onValueChange={handleAddTable}>
                  <SelectTrigger className="flex-1">
                    <SelectValue placeholder="Select a table to add..." />
                  </SelectTrigger>
                  <SelectContent>
                    <div className="p-2">
                      <div className="relative">
                        <Search className="absolute left-2 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
                        <Input
                          placeholder="Search tables..."
                          value={searchTerm}
                          onChange={(e) => setSearchTerm(e.target.value)}
                          className="pl-8 h-8"
                        />
                      </div>
                    </div>
                    {availableTables.length === 0 ? (
                      <div className="px-2 py-4 text-center text-gray-500 text-sm">
                        {searchTerm ? "No tables match your search" : "All tables are already selected"}
                      </div>
                    ) : (
                      availableTables.map((table) => (
                        <SelectItem key={table.name} value={table.name}>
                          <div className="flex items-center justify-between w-full">
                            <span className="font-medium">{table.name}</span>
                            <span className="text-xs text-gray-500 ml-2">
                              {typeof table.recordCount === 'number' 
                                ? `${table.recordCount.toLocaleString()} records`
                                : 'N/A'
                              }
                            </span>
                          </div>
                        </SelectItem>
                      ))
                    )}
                  </SelectContent>
                </Select>
              </div>
            </div>
            <div className="flex gap-2">
              <Button
                onClick={handleSelectAll}
                variant="outline"
                size="sm"
                disabled={currentSelectedTables.length === tables.length}
                className="whitespace-nowrap"
              >
                Select All
              </Button>
              <Button
                onClick={handleClearAll}
                variant="outline"
                size="sm"
                disabled={currentSelectedTables.length === 0}
                className="whitespace-nowrap"
              >
                Clear All
              </Button>
            </div>
          </div>
        </div>

        {/* Selected Tables Display */}
        {currentSelectedTables.length > 0 && (
          <div className="space-y-3">
            <Label className="text-sm font-medium text-gray-700">
              Selected Tables ({currentSelectedTables.length})
            </Label>
            <div className="space-y-2 max-h-48 overflow-y-auto">
              {currentSelectedTables.map((tableName) => (
                <div
                  key={tableName}
                  className="flex items-center justify-between p-3 bg-blue-50 border border-blue-200 rounded-lg"
                >
                  <div className="flex items-center gap-3">
                    <div className="p-1.5 bg-blue-500 rounded">
                      <Table className="h-3 w-3 text-white" />
                    </div>
                    <div>
                      <div className="font-medium text-gray-900">{tableName}</div>
                      <div className="text-sm text-gray-600 flex items-center gap-1">
                        <BarChart3 className="h-3 w-3" />
                        {typeof getTableRecordCount(tableName) === 'number' 
                          ? `${getTableRecordCount(tableName).toLocaleString()} records`
                          : 'Record count unavailable'
                        }
                      </div>
                    </div>
                  </div>
                  <Button
                    onClick={() => handleRemoveTable(tableName)}
                    variant="ghost"
                    size="sm"
                    className="text-red-500 hover:text-red-700 hover:bg-red-50"
                  >
                    <X className="h-4 w-4" />
                  </Button>
                </div>
              ))}
            </div>
          </div>
        )}

        {currentSelectedTables.length === 0 && (
          <div className="bg-amber-50 border border-amber-200 rounded-lg p-4">
            <div className="flex items-center gap-2">
              <div className="p-1 bg-amber-500 rounded">
                <Plus className="h-3 w-3 text-white" />
              </div>
              <p className="text-sm text-amber-700 font-medium">
                No tables selected for analysis
              </p>
            </div>
            <p className="text-xs text-amber-600 mt-1 ml-6">
              Use the dropdown above to select tables for quality analysis and anomaly detection.
            </p>
          </div>
        )}
      </CardContent>
    </Card>
  )
}
