import sys
import os
sys.path.append(os.getcwd())

from analysis import run_anomaly_detection
from file_utils import process_uploaded_file
import pandas as pd
import numpy as np
import tempfile
from fastapi import UploadFile
import io

def test_analysis_step_by_step():
    """Debug the analysis step that's failing"""
    
    print("=== Step-by-step Analysis Debug ===")
    
    # Create test data
    np.random.seed(42)
    test_df = pd.DataFrame({
        'sales_revenue': np.random.randn(50).cumsum() + 1000,
        'order_count': np.random.randn(50).cumsum() + 500,
        'visitor_count': np.random.randn(50) * 20 + 200,
        'store_id': ['store_' + str(i % 3) for i in range(50)],
        'category': np.random.choice(['A', 'B', 'C'], 50)
    })
    
    print(f"✓ Created test data: {test_df.shape}")
    print(f"Columns: {list(test_df.columns)}")
    print(f"Data types:\n{test_df.dtypes}")
    
    # Create CSV content
    csv_content = test_df.to_csv(index=False)
    csv_bytes = csv_content.encode('utf-8')
    
    # Create a mock UploadFile
    file_obj = io.BytesIO(csv_bytes)
    
    class MockUploadFile:
        def __init__(self, content, filename):
            self.file = io.BytesIO(content)
            self.filename = filename
            self.size = len(content)
            self.content_type = "text/csv"
        
        def read(self, size=-1):
            return self.file.read(size)
        
        def seek(self, offset, whence=0):
            return self.file.seek(offset, whence)
    
    mock_file = MockUploadFile(csv_bytes, "test_debug.csv")
    
    print("\n1. Testing file processing...")
    try:
        file_result = process_uploaded_file(mock_file)
        connection_id = file_result['connection_id']
        print(f"✓ File processed successfully: {connection_id}")
        print(f"  - Record count: {file_result['details']['record_count']}")
        print(f"  - Columns: {file_result['details']['columns']}")
    except Exception as e:
        print(f"✗ File processing failed: {e}")
        import traceback
        traceback.print_exc()
        return
    
    print("\n2. Testing anomaly detection...")
    try:
        anomaly_result = run_anomaly_detection(connection_id)
        print(f"✓ Anomaly detection completed")
        print(f"  - Connection ID: {anomaly_result['connection_id']}")
        print(f"  - Total observations: {anomaly_result['total_observations']}")
        print(f"  - Columns analyzed: {anomaly_result['columns_analyzed']}")
        print(f"  - Anomalies detected: {anomaly_result['anomalies_detected']}")
        print(f"  - Anomaly percentage: {anomaly_result['anomaly_percentage']:.2f}%")
        
    except Exception as e:
        print(f"✗ Anomaly detection failed: {e}")
        print(f"Error type: {type(e).__name__}")
        import traceback
        traceback.print_exc()
        return
    
    print("\n=== Debug Complete ===")

if __name__ == "__main__":
    test_analysis_step_by_step()
