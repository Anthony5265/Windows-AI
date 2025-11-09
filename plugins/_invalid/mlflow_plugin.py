"""
MLflow Experiment Tracking Plugin
Supports experiment tracking, model registry, and model serving
"""

from typing import Dict, Any, Optional, List
import os
import json
import tempfile


class MLflowPlugin:
    """Plugin for MLflow experiment tracking and model management"""
    
    name = "mlflow"
    version = "1.0.0"
    description = "Integration with MLflow for experiment tracking and model management"
    author = "Windows AI Team"
    
    def __init__(self):
        self.client = None
        self.tracking_uri: Optional[str] = None
        self.registry_uri: Optional[str] = None
        self._initialized = False
        
    def initialize(self, config: Optional[Dict[str, Any]] = None) -> bool:
        """Initialize the MLflow plugin"""
        try:
            import mlflow
            import mlflow.sklearn
            import mlflow.pytorch
            import mlflow.tensorflow
            
            # Get configuration
            if config:
                self.tracking_uri = config.get("tracking_uri") or os.getenv("MLFLOW_TRACKING_URI")
                self.registry_uri = config.get("registry_uri") or os.getenv("MLFLOW_REGISTRY_URI")
            else:
                self.tracking_uri = os.getenv("MLFLOW_TRACKING_URI")
                self.registry_uri = os.getenv("MLFLOW_REGISTRY_URI")
            
            # Set tracking URI
            if self.tracking_uri:
                mlflow.set_tracking_uri(self.tracking_uri)
            
            # Set registry URI
            if self.registry_uri:
                mlflow.set_registry_uri(self.registry_uri)
            
            self.client = mlflow
            self._initialized = True
            return True
            
        except ImportError:
            print("mlflow package not installed. Install with: pip install mlflow")
            return False
        except Exception as e:
            print(f"Error initializing MLflow plugin: {e}")
            return False
    
    def execute(self, action: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute an MLflow action"""
        if not self._initialized:
            return {"error": "Plugin not initialized"}
        
        try:
            if action == "create_experiment":
                return self._create_experiment(params)
            elif action == "log_experiment":
                return self._log_experiment(params)
            elif action == "log_model":
                return self._log_model(params)
            elif action == "register_model":
                return self._register_model(params)
            elif action == "list_experiments":
                return self._list_experiments(params)
            elif action == "get_experiment":
                return self._get_experiment(params)
            elif action == "list_runs":
                return self._list_runs(params)
            elif action == "get_run":
                return self._get_run(params)
            elif action == "search_runs":
                return self._search_runs(params)
            elif action == "list_models":
                return self._list_models(params)
            elif action == "get_model_version":
                return self._get_model_version(params)
            elif action == "transition_model_stage":
                return self._transition_model_stage(params)
            elif action == "serve_model":
                return self._serve_model(params)
            elif action == "compare_runs":
                return self._compare_runs(params)
            elif action == "delete_experiment":
                return self._delete_experiment(params)
            elif action == "delete_run":
                return self._delete_run(params)
            else:
                return {"error": f"Unknown action: {action}"}
                
        except Exception as e:
            return {"error": str(e)}
    
    def _create_experiment(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new experiment"""
        name = params.get("name")
        artifact_location = params.get("artifact_location")
        tags = params.get("tags", {})
        
        if not name:
            return {"error": "name parameter is required"}
        
        experiment_id = self.client.create_experiment(
            name=name,
            artifact_location=artifact_location,
            tags=tags
        )
        
        return {
            "experiment_id": experiment_id,
            "name": name,
            "artifact_location": artifact_location
        }
    
    def _log_experiment(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Log experiment data"""
        experiment_id = params.get("experiment_id")
        run_name = params.get("run_name")
        metrics = params.get("metrics", {})
        params_dict = params.get("params", {})
        artifacts = params.get("artifacts", {})
        tags = params.get("tags", {})
        
        with self.client.start_run(
            experiment_id=experiment_id,
            run_name=run_name,
            tags=tags
        ) as run:
            # Log metrics
            for key, value in metrics.items():
                self.client.log_metric(key, value)
            
            # Log parameters
            for key, value in params_dict.items():
                self.client.log_param(key, value)
            
            # Log artifacts
            for key, value in artifacts.items():
                if isinstance(value, str) and os.path.exists(value):
                    self.client.log_artifact(value, artifact_path=key)
                elif isinstance(value, (dict, list)):
                    # Save JSON data as artifact
                    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
                        json.dump(value, f, indent=2)
                        temp_path = f.name
                    
                    self.client.log_artifact(temp_path, artifact_path=key)
                    os.unlink(temp_path)
            
            return {
                "run_id": run.info.run_id,
                "experiment_id": run.info.experiment_id,
                "status": run.info.status
            }
    
    def _log_model(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Log a model"""
        model = params.get("model")
        model_type = params.get("model_type", "sklearn")
        artifact_path = params.get("artifact_path", "model")
        registered_model_name = params.get("registered_model_name")
        signature = params.get("signature")
        input_example = params.get("input_example")
        
        if not model:
            return {"error": "model parameter is required"}
        
        # Choose the appropriate logging method based on model type
        if model_type == "sklearn":
            model_info = self.client.sklearn.log_model(
                model=model,
                artifact_path=artifact_path,
                registered_model_name=registered_model_name,
                signature=signature,
                input_example=input_example
            )
        elif model_type == "pytorch":
            model_info = self.client.pytorch.log_model(
                model=model,
                artifact_path=artifact_path,
                registered_model_name=registered_model_name,
                signature=signature,
                input_example=input_example
            )
        elif model_type == "tensorflow":
            model_info = self.client.tensorflow.log_model(
                model=model,
                artifact_path=artifact_path,
                registered_model_name=registered_model_name,
                signature=signature,
                input_example=input_example
            )
        else:
            # Generic model logging
            model_info = self.client.log_model(
                model=model,
                artifact_path=artifact_path,
                registered_model_name=registered_model_name,
                signature=signature,
                input_example=input_example
            )
        
        return {
            "model_uri": model_info.model_uri,
            "run_id": model_info.run_id,
            "registered_model_name": registered_model_name
        }
    
    def _register_model(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Register a model in the model registry"""
        model_uri = params.get("model_uri")
        name = params.get("name")
        description = params.get("description")
        tags = params.get("tags", {})
        
        if not model_uri or not name:
            return {"error": "model_uri and name parameters are required"}
        
        model_version = self.client.register_model(
            model_uri=model_uri,
            name=name,
            description=description,
            tags=tags
        )
        
        return {
            "name": model_version.name,
            "version": model_version.version,
            "creation_timestamp": model_version.creation_timestamp
        }
    
    def _list_experiments(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """List all experiments"""
        view_type = params.get("view_type", "ACTIVE_ONLY")
        
        experiments = self.client.list_experiments(view_type=view_type)
        
        experiment_list = []
        for exp in experiments:
            experiment_list.append({
                "experiment_id": exp.experiment_id,
                "name": exp.name,
                "artifact_location": exp.artifact_location,
                "lifecycle_stage": exp.lifecycle_stage,
                "tags": exp.tags
            })
        
        return {"experiments": experiment_list}
    
    def _get_experiment(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get experiment details"""
        experiment_id = params.get("experiment_id")
        
        if not experiment_id:
            return {"error": "experiment_id parameter is required"}
        
        experiment = self.client.get_experiment(experiment_id)
        
        return {
            "experiment_id": experiment.experiment_id,
            "name": experiment.name,
            "artifact_location": experiment.artifact_location,
            "lifecycle_stage": experiment.lifecycle_stage,
            "tags": experiment.tags
        }
    
    def _list_runs(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """List runs in an experiment"""
        experiment_id = params.get("experiment_id")
        max_results = params.get("max_results", 1000)
        
        if not experiment_id:
            return {"error": "experiment_id parameter is required"}
        
        runs = self.client.list_run_infos(experiment_id, max_results=max_results)
        
        run_list = []
        for run in runs:
            run_list.append({
                "run_id": run.run_id,
                "experiment_id": run.experiment_id,
                "status": run.status,
                "start_time": run.start_time,
                "end_time": run.end_time,
                "lifecycle_stage": run.lifecycle_stage
            })
        
        return {"runs": run_list}
    
    def _get_run(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get run details"""
        run_id = params.get("run_id")
        
        if not run_id:
            return {"error": "run_id parameter is required"}
        
        run = self.client.get_run(run_id)
        
        return {
            "run_id": run.info.run_id,
            "experiment_id": run.info.experiment_id,
            "status": run.info.status,
            "start_time": run.info.start_time,
            "end_time": run.info.end_time,
            "metrics": run.data.metrics,
            "params": run.data.params,
            "tags": run.data.tags
        }
    
    def _search_runs(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Search runs with filters"""
        experiment_ids = params.get("experiment_ids")
        filter_string = params.get("filter_string", "")
        max_results = params.get("max_results", 1000)
        order_by = params.get("order_by", ["start_time DESC"])
        
        runs = self.client.search_runs(
            experiment_ids=experiment_ids,
            filter_string=filter_string,
            max_results=max_results,
            order_by=order_by
        )
        
        run_list = []
        for run in runs:
            run_list.append({
                "run_id": run.info.run_id,
                "experiment_id": run.info.experiment_id,
                "status": run.info.status,
                "start_time": run.info.start_time,
                "end_time": run.info.end_time,
                "metrics": run.data.metrics,
                "params": run.data.params,
                "tags": run.data.tags
            })
        
        return {"runs": run_list}
    
    def _list_models(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """List registered models"""
        max_results = params.get("max_results", 1000)
        
        models = self.client.list_registered_models(max_results=max_results)
        
        model_list = []
        for model in models:
            model_list.append({
                "name": model.name,
                "creation_timestamp": model.creation_timestamp,
                "last_updated_timestamp": model.last_updated_timestamp,
                "latest_versions": [
                    {
                        "version": version.version,
                        "stage": version.current_stage,
                        "status": version.status,
                        "run_id": version.run_id
                    }
                    for version in model.latest_versions
                ]
            })
        
        return {"models": model_list}
    
    def _get_model_version(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get model version details"""
        name = params.get("name")
        version = params.get("version")
        
        if not name or not version:
            return {"error": "name and version parameters are required"}
        
        model_version = self.client.get_model_version(name, version)
        
        return {
            "name": model_version.name,
            "version": model_version.version,
            "stage": model_version.current_stage,
            "status": model_version.status,
            "run_id": model_version.run_id,
            "creation_timestamp": model_version.creation_timestamp,
            "last_updated_timestamp": model_version.last_updated_timestamp
        }
    
    def _transition_model_stage(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Transition model version to a new stage"""
        name = params.get("name")
        version = params.get("version")
        stage = params.get("stage")
        archive_existing_versions = params.get("archive_existing_versions", False)
        
        if not all([name, version, stage]):
            return {"error": "name, version, and stage parameters are required"}
        
        model_version = self.client.transition_model_version_stage(
            name=name,
            version=version,
            stage=stage,
            archive_existing_versions=archive_existing_versions
        )
        
        return {
            "name": model_version.name,
            "version": model_version.version,
            "stage": model_version.current_stage
        }
    
    def _serve_model(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Serve a model (returns command for manual execution)"""
        model_uri = params.get("model_uri")
        port = params.get("port", 5000)
        host = params.get("host", "127.0.0.1")
        workers = params.get("workers", 1)
        
        if not model_uri:
            return {"error": "model_uri parameter is required"}
        
        # Return the command to serve the model
        serve_command = f"mlflow models serve -m {model_uri} -h {host} -p {port} --workers {workers}"
        
        return {
            "serve_command": serve_command,
            "model_uri": model_uri,
            "host": host,
            "port": port,
            "workers": workers,
            "message": "Run this command in your terminal to serve the model"
        }
    
    def _compare_runs(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Compare multiple runs"""
        run_ids = params.get("run_ids", [])
        metrics_to_compare = params.get("metrics", [])
        params_to_compare = params.get("params", [])
        
        if not run_ids:
            return {"error": "run_ids parameter is required"}
        
        comparison_data = []
        for run_id in run_ids:
            run = self.client.get_run(run_id)
            
            run_data = {
                "run_id": run_id,
                "experiment_id": run.info.experiment_id,
                "status": run.info.status
            }
            
            # Add selected metrics
            if metrics_to_compare:
                run_data["metrics"] = {k: run.data.metrics.get(k) for k in metrics_to_compare}
            else:
                run_data["metrics"] = run.data.metrics
            
            # Add selected params
            if params_to_compare:
                run_data["params"] = {k: run.data.params.get(k) for k in params_to_compare}
            else:
                run_data["params"] = run.data.params
            
            comparison_data.append(run_data)
        
        return {"comparison": comparison_data}
    
    def _delete_experiment(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Delete an experiment"""
        experiment_id = params.get("experiment_id")
        
        if not experiment_id:
            return {"error": "experiment_id parameter is required"}
        
        self.client.delete_experiment(experiment_id)
        
        return {"experiment_id": experiment_id, "deleted": True}
    
    def _delete_run(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Delete a run"""
        run_id = params.get("run_id")
        
        if not run_id:
            return {"error": "run_id parameter is required"}
        
        self.client.delete_run(run_id)
        
        return {"run_id": run_id, "deleted": True}
    
    def cleanup(self):
        """Cleanup resources"""
        self.client = None
        self._initialized = False


# Plugin metadata
PLUGIN_CLASS = MLflowPlugin
PLUGIN_NAME = "mlflow"
PLUGIN_VERSION = "1.0.0"
PLUGIN_DESCRIPTION = "Integration with MLflow for experiment tracking and model management"
PLUGIN_ACTIONS = [
    "create_experiment", "log_experiment", "log_model", "register_model",
    "list_experiments", "get_experiment", "list_runs", "get_run", "search_runs",
    "list_models", "get_model_version", "transition_model_stage", "serve_model",
    "compare_runs", "delete_experiment", "delete_run"
]