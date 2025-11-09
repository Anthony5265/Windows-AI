"""
W&B (Weights & Biases) Plugin for Windows AI
Provides experiment tracking, model monitoring, and visualization capabilities
"""

import os
import json
import logging
import requests
from typing import Dict, Any, Optional, List
from datetime import datetime
import threading
import time

logger = logging.getLogger(__name__)

class WandBPlugin:
    """W&B integration plugin for experiment tracking and monitoring"""
    
    def __init__(self):
        self.name = "wandb"
        self.version = "1.0.0"
        self.description = "W&B integration for experiment tracking and monitoring"
        self.api_key = None
        self.project = None
        self.entity = None
        self.base_url = "https://api.wandb.ai"
        self.active_runs = {}
        self.monitoring_active = False
        
    def initialize(self, config: Dict[str, Any]) -> bool:
        """Initialize W&B plugin with configuration"""
        try:
            self.api_key = config.get('api_key') or os.getenv('WANDB_API_KEY')
            self.project = config.get('project', 'windows-ai-experiments')
            self.entity = config.get('entity')
            
            if not self.api_key:
                logger.warning("W&B API key not provided. Set WANDB_API_KEY environment variable or provide in config.")
                return False
                
            # Test API connection
            if self._test_connection():
                logger.info(f"W&B plugin initialized for project: {self.project}")
                return True
            else:
                logger.error("Failed to connect to W&B API")
                return False
                
        except Exception as e:
            logger.error(f"Failed to initialize W&B plugin: {e}")
            return False
    
    def _test_connection(self) -> bool:
        """Test connection to W&B API"""
        try:
            headers = {'Authorization': f'Bearer {self.api_key}'}
            response = requests.get(f"{self.base_url}/v1/entities", headers=headers, timeout=10)
            return response.status_code == 200
        except Exception as e:
            logger.error(f"W&B connection test failed: {e}")
            return False
    
    def create_run(self, run_name: str, config: Optional[Dict] = None, tags: Optional[List[str]] = None) -> Optional[str]:
        """Create a new W&B run"""
        try:
            headers = {
                'Authorization': f'Bearer {self.api_key}',
                'Content-Type': 'application/json'
            }
            
            payload = {
                'name': run_name,
                'project': self.project
            }
            
            if self.entity:
                payload['entity'] = self.entity
                
            if config:
                payload['config'] = config
                
            if tags:
                payload['tags'] = tags
            
            response = requests.post(
                f"{self.base_url}/v1/runs",
                headers=headers,
                json=payload,
                timeout=10
            )
            
            if response.status_code == 200:
                run_data = response.json()
                run_id = run_data.get('id')
                self.active_runs[run_id] = {
                    'name': run_name,
                    'created_at': datetime.now().isoformat(),
                    'config': config or {},
                    'tags': tags or []
                }
                logger.info(f"Created W&B run: {run_name} (ID: {run_id})")
                return run_id
            else:
                logger.error(f"Failed to create W&B run: {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"Error creating W&B run: {e}")
            return None
    
    def log_metrics(self, run_id: str, metrics: Dict[str, float], step: Optional[int] = None) -> bool:
        """Log metrics to a W&B run"""
        try:
            if run_id not in self.active_runs:
                logger.error(f"Run {run_id} not found in active runs")
                return False
            
            headers = {
                'Authorization': f'Bearer {self.api_key}',
                'Content-Type': 'application/json'
            }
            
            payload = {
                'run': run_id,
                'metrics': metrics
            }
            
            if step is not None:
                payload['step'] = step
            
            response = requests.post(
                f"{self.base_url}/v1/runs/{run_id}/history",
                headers=headers,
                json=payload,
                timeout=10
            )
            
            if response.status_code == 200:
                logger.debug(f"Logged metrics to run {run_id}: {metrics}")
                return True
            else:
                logger.error(f"Failed to log metrics: {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"Error logging metrics: {e}")
            return False
    
    def log_artifact(self, run_id: str, artifact_path: str, artifact_type: str = "dataset", name: Optional[str] = None) -> bool:
        """Log an artifact to a W&B run"""
        try:
            if run_id not in self.active_runs:
                logger.error(f"Run {run_id} not found in active runs")
                return False
            
            if not os.path.exists(artifact_path):
                logger.error(f"Artifact path does not exist: {artifact_path}")
                return False
            
            headers = {'Authorization': f'Bearer {self.api_key}'}
            
            # Create artifact
            artifact_name = name or os.path.basename(artifact_path)
            payload = {
                'name': artifact_name,
                'type': artifact_type
            }
            
            response = requests.post(
                f"{self.base_url}/v1/artifacts",
                headers=headers,
                json=payload,
                timeout=10
            )
            
            if response.status_code == 200:
                artifact_data = response.json()
                artifact_id = artifact_data.get('id')
                
                # Upload file (simplified - in production would use multipart upload)
                with open(artifact_path, 'rb') as f:
                    files = {'file': f}
                    upload_response = requests.post(
                        f"{self.base_url}/v1/artifacts/{artifact_id}/files",
                        headers=headers,
                        files=files,
                        timeout=60
                    )
                
                if upload_response.status_code == 200:
                    # Link artifact to run
                    link_payload = {'artifactID': artifact_id}
                    link_response = requests.post(
                        f"{self.base_url}/v1/runs/{run_id}/artifacts",
                        headers=headers,
                        json=link_payload,
                        timeout=10
                    )
                    
                    if link_response.status_code == 200:
                        logger.info(f"Logged artifact {artifact_name} to run {run_id}")
                        return True
            
            logger.error(f"Failed to log artifact: {response.text}")
            return False
            
        except Exception as e:
            logger.error(f"Error logging artifact: {e}")
            return False
    
    def finish_run(self, run_id: str, status: str = "finished") -> bool:
        """Finish a W&B run"""
        try:
            if run_id not in self.active_runs:
                logger.error(f"Run {run_id} not found in active runs")
                return False
            
            headers = {
                'Authorization': f'Bearer {self.api_key}',
                'Content-Type': 'application/json'
            }
            
            payload = {'state': status}
            
            response = requests.patch(
                f"{self.base_url}/v1/runs/{run_id}",
                headers=headers,
                json=payload,
                timeout=10
            )
            
            if response.status_code == 200:
                logger.info(f"Finished W&B run {run_id} with status: {status}")
                del self.active_runs[run_id]
                return True
            else:
                logger.error(f"Failed to finish run: {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"Error finishing run: {e}")
            return False
    
    def get_runs(self, project: Optional[str] = None, limit: int = 50) -> List[Dict]:
        """Get list of runs from W&B"""
        try:
            headers = {'Authorization': f'Bearer {self.api_key}'}
            
            params = {
                'project': project or self.project,
                'limit': limit
            }
            
            if self.entity:
                params['entity'] = self.entity
            
            response = requests.get(
                f"{self.base_url}/v1/runs",
                headers=headers,
                params=params,
                timeout=10
            )
            
            if response.status_code == 200:
                return response.json().get('runs', [])
            else:
                logger.error(f"Failed to get runs: {response.text}")
                return []
                
        except Exception as e:
            logger.error(f"Error getting runs: {e}")
            return []
    
    def get_run_metrics(self, run_id: str) -> Dict[str, List]:
        """Get metrics history for a specific run"""
        try:
            headers = {'Authorization': f'Bearer {self.api_key}'}
            
            response = requests.get(
                f"{self.base_url}/v1/runs/{run_id}/history",
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                return response.json().get('history', {})
            else:
                logger.error(f"Failed to get run metrics: {response.text}")
                return {}
                
        except Exception as e:
            logger.error(f"Error getting run metrics: {e}")
            return {}
    
    def start_monitoring(self, run_id: str, metrics_callback: callable, interval: int = 30) -> bool:
        """Start monitoring a run for new metrics"""
        try:
            if run_id not in self.active_runs:
                logger.error(f"Run {run_id} not found in active runs")
                return False
            
            self.monitoring_active = True
            
            def monitor_loop():
                last_step = 0
                while self.monitoring_active and run_id in self.active_runs:
                    try:
                        metrics = self.get_run_metrics(run_id)
                        if metrics:
                            # Call callback with new metrics
                            metrics_callback(run_id, metrics)
                        
                        time.sleep(interval)
                    except Exception as e:
                        logger.error(f"Error in monitoring loop: {e}")
                        time.sleep(interval)
            
            monitor_thread = threading.Thread(target=monitor_loop, daemon=True)
            monitor_thread.start()
            
            logger.info(f"Started monitoring run {run_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error starting monitoring: {e}")
            return False
    
    def stop_monitoring(self):
        """Stop monitoring all runs"""
        self.monitoring_active = False
        logger.info("Stopped monitoring runs")
    
    def create_report(self, run_ids: List[str], title: str, description: str = "") -> Optional[str]:
        """Create a W&B report from multiple runs"""
        try:
            headers = {
                'Authorization': f'Bearer {self.api_key}',
                'Content-Type': 'application/json'
            }
            
            payload = {
                'title': title,
                'description': description,
                'project': self.project,
                'runs': run_ids
            }
            
            if self.entity:
                payload['entity'] = self.entity
            
            response = requests.post(
                f"{self.base_url}/v1/reports",
                headers=headers,
                json=payload,
                timeout=10
            )
            
            if response.status_code == 200:
                report_data = response.json()
                report_url = report_data.get('url')
                logger.info(f"Created W&B report: {report_url}")
                return report_url
            else:
                logger.error(f"Failed to create report: {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"Error creating report: {e}")
            return None
    
    def get_sweeps(self, project: Optional[str] = None) -> List[Dict]:
        """Get list of sweeps from W&B"""
        try:
            headers = {'Authorization': f'Bearer {self.api_key}'}
            
            params = {'project': project or self.project}
            if self.entity:
                params['entity'] = self.entity
            
            response = requests.get(
                f"{self.base_url}/v1/sweeps",
                headers=headers,
                params=params,
                timeout=10
            )
            
            if response.status_code == 200:
                return response.json().get('sweeps', [])
            else:
                logger.error(f"Failed to get sweeps: {response.text}")
                return []
                
        except Exception as e:
            logger.error(f"Error getting sweeps: {e}")
            return []
    
    def cleanup(self):
        """Cleanup plugin resources"""
        self.stop_monitoring()
        
        # Finish all active runs
        for run_id in list(self.active_runs.keys()):
            self.finish_run(run_id, "cancelled")
        
        logger.info("W&B plugin cleanup completed")

# Plugin factory function
def create_plugin():
    return WandBPlugin()

# Plugin metadata
PLUGIN_INFO = {
    'name': 'wandb',
    'version': '1.0.0',
    'description': 'W&B integration for experiment tracking and monitoring',
    'author': 'Windows AI Team',
    'category': 'data-science',
    'dependencies': ['requests'],
    'config_schema': {
        'api_key': {
            'type': 'string',
            'required': False,
            'description': 'W&B API key (can also be set via WANDB_API_KEY env var)'
        },
        'project': {
            'type': 'string',
            'default': 'windows-ai-experiments',
            'description': 'W&B project name'
        },
        'entity': {
            'type': 'string',
            'required': False,
            'description': 'W&B entity (team or user)'
        }
    }
}