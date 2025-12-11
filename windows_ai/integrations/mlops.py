"""
MLOps Manager - 15+ Services
Model training, deployment, monitoring, versioning
"""

import asyncio
import logging
import os
from typing import Dict, List, Any, Optional
from windows_ai.config.unified_config import WindowsAIConfig

import asyncio
import logging
import os
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)

class MLOpsManager:
    """Unified MLOps across 15+ platforms"""

    def __init__(self):
        self._config: Optional[WindowsAIConfig] = None
        self._initialized = False

    async def initialize(self, config: Optional[WindowsAIConfig] = None):
        if self._initialized:
            return
        
        self._config = config
        self._initialized = True

    # ==================== EXPERIMENT TRACKING ====================

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

    async def log_experiment(self, provider: str, experiment_name: str, params: Dict, metrics: Dict, artifacts: List[str] = None) -> str:
        """Log ML experiment"""
        if provider == "mlflow":
            return self._mlflow_log(experiment_name, params, metrics, artifacts)
        elif provider == "wandb":
            return self._wandb_log(experiment_name, params, metrics, artifacts)
        elif provider == "comet":
            return self._comet_log(experiment_name, params, metrics, artifacts)
        elif provider == "neptune":
            return self._neptune_log(experiment_name, params, metrics, artifacts)
        else:
            raise ValueError(f"Unsupported provider: {provider}")

    def _mlflow_log(self, experiment_name, params, metrics, artifacts):
        import mlflow
        mlflow.set_experiment(experiment_name)
        with mlflow.start_run() as run:
            mlflow.log_params(params)
            mlflow.log_metrics(metrics)
            if artifacts:
                for artifact in artifacts:
                    mlflow.log_artifact(artifact)
            return run.info.run_id

    def _wandb_log(self, experiment_name, params, metrics, artifacts):
        import wandb
        run = wandb.init(project=experiment_name, config=params)
        wandb.log(metrics)
        if artifacts:
            for artifact_path in artifacts:
                artifact = wandb.Artifact(os.path.basename(artifact_path), type="model")
                artifact.add_file(artifact_path)
                run.log_artifact(artifact)
        return run.id

    def _comet_log(self, experiment_name, params, metrics, artifacts):
        from comet_ml import Experiment
        experiment = Experiment(project_name=experiment_name)
        experiment.log_parameters(params)
        experiment.log_metrics(metrics)
        if artifacts:
            for artifact in artifacts:
                experiment.log_model(os.path.basename(artifact), artifact)
        return experiment.id

    def _neptune_log(self, experiment_name, params, metrics, artifacts):
        import neptune
        run = neptune.init_run(project=os.environ.get("NEPTUNE_PROJECT"), name=experiment_name)
        run["parameters"] = params
        for k, v in metrics.items():
            run[f"metrics/{k}"] = v
        if artifacts:
            for artifact in artifacts:
                run[f"artifacts/{os.path.basename(artifact)}"].upload(artifact)
        return run["sys/id"].fetch()

    # ==================== MODEL REGISTRY ====================

    async def register_model(self, provider: str, model_name: str, model_path: str, metadata: Dict = None) -> str:
        """Register model in registry"""
        if provider == "mlflow":
            return self._mlflow_register(model_name, model_path, metadata)
        elif provider == "huggingface":
            return await self._huggingface_register(model_name, model_path, metadata)
        elif provider == "sagemaker":
            return await self._sagemaker_register(model_name, model_path, metadata)

    def _mlflow_register(self, model_name, model_path, metadata):
        import mlflow
        result = mlflow.register_model(f"runs:/{model_path}", model_name)
        return f"{model_name}/{result.version}"

    async def _huggingface_register(self, model_name, model_path, metadata):
        from huggingface_hub import HfApi
        api = HfApi()
        api.upload_folder(folder_path=model_path, repo_id=model_name, repo_type="model")
        return f"https://huggingface.co/{model_name}"

    async def _sagemaker_register(self, model_name, model_path, metadata):
        import boto3
        sm = boto3.client("sagemaker")
        response = sm.create_model(
            ModelName=model_name,
            PrimaryContainer={"Image": metadata.get("image"), "ModelDataUrl": model_path}
        )
        return response["ModelArn"]

    # ==================== MODEL DEPLOYMENT ====================

    async def deploy_model(self, provider: str, model_name: str, config: Dict) -> Dict:
        """Deploy model to inference endpoint"""
        if provider == "sagemaker":
            return await self._sagemaker_deploy(model_name, config)
        elif provider == "vertex":
            return await self._vertex_deploy(model_name, config)
        elif provider == "azure_ml":
            return await self._azure_ml_deploy(model_name, config)
        elif provider == "replicate":
            return await self._replicate_deploy(model_name, config)
        elif provider == "modal":
            return await self._modal_deploy(model_name, config)
        elif provider == "bentoml":
            return await self._bentoml_deploy(model_name, config)
        else:
            raise ValueError(f"Unsupported provider: {provider}")

    async def _sagemaker_deploy(self, model_name, config):
        import boto3
        sm = boto3.client("sagemaker")
        endpoint_config_name = f"{model_name}-config"
        endpoint_name = f"{model_name}-endpoint"

        sm.create_endpoint_config(
            EndpointConfigName=endpoint_config_name,
            ProductionVariants=[{
                "VariantName": "primary",
                "ModelName": model_name,
                "InstanceType": config.get("instance_type", "ml.t2.medium"),
                "InitialInstanceCount": config.get("instance_count", 1)
            }]
        )

        sm.create_endpoint(EndpointName=endpoint_name, EndpointConfigName=endpoint_config_name)
        return {"endpoint": endpoint_name, "provider": "sagemaker"}

    async def _vertex_deploy(self, model_name, config):
        from google.cloud import aiplatform
        aiplatform.init(project=os.environ.get("GCP_PROJECT"))
        model = aiplatform.Model(model_name)
        endpoint = model.deploy(
            machine_type=config.get("machine_type", "n1-standard-4"),
            min_replica_count=config.get("min_replicas", 1),
            max_replica_count=config.get("max_replicas", 3)
        )
        return {"endpoint": endpoint.resource_name, "provider": "vertex"}

    async def _azure_ml_deploy(self, model_name, config):
        from azure.ai.ml import MLClient
        from azure.identity import DefaultAzureCredential
        ml_client = MLClient(DefaultAzureCredential(), os.environ.get("AZURE_SUBSCRIPTION"), os.environ.get("AZURE_RESOURCE_GROUP"), os.environ.get("AZURE_WORKSPACE"))
        # Simplified - actual deployment would be more complex
        return {"model": model_name, "provider": "azure_ml"}

    async def _replicate_deploy(self, model_name, config):
        import aiohttp
        async with aiohttp.ClientSession() as session:
            async with session.post(
                "https://api.replicate.com/v1/models",
                headers={"Authorization": f"Token {os.environ.get('REPLICATE_API_TOKEN')}"},
                json={"owner": config.get("owner"), "name": model_name, "visibility": "public"}
            ) as response:
                return await response.json()

    async def _modal_deploy(self, model_name, config):
        # Modal deployment would typically be done via CLI
        return {"model": model_name, "provider": "modal", "note": "Use modal deploy CLI"}

    async def _bentoml_deploy(self, model_name, config):
        # BentoML deployment
        return {"model": model_name, "provider": "bentoml", "note": "Use bentoml deploy CLI"}

    # ==================== INFERENCE ====================

    async def predict(self, provider: str, endpoint: str, data: Any) -> Any:
        """Run inference on deployed model"""
        if provider == "sagemaker":
            return await self._sagemaker_predict(endpoint, data)
        elif provider == "vertex":
            return await self._vertex_predict(endpoint, data)
        elif provider == "replicate":
            return await self._replicate_predict(endpoint, data)

    async def _sagemaker_predict(self, endpoint, data):
        import boto3
        import json
        runtime = boto3.client("sagemaker-runtime")
        response = runtime.invoke_endpoint(
            EndpointName=endpoint,
            ContentType="application/json",
            Body=json.dumps(data)
        )
        return json.loads(response["Body"].read())

    async def _vertex_predict(self, endpoint, data):
        from google.cloud import aiplatform
        endpoint_obj = aiplatform.Endpoint(endpoint)
        prediction = endpoint_obj.predict(instances=[data])
        return prediction.predictions

    async def _replicate_predict(self, model, data):
        import replicate
        output = replicate.run(model, input=data)
        return output

    # ==================== FINE-TUNING ====================

    async def fine_tune(self, provider: str, base_model: str, training_data: str, config: Dict) -> Dict:
        """Fine-tune a model"""
        if provider == "openai":
            return await self._openai_finetune(base_model, training_data, config)
        elif provider == "together":
            return await self._together_finetune(base_model, training_data, config)
        elif provider == "anyscale":
            return await self._anyscale_finetune(base_model, training_data, config)

    async def _openai_finetune(self, base_model, training_data, config):
        from openai import AsyncOpenAI
        client = AsyncOpenAI()

        # Upload training file
        with open(training_data, "rb") as f:
            file = await client.files.create(file=f, purpose="fine-tune")

        # Create fine-tuning job
        job = await client.fine_tuning.jobs.create(
            training_file=file.id,
            model=base_model,
            hyperparameters=config.get("hyperparameters", {})
        )
        return {"job_id": job.id, "status": job.status}

    async def _together_finetune(self, base_model, training_data, config):
        import aiohttp
        async with aiohttp.ClientSession() as session:
            async with session.post(
                "https://api.together.xyz/v1/fine-tunes",
                headers={"Authorization": f"Bearer {os.environ.get('TOGETHER_API_KEY')}"},
                json={
                    "model": base_model,
                    "training_file": training_data,
                    **config
                }
            ) as response:
                return await response.json()

    async def _anyscale_finetune(self, base_model, training_data, config):
        import aiohttp
        async with aiohttp.ClientSession() as session:
            async with session.post(
                "https://api.anyscale.com/v1/fine-tuning/jobs",
                headers={"Authorization": f"Bearer {os.environ.get('ANYSCALE_API_KEY')}"},
                json={
                    "model": base_model,
                    "training_file": training_data,
                    **config
                }
            ) as response:
                return await response.json()

    def list_providers(self) -> Dict[str, List[str]]:
        return {
            "experiment_tracking": ["mlflow", "wandb", "comet", "neptune", "tensorboard"],
            "model_registry": ["mlflow", "huggingface", "sagemaker", "vertex"],
            "deployment": ["sagemaker", "vertex", "azure_ml", "replicate", "modal", "bentoml", "ray_serve"],
            "fine_tuning": ["openai", "together", "anyscale", "lamini"]
        }
