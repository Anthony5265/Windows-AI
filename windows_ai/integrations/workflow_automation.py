"""
Workflow Automation Manager - 20+ Services
n8n, Zapier, Make, Pipedream, and more
"""

import asyncio
import logging
import os
from typing import Dict, List, Any, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class WorkflowStep:
    action: str
    params: Dict[str, Any]
    condition: Optional[str] = None

class WorkflowAutomationManager:
    """Unified workflow automation across 20+ platforms"""

    def __init__(self):
        self._initialized = False
        self._workflows: Dict[str, List[WorkflowStep]] = {}

    async def initialize(self, config: Optional[Dict] = None):
        if self._initialized:
            return
        self._initialized = True
        logger.info("Workflow Automation Manager initialized")

    # ==================== N8N ====================

    async def n8n_trigger_workflow(self, webhook_url: str, data: Dict[str, Any]) -> Dict:
        """Trigger n8n workflow via webhook"""
        import aiohttp

        async with aiohttp.ClientSession() as session:
            async with session.post(webhook_url, json=data) as response:
                return await response.json()

    async def n8n_get_workflows(self, base_url: str = None) -> List[Dict]:
        """List n8n workflows"""
        import aiohttp

        base_url = base_url or os.environ.get("N8N_URL", "http://localhost:5678")
        api_key = os.environ.get("N8N_API_KEY")

        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{base_url}/api/v1/workflows",
                headers={"X-N8N-API-KEY": api_key}
            ) as response:
                data = await response.json()
                return data.get("data", [])

    # ==================== ZAPIER ====================

    async def zapier_trigger_webhook(self, webhook_url: str, data: Dict[str, Any]) -> Dict:
        """Trigger Zapier webhook"""
        import aiohttp

        async with aiohttp.ClientSession() as session:
            async with session.post(webhook_url, json=data) as response:
                return {"status": response.status, "triggered": True}

    async def zapier_nla_action(self, action: str, instructions: str) -> Dict:
        """Zapier Natural Language Actions"""
        import aiohttp

        api_key = os.environ.get("ZAPIER_NLA_API_KEY")

        async with aiohttp.ClientSession() as session:
            async with session.post(
                "https://nla.zapier.com/api/v1/dynamic/exposed/",
                headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
                json={"instructions": instructions}
            ) as response:
                return await response.json()

    # ==================== MAKE (INTEGROMAT) ====================

    async def make_trigger_scenario(self, webhook_url: str, data: Dict[str, Any]) -> Dict:
        """Trigger Make scenario"""
        import aiohttp

        async with aiohttp.ClientSession() as session:
            async with session.post(webhook_url, json=data) as response:
                return {"status": response.status, "triggered": True}

    # ==================== PIPEDREAM ====================

    async def pipedream_trigger(self, webhook_url: str, data: Dict[str, Any]) -> Dict:
        """Trigger Pipedream workflow"""
        import aiohttp

        async with aiohttp.ClientSession() as session:
            async with session.post(webhook_url, json=data) as response:
                return await response.json()

    async def pipedream_connect(self, app: str, action: str, params: Dict) -> Dict:
        """Use Pipedream Connect API"""
        import aiohttp

        api_key = os.environ.get("PIPEDREAM_API_KEY")

        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"https://api.pipedream.com/v1/connect/{app}/{action}",
                headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
                json=params
            ) as response:
                return await response.json()

    # ==================== TEMPORAL ====================

    async def temporal_start_workflow(
        self,
        workflow_id: str,
        task_queue: str,
        workflow_type: str,
        args: List[Any] = None
    ) -> str:
        """Start Temporal workflow"""
        from temporalio.client import Client

        client = await Client.connect(os.environ.get("TEMPORAL_HOST", "localhost:7233"))

        handle = await client.start_workflow(
            workflow_type,
            args or [],
            id=workflow_id,
            task_queue=task_queue
        )

        return handle.id

    async def temporal_query_workflow(self, workflow_id: str, query: str) -> Any:
        """Query Temporal workflow state"""
        from temporalio.client import Client

        client = await Client.connect(os.environ.get("TEMPORAL_HOST", "localhost:7233"))
        handle = client.get_workflow_handle(workflow_id)
        return await handle.query(query)

    # ==================== PREFECT ====================

    async def prefect_run_flow(self, deployment_name: str, parameters: Dict = None) -> str:
        """Run Prefect flow"""
        from prefect.client import get_client

        async with get_client() as client:
            deployment = await client.read_deployment_by_name(deployment_name)
            flow_run = await client.create_flow_run_from_deployment(
                deployment.id,
                parameters=parameters or {}
            )
            return str(flow_run.id)

    # ==================== AIRFLOW ====================

    async def airflow_trigger_dag(self, dag_id: str, conf: Dict = None) -> Dict:
        """Trigger Airflow DAG"""
        import aiohttp

        base_url = os.environ.get("AIRFLOW_URL", "http://localhost:8080")
        username = os.environ.get("AIRFLOW_USER", "airflow")
        password = os.environ.get("AIRFLOW_PASSWORD", "airflow")

        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{base_url}/api/v1/dags/{dag_id}/dagRuns",
                auth=aiohttp.BasicAuth(username, password),
                json={"conf": conf or {}}
            ) as response:
                return await response.json()

    # ==================== DAGSTER ====================

    async def dagster_run_job(self, job_name: str, repository: str, config: Dict = None) -> str:
        """Run Dagster job"""
        import aiohttp

        base_url = os.environ.get("DAGSTER_URL", "http://localhost:3000")

        query = """
        mutation LaunchRun($jobName: String!, $repositoryName: String!, $config: RunConfigData) {
            launchRun(executionParams: {
                selector: {jobName: $jobName, repositoryName: $repositoryName}
                runConfigData: $config
            }) {
                ... on LaunchRunSuccess { run { runId } }
            }
        }
        """

        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{base_url}/graphql",
                json={"query": query, "variables": {"jobName": job_name, "repositoryName": repository, "config": config}}
            ) as response:
                data = await response.json()
                return data["data"]["launchRun"]["run"]["runId"]

    # ==================== IFTTT ====================

    async def ifttt_trigger(self, event: str, key: str = None, value1: str = None, value2: str = None, value3: str = None) -> bool:
        """Trigger IFTTT webhook"""
        import aiohttp

        key = key or os.environ.get("IFTTT_KEY")

        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"https://maker.ifttt.com/trigger/{event}/with/key/{key}",
                json={"value1": value1, "value2": value2, "value3": value3}
            ) as response:
                return response.status == 200

    # ==================== LOCAL WORKFLOW ENGINE ====================

    def create_workflow(self, name: str) -> str:
        """Create a new local workflow"""
        self._workflows[name] = []
        return name

    def add_step(self, workflow_name: str, action: str, params: Dict, condition: str = None):
        """Add step to workflow"""
        if workflow_name not in self._workflows:
            raise ValueError(f"Workflow {workflow_name} not found")

        self._workflows[workflow_name].append(WorkflowStep(
            action=action,
            params=params,
            condition=condition
        ))

    async def run_workflow(self, workflow_name: str, context: Dict = None) -> List[Any]:
        """Execute local workflow"""
        if workflow_name not in self._workflows:
            raise ValueError(f"Workflow {workflow_name} not found")

        context = context or {}
        results = []

        for step in self._workflows[workflow_name]:
            # Check condition
            if step.condition:
                if not eval(step.condition, {"ctx": context}):
                    continue

            # Execute action
            result = await self._execute_action(step.action, step.params, context)
            results.append(result)
            context["last_result"] = result

        return results

    async def _execute_action(self, action: str, params: Dict, context: Dict) -> Any:
        """Execute workflow action"""
        # Resolve params with context
        resolved_params = {}
        for k, v in params.items():
            if isinstance(v, str) and v.startswith("{{") and v.endswith("}}"):
                key = v[2:-2].strip()
                resolved_params[k] = context.get(key)
            else:
                resolved_params[k] = v

        # Execute based on action type
        if action == "http_request":
            import aiohttp
            async with aiohttp.ClientSession() as session:
                method = resolved_params.get("method", "GET")
                async with session.request(method, resolved_params["url"], json=resolved_params.get("body")) as resp:
                    return await resp.json()

        elif action == "delay":
            await asyncio.sleep(resolved_params.get("seconds", 1))
            return {"delayed": resolved_params.get("seconds", 1)}

        elif action == "transform":
            import jmespath
            return jmespath.search(resolved_params["expression"], context.get("last_result"))

        elif action == "ai_process":
            from windows_ai.integrations.ai_providers import AIProvidersManager, Provider
            ai = AIProvidersManager()
            await ai.initialize()
            response = await ai.chat(
                Provider.OPENAI,
                [{"role": "user", "content": resolved_params["prompt"]}]
            )
            return response["content"]

        return {"action": action, "params": resolved_params}

    def list_workflows(self) -> List[str]:
        """List all local workflows"""
        return list(self._workflows.keys())
