import pandas as pd
import numpy as np

def debug_column_detection():
    """Debug the column detection issue step by step"""
    
    print("=== Debugging Column Detection ===")
    
    # Create simple test data
    np.random.seed(42)
    df = pd.DataFrame({
        'daily_revenue': [1000.0, 1050.0, 980.0, 1100.0, 1020.0] * 10,  # 50 values with repeats
        'transaction_count': [40, 42, 39, 44, 41] * 10,  # 50 values with repeats
        'avg_order_value': [25.0, 25.5, 24.8, 26.0, 25.2] * 10,  # 50 values with repeats
    })
    
    print(f"Test data shape: {df.shape}")
    print(f"Columns: {list(df.columns)}")
    
    # Test each function step by step
    from varima_detector import is_id_column, is_boolean_column, numeric_columns
    
    print("\n1. Testing is_id_column for each column:")
    for col in df.columns:
        try:
            result = is_id_column(df[col], col)
            unique_count = df[col].nunique()
            total_count = len(df[col])
            print(f"   {col}: is_id={result}, unique={unique_count}/{total_count}")
        except Exception as e:
            print(f"   {col}: ERROR - {e}")
            import traceback
            traceback.print_exc()
    
    print("\n2. Testing is_boolean_column for each column:")
    for col in df.columns:
        try:
            result = is_boolean_column(df[col])
            print(f"   {col}: is_boolean={result}")
        except Exception as e:
            print(f"   {col}: ERROR - {e}")
    
    print("\n3. Testing numeric_columns function:")
    try:
        numeric_cols = numeric_columns(df)
        print(f"   Numeric columns: {numeric_cols}")
    except Exception as e:
        print(f"   ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_column_detection()
