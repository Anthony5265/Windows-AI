"""
Matplotlib Plugin for Data Science Visualization
Provides comprehensive plotting and visualization capabilities
"""

from typing import Dict, Any, Optional, List, Union
import os
import io
import base64


class MatplotlibPlugin:
    """Plugin for Matplotlib data visualization"""
    
    name = "matplotlib"
    version = "1.0.0"
    description = "Data visualization with Matplotlib"
    author = "Windows AI Team"
    
    def __init__(self):
        self.plt = None
        self.np = None
        self._initialized = False
        
    def initialize(self, config: Optional[Dict[str, Any]] = None) -> bool:
        """Initialize the Matplotlib plugin"""
        try:
            import matplotlib
            matplotlib.use('Agg')  # Use non-interactive backend
            import matplotlib.pyplot as plt
            import numpy as np
            
            self.plt = plt
            self.np = np
            
            # Set default style
            if config and config.get("style"):
                plt.style.use(config["style"])
            else:
                plt.style.use('default')
                
            self._initialized = True
            return True
            
        except ImportError:
            print("matplotlib package not installed. Install with: pip install matplotlib numpy")
            return False
        except Exception as e:
            print(f"Error initializing Matplotlib plugin: {e}")
            return False
    
    def execute(self, action: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a Matplotlib action"""
        if not self._initialized:
            return {"error": "Plugin not initialized"}
        
        try:
            if action == "line_plot":
                return self._line_plot(params)
            elif action == "scatter_plot":
                return self._scatter_plot(params)
            elif action == "bar_plot":
                return self._bar_plot(params)
            elif action == "histogram":
                return self._histogram(params)
            elif action == "box_plot":
                return self._box_plot(params)
            elif action == "heatmap":
                return self._heatmap(params)
            elif action == "pie_chart":
                return self._pie_chart(params)
            elif action == "subplots":
                return self._subplots(params)
            elif action == "3d_plot":
                return self._3d_plot(params)
            elif action == "contour_plot":
                return self._contour_plot(params)
            elif action == "save_plot":
                return self._save_plot(params)
            elif action == "custom_plot":
                return self._custom_plot(params)
            else:
                return {"error": f"Unknown action: {action}"}
                
        except Exception as e:
            return {"error": str(e)}
    
    def _line_plot(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Create a line plot"""
        x = params.get("x", [])
        y = params.get("y", [])
        title = params.get("title", "Line Plot")
        xlabel = params.get("xlabel", "X")
        ylabel = params.get("ylabel", "Y")
        color = params.get("color", "blue")
        linewidth = params.get("linewidth", 2)
        grid = params.get("grid", True)
        
        fig, ax = self.plt.subplots(figsize=(10, 6))
        ax.plot(x, y, color=color, linewidth=linewidth)
        ax.set_title(title)
        ax.set_xlabel(xlabel)
        ax.set_ylabel(ylabel)
        if grid:
            ax.grid(True, alpha=0.3)
        
        return self._save_figure_to_base64(fig)
    
    def _scatter_plot(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Create a scatter plot"""
        x = params.get("x", [])
        y = params.get("y", [])
        title = params.get("title", "Scatter Plot")
        xlabel = params.get("xlabel", "X")
        ylabel = params.get("ylabel", "Y")
        color = params.get("color", "blue")
        size = params.get("size", 50)
        alpha = params.get("alpha", 0.7)
        grid = params.get("grid", True)
        
        fig, ax = self.plt.subplots(figsize=(10, 6))
        ax.scatter(x, y, c=color, s=size, alpha=alpha)
        ax.set_title(title)
        ax.set_xlabel(xlabel)
        ax.set_ylabel(ylabel)
        if grid:
            ax.grid(True, alpha=0.3)
        
        return self._save_figure_to_base64(fig)
    
    def _bar_plot(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Create a bar plot"""
        categories = params.get("categories", [])
        values = params.get("values", [])
        title = params.get("title", "Bar Plot")
        xlabel = params.get("xlabel", "Categories")
        ylabel = params.get("ylabel", "Values")
        color = params.get("color", "blue")
        orientation = params.get("orientation", "vertical")
        
        fig, ax = self.plt.subplots(figsize=(10, 6))
        
        if orientation == "horizontal":
            ax.barh(categories, values, color=color)
        else:
            ax.bar(categories, values, color=color)
            
        ax.set_title(title)
        ax.set_xlabel(xlabel)
        ax.set_ylabel(ylabel)
        
        # Rotate x-axis labels if there are many categories
        if len(categories) > 5:
            self.plt.xticks(rotation=45)
        
        return self._save_figure_to_base64(fig)
    
    def _histogram(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Create a histogram"""
        data = params.get("data", [])
        bins = params.get("bins", 30)
        title = params.get("title", "Histogram")
        xlabel = params.get("xlabel", "Value")
        ylabel = params.get("ylabel", "Frequency")
        color = params.get("color", "blue")
        alpha = params.get("alpha", 0.7)
        density = params.get("density", False)
        
        fig, ax = self.plt.subplots(figsize=(10, 6))
        ax.hist(data, bins=bins, color=color, alpha=alpha, density=density)
        ax.set_title(title)
        ax.set_xlabel(xlabel)
        ax.set_ylabel(ylabel)
        ax.grid(True, alpha=0.3)
        
        return self._save_figure_to_base64(fig)
    
    def _box_plot(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Create a box plot"""
        data = params.get("data", [])
        title = params.get("title", "Box Plot")
        labels = params.get("labels", [])
        
        fig, ax = self.plt.subplots(figsize=(10, 6))
        ax.boxplot(data, labels=labels)
        ax.set_title(title)
        ax.grid(True, alpha=0.3)
        
        return self._save_figure_to_base64(fig)
    
    def _heatmap(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Create a heatmap"""
        data = params.get("data", [])
        title = params.get("title", "Heatmap")
        cmap = params.get("cmap", "viridis")
        annot = params.get("annot", True)
        fmt = params.get("fmt", ".2f")
        
        fig, ax = self.plt.subplots(figsize=(10, 8))
        
        # Convert to numpy array if needed
        if isinstance(data, list):
            data = self.np.array(data)
            
        im = ax.imshow(data, cmap=cmap)
        
        if annot:
            # Add text annotations
            for i in range(data.shape[0]):
                for j in range(data.shape[1]):
                    text = ax.text(j, i, format(data[i, j], fmt),
                                 ha="center", va="center", color="black")
        
        ax.set_title(title)
        fig.colorbar(im)
        
        return self._save_figure_to_base64(fig)
    
    def _pie_chart(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Create a pie chart"""
        sizes = params.get("sizes", [])
        labels = params.get("labels", [])
        title = params.get("title", "Pie Chart")
        explode = params.get("explode", None)
        autopct = params.get("autopct", "%1.1f%%")
        
        fig, ax = self.plt.subplots(figsize=(8, 8))
        ax.pie(sizes, labels=labels, explode=explode, autopct=autopct, startangle=90)
        ax.set_title(title)
        
        return self._save_figure_to_base64(fig)
    
    def _subplots(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Create multiple subplots"""
        plots = params.get("plots", [])
        rows = params.get("rows", 2)
        cols = params.get("cols", 2)
        figsize = params.get("figsize", (12, 8))
        title = params.get("title", "Subplots")
        
        fig, axes = self.plt.subplots(rows, cols, figsize=figsize)
        fig.suptitle(title)
        
        if rows == 1 and cols == 1:
            axes = [axes]
        elif rows == 1 or cols == 1:
            axes = axes.flatten()
        else:
            axes = axes.flatten()
        
        for i, plot_config in enumerate(plots[:len(axes)]):
            ax = axes[i]
            plot_type = plot_config.get("type", "line")
            
            if plot_type == "line":
                ax.plot(plot_config.get("x", []), plot_config.get("y", []))
            elif plot_type == "scatter":
                ax.scatter(plot_config.get("x", []), plot_config.get("y", []))
            elif plot_type == "bar":
                ax.bar(plot_config.get("categories", []), plot_config.get("values", []))
            elif plot_type == "hist":
                ax.hist(plot_config.get("data", []))
            
            ax.set_title(plot_config.get("title", f"Plot {i+1}"))
            ax.grid(True, alpha=0.3)
        
        # Hide unused subplots
        for i in range(len(plots), len(axes)):
            axes[i].set_visible(False)
        
        return self._save_figure_to_base64(fig)
    
    def _3d_plot(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Create a 3D plot"""
        plot_type = params.get("plot_type", "surface")
        title = params.get("title", "3D Plot")
        
        fig = self.plt.figure(figsize=(10, 8))
        ax = fig.add_subplot(111, projection='3d')
        
        if plot_type == "surface":
            x = params.get("x", [])
            y = params.get("y", [])
            z = params.get("z", [])
            X, Y = self.np.meshgrid(x, y)
            Z = self.np.array(z).reshape(X.shape)
            ax.plot_surface(X, Y, Z, cmap='viridis')
        elif plot_type == "scatter3d":
            x = params.get("x", [])
            y = params.get("y", [])
            z = params.get("z", [])
            ax.scatter(x, y, z)
        elif plot_type == "line3d":
            x = params.get("x", [])
            y = params.get("y", [])
            z = params.get("z", [])
            ax.plot(x, y, z)
        
        ax.set_title(title)
        
        return self._save_figure_to_base64(fig)
    
    def _contour_plot(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Create a contour plot"""
        x = params.get("x", [])
        y = params.get("y", [])
        z = params.get("z", [])
        title = params.get("title", "Contour Plot")
        levels = params.get("levels", 20)
        filled = params.get("filled", True)
        
        fig, ax = self.plt.subplots(figsize=(10, 8))
        X, Y = self.np.meshgrid(x, y)
        Z = self.np.array(z).reshape(X.shape)
        
        if filled:
            contour = ax.contourf(X, Y, Z, levels=levels)
        else:
            contour = ax.contour(X, Y, Z, levels=levels)
        
        fig.colorbar(contour)
        ax.set_title(title)
        
        return self._save_figure_to_base64(fig)
    
    def _save_plot(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Save current plot to file"""
        filename = params.get("filename", "plot.png")
        dpi = params.get("dpi", 300)
        format = params.get("format", "png")
        
        try:
            self.plt.savefig(filename, dpi=dpi, format=format, bbox_inches='tight')
            self.plt.close()
            return {"success": True, "filename": filename}
        except Exception as e:
            return {"error": str(e)}
    
    def _custom_plot(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute custom matplotlib code"""
        code = params.get("code", "")
        
        try:
            # Create a safe namespace for execution
            namespace = {
                'plt': self.plt,
                'np': self.np,
                'fig': None,
                'ax': None
            }
            
            exec(code, namespace)
            
            fig = namespace.get('fig')
            if fig is None:
                # Try to get current figure
                fig = self.plt.gcf()
            
            return self._save_figure_to_base64(fig)
            
        except Exception as e:
            return {"error": f"Error executing custom code: {str(e)}"}
    
    def _save_figure_to_base64(self, fig) -> Dict[str, Any]:
        """Save figure to base64 string"""
        try:
            buffer = io.BytesIO()
            fig.savefig(buffer, format='png', bbox_inches='tight', dpi=150)
            buffer.seek(0)
            image_base64 = base64.b64encode(buffer.getvalue()).decode()
            self.plt.close(fig)
            
            return {
                "success": True,
                "image_base64": image_base64,
                "format": "png"
            }
        except Exception as e:
            self.plt.close(fig)
            return {"error": f"Error saving figure: {str(e)}"}
    
    def cleanup(self):
        """Cleanup resources"""
        self.plt.close('all')
        self._initialized = False


# Plugin metadata
PLUGIN_CLASS = MatplotlibPlugin
PLUGIN_NAME = "matplotlib"
PLUGIN_VERSION = "1.0.0"
PLUGIN_DESCRIPTION = "Data visualization with Matplotlib"
PLUGIN_ACTIONS = [
    "line_plot", "scatter_plot", "bar_plot", "histogram", "box_plot",
    "heatmap", "pie_chart", "subplots", "3d_plot", "contour_plot",
    "save_plot", "custom_plot"
]