"""
New Relic DevOps Plugin
Integration with New Relic for application performance monitoring and observability
"""

from typing import Dict, Any, Optional, List
import os
import logging
import requests
from urllib.parse import urljoin


class NewRelicPlugin:
    """Plugin for New Relic APM and observability integration"""

    name = "newrelic"
    version = "1.0.0"
    description = "Integration with New Relic for application performance monitoring and observability"
    author = "Windows AI Team"

    def __init__(self):
        self.api_key: Optional[str] = None
        self.account_id: Optional[str] = None
        self.region: str = "us"  # Default to US region
        self.base_url: str = "https://api.newrelic.com/v2/"
        self.nerdgraph_url: str = "https://api.newrelic.com/graphql"
        self.session = None
        self._initialized = False
        self.logger = logging.getLogger(__name__)

    def initialize(self, config: Optional[Dict[str, Any]] = None) -> bool:
        """Initialize the New Relic plugin"""
        try:
            # Get New Relic configuration
            self.api_key = (
                config.get("api_key") if config
                else os.getenv("NEW_RELIC_API_KEY")
            )

            self.account_id = (
                config.get("account_id") if config
                else os.getenv("NEW_RELIC_ACCOUNT_ID")
            )

            self.region = (
                config.get("region", "us") if config
                else os.getenv("NEW_RELIC_REGION", "us")
            )

            if not self.api_key:
                self.logger.error("New Relic API key not provided")
                return False

            if not self.account_id:
                self.logger.error("New Relic account ID not provided")
                return False

            # Set base URL based on region
            if self.region == "eu":
                self.base_url = "https://api.eu.newrelic.com/v2/"
                self.nerdgraph_url = "https://api.eu.newrelic.com/graphql"
            elif self.region == "staging":
                self.base_url = "https://staging-api.newrelic.com/v2/"
                self.nerdgraph_url = "https://staging-api.newrelic.com/graphql"

            # Create session for API calls
            self.session = requests.Session()
            self.session.headers.update({
                "X-Api-Key": self.api_key,
                "Content-Type": "application/json"
            })

            # Test connection with a simple API call
            test_url = f"{self.base_url}applications.json"
            response = self.session.get(test_url, timeout=10)
            response.raise_for_status()

            self._initialized = True
            self.logger.info("New Relic plugin initialized successfully")
            return True

        except Exception as e:
            self.logger.error(f"Error initializing New Relic plugin: {e}")
            return False

    def execute(self, action: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a New Relic action"""
        if not self._initialized:
            return {"error": "Plugin not initialized. Please provide New Relic API key and account ID."}

        try:
            if action == "get_applications":
                return self._get_applications(params)
            elif action == "get_application_metrics":
                return self._get_application_metrics(params)
            elif action == "create_deployment_marker":
                return self._create_deployment_marker(params)
            elif action == "get_alert_violations":
                return self._get_alert_violations(params)
            elif action == "query_nrql":
                return self._query_nrql(params)
            elif action == "get_infrastructure_hosts":
                return self._get_infrastructure_hosts(params)
            else:
                return {"error": f"Unknown action: {action}"}

        except Exception as e:
            self.logger.error(f"Error executing action {action}: {e}")
            return {"error": str(e)}

    def _get_applications(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get list of New Relic applications"""
        try:
            url = f"{self.base_url}applications.json"
            params_filter = {
                "filter[ids]": params.get("app_ids"),
                "filter[name]": params.get("name"),
                "filter[host]": params.get("host"),
                "page": params.get("page", 1)
            }
            # Remove None values
            params_filter = {k: v for k, v in params_filter.items() if v is not None}

            response = self.session.get(url, params=params_filter, timeout=10)
            response.raise_for_status()

            data = response.json()
            applications = data.get("applications", [])

            return {
                "success": True,
                "applications": applications,
                "total_count": len(applications)
            }

        except Exception as e:
            return {"error": f"Failed to get applications: {e}"}

    def _get_application_metrics(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get metrics for a specific application"""
        app_id = params.get("app_id")
        if not app_id:
            return {"error": "Application ID not provided"}

        try:
            url = f"{self.base_url}applications/{app_id}/metrics.json"
            
            # Build query parameters
            query_params = {
                "name": params.get("metric_names", []),
                "period": params.get("period", "3600"),  # Default to 1 hour
                "from": params.get("from_time"),
                "to": params.get("to_time"),
                "summary": params.get("summary", "true")
            }
            # Remove None values
            query_params = {k: v for k, v in query_params.items() if v is not None}

            response = self.session.get(url, params=query_params, timeout=10)
            response.raise_for_status()

            data = response.json()
            metrics = data.get("metrics", [])

            return {
                "success": True,
                "app_id": app_id,
                "metrics": metrics,
                "total_count": len(metrics)
            }

        except Exception as e:
            return {"error": f"Failed to get application metrics: {e}"}

    def _create_deployment_marker(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Create a deployment marker in New Relic"""
        app_id = params.get("app_id")
        if not app_id:
            return {"error": "Application ID not provided"}

        try:
            url = f"{self.base_url}applications/{app_id}/deployments.json"
            
            deployment_data = {
                "deployment": {
                    "revision": params.get("revision"),
                    "changelog": params.get("changelog"),
                    "description": params.get("description"),
                    "user": params.get("user"),
                    "timestamp": params.get("timestamp")
                }
            }
            # Remove None values from deployment data
            deployment_data["deployment"] = {k: v for k, v in deployment_data["deployment"].items() if v is not None}

            response = self.session.post(url, json=deployment_data, timeout=10)
            response.raise_for_status()

            data = response.json()
            deployment = data.get("deployment", {})

            return {
                "success": True,
                "app_id": app_id,
                "deployment": deployment,
                "message": "Deployment marker created successfully"
            }

        except Exception as e:
            return {"error": f"Failed to create deployment marker: {e}"}

    def _get_alert_violations(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get alert violations"""
        try:
            url = f"{self.base_url}violations.json"
            
            query_params = {
                "only_open": params.get("only_open", "true"),
                "start_time": params.get("start_time"),
                "end_time": params.get("end_time")
            }
            # Remove None values
            query_params = {k: v for k, v in query_params.items() if v is not None}

            response = self.session.get(url, params=query_params, timeout=10)
            response.raise_for_status()

            data = response.json()
            violations = data.get("violations", [])

            return {
                "success": True,
                "violations": violations,
                "total_count": len(violations)
            }

        except Exception as e:
            return {"error": f"Failed to get alert violations: {e}"}

    def _query_nrql(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a NRQL (New Relic Query Language) query"""
        query = params.get("query")
        if not query:
            return {"error": "NRQL query not provided"}

        try:
            # Use NerdGraph API for NRQL queries
            graphql_query = {
                "query": f"""
                {{
                    actor {{
                        account(id: {self.account_id}) {{
                            nrql(query: "{query}")
                        }}
                    }}
                }}
                """
            }

            response = self.session.post(self.nerdgraph_url, json=graphql_query, timeout=30)
            response.raise_for_status()

            data = response.json()
            nrql_result = data.get("data", {}).get("actor", {}).get("account", {}).get("nrql", {})

            return {
                "success": True,
                "query": query,
                "results": nrql_result,
                "message": "NRQL query executed successfully"
            }

        except Exception as e:
            return {"error": f"Failed to execute NRQL query: {e}"}

    def _get_infrastructure_hosts(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get infrastructure hosts"""
        try:
            # Use NerdGraph API for infrastructure data
            graphql_query = {
                "query": f"""
                {{
                    actor {{
                        account(id: {self.account_id}) {{
                            infrastructureSearch(query: "{params.get('query', '')}") {{
                                results {{
                                    entity {{
                                        name
                                        hostname
                                        id
                                        entityType
                                        reporting
                                        lastReportingChangeAt
                                    }}
                                }}
                                totalCount
                            }}
                        }}
                    }}
                }}
                """
            }

            response = self.session.post(self.nerdgraph_url, json=graphql_query, timeout=30)
            response.raise_for_status()

            data = response.json()
            search_result = data.get("data", {}).get("actor", {}).get("account", {}).get("infrastructureSearch", {})
            
            hosts = []
            for result in search_result.get("results", []):
                entity = result.get("entity", {})
                hosts.append({
                    "id": entity.get("id"),
                    "name": entity.get("name"),
                    "hostname": entity.get("hostname"),
                    "entity_type": entity.get("entityType"),
                    "reporting": entity.get("reporting"),
                    "last_reporting_change": entity.get("lastReportingChangeAt")
                })

            return {
                "success": True,
                "hosts": hosts,
                "total_count": search_result.get("totalCount", 0)
            }

        except Exception as e:
            return {"error": f"Failed to get infrastructure hosts: {e}"}

    def cleanup(self):
        """Cleanup resources"""
        if self.session:
            self.session.close()
        self.session = None
        self._initialized = False


# Plugin metadata
PLUGIN_CLASS = NewRelicPlugin
PLUGIN_NAME = "newrelic"
PLUGIN_VERSION = "1.0.0"
PLUGIN_DESCRIPTION = "Integration with New Relic for application performance monitoring and observability"
PLUGIN_ACTIONS = ["get_applications", "get_application_metrics", "create_deployment_marker", "get_alert_violations", "query_nrql", "get_infrastructure_hosts"]