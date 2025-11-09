"""
Plotly Data Visualization Plugin
Supports interactive charts and plots for data science
"""

from typing import Dict, Any, Optional, List, Union
import os
import json
import base64
import io


class PlotlyPlugin:
    """Plugin for Plotly data visualization"""

    name = "plotly"
    version = "1.0.0"
    description = "Interactive data visualization with Plotly"
    author = "Windows AI Team"

    def __init__(self):
        self._initialized = False

    def initialize(self, config: Optional[Dict[str, Any]] = None) -> bool:
        """Initialize the Plotly plugin"""
        try:
            import plotly
            import plotly.graph_objects as go
            import plotly.express as px
            import pandas as pd
            import numpy as np
            
            self.plotly = plotly
            self.go = go
            self.px = px
            self.pd = pd
            self.np = np
            self._initialized = True
            return True

        except ImportError as e:
            missing_packages = []
            try:
                import plotly
            except ImportError:
                missing_packages.append("plotly")
            try:
                import pandas
            except ImportError:
                missing_packages.append("pandas")
            try:
                import numpy
            except ImportError:
                missing_packages.append("numpy")
            
            print(f"Missing required packages: {', '.join(missing_packages)}")
            print(f"Install with: pip install {' '.join(missing_packages)}")
            return False
        except Exception as e:
            print(f"Error initializing Plotly plugin: {e}")
            return False

    def execute(self, action: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a Plotly action"""
        if not self._initialized:
            return {"error": "Plugin not initialized. Required packages not available."}

        try:
            if action == "scatter_plot":
                return self._scatter_plot(params)
            elif action == "line_plot":
                return self._line_plot(params)
            elif action == "bar_chart":
                return self._bar_chart(params)
            elif action == "histogram":
                return self._histogram(params)
            elif action == "box_plot":
                return self._box_plot(params)
            elif action == "heatmap":
                return self._heatmap(params)
            elif action == "3d_scatter":
                return self._3d_scatter(params)
            elif action == "3d_surface":
                return self._3d_surface(params)
            elif action == "pie_chart":
                return self._pie_chart(params)
            elif action == "violin_plot":
                return self._violin_plot(params)
            elif action == "sunburst":
                return self._sunburst(params)
            elif action == "treemap":
                return self._treemap(params)
            elif action == "correlation_matrix":
                return self._correlation_matrix(params)
            elif action == "distribution_plot":
                return self._distribution_plot(params)
            elif action == "time_series":
                return self._time_series(params)
            elif action == "save_plot":
                return self._save_plot(params)
            else:
                return {"error": f"Unknown action: {action}"}

        except Exception as e:
            return {"error": str(e)}

    def _prepare_data(self, data: Union[List, Dict, str]) -> Any:
        """Prepare data for plotting"""
        if isinstance(data, str):
            # Assume it's a path to a CSV file
            if os.path.exists(data):
                return self.pd.read_csv(data)
            else:
                raise ValueError(f"File not found: {data}")
        elif isinstance(data, dict):
            # Convert dict to DataFrame
            return self.pd.DataFrame(data)
        elif isinstance(data, list):
            # Convert list to DataFrame/Series as appropriate
            if all(isinstance(item, dict) for item in data):
                return self.pd.DataFrame(data)
            else:
                return self.pd.Series(data)
        else:
            return data

    def _scatter_plot(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Create a scatter plot"""
        data = self._prepare_data(params.get("data", []))
        x = params.get("x")
        y = params.get("y")
        color = params.get("color")
        size = params.get("size")
        title = params.get("title", "Scatter Plot")
        width = params.get("width", 800)
        height = params.get("height", 600)

        if isinstance(data, self.pd.DataFrame):
            fig = self.px.scatter(
                data, x=x, y=y, color=color, size=size,
                title=title, width=width, height=height
            )
        else:
            fig = self.go.Figure()
            fig.add_trace(self.go.Scatter(
                x=data if x is None else x,
                y=y,
                mode='markers',
                name='Data'
            ))
            fig.update_layout(title=title, width=width, height=height)

        return self._figure_to_dict(fig)

    def _line_plot(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Create a line plot"""
        data = self._prepare_data(params.get("data", []))
        x = params.get("x")
        y = params.get("y")
        color = params.get("color")
        title = params.get("title", "Line Plot")
        width = params.get("width", 800)
        height = params.get("height", 600)

        if isinstance(data, self.pd.DataFrame):
            fig = self.px.line(
                data, x=x, y=y, color=color,
                title=title, width=width, height=height
            )
        else:
            fig = self.go.Figure()
            fig.add_trace(self.go.Scatter(
                x=data if x is None else x,
                y=y,
                mode='lines',
                name='Data'
            ))
            fig.update_layout(title=title, width=width, height=height)

        return self._figure_to_dict(fig)

    def _bar_chart(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Create a bar chart"""
        data = self._prepare_data(params.get("data", []))
        x = params.get("x")
        y = params.get("y")
        color = params.get("color")
        title = params.get("title", "Bar Chart")
        width = params.get("width", 800)
        height = params.get("height", 600)

        if isinstance(data, self.pd.DataFrame):
            fig = self.px.bar(
                data, x=x, y=y, color=color,
                title=title, width=width, height=height
            )
        else:
            fig = self.go.Figure()
            fig.add_trace(self.go.Bar(
                x=data if x is None else x,
                y=y,
                name='Data'
            ))
            fig.update_layout(title=title, width=width, height=height)

        return self._figure_to_dict(fig)

    def _histogram(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Create a histogram"""
        data = self._prepare_data(params.get("data", []))
        x = params.get("x")
        color = params.get("color")
        nbins = params.get("nbins")
        title = params.get("title", "Histogram")
        width = params.get("width", 800)
        height = params.get("height", 600)

        if isinstance(data, self.pd.DataFrame):
            fig = self.px.histogram(
                data, x=x, color=color, nbins=nbins,
                title=title, width=width, height=height
            )
        else:
            fig = self.go.Figure()
            fig.add_trace(self.go.Histogram(
                x=data if x is None else x,
                nbinsx=nbins or 30,
                name='Data'
            ))
            fig.update_layout(title=title, width=width, height=height)

        return self._figure_to_dict(fig)

    def _box_plot(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Create a box plot"""
        data = self._prepare_data(params.get("data", []))
        x = params.get("x")
        y = params.get("y")
        color = params.get("color")
        title = params.get("title", "Box Plot")
        width = params.get("width", 800)
        height = params.get("height", 600)

        if isinstance(data, self.pd.DataFrame):
            fig = self.px.box(
                data, x=x, y=y, color=color,
                title=title, width=width, height=height
            )
        else:
            fig = self.go.Figure()
            fig.add_trace(self.go.Box(
                y=data if y is None else y,
                name='Data'
            ))
            fig.update_layout(title=title, width=width, height=height)

        return self._figure_to_dict(fig)

    def _heatmap(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Create a heatmap"""
        data = params.get("data")
        x = params.get("x")
        y = params.get("y")
        colorscale = params.get("colorscale", "Viridis")
        title = params.get("title", "Heatmap")
        width = params.get("width", 800)
        height = params.get("height", 600)

        if isinstance(data, self.pd.DataFrame):
            fig = self.px.imshow(
                data, color_continuous_scale=colorscale,
                title=title, width=width, height=height
            )
        else:
            fig = self.go.Figure(data=self.go.Heatmap(
                z=data,
                x=x,
                y=y,
                colorscale=colorscale
            ))
            fig.update_layout(title=title, width=width, height=height)

        return self._figure_to_dict(fig)

    def _3d_scatter(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Create a 3D scatter plot"""
        data = self._prepare_data(params.get("data", []))
        x = params.get("x")
        y = params.get("y")
        z = params.get("z")
        color = params.get("color")
        size = params.get("size")
        title = params.get("title", "3D Scatter Plot")
        width = params.get("width", 800)
        height = params.get("height", 600)

        if isinstance(data, self.pd.DataFrame):
            fig = self.px.scatter_3d(
                data, x=x, y=y, z=z, color=color, size=size,
                title=title, width=width, height=height
            )
        else:
            fig = self.go.Figure()
            fig.add_trace(self.go.Scatter3d(
                x=data[0] if isinstance(data, list) and len(data) > 0 else x,
                y=data[1] if isinstance(data, list) and len(data) > 1 else y,
                z=data[2] if isinstance(data, list) and len(data) > 2 else z,
                mode='markers',
                name='Data'
            ))
            fig.update_layout(title=title, width=width, height=height)

        return self._figure_to_dict(fig)

    def _3d_surface(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Create a 3D surface plot"""
        data = params.get("data")
        colorscale = params.get("colorscale", "Viridis")
        title = params.get("title", "3D Surface Plot")
        width = params.get("width", 800)
        height = params.get("height", 600)

        fig = self.go.Figure(data=self.go.Surface(
            z=data,
            colorscale=colorscale
        ))
        fig.update_layout(title=title, width=width, height=height)

        return self._figure_to_dict(fig)

    def _pie_chart(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Create a pie chart"""
        data = self._prepare_data(params.get("data", []))
        names = params.get("names")
        values = params.get("values")
        title = params.get("title", "Pie Chart")
        width = params.get("width", 800)
        height = params.get("height", 600)

        if isinstance(data, self.pd.DataFrame):
            fig = self.px.pie(
                data, names=names, values=values,
                title=title, width=width, height=height
            )
        else:
            fig = self.go.Figure(data=self.go.Pie(
                labels=names,
                values=values
            ))
            fig.update_layout(title=title, width=width, height=height)

        return self._figure_to_dict(fig)

    def _violin_plot(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Create a violin plot"""
        data = self._prepare_data(params.get("data", []))
        x = params.get("x")
        y = params.get("y")
        color = params.get("color")
        title = params.get("title", "Violin Plot")
        width = params.get("width", 800)
        height = params.get("height", 600)

        if isinstance(data, self.pd.DataFrame):
            fig = self.px.violin(
                data, x=x, y=y, color=color,
                title=title, width=width, height=height
            )
        else:
            fig = self.go.Figure()
            fig.add_trace(self.go.Violin(
                y=data if y is None else y,
                name='Data'
            ))
            fig.update_layout(title=title, width=width, height=height)

        return self._figure_to_dict(fig)

    def _sunburst(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Create a sunburst chart"""
        data = self._prepare_data(params.get("data", []))
        names = params.get("names")
        parents = params.get("parents")
        values = params.get("values")
        title = params.get("title", "Sunburst Chart")
        width = params.get("width", 800)
        height = params.get("height", 600)

        if isinstance(data, self.pd.DataFrame):
            fig = self.px.sunburst(
                data, names=names, parents=parents, values=values,
                title=title, width=width, height=height
            )
        else:
            fig = self.go.Figure(data=self.go.Sunburst(
                labels=names,
                parents=parents,
                values=values
            ))
            fig.update_layout(title=title, width=width, height=height)

        return self._figure_to_dict(fig)

    def _treemap(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Create a treemap"""
        data = self._prepare_data(params.get("data", []))
        names = params.get("names")
        parents = params.get("parents")
        values = params.get("values")
        title = params.get("title", "Treemap")
        width = params.get("width", 800)
        height = params.get("height", 600)

        if isinstance(data, self.pd.DataFrame):
            fig = self.px.treemap(
                data, names=names, parents=parents, values=values,
                title=title, width=width, height=height
            )
        else:
            fig = self.go.Figure(data=self.go.Treemap(
                labels=names,
                parents=parents,
                values=values
            ))
            fig.update_layout(title=title, width=width, height=height)

        return self._figure_to_dict(fig)

    def _correlation_matrix(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Create a correlation matrix heatmap"""
        data = self._prepare_data(params.get("data", []))
        title = params.get("title", "Correlation Matrix")
        width = params.get("width", 800)
        height = params.get("height", 600)

        if not isinstance(data, self.pd.DataFrame):
            data = self.pd.DataFrame(data)

        corr_matrix = data.corr()
        fig = self.px.imshow(
            corr_matrix,
            text_auto=True,
            aspect="auto",
            title=title,
            width=width,
            height=height
        )

        return self._figure_to_dict(fig)

    def _distribution_plot(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Create a distribution plot"""
        data = self._prepare_data(params.get("data", []))
        x = params.get("x")
        color = params.get("color")
        title = params.get("title", "Distribution Plot")
        width = params.get("width", 800)
        height = params.get("height", 600)

        if isinstance(data, self.pd.DataFrame):
            fig = self.px.histogram(
                data, x=x, color=color, marginal="box",
                title=title, width=width, height=height
            )
        else:
            fig = self.go.Figure()
            fig.add_trace(self.go.Histogram(
                x=data if x is None else x,
                name='Distribution'
            ))
            fig.update_layout(title=title, width=width, height=height)

        return self._figure_to_dict(fig)

    def _time_series(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Create a time series plot"""
        data = self._prepare_data(params.get("data", []))
        x = params.get("x")
        y = params.get("y")
        title = params.get("title", "Time Series")
        width = params.get("width", 800)
        height = params.get("height", 600)

        if isinstance(data, self.pd.DataFrame):
            fig = self.px.line(
                data, x=x, y=y,
                title=title, width=width, height=height
            )
        else:
            fig = self.go.Figure()
            fig.add_trace(self.go.Scatter(
                x=data if x is None else x,
                y=y,
                mode='lines',
                name='Time Series'
            ))
            fig.update_layout(title=title, width=width, height=height)

        return self._figure_to_dict(fig)

    def _save_plot(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Save plot to file"""
        fig_dict = params.get("figure")
        filename = params.get("filename", "plot.html")
        format_type = params.get("format", "html")

        if not fig_dict:
            return {"error": "figure parameter is required"}

        try:
            # Reconstruct figure from dict
            fig = self.go.Figure(fig_dict)

            if format_type.lower() == "html":
                fig.write_html(filename)
            elif format_type.lower() == "png":
                fig.write_image(filename)
            elif format_type.lower() == "pdf":
                fig.write_image(filename)
            elif format_type.lower() == "svg":
                fig.write_image(filename)
            else:
                return {"error": f"Unsupported format: {format_type}"}

            return {
                "success": True,
                "filename": filename,
                "format": format_type
            }

        except Exception as e:
            return {"error": f"Failed to save plot: {str(e)}"}

    def _figure_to_dict(self, fig) -> Dict[str, Any]:
        """Convert Plotly figure to dictionary"""
        try:
            fig_dict = fig.to_dict()
            
            # Also include HTML representation for easy display
            html_str = fig.to_html(include_plotlyjs='cdn')
            
            return {
                "figure": fig_dict,
                "html": html_str,
                "success": True
            }
        except Exception as e:
            return {"error": f"Failed to convert figure: {str(e)}"}

    def cleanup(self):
        """Cleanup resources"""
        self._initialized = False


# Plugin metadata for registration
PLUGIN_CLASS = PlotlyPlugin
PLUGIN_NAME = "plotly"
PLUGIN_VERSION = "1.0.0"
PLUGIN_DESCRIPTION = "Interactive data visualization with Plotly"
PLUGIN_ACTIONS = [
    "scatter_plot", "line_plot", "bar_chart", "histogram", "box_plot",
    "heatmap", "3d_scatter", "3d_surface", "pie_chart", "violin_plot",
    "sunburst", "treemap", "correlation_matrix", "distribution_plot",
    "time_series", "save_plot"
]