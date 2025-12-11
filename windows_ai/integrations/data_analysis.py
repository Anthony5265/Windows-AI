"""
Data Analysis Manager
PandasAI, Text-to-SQL, and AI-powered data analysis
"""

import asyncio
import logging
import os
from typing import Dict, List, Any, Optional
from windows_ai.config.unified_config import WindowsAIConfig

import asyncio
import logging
import os
from typing import Dict, List, Any, Optional, Union
from pathlib import Path
import pandas as pd

logger = logging.getLogger(__name__)

class DataAnalysisManager:
    """AI-powered data analysis with natural language"""

    def __init__(self):
        self._config: Optional[WindowsAIConfig] = None
        self._initialized = False
        self._dataframes: Dict[str, pd.DataFrame] = {}

    async def initialize(self, config: Optional[WindowsAIConfig] = None):
        if self._initialized:
            return
        
        self._config = config
        self._initialized = True
        logger.info("Data Analysis Manager initialized")

    async def cleanup(self):
        """Cleanup resources before shutdown"""
        try:
            # Close any open connections
            if hasattr(self, '_clients'):
                for client in self._clients.values():
                    if hasattr(client, 'close'):
                        await client.close() if asyncio.iscoroutinefunction(client.close) else client.close()
            
            # Reset initialization flag
            self._initialized = False
            logger.info(f"{self.__class__.__name__} cleanup completed")
            
        except Exception as e:
            logger.error(f"{self.__class__.__name__} cleanup failed: {e}")

    def load_csv(self, name: str, path: str) -> pd.DataFrame:
        """Load a CSV file"""
        df = pd.read_csv(path)
        self._dataframes[name] = df
        return df

    def load_excel(self, name: str, path: str, sheet: str = None) -> pd.DataFrame:
        """Load an Excel file"""
        df = pd.read_excel(path, sheet_name=sheet)
        self._dataframes[name] = df
        return df

    def load_json(self, name: str, path: str) -> pd.DataFrame:
        """Load a JSON file"""
        df = pd.read_json(path)
        self._dataframes[name] = df
        return df

    async def query(
        self,
        question: str,
        dataframe_name: str = None,
        llm_provider: str = "openai"
    ) -> Any:
        """Query data using natural language"""
        from windows_ai.integrations.ai_providers import AIProvidersManager, Provider

        df = self._dataframes.get(dataframe_name) if dataframe_name else list(self._dataframes.values())[0] if self._dataframes else None

        if df is None:
            raise ValueError("No dataframe loaded")

        # Get dataframe info
        info = {
            "columns": list(df.columns),
            "dtypes": df.dtypes.astype(str).to_dict(),
            "shape": df.shape,
            "sample": df.head(5).to_dict()
        }

        ai = AIProvidersManager()
        await ai.initialize()

        messages = [
            {"role": "system", "content": f"""You are a data analysis assistant. Given a pandas DataFrame with the following structure:
Columns: {info['columns']}
Data types: {info['dtypes']}
Shape: {info['shape']}
Sample data: {info['sample']}

Generate Python pandas code to answer the user's question. Return ONLY the code, no explanation."""},
            {"role": "user", "content": question}
        ]

        provider = Provider(llm_provider)
        response = await ai.chat(provider, messages)

        # Execute the generated code
        code = response["content"].strip()
        if code.startswith("```"):
            code = code.split("```")[1]
            if code.startswith("python"):
                code = code[6:]

        local_vars = {"df": df, "pd": pd}
        exec(code, {"pd": pd}, local_vars)

        # Return the result (usually stored in 'result' variable)
        return local_vars.get("result", local_vars.get("df", code))

    async def generate_sql(
        self,
        question: str,
        table_schema: Dict[str, Any],
        llm_provider: str = "openai"
    ) -> str:
        """Generate SQL from natural language"""
        from windows_ai.integrations.ai_providers import AIProvidersManager, Provider

        ai = AIProvidersManager()
        await ai.initialize()

        messages = [
            {"role": "system", "content": f"""You are a SQL expert. Generate SQL queries based on natural language questions.
Table schema: {table_schema}
Return ONLY the SQL query, no explanation."""},
            {"role": "user", "content": question}
        ]

        provider = Provider(llm_provider)
        response = await ai.chat(provider, messages)

        sql = response["content"].strip()
        if sql.startswith("```"):
            sql = sql.split("```")[1]
            if sql.startswith("sql"):
                sql = sql[3:]

        return sql.strip()

    async def analyze(
        self,
        dataframe_name: str = None,
        llm_provider: str = "openai"
    ) -> Dict[str, Any]:
        """Get AI-powered analysis of data"""
        from windows_ai.integrations.ai_providers import AIProvidersManager, Provider

        df = self._dataframes.get(dataframe_name) if dataframe_name else list(self._dataframes.values())[0] if self._dataframes else None

        if df is None:
            raise ValueError("No dataframe loaded")

        # Generate statistics
        stats = {
            "shape": df.shape,
            "columns": list(df.columns),
            "dtypes": df.dtypes.astype(str).to_dict(),
            "describe": df.describe().to_dict(),
            "missing": df.isnull().sum().to_dict(),
            "sample": df.head(10).to_dict()
        }

        ai = AIProvidersManager()
        await ai.initialize()

        messages = [
            {"role": "system", "content": "You are a data analyst. Analyze the dataset and provide insights including: 1) Data quality assessment 2) Key statistics 3) Patterns and trends 4) Recommendations for further analysis"},
            {"role": "user", "content": f"Analyze this dataset:\n{stats}"}
        ]

        provider = Provider(llm_provider)
        response = await ai.chat(provider, messages)

        return {
            "statistics": stats,
            "analysis": response["content"]
        }

    async def visualize(
        self,
        dataframe_name: str,
        chart_type: str,
        x: str = None,
        y: str = None,
        **kwargs
    ) -> str:
        """Generate visualization"""
        import matplotlib.pyplot as plt

        df = self._dataframes.get(dataframe_name)
        if df is None:
            raise ValueError(f"Dataframe '{dataframe_name}' not found")

        fig, ax = plt.subplots(figsize=kwargs.get("figsize", (10, 6)))

        if chart_type == "line":
            df.plot(x=x, y=y, kind="line", ax=ax)
        elif chart_type == "bar":
            df.plot(x=x, y=y, kind="bar", ax=ax)
        elif chart_type == "scatter":
            df.plot(x=x, y=y, kind="scatter", ax=ax)
        elif chart_type == "hist":
            df[y or x].plot(kind="hist", ax=ax, bins=kwargs.get("bins", 30))
        elif chart_type == "pie":
            df[y or x].value_counts().plot(kind="pie", ax=ax)
        elif chart_type == "box":
            df.boxplot(column=y, by=x, ax=ax)

        plt.title(kwargs.get("title", f"{chart_type.capitalize()} Chart"))
        plt.tight_layout()

        output_dir = Path.home() / ".windowsai" / "charts"
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = str(output_dir / f"chart_{hash(str(kwargs))}.png")

        plt.savefig(output_path, dpi=kwargs.get("dpi", 100))
        plt.close()

        return output_path

    def get_dataframes(self) -> List[str]:
        """List loaded dataframes"""
        return list(self._dataframes.keys())

    def get_info(self, name: str) -> Dict[str, Any]:
        """Get dataframe info"""
        df = self._dataframes.get(name)
        if df is None:
            return {}
        return {
            "columns": list(df.columns),
            "shape": df.shape,
            "dtypes": df.dtypes.astype(str).to_dict()
        }
