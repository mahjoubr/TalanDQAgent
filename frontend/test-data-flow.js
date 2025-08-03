// Test script to check data flow
console.log('Testing report generation data flow...')

// Simulate the expected data structures
const mockQualityMetrics = {
  metrics: {
    completeness: 85,
    uniqueness: 90,
    cardinality: 75,
    consistency: 80,
    volumetry: 88
  },
  detailed_analysis: {
    table1: { issues: ['missing values'] },
    table2: { issues: ['duplicates'] }
  },
  sample_size: 1000,
  connection_id: 'test-connection-1',
  analyzed_tables: ['table1', 'table2', 'table3'],
  table_count: 3
}

const mockVarimaResults = {
  anomaly_rate: 5.2,
  risk_level: 'Medium',
  total_anomalies: 52,
  total_records: 1000,
  connection_id: 'test-connection-1',
  analyzed_tables: ['table1', 'table2', 'table3'],
  tables_count: 3
}

console.log('Expected quality metrics structure:', mockQualityMetrics)
console.log('Expected varima results structure:', mockVarimaResults)

// Test the report generation logic
const tablesCount = mockQualityMetrics?.analyzed_tables?.length || 0
const anomaliesCount = mockVarimaResults?.total_anomalies || 0
const overallQuality = mockQualityMetrics?.metrics ? 
  Math.round((
    (mockQualityMetrics.metrics.completeness || 0) + 
    (mockQualityMetrics.metrics.uniqueness || 0) + 
    (mockQualityMetrics.metrics.cardinality || 0) + 
    (mockQualityMetrics.metrics.consistency || 0) + 
    (mockQualityMetrics.metrics.volumetry || 0)
  ) / 5) : 0

console.log('Computed values:', {
  tablesCount,
  anomaliesCount, 
  overallQuality
})
