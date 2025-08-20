import sys
import os
sys.path.append(os.getcwd())

import pandas as pd
import numpy as np
from varima_detector import numeric_columns, is_boolean_column, is_id_column

def test_detailed_column_detection():
    """Test detailed column detection functions"""
    
    print("=== Detailed Column Detection Test ===")
    
    # Create test data
    np.random.seed(42)
    test_df = pd.DataFrame({
        'sales_revenue': np.random.randn(50).cumsum() + 1000,
        'order_count': np.random.randn(50).cumsum() + 500,
        'visitor_count': np.random.randn(50) * 20 + 200,
        'store_id': ['store_' + str(i % 3) for i in range(50)],
        'category': np.random.choice(['A', 'B', 'C'], 50)
    })
    
    print(f"Test DataFrame columns: {list(test_df.columns)}")
    
    # Test each detection function
    for col in test_df.columns:
        col_data = test_df[col]
        is_numeric = pd.api.types.is_numeric_dtype(col_data)
        is_bool = is_boolean_column(test_df, col)
        is_id = is_id_column(test_df, col)
        
        print(f"\nColumn: {col}")
        print(f"  Data type: {col_data.dtype}")
        print(f"  Is numeric: {is_numeric}")
        print(f"  Is boolean: {is_bool}")
        print(f"  Is ID: {is_id}")
        
        if is_numeric and not is_bool and not is_id:
            print(f"  ✓ Should be included in numeric_columns")
        else:
            print(f"  ✗ Will be filtered out")
    
    # Test final numeric_columns function
    print(f"\nFinal numeric_columns result: {numeric_columns(test_df)}")

if __name__ == "__main__":
    test_detailed_column_detection()
