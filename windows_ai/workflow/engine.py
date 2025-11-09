"""
Workflow Execution Engine
Execute workflows as directed acyclic graphs (DAGs)
"""
from typing import Dict, Any, List, Optional, Callable
import logging
import asyncio
import time
import json
from enum import Enum

logger = logging.getLogger(__name__)


class NodeStatus(Enum):
    """Node execution status"""
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    SKIPPED = "skipped"


class WorkflowNode:
    """Workflow node representing a task"""

    def __init__(self, node_id: str, node_type: str, **kwargs):
        self.node_id = node_id
        self.node_type = node_type
        self.config = kwargs.get("config", {})
        self.inputs = kwargs.get("inputs", {})
        self.outputs = {}
        self.status = NodeStatus.PENDING
        self.error = None
        self.start_time = None
        self.end_time = None
        self.execution_time = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert node to dictionary"""
        return {
            "node_id": self.node_id,
            "node_type": self.node_type,
            "config": self.config,
            "inputs": self.inputs,
            "outputs": self.outputs,
            "status": self.status.value,
            "error": self.error,
            "execution_time": self.execution_time
        }


class WorkflowEdge:
    """Workflow edge connecting nodes"""

    def __init__(self, from_node: str, to_node: str, **kwargs):
        self.from_node = from_node
        self.to_node = to_node
        self.condition = kwargs.get("condition")
        self.data_mapping = kwargs.get("data_mapping", {})

    def to_dict(self) -> Dict[str, Any]:
        """Convert edge to dictionary"""
        return {
            "from": self.from_node,
            "to": self.to_node,
            "condition": self.condition,
            "data_mapping": self.data_mapping
        }


class Workflow:
    """Workflow definition"""

    def __init__(self, workflow_id: str, name: str):
        self.workflow_id = workflow_id
        self.name = name
        self.description = ""
        self.nodes = {}
        self.edges = []
        self.metadata = {}
        self.created_at = time.time()

    def add_node(self, node: WorkflowNode):
        """Add node to workflow"""
        self.nodes[node.node_id] = node

    def add_edge(self, edge: WorkflowEdge):
        """Add edge to workflow"""
        self.edges.append(edge)

    def to_dict(self) -> Dict[str, Any]:
        """Convert workflow to dictionary"""
        return {
            "workflow_id": self.workflow_id,
            "name": self.name,
            "description": self.description,
            "nodes": {nid: node.to_dict() for nid, node in self.nodes.items()},
            "edges": [edge.to_dict() for edge in self.edges],
            "metadata": self.metadata,
            "created_at": self.created_at
        }

    def get_node_dependencies(self, node_id: str) -> List[str]:
        """Get list of nodes that must complete before this node"""
        dependencies = []
        for edge in self.edges:
            if edge.to_node == node_id:
                dependencies.append(edge.from_node)
        return dependencies

    def get_node_dependents(self, node_id: str) -> List[str]:
        """Get list of nodes that depend on this node"""
        dependents = []
        for edge in self.edges:
            if edge.from_node == node_id:
                dependents.append(edge.to_node)
        return dependents

    def validate(self) -> Dict[str, Any]:
        """Validate workflow structure"""
        errors = []

        # Check for cycles (DAG requirement)
        if self._has_cycles():
            errors.append("Workflow contains cycles")

        # Check all edge references exist
        for edge in self.edges:
            if edge.from_node not in self.nodes:
                errors.append(f"Edge references non-existent node: {edge.from_node}")
            if edge.to_node not in self.nodes:
                errors.append(f"Edge references non-existent node: {edge.to_node}")

        return {
            "valid": len(errors) == 0,
            "errors": errors
        }

    def _has_cycles(self) -> bool:
        """Check for cycles using DFS"""
        visited = set()
        rec_stack = set()

        def dfs(node_id):
            visited.add(node_id)
            rec_stack.add(node_id)

            for dependent in self.get_node_dependents(node_id):
                if dependent not in visited:
                    if dfs(dependent):
                        return True
                elif dependent in rec_stack:
                    return True

            rec_stack.remove(node_id)
            return False

        for node_id in self.nodes:
            if node_id not in visited:
                if dfs(node_id):
                    return True

        return False


class WorkflowEngine:
    """Production workflow execution engine"""

    def __init__(self):
        self.workflows = {}
        self.executions = {}
        self.node_executors = {}

    def register_node_executor(self, node_type: str, executor: Callable):
        """
        Register executor function for node type

        Args:
            node_type: Type of node
            executor: Async function(node, context) -> Dict[str, Any]
        """
        self.node_executors[node_type] = executor
        logger.info(f"Registered executor for node type: {node_type}")

    def create_workflow(self, workflow_id: str, name: str) -> Dict[str, Any]:
        """Create new workflow"""
        if workflow_id in self.workflows:
            return {
                "status": "error",
                "message": f"Workflow already exists: {workflow_id}"
            }

        workflow = Workflow(workflow_id, name)
        self.workflows[workflow_id] = workflow

        return {
            "status": "success",
            "workflow": workflow.to_dict()
        }

    def add_node_to_workflow(self, workflow_id: str, node_id: str,
                            node_type: str, **kwargs) -> Dict[str, Any]:
        """Add node to workflow"""
        if workflow_id not in self.workflows:
            return {
                "status": "error",
                "message": f"Workflow not found: {workflow_id}"
            }

        workflow = self.workflows[workflow_id]
        node = WorkflowNode(node_id, node_type, **kwargs)
        workflow.add_node(node)

        return {
            "status": "success",
            "node": node.to_dict()
        }

    def connect_nodes(self, workflow_id: str, from_node: str,
                     to_node: str, **kwargs) -> Dict[str, Any]:
        """Connect two nodes with an edge"""
        if workflow_id not in self.workflows:
            return {
                "status": "error",
                "message": f"Workflow not found: {workflow_id}"
            }

        workflow = self.workflows[workflow_id]
        edge = WorkflowEdge(from_node, to_node, **kwargs)
        workflow.add_edge(edge)

        return {
            "status": "success",
            "edge": edge.to_dict()
        }

    async def execute_workflow(self, workflow_id: str, inputs: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Execute workflow

        Args:
            workflow_id: ID of workflow to execute
            inputs: Initial workflow inputs

        Returns:
            Dict with execution results
        """
        if workflow_id not in self.workflows:
            return {
                "status": "error",
                "message": f"Workflow not found: {workflow_id}"
            }

        workflow = self.workflows[workflow_id]

        # Validate workflow
        validation = workflow.validate()
        if not validation["valid"]:
            return {
                "status": "error",
                "message": "Workflow validation failed",
                "errors": validation["errors"]
            }

        # Create execution context
        execution_id = f"{workflow_id}_{int(time.time())}"
        context = {
            "execution_id": execution_id,
            "workflow_id": workflow_id,
            "inputs": inputs or {},
            "outputs": {},
            "start_time": time.time()
        }

        self.executions[execution_id] = context

        try:
            # Find starting nodes (no dependencies)
            starting_nodes = [
                node_id for node_id in workflow.nodes
                if not workflow.get_node_dependencies(node_id)
            ]

            logger.info(f"Starting workflow execution: {execution_id}")
            logger.info(f"Starting nodes: {starting_nodes}")

            # Execute workflow using topological sort
            completed_nodes = set()
            failed_nodes = set()

            while len(completed_nodes) < len(workflow.nodes):
                # Find nodes ready to execute
                ready_nodes = []
                for node_id in workflow.nodes:
                    if node_id in completed_nodes or node_id in failed_nodes:
                        continue

                    dependencies = workflow.get_node_dependencies(node_id)
                    if all(dep in completed_nodes for dep in dependencies):
                        ready_nodes.append(node_id)

                if not ready_nodes:
                    # Check if we're stuck
                    remaining = set(workflow.nodes.keys()) - completed_nodes - failed_nodes
                    if remaining:
                        return {
                            "status": "error",
                            "message": "Workflow execution stuck",
                            "remaining_nodes": list(remaining)
                        }
                    break

                # Execute ready nodes in parallel
                tasks = [
                    self._execute_node(workflow, node_id, context)
                    for node_id in ready_nodes
                ]

                results = await asyncio.gather(*tasks, return_exceptions=True)

                # Process results
                for node_id, result in zip(ready_nodes, results):
                    if isinstance(result, Exception):
                        logger.error(f"Node {node_id} failed: {result}")
                        workflow.nodes[node_id].status = NodeStatus.FAILED
                        workflow.nodes[node_id].error = str(result)
                        failed_nodes.add(node_id)
                    elif result["status"] == "success":
                        completed_nodes.add(node_id)
                    else:
                        failed_nodes.add(node_id)

            # Collect final results
            context["end_time"] = time.time()
            context["execution_time"] = context["end_time"] - context["start_time"]
            context["node_results"] = {
                node_id: node.to_dict()
                for node_id, node in workflow.nodes.items()
            }

            return {
                "status": "success",
                "execution_id": execution_id,
                "execution_time": context["execution_time"],
                "completed_nodes": len(completed_nodes),
                "failed_nodes": len(failed_nodes),
                "results": context
            }

        except Exception as e:
            logger.error(f"Workflow execution error: {e}")
            return {
                "status": "error",
                "message": str(e),
                "execution_id": execution_id
            }

    async def _execute_node(self, workflow: Workflow, node_id: str,
                           context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a single node"""
        node = workflow.nodes[node_id]
        node.status = NodeStatus.RUNNING
        node.start_time = time.time()

        logger.info(f"Executing node: {node_id} ({node.node_type})")

        try:
            # Get executor for node type
            if node.node_type not in self.node_executors:
                raise ValueError(f"No executor registered for node type: {node.node_type}")

            executor = self.node_executors[node.node_type]

            # Prepare node inputs from dependencies
            for edge in workflow.edges:
                if edge.to_node == node_id:
                    from_node = workflow.nodes[edge.from_node]
                    # Map outputs to inputs
                    for output_key, input_key in edge.data_mapping.items():
                        if output_key in from_node.outputs:
                            node.inputs[input_key] = from_node.outputs[output_key]

            # Execute node
            result = await executor(node, context)

            if result["status"] == "success":
                node.status = NodeStatus.SUCCESS
                node.outputs = result.get("outputs", {})
            else:
                node.status = NodeStatus.FAILED
                node.error = result.get("message", "Unknown error")

            node.end_time = time.time()
            node.execution_time = node.end_time - node.start_time

            return result

        except Exception as e:
            logger.error(f"Node execution error ({node_id}): {e}")
            node.status = NodeStatus.FAILED
            node.error = str(e)
            node.end_time = time.time()
            node.execution_time = node.end_time - node.start_time

            return {
                "status": "error",
                "message": str(e)
            }

    def get_execution_status(self, execution_id: str) -> Dict[str, Any]:
        """Get execution status"""
        if execution_id not in self.executions:
            return {
                "status": "error",
                "message": f"Execution not found: {execution_id}"
            }

        return {
            "status": "success",
            "execution": self.executions[execution_id]
        }

    def export_workflow(self, workflow_id: str, file_path: str = None) -> Dict[str, Any]:
        """Export workflow to JSON"""
        if workflow_id not in self.workflows:
            return {
                "status": "error",
                "message": f"Workflow not found: {workflow_id}"
            }

        workflow = self.workflows[workflow_id]
        data = workflow.to_dict()

        if file_path:
            try:
                with open(file_path, 'w') as f:
                    json.dump(data, f, indent=2)

                return {
                    "status": "success",
                    "message": "Workflow exported",
                    "file_path": file_path
                }
            except Exception as e:
                return {
                    "status": "error",
                    "message": str(e)
                }
        else:
            return {
                "status": "success",
                "workflow": data
            }

    def import_workflow(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Import workflow from dictionary"""
        try:
            workflow_id = data["workflow_id"]
            name = data["name"]

            workflow = Workflow(workflow_id, name)
            workflow.description = data.get("description", "")
            workflow.metadata = data.get("metadata", {})

            # Import nodes
            for node_id, node_data in data["nodes"].items():
                node = WorkflowNode(
                    node_id,
                    node_data["node_type"],
                    config=node_data.get("config", {}),
                    inputs=node_data.get("inputs", {})
                )
                workflow.add_node(node)

            # Import edges
            for edge_data in data["edges"]:
                edge = WorkflowEdge(
                    edge_data["from"],
                    edge_data["to"],
                    condition=edge_data.get("condition"),
                    data_mapping=edge_data.get("data_mapping", {})
                )
                workflow.add_edge(edge)

            self.workflows[workflow_id] = workflow

            return {
                "status": "success",
                "workflow_id": workflow_id
            }

        except Exception as e:
            logger.error(f"Import workflow error: {e}")
            return {
                "status": "error",
                "message": str(e)
            }
