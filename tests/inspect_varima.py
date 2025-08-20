import pandas as pd
import numpy as np
from varima_detector import detect_varima_anomalies

def inspect_varima_output():
    """Inspect the exact output format of the VARIMA detector"""
    print("=== Inspecting VARIMA Output Format ===")
    
    # Create simple test data
    dates = pd.date_range(start='2023-01-01', periods=50, freq='H')
    
    df = pd.DataFrame({
        'timestamp': dates,
        'sales': np.random.randn(50).cumsum() + 100,
        'orders': np.random.randn(50).cumsum() + 50,
        'visitors': np.random.randn(50) * 10 + 75,
    })
    
    print(f"Input data shape: {df.shape}")
    print(f"Input columns: {list(df.columns)}")
    
    # Run VARIMA
    result = detect_varima_anomalies(df)
    
    print(f"\nOutput data shape: {result.shape}")
    print(f"Output columns: {list(result.columns)}")
    print(f"Output dtypes:\n{result.dtypes}")
    
    # Check for anomaly-related columns
    anomaly_cols = [col for col in result.columns if 'anomaly' in col.lower()]
    print(f"\nAnomaly-related columns: {anomaly_cols}")
    
    if anomaly_cols:
        print(f"\nFirst 10 rows of anomaly columns:")
        print(result[anomaly_cols].head(10))
        
        # Check for actual anomalies
        for col in anomaly_cols:
            if result[col].dtype in ['bool', 'int64', 'float64']:
                anomaly_count = (result[col] > 0).sum() if result[col].dtype != bool else result[col].sum()
                print(f"Column '{col}' has {anomaly_count} anomalies")
    
    # Show sample of the result
    print(f"\nFirst 5 rows of result:")
    print(result.head().to_string())
    
    return result

if __name__ == "__main__":
    inspect_varima_output()
