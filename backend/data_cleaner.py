"""
Comprehensive Data Cleaning Module
Provides various cleaning options with configurable parameters
"""
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Any, Union
import os
import tempfile
from datetime import datetime
import uuid

class DataCleaner:
    """
    Comprehensive data cleaning class with configurable options
    """
    
    def __init__(self, df: pd.DataFrame):
        """Initialize with source dataframe"""
        self.original_df = df.copy()
        self.df = df.copy()
        self.cleaning_log = []
        self.stats = {
            'original_shape': df.shape,
            'original_nulls': df.isnull().sum().sum(),
            'original_duplicates': df.duplicated().sum()
        }
    
    def log_action(self, action: str, details: Dict[str, Any]):
        """Log cleaning action for reporting"""
        self.cleaning_log.append({
            'action': action,
            'timestamp': datetime.now().isoformat(),
            'details': details,
            'shape_after': self.df.shape
        })
    
    def drop_null_values(self, method: str = 'any', threshold: Optional[float] = None) -> 'DataCleaner':
        """
        Drop rows/columns with null values
        
        Args:
            method: 'any' (drop if any null), 'all' (drop if all null), 'threshold' (drop if null % > threshold)
            threshold: Percentage threshold for dropping (0.0 to 1.0)
        """
        initial_shape = self.df.shape
        
        if method == 'any':
            self.df = self.df.dropna()
        elif method == 'all':
            self.df = self.df.dropna(how='all')
        elif method == 'threshold' and threshold is not None:
            # Drop columns with more than threshold% missing values
            missing_ratio = self.df.isnull().mean()
            cols_to_drop = missing_ratio[missing_ratio > threshold].index
            self.df = self.df.drop(columns=cols_to_drop)
            
            # Drop rows with more than threshold% missing values
            row_missing_ratio = self.df.isnull().mean(axis=1)
            rows_to_drop = row_missing_ratio[row_missing_ratio > threshold].index
            self.df = self.df.drop(index=rows_to_drop)
        
        rows_dropped = initial_shape[0] - self.df.shape[0]
        cols_dropped = initial_shape[1] - self.df.shape[1]
        
        self.log_action('drop_null_values', {
            'method': method,
            'threshold': threshold,
            'rows_dropped': rows_dropped,
            'cols_dropped': cols_dropped,
            'initial_shape': initial_shape,
            'final_shape': self.df.shape
        })
        
        return self
    
    def drop_duplicates(self, subset: Optional[List[str]] = None, keep: str = 'first') -> 'DataCleaner':
        """
        Remove duplicate rows
        
        Args:
            subset: Columns to consider for identifying duplicates
            keep: Which duplicates to keep ('first', 'last', False)
        """
        initial_shape = self.df.shape
        initial_duplicates = self.df.duplicated(subset=subset, keep=False).sum()
        
        self.df = self.df.drop_duplicates(subset=subset, keep=keep)
        
        duplicates_removed = initial_shape[0] - self.df.shape[0]
        
        self.log_action('drop_duplicates', {
            'subset': subset,
            'keep': keep,
            'duplicates_removed': duplicates_removed,
            'initial_duplicates': initial_duplicates,
            'initial_shape': initial_shape,
            'final_shape': self.df.shape
        })
        
        return self
    
    def fill_missing_values(self, method: str = 'mean', columns: Optional[List[str]] = None) -> 'DataCleaner':
        """
        Fill missing values using specified method
        
        Args:
            method: 'mean', 'median', 'mode', 'forward_fill', 'backward_fill', 'interpolate', 'constant'
            columns: Specific columns to fill (None for all)
        """
        if columns is None:
            columns = self.df.columns.tolist()
        
        filled_counts = {}
        
        for col in columns:
            if col not in self.df.columns:
                continue
                
            initial_nulls = self.df[col].isnull().sum()
            
            if initial_nulls == 0:
                continue
            
            if method == 'mean' and pd.api.types.is_numeric_dtype(self.df[col]):
                self.df[col] = self.df[col].fillna(self.df[col].mean())
            elif method == 'median' and pd.api.types.is_numeric_dtype(self.df[col]):
                self.df[col] = self.df[col].fillna(self.df[col].median())
            elif method == 'mode':
                mode_val = self.df[col].mode()
                if len(mode_val) > 0:
                    self.df[col] = self.df[col].fillna(mode_val.iloc[0])
            elif method == 'forward_fill':
                self.df[col] = self.df[col].fillna(method='ffill')
            elif method == 'backward_fill':
                self.df[col] = self.df[col].fillna(method='bfill')
            elif method == 'interpolate' and pd.api.types.is_numeric_dtype(self.df[col]):
                self.df[col] = self.df[col].interpolate()
            elif method == 'constant':
                # Use a reasonable constant based on data type
                if pd.api.types.is_numeric_dtype(self.df[col]):
                    self.df[col] = self.df[col].fillna(0)
                else:
                    self.df[col] = self.df[col].fillna('Unknown')
            
            final_nulls = self.df[col].isnull().sum()
            filled_counts[col] = initial_nulls - final_nulls
        
        self.log_action('fill_missing_values', {
            'method': method,
            'columns': columns,
            'filled_counts': filled_counts,
            'total_filled': sum(filled_counts.values())
        })
        
        return self
    
    def remove_outliers(self, method: str = 'iqr', columns: Optional[List[str]] = None, 
                       threshold: float = 1.5) -> 'DataCleaner':
        """
        Remove outliers using specified method
        
        Args:
            method: 'iqr' (Interquartile Range), 'zscore', 'isolation_forest'
            columns: Specific numeric columns (None for all numeric)
            threshold: Threshold for outlier detection
        """
        if columns is None:
            columns = self.df.select_dtypes(include=[np.number]).columns.tolist()
        
        initial_shape = self.df.shape
        outliers_removed = 0
        
        if method == 'iqr':
            for col in columns:
                if col not in self.df.columns or not pd.api.types.is_numeric_dtype(self.df[col]):
                    continue
                
                Q1 = self.df[col].quantile(0.25)
                Q3 = self.df[col].quantile(0.75)
                IQR = Q3 - Q1
                
                lower_bound = Q1 - threshold * IQR
                upper_bound = Q3 + threshold * IQR
                
                outlier_mask = (self.df[col] < lower_bound) | (self.df[col] > upper_bound)
                outliers_removed += outlier_mask.sum()
                self.df = self.df[~outlier_mask]
        
        elif method == 'zscore':
            for col in columns:
                if col not in self.df.columns or not pd.api.types.is_numeric_dtype(self.df[col]):
                    continue
                
                z_scores = np.abs((self.df[col] - self.df[col].mean()) / self.df[col].std())
                outlier_mask = z_scores > threshold
                outliers_removed += outlier_mask.sum()
                self.df = self.df[~outlier_mask]
        
        self.log_action('remove_outliers', {
            'method': method,
            'columns': columns,
            'threshold': threshold,
            'outliers_removed': outliers_removed,
            'initial_shape': initial_shape,
            'final_shape': self.df.shape
        })
        
        return self
    
    def standardize_data(self, method: str = 'zscore', columns: Optional[List[str]] = None) -> 'DataCleaner':
        """
        Standardize/normalize numeric data
        
        Args:
            method: 'zscore' (standardization), 'minmax' (normalization)
            columns: Specific numeric columns (None for all numeric)
        """
        if columns is None:
            columns = self.df.select_dtypes(include=[np.number]).columns.tolist()
        
        standardized_columns = []
        
        for col in columns:
            if col not in self.df.columns or not pd.api.types.is_numeric_dtype(self.df[col]):
                continue
            
            if method == 'zscore':
                mean_val = self.df[col].mean()
                std_val = self.df[col].std()
                if std_val != 0:
                    self.df[col] = (self.df[col] - mean_val) / std_val
                    standardized_columns.append(col)
            
            elif method == 'minmax':
                min_val = self.df[col].min()
                max_val = self.df[col].max()
                if max_val != min_val:
                    self.df[col] = (self.df[col] - min_val) / (max_val - min_val)
                    standardized_columns.append(col)
        
        self.log_action('standardize_data', {
            'method': method,
            'columns': columns,
            'standardized_columns': standardized_columns
        })
        
        return self
    
    def convert_data_types(self, conversions: Dict[str, str]) -> 'DataCleaner':
        """
        Convert data types of specified columns
        
        Args:
            conversions: Dictionary mapping column names to target types
                        ('int', 'float', 'string', 'datetime', 'category')
        """
        converted_columns = {}
        
        for col, target_type in conversions.items():
            if col not in self.df.columns:
                continue
            
            try:
                initial_type = str(self.df[col].dtype)
                
                if target_type == 'int':
                    self.df[col] = pd.to_numeric(self.df[col], errors='coerce').astype('Int64')
                elif target_type == 'float':
                    self.df[col] = pd.to_numeric(self.df[col], errors='coerce')
                elif target_type == 'string':
                    self.df[col] = self.df[col].astype(str)
                elif target_type == 'datetime':
                    self.df[col] = pd.to_datetime(self.df[col], errors='coerce')
                elif target_type == 'category':
                    self.df[col] = self.df[col].astype('category')
                
                converted_columns[col] = {
                    'from': initial_type,
                    'to': target_type,
                    'success': True
                }
            
            except Exception as e:
                converted_columns[col] = {
                    'from': initial_type if 'initial_type' in locals() else 'unknown',
                    'to': target_type,
                    'success': False,
                    'error': str(e)
                }
        
        self.log_action('convert_data_types', {
            'conversions': conversions,
            'results': converted_columns
        })
        
        return self
    
    def get_cleaning_summary(self) -> Dict[str, Any]:
        """Get summary of all cleaning operations performed"""
        current_stats = {
            'final_shape': self.df.shape,
            'final_nulls': self.df.isnull().sum().sum(),
            'final_duplicates': self.df.duplicated().sum()
        }
        
        return {
            'original_stats': self.stats,
            'final_stats': current_stats,
            'improvements': {
                'rows_change': current_stats['final_shape'][0] - self.stats['original_shape'][0],
                'cols_change': current_stats['final_shape'][1] - self.stats['original_shape'][1],
                'nulls_reduced': self.stats['original_nulls'] - current_stats['final_nulls'],
                'duplicates_reduced': self.stats['original_duplicates'] - current_stats['final_duplicates']
            },
            'cleaning_log': self.cleaning_log,
            'data_types': {col: str(dtype) for col, dtype in self.df.dtypes.items()}
        }
    
    def export_to_csv(self, filename: Optional[str] = None) -> str:
        """
        Export cleaned data to CSV file
        
        Args:
            filename: Custom filename (None for auto-generated)
        
        Returns:
            Path to the exported file
        """
        if filename is None:
            timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            unique_id = str(uuid.uuid4())[:8]
            filename = f"cleaned_data_{unique_id}_{timestamp}.csv"
        
        # Create temporary directory for exports
        export_dir = tempfile.gettempdir()
        filepath = os.path.join(export_dir, filename)
        
        # Export to CSV
        self.df.to_csv(filepath, index=False)
        
        return filepath

