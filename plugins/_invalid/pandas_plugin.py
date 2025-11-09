"""
Pandas Plugin for Windows AI
Provides data manipulation and analysis capabilities using pandas
"""

import pandas as pd
import numpy as np
import io
import json
from typing import Dict, List, Any, Optional, Union
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

class PandasPlugin:
    """Pandas data manipulation and analysis plugin"""
    
    def __init__(self):
        self.name = "pandas"
        self.version = "1.0.0"
        self.description = "Data manipulation and analysis using pandas"
        self.dataframes = {}
        
    def get_info(self) -> Dict[str, Any]:
        """Return plugin information"""
        return {
            "name": self.name,
            "version": self.version,
            "description": self.description,
            "capabilities": [
                "read_csv", "read_excel", "read_json", "read_parquet",
                "data_analysis", "data_cleaning", "data_transformation",
                "statistical_analysis", "data_visualization"
            ]
        }
    
    def read_csv(self, file_path: str, **kwargs) -> str:
        """Read CSV file and store as dataframe"""
        try:
            df = pd.read_csv(file_path, **kwargs)
            df_id = f"df_{len(self.dataframes)}"
            self.dataframes[df_id] = df
            return f"Successfully loaded CSV as {df_id}. Shape: {df.shape}"
        except Exception as e:
            return f"Error reading CSV: {str(e)}"
    
    def read_excel(self, file_path: str, sheet_name: Optional[str] = None, **kwargs) -> str:
        """Read Excel file and store as dataframe"""
        try:
            df = pd.read_excel(file_path, sheet_name=sheet_name, **kwargs)
            df_id = f"df_{len(self.dataframes)}"
            self.dataframes[df_id] = df
            return f"Successfully loaded Excel as {df_id}. Shape: {df.shape}"
        except Exception as e:
            return f"Error reading Excel: {str(e)}"
    
    def read_json(self, file_path: str, **kwargs) -> str:
        """Read JSON file and store as dataframe"""
        try:
            df = pd.read_json(file_path, **kwargs)
            df_id = f"df_{len(self.dataframes)}"
            self.dataframes[df_id] = df
            return f"Successfully loaded JSON as {df_id}. Shape: {df.shape}"
        except Exception as e:
            return f"Error reading JSON: {str(e)}"
    
    def create_dataframe(self, data: Union[Dict, List], columns: Optional[List[str]] = None) -> str:
        """Create dataframe from data"""
        try:
            df = pd.DataFrame(data, columns=columns)
            df_id = f"df_{len(self.dataframes)}"
            self.dataframes[df_id] = df
            return f"Successfully created {df_id}. Shape: {df.shape}"
        except Exception as e:
            return f"Error creating dataframe: {str(e)}"
    
    def get_dataframe_info(self, df_id: str) -> str:
        """Get information about a dataframe"""
        if df_id not in self.dataframes:
            return f"Dataframe {df_id} not found"
        
        df = self.dataframes[df_id]
        buffer = io.StringIO()
        
        buffer.write(f"Dataframe: {df_id}\n")
        buffer.write(f"Shape: {df.shape}\n")
        buffer.write(f"Columns: {list(df.columns)}\n")
        buffer.write(f"Dtypes:\n{df.dtypes}\n")
        buffer.write(f"Memory usage: {df.memory_usage(deep=True).sum() / 1024:.2f} KB\n")
        
        return buffer.getvalue()
    
    def get_head(self, df_id: str, n: int = 5) -> str:
        """Get first n rows of dataframe"""
        if df_id not in self.dataframes:
            return f"Dataframe {df_id} not found"
        
        df = self.dataframes[df_id]
        return df.head(n).to_string()
    
    def get_tail(self, df_id: str, n: int = 5) -> str:
        """Get last n rows of dataframe"""
        if df_id not in self.dataframes:
            return f"Dataframe {df_id} not found"
        
        df = self.dataframes[df_id]
        return df.tail(n).to_string()
    
    def describe(self, df_id: str) -> str:
        """Get statistical description of dataframe"""
        if df_id not in self.dataframes:
            return f"Dataframe {df_id} not found"
        
        df = self.dataframes[df_id]
        return df.describe().to_string()
    
    def get_missing_values(self, df_id: str) -> str:
        """Get missing values summary"""
        if df_id not in self.dataframes:
            return f"Dataframe {df_id} not found"
        
        df = self.dataframes[df_id]
        missing = df.isnull().sum()
        missing_pct = (missing / len(df) * 100).round(2)
        
        result = "Missing Values Summary:\n"
        result += f"{'Column':<20} {'Missing':<10} {'Percentage':<12}\n"
        result += "-" * 45 + "\n"
        
        for col in df.columns:
            result += f"{col:<20} {missing[col]:<10} {missing_pct[col]:<12}%\n"
        
        return result
    
    def filter_data(self, df_id: str, condition: str, new_df_id: Optional[str] = None) -> str:
        """Filter dataframe based on condition"""
        if df_id not in self.dataframes:
            return f"Dataframe {df_id} not found"
        
        try:
            df = self.dataframes[df_id]
            filtered_df = df.query(condition)
            
            if new_df_id is None:
                new_df_id = f"df_{len(self.dataframes)}"
            
            self.dataframes[new_df_id] = filtered_df
            return f"Filtered data saved as {new_df_id}. Shape: {filtered_df.shape}"
        except Exception as e:
            return f"Error filtering data: {str(e)}"
    
    def group_by(self, df_id: str, group_columns: Union[str, List[str]], 
                 agg_func: Union[str, Dict[str, str]], new_df_id: Optional[str] = None) -> str:
        """Group dataframe and apply aggregation"""
        if df_id not in self.dataframes:
            return f"Dataframe {df_id} not found"
        
        try:
            df = self.dataframes[df_id]
            grouped = df.groupby(group_columns).agg(agg_func)
            
            if new_df_id is None:
                new_df_id = f"df_{len(self.dataframes)}"
            
            self.dataframes[new_df_id] = grouped
            return f"Grouped data saved as {new_df_id}. Shape: {grouped.shape}"
        except Exception as e:
            return f"Error grouping data: {str(e)}"
    
    def merge_dataframes(self, df1_id: str, df2_id: str, on: Union[str, List[str]], 
                        how: str = 'inner', new_df_id: Optional[str] = None) -> str:
        """Merge two dataframes"""
        if df1_id not in self.dataframes or df2_id not in self.dataframes:
            return "One or both dataframes not found"
        
        try:
            df1 = self.dataframes[df1_id]
            df2 = self.dataframes[df2_id]
            merged = pd.merge(df1, df2, on=on, how=how)
            
            if new_df_id is None:
                new_df_id = f"df_{len(self.dataframes)}"
            
            self.dataframes[new_df_id] = merged
            return f"Merged data saved as {new_df_id}. Shape: {merged.shape}"
        except Exception as e:
            return f"Error merging dataframes: {str(e)}"
    
    def pivot_table(self, df_id: str, values: Optional[str] = None, 
                   index: Optional[Union[str, List[str]]] = None,
                   columns: Optional[Union[str, List[str]]] = None,
                   aggfunc: str = 'mean', new_df_id: Optional[str] = None) -> str:
        """Create pivot table"""
        if df_id not in self.dataframes:
            return f"Dataframe {df_id} not found"
        
        try:
            df = self.dataframes[df_id]
            pivot = pd.pivot_table(df, values=values, index=index, 
                                 columns=columns, aggfunc=aggfunc)
            
            if new_df_id is None:
                new_df_id = f"df_{len(self.dataframes)}"
            
            self.dataframes[new_df_id] = pivot
            return f"Pivot table saved as {new_df_id}. Shape: {pivot.shape}"
        except Exception as e:
            return f"Error creating pivot table: {str(e)}"
    
    def handle_missing_values(self, df_id: str, method: str = 'drop', 
                            value: Any = None, new_df_id: Optional[str] = None) -> str:
        """Handle missing values in dataframe"""
        if df_id not in self.dataframes:
            return f"Dataframe {df_id} not found"
        
        try:
            df = self.dataframes[df_id]
            
            if method == 'drop':
                cleaned_df = df.dropna()
            elif method == 'fill':
                cleaned_df = df.fillna(value)
            elif method == 'forward':
                cleaned_df = df.fillna(method='ffill')
            elif method == 'backward':
                cleaned_df = df.fillna(method='bfill')
            else:
                return f"Unknown method: {method}"
            
            if new_df_id is None:
                new_df_id = f"df_{len(self.dataframes)}"
            
            self.dataframes[new_df_id] = cleaned_df
            return f"Missing values handled using {method}. Saved as {new_df_id}. Shape: {cleaned_df.shape}"
        except Exception as e:
            return f"Error handling missing values: {str(e)}"
    
    def convert_dtypes(self, df_id: str, dtype_mapping: Dict[str, str], 
                      new_df_id: Optional[str] = None) -> str:
        """Convert dataframe column data types"""
        if df_id not in self.dataframes:
            return f"Dataframe {df_id} not found"
        
        try:
            df = self.dataframes[df_id]
            converted_df = df.astype(dtype_mapping)
            
            if new_df_id is None:
                new_df_id = f"df_{len(self.dataframes)}"
            
            self.dataframes[new_df_id] = converted_df
            return f"Data types converted. Saved as {new_df_id}"
        except Exception as e:
            return f"Error converting data types: {str(e)}"
    
    def save_dataframe(self, df_id: str, file_path: str, file_format: str = 'csv', **kwargs) -> str:
        """Save dataframe to file"""
        if df_id not in self.dataframes:
            return f"Dataframe {df_id} not found"
        
        try:
            df = self.dataframes[df_id]
            
            if file_format.lower() == 'csv':
                df.to_csv(file_path, index=False, **kwargs)
            elif file_format.lower() == 'excel':
                df.to_excel(file_path, index=False, **kwargs)
            elif file_format.lower() == 'json':
                df.to_json(file_path, **kwargs)
            elif file_format.lower() == 'parquet':
                df.to_parquet(file_path, **kwargs)
            else:
                return f"Unsupported format: {file_format}"
            
            return f"Dataframe {df_id} saved to {file_path}"
        except Exception as e:
            return f"Error saving dataframe: {str(e)}"
    
    def list_dataframes(self) -> str:
        """List all stored dataframes"""
        if not self.dataframes:
            return "No dataframes stored"
        
        result = "Stored Dataframes:\n"
        result += f"{'ID':<15} {'Shape':<15} {'Columns':<20}\n"
        result += "-" * 50 + "\n"
        
        for df_id, df in self.dataframes.items():
            result += f"{df_id:<15} {str(df.shape):<15} {len(df.columns)} columns\n"
        
        return result
    
    def delete_dataframe(self, df_id: str) -> str:
        """Delete a stored dataframe"""
        if df_id not in self.dataframes:
            return f"Dataframe {df_id} not found"
        
        del self.dataframes[df_id]
        return f"Dataframe {df_id} deleted"
    
    def execute_query(self, df_id: str, query: str) -> str:
        """Execute pandas query on dataframe"""
        if df_id not in self.dataframes:
            return f"Dataframe {df_id} not found"
        
        try:
            df = self.dataframes[df_id]
            result = df.query(query)
            return f"Query result:\n{result.to_string()}"
        except Exception as e:
            return f"Error executing query: {str(e)}"
    
    def correlation_matrix(self, df_id: str) -> str:
        """Calculate correlation matrix for numeric columns"""
        if df_id not in self.dataframes:
            return f"Dataframe {df_id} not found"
        
        try:
            df = self.dataframes[df_id]
            numeric_df = df.select_dtypes(include=[np.number])
            if numeric_df.empty:
                return "No numeric columns found for correlation analysis"
            
            corr_matrix = numeric_df.corr()
            return f"Correlation Matrix:\n{corr_matrix.round(3).to_string()}"
        except Exception as e:
            return f"Error calculating correlation matrix: {str(e)}"

# Plugin instance
plugin = PandasPlugin()

def get_plugin():
    """Return plugin instance"""
    return plugin