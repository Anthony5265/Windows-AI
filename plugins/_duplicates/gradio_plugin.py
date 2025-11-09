"""
Gradio Plugin for Data Science
Provides web interface capabilities for data visualization and model interaction
"""

import gradio as gr
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from typing import Dict, Any, List, Optional
import io
import base64
import json

class GradioPlugin:
    """Gradio integration plugin for data science workflows"""
    
    def __init__(self):
        self.name = "gradio"
        self.version = "1.0.0"
        self.description = "Web interface for data visualization and model interaction"
        self.interface = None
        self.data_cache = {}
        
    def initialize(self) -> bool:
        """Initialize the Gradio plugin"""
        try:
            import gradio as gr
            self.gradio = gr
            return True
        except ImportError:
            return False
    
    def create_data_viewer(self, data: pd.DataFrame) -> Any:
        """Create an interactive data viewer interface"""
        def filter_data(search_term: str, column: str):
            if not search_term:
                return data
            if column and column in data.columns:
                return data[data[column].astype(str).str.contains(search_term, case=False, na=False)]
            return data[data.astype(str).apply(lambda x: x.str.contains(search_term, case=False, na=False)).any(axis=1)]
        
        def get_statistics():
            return data.describe().to_string()
        
        with self.gradio.Blocks() as interface:
            self.gradio.Markdown("# Data Viewer")
            
            with self.gradio.Row():
                search_input = self.gradio.Textbox(label="Search")
                column_dropdown = self.gradio.Dropdown(
                    choices=["All"] + list(data.columns),
                    value="All",
                    label="Column"
                )
                search_btn = self.gradio.Button("Filter")
            
            with self.gradio.Row():
                data_table = self.gradio.DataFrame(value=data, label="Data")
                stats_text = self.gradio.Textbox(value=get_statistics(), label="Statistics", lines=10)
            
            search_btn.click(
                filter_data,
                inputs=[search_input, column_dropdown],
                outputs=data_table
            )
        
        return interface
    
    def create_plot_interface(self, data: pd.DataFrame) -> Any:
        """Create an interactive plotting interface"""
        def create_plot(plot_type: str, x_column: str, y_column: str, color_column: str):
            plt.figure(figsize=(10, 6))
            
            if plot_type == "Scatter":
                if color_column and color_column in data.columns:
                    sns.scatterplot(data=data, x=x_column, y=y_column, hue=color_column)
                else:
                    plt.scatter(data[x_column], data[y_column])
            elif plot_type == "Line":
                plt.plot(data[x_column], data[y_column])
            elif plot_type == "Histogram":
                plt.hist(data[x_column].dropna(), bins=30)
            elif plot_type == "Box":
                sns.boxplot(data=data, x=x_column, y=y_column)
            elif plot_type == "Heatmap":
                numeric_data = data.select_dtypes(include=[np.number])
                sns.heatmap(numeric_data.corr(), annot=True, cmap='coolwarm')
            
            plt.title(f"{plot_type} Plot")
            plt.xlabel(x_column)
            plt.ylabel(y_column)
            plt.tight_layout()
            
            buf = io.BytesIO()
            plt.savefig(buf, format='png')
            buf.seek(0)
            plot_data = base64.b64encode(buf.read()).decode('utf-8')
            plt.close()
            
            return f'<img src="data:image/png;base64,{plot_data}" alt="Plot">'
        
        numeric_columns = data.select_dtypes(include=[np.number]).columns.tolist()
        all_columns = data.columns.tolist()
        
        with self.gradio.Blocks() as interface:
            self.gradio.Markdown("# Interactive Plotting")
            
            with self.gradio.Row():
                plot_type = self.gradio.Dropdown(
                    choices=["Scatter", "Line", "Histogram", "Box", "Heatmap"],
                    value="Scatter",
                    label="Plot Type"
                )
                x_column = self.gradio.Dropdown(choices=all_columns, label="X Column")
                y_column = self.gradio.Dropdown(choices=numeric_columns, label="Y Column")
                color_column = self.gradio.Dropdown(choices=["None"] + all_columns, label="Color Column")
            
            plot_btn = self.gradio.Button("Generate Plot")
            plot_output = self.gradio.HTML()
            
            plot_btn.click(
                create_plot,
                inputs=[plot_type, x_column, y_column, color_column],
                outputs=plot_output
            )
        
        return interface
    
    def create_model_interface(self, model_predict_fn, feature_names: List[str]) -> Any:
        """Create an interface for model prediction"""
        def predict(*inputs):
            try:
                features = np.array(inputs).reshape(1, -1)
                prediction = model_predict_fn(features)
                return f"Prediction: {prediction[0] if hasattr(prediction, '__iter__') else prediction}"
            except Exception as e:
                return f"Error: {str(e)}"
        
        input_components = []
        for feature in feature_names:
            input_components.append(self.gradio.Number(label=feature))
        
        with self.gradio.Blocks() as interface:
            self.gradio.Markdown("# Model Prediction Interface")
            
            with self.gradio.Row():
                for component in input_components:
                    component.render()
            
            predict_btn = self.gradio.Button("Predict")
            output = self.gradio.Textbox(label="Prediction Result")
            
            predict_btn.click(
                predict,
                inputs=input_components,
                outputs=output
            )
        
        return interface
    
    def create_dashboard(self, data: pd.DataFrame, model_predict_fn=None) -> Any:
        """Create a comprehensive dashboard"""
        with self.gradio.Blocks() as dashboard:
            self.gradio.Markdown("# Data Science Dashboard")
            
            with self.gradio.Tabs():
                with self.gradio.TabItem("Data Viewer"):
                    self.create_data_viewer(data)
                
                with self.gradio.TabItem("Plots"):
                    self.create_plot_interface(data)
                
                if model_predict_fn:
                    with self.gradio.TabItem("Model Prediction"):
                        numeric_columns = data.select_dtypes(include=[np.number]).columns.tolist()
                        self.create_model_interface(model_predict_fn, numeric_columns)
        
        return dashboard
    
    def launch(self, interface: Any, share: bool = False, port: int = 7860) -> str:
        """Launch the Gradio interface"""
        try:
            interface.launch(share=share, port=port)
            return f"Interface launched on port {port}"
        except Exception as e:
            return f"Failed to launch interface: {str(e)}"
    
    def cache_data(self, key: str, data: Any) -> None:
        """Cache data for later use"""
        self.data_cache[key] = data
    
    def get_cached_data(self, key: str) -> Any:
        """Retrieve cached data"""
        return self.data_cache.get(key)
    
    def export_interface_config(self, interface: Any) -> Dict[str, Any]:
        """Export interface configuration"""
        return {
            "plugin": self.name,
            "version": self.version,
            "interface_type": type(interface).__name__,
            "config": {}
        }

# Plugin registration
plugin = GradioPlugin()

def get_plugin():
    """Get the plugin instance"""
    return plugin

def register_plugin():
    """Register the plugin with the system"""
    return {
        "name": plugin.name,
        "version": plugin.version,
        "description": plugin.description,
        "instance": plugin
    }