# 🧪 Test Suite Documentation

This folder contains all testing files for the Data Quality Agent project.

## 📁 Test Files Overview

### **VARIMA Analysis Tests**
- `test_varima.py` - Core VARIMA functionality tests
- `test_varima_advanced.py` - Advanced VARIMA model testing
- `test_varima_endpoint.py` - VARIMA API endpoint testing
- `final_test_varima.py` - Final VARIMA implementation validation
- `inspect_varima.py` - VARIMA model inspection and debugging

### **API Integration Tests**
- `test_api_integration.py` - API endpoint integration testing
- `test_endpoint.py` - General endpoint functionality tests
- `test_live_endpoint.py` - Live API endpoint testing

### **Data Processing Tests**
- `test_column_detection.py` - Column detection and analysis
- `test_realistic_data.py` - Testing with realistic datasets
- `test_detailed_detection.py` - Detailed anomaly detection testing

### **Workflow Tests**
- `test_full_workflow.py` - End-to-end workflow testing
- `test_integration.py` - Component integration testing
- `test_analysis_integration.py` - Analysis pipeline integration

### **Debug & Development**
- `test_debug_analysis.py` - Debug analysis tools
- `quick_test.py` - Quick validation tests

### **Frontend Tests**
- `test-data-flow.js` - Frontend data flow testing

### **Test Data**
- `full_varima_test.csv` - Sample dataset for VARIMA testing

## 🚀 Running Tests

### Backend Tests
```bash
# Navigate to project root
cd "C:\Users\Refka\Downloads\power-bi-dashboard-setup (2)"

# Run individual test
python tests/test_varima.py

# Run all VARIMA tests
python tests/test_varima*.py
```

### Frontend Tests
```bash
# Navigate to frontend directory
cd frontend

# Run frontend tests
node ../tests/test-data-flow.js
```

## 📋 Test Categories

1. **Unit Tests** - Individual component testing
2. **Integration Tests** - Component interaction testing
3. **API Tests** - Endpoint and service testing
4. **End-to-End Tests** - Full workflow validation
5. **Performance Tests** - VARIMA model performance
6. **Data Tests** - Data processing and validation

## 🔧 Test Dependencies

Make sure your virtual environment is activated and all dependencies are installed:

```bash
# Backend dependencies
pip install -r backend/requirements.txt

# Frontend dependencies (if needed)
cd frontend && npm install
```

## 📊 Test Data

The `full_varima_test.csv` file contains sample data specifically designed for:
- VARIMA model training
- Anomaly detection validation
- Data quality metrics testing
- Time series analysis

## 🐛 Debug Tests

Use the debug test files for troubleshooting:
- `inspect_varima.py` - Model inspection
- `test_debug_analysis.py` - Analysis debugging
- `quick_test.py` - Rapid validation