def clean_data_comprehensive(df: pd.DataFrame, cleaning_options: Dict[str, Any]) -> Dict[str, Any]:
    """
    Main function to perform comprehensive data cleaning based on options
    
    Args:
        df: Source dataframe
        cleaning_options: Dictionary of cleaning options and parameters
    
    Returns:
        Dictionary with cleaned data info and summary
    """
    cleaner = DataCleaner(df)
    
    # Apply cleaning operations based on options
    if cleaning_options.get('drop_nulls', {}).get('enabled', False):
        null_options = cleaning_options['drop_nulls']
        cleaner.drop_null_values(
            method=null_options.get('method', 'any'),
            threshold=null_options.get('threshold')
        )
    
    if cleaning_options.get('drop_duplicates', {}).get('enabled', False):
        dup_options = cleaning_options['drop_duplicates']
        cleaner.drop_duplicates(
            subset=dup_options.get('subset'),
            keep=dup_options.get('keep', 'first')
        )
    
    if cleaning_options.get('fill_missing', {}).get('enabled', False):
        fill_options = cleaning_options['fill_missing']
        cleaner.fill_missing_values(
            method=fill_options.get('method', 'mean'),
            columns=fill_options.get('columns')
        )
    
    if cleaning_options.get('remove_outliers', {}).get('enabled', False):
        outlier_options = cleaning_options['remove_outliers']
        cleaner.remove_outliers(
            method=outlier_options.get('method', 'iqr'),
            columns=outlier_options.get('columns'),
            threshold=outlier_options.get('threshold', 1.5)
        )
    
    if cleaning_options.get('standardize', {}).get('enabled', False):
        std_options = cleaning_options['standardize']
        cleaner.standardize_data(
            method=std_options.get('method', 'zscore'),
            columns=std_options.get('columns')
        )
    
    if cleaning_options.get('convert_types', {}).get('enabled', False):
        type_options = cleaning_options['convert_types']
        cleaner.convert_data_types(type_options.get('conversions', {}))
    
    # Export if requested
    export_path = None
    if cleaning_options.get('export', {}).get('enabled', False):
        export_options = cleaning_options['export']
        export_path = cleaner.export_to_csv(export_options.get('filename'))
    
    # Get summary
    summary = cleaner.get_cleaning_summary()
    
    return {
        'success': True,
        'cleaned_data': cleaner.df,
        'export_path': export_path,
        'summary': summary,
        'original_shape': cleaner.stats['original_shape'],
        'final_shape': cleaner.df.shape
    }
