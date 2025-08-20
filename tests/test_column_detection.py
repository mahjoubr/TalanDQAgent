import sys
import os
sys.path.append(os.getcwd())

import pandas as pd
import numpy as np
from varima_detector import numeric_columns

def test_column_detection():
    """Test the column detection issue"""
    
    print("=== Testing Column Detection ===")
    
    # Create the same test data
    np.random.seed(42)
    test_df = pd.DataFrame({
        'sales_revenue': np.random.randn(50).cumsum() + 1000,
        'order_count': np.random.randn(50).cumsum() + 500,
        'visitor_count': np.random.randn(50) * 20 + 200,
        'store_id': ['store_' + str(i % 3) for i in range(50)],
        'category': np.random.choice(['A', 'B', 'C'], 50)
    })
    
    print(f"Test DataFrame:")
    print(f"Shape: {test_df.shape}")
    print(f"Columns: {list(test_df.columns)}")
    print(f"Data types:\n{test_df.dtypes}")
    
    print(f"\nFirst few rows:")
    print(test_df.head())
    
    # Test our numeric_columns function
    print(f"\nTesting numeric_columns function...")
    try:
        numeric_cols = numeric_columns(test_df)
        print(f"Numeric columns found: {numeric_cols}")
        print(f"Number of numeric columns: {len(numeric_cols)}")
        
        if len(numeric_cols) >= 2:
            print("✓ Sufficient numeric columns for VARIMA")
        else:
            print("✗ Insufficient numeric columns for VARIMA")
            
        # Test each column individually
        print(f"\nColumn analysis:")
        for col in test_df.columns:
            col_data = test_df[col]
            is_numeric = pd.api.types.is_numeric_dtype(col_data)
            print(f"  {col}: dtype={col_data.dtype}, is_numeric={is_numeric}")
            
    except Exception as e:
        print(f"✗ numeric_columns function failed: {e}")
        import traceback
        traceback.print_exc()
        
    # Test standard pandas numeric detection
    print(f"\nStandard pandas numeric detection:")
    for col in test_df.columns:
        col_data = test_df[col]
        if pd.api.types.is_numeric_dtype(col_data):
            print(f"  {col}: numeric")
        else:
            print(f"  {col}: non-numeric")

if __name__ == "__main__":
    test_column_detection()
