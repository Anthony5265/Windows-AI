"""
SQLCoder Plugin
Supports SQL-specialized code generation
"""

from typing import Dict, Any, Optional, List
import os


class SQLCoderPlugin:
    """Plugin for SQLCoder SQL generation model"""

    name = "sqlcoder"
    version = "1.0.0"
    description = "Integration with SQLCoder for SQL query generation"
    author = "Windows AI Team"

    def __init__(self):
        self.base_url: str = "http://localhost:11434"
        self.client = None
        self._initialized = False

    def initialize(self, config: Optional[Dict[str, Any]] = None) -> bool:
        """Initialize the SQLCoder plugin"""
        try:
            import requests

            self.base_url = (
                config.get("base_url") if config
                else os.getenv("SQLCODER_HOST", "http://localhost:11434")
            )

            self.client = requests
            self._initialized = True
            return True

        except ImportError:
            print("requests package not installed. Install with: pip install requests")
            return False
        except Exception as e:
            print(f"Error initializing SQLCoder plugin: {e}")
            return False

    def execute(self, action: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a SQLCoder action"""
        if not self._initialized:
            return {"success": False, "error": "Plugin not initialized"}

        try:
            if action == "generate":
                return self._generate_sql(params)
            elif action == "explain":
                return self._explain_sql(params)
            elif action == "optimize":
                return self._optimize_sql(params)
            elif action == "fix":
                return self._fix_sql(params)
            else:
                return {"success": False, "error": f"Unknown action: {action}"}

        except Exception as e:
            return {"success": False, "error": str(e)}

    def _generate_sql(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Generate SQL from natural language"""
        description = params.get("description", "")
        schema = params.get("schema", "")
        dialect = params.get("dialect", "PostgreSQL")
        model = params.get("model", "sqlcoder:latest")

        # Format prompt with schema and description
        prompt = f"""-- Database Schema:\n{schema}\n\n-- Task: {description}\n-- SQL ({dialect}):\n"""

        response = self.client.post(
            f"{self.base_url}/api/generate",
            json={
                "model": model,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.1
                }
            }
        )

        if response.status_code == 200:
            data = response.json()
            return {
                "success": True,
                "sql": data.get("response", "").strip()
            }
        return {"success": False, "error": response.text}

    def _explain_sql(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Explain SQL query"""
        sql = params.get("sql", "")

        prompt = f"Explain what this SQL query does:\n\n{sql}"

        response = self.client.post(
            f"{self.base_url}/api/generate",
            json={
                "model": "sqlcoder:latest",
                "prompt": prompt,
                "stream": False
            }
        )

        if response.status_code == 200:
            data = response.json()
            return {
                "success": True,
                "explanation": data.get("response", "")
            }
        return {"success": False, "error": response.text}

    def _optimize_sql(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Optimize SQL query"""
        sql = params.get("sql", "")
        schema = params.get("schema", "")

        prompt = f"""-- Schema:\n{schema}\n\n-- Original Query:\n{sql}\n\n-- Optimized Query:"""

        response = self.client.post(
            f"{self.base_url}/api/generate",
            json={
                "model": "sqlcoder:latest",
                "prompt": prompt,
                "stream": False
            }
        )

        if response.status_code == 200:
            data = response.json()
            return {
                "success": True,
                "optimized_sql": data.get("response", "")
            }
        return {"success": False, "error": response.text}

    def _fix_sql(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Fix SQL syntax errors"""
        sql = params.get("sql", "")
        error = params.get("error", "")

        prompt = f"Fix this SQL query:\n\nQuery:\n{sql}\n\nError:\n{error}\n\nCorrected Query:"

        response = self.client.post(
            f"{self.base_url}/api/generate",
            json={
                "model": "sqlcoder:latest",
                "prompt": prompt,
                "stream": False
            }
        )

        if response.status_code == 200:
            data = response.json()
            return {
                "success": True,
                "fixed_sql": data.get("response", "")
            }
        return {"success": False, "error": response.text}

    def shutdown(self) -> bool:
        """Cleanup plugin resources"""
        self._initialized = False
        self.client = None
        return True
