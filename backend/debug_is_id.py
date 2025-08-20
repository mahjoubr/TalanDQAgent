import sys
import os
sys.path.append(os.getcwd())

import pandas as pd
import numpy as np

def debug_is_id_column(df, column_name, correlation_threshold=0.3):
    """Debug version of is_id_column to see what's triggering"""
    if column_name not in df.columns:
        return False

    col_lower = column_name.lower()
    series = df[column_name]
    
    print(f"\n=== Debugging {column_name} ===")
    print(f"Column type: {series.dtype}")
    print(f"First 5 values: {series.head().tolist()}")
    print(f"Unique values: {series.nunique()}")
    print(f"Total values: {len(series)}")

    # Name patterns
    name_patterns = [
        col_lower == 'id',
        col_lower.endswith('_id'),
        col_lower.startswith('id_'),
        col_lower.endswith('id'),
        col_lower in ['index', 'idx', 'key', 'pk', 'primary_key'],
        'id' in col_lower and len(col_lower) <= 10
    ]
    
    print(f"Name patterns: {name_patterns}")
    print(f"Any name pattern: {any(name_patterns)}")

    if pd.api.types.is_numeric_dtype(series):
        is_sequential = series.dropna().is_monotonic_increasing
        is_unique = series.nunique() == len(series.dropna())
        is_integer = series.dropna().apply(lambda x: float(x).is_integer()).all()
        starts_from_low = series.min() in [0, 1] if not series.empty else False

        print(f"Is sequential: {is_sequential}")
        print(f"Is unique: {is_unique}")
        print(f"Is integer: {is_integer}")
        print(f"Starts from low (0,1): {starts_from_low}")

        data_patterns = [
            is_sequential and is_unique,
            is_unique and is_integer and starts_from_low,
            is_unique and len(series) > 10
        ]
        
        print(f"Data patterns: {data_patterns}")
        print(f"Any data pattern: {any(data_patterns)}")

        # Check correlations
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        correlations = []

        for other_col in numeric_cols:
            if other_col != column_name:
                try:
                    corr_value = df[column_name].corr(df[other_col])
                    if not pd.isna(corr_value):
                        correlations.append(abs(corr_value))
                        print(f"Correlation with {other_col}: {corr_value:.4f}")
                except:
                    continue

        if correlations:
            avg_correlation = np.mean(correlations)
            max_correlation = max(correlations)
            print(f"Average correlation: {avg_correlation:.4f}")
            print(f"Max correlation: {max_correlation:.4f}")
            
        result = any(name_patterns) or any(data_patterns)
        print(f"Final result: {result}")
        return result

    return False

def test_debug():
    # Create test data
    np.random.seed(42)
    test_df = pd.DataFrame({
        'sales_revenue': np.random.randn(50).cumsum() + 1000,
        'order_count': np.random.randn(50).cumsum() + 500,
        'visitor_count': np.random.randn(50) * 20 + 200,
    })
    
    for col in test_df.columns:
        debug_is_id_column(test_df, col)

if __name__ == "__main__":
    test_debug()
