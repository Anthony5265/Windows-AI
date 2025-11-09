"""
Jenkins DevOps Plugin
Integration with Jenkins CI/CD server for build management and automation
"""

from typing import Dict, Any, Optional, List
import os
import logging
import requests
from urllib.parse import urljoin


class JenkinsPlugin:
    """Plugin for Jenkins CI/CD integration"""

    name = "jenkins"
    version = "1.0.0"
    description = "Integration with Jenkins CI/CD server for build management and automation"
    author = "Windows AI Team"

    def __init__(self):
        self.jenkins_url: Optional[str] = None
        self.username: Optional[str] = None
        self.api_token: Optional[str] = None
        self.session = None
        self._initialized = False
        self.logger = logging.getLogger(__name__)

    def initialize(self, config: Optional[Dict[str, Any]] = None) -> bool:
        """Initialize the Jenkins plugin"""
        try:
            # Get Jenkins configuration
            self.jenkins_url = (
                config.get("jenkins_url") if config
                else os.getenv("JENKINS_URL")
            )

            self.username = (
                config.get("username") if config
                else os.getenv("JENKINS_USERNAME")
            )

            self.api_token = (
                config.get("api_token") if config
                else os.getenv("JENKINS_API_TOKEN")
            )

            if not self.jenkins_url:
                self.logger.error("Jenkins URL not provided")
                return False

            # Create session for API calls
            self.session = requests.Session()
            if self.username and self.api_token:
                self.session.auth = (self.username, self.api_token)

            # Test connection
            test_url = urljoin(self.jenkins_url, "api/json")
            response = self.session.get(test_url, timeout=10)
            response.raise_for_status()

            self._initialized = True
            self.logger.info("Jenkins plugin initialized successfully")
            return True

        except Exception as e:
            self.logger.error(f"Error initializing Jenkins plugin: {e}")
            return False

    def execute(self, action: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a Jenkins action"""
        if not self._initialized:
            return {"error": "Plugin not initialized. Please provide Jenkins URL and credentials."}

        try:
            if action == "trigger_job":
                return self._trigger_job(params)
            elif action == "get_job_status":
                return self._get_job_status(params)
            elif action == "get_build_info":
                return self._get_build_info(params)
            elif action == "list_jobs":
                return self._list_jobs(params)
            else:
                return {"error": f"Unknown action: {action}"}

        except Exception as e:
            self.logger.error(f"Error executing action {action}: {e}")
            return {"error": str(e)}

    def _trigger_job(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Trigger a Jenkins job build"""
        job_name = params.get("job_name", "")
        if not job_name:
            return {"error": "Job name not provided"}

        try:
            # Build trigger URL
            trigger_url = urljoin(self.jenkins_url, f"job/{job_name}/build")

            # Add parameters if provided
            build_params = params.get("parameters", {})
            if build_params:
                # For parameterized builds, use buildWithParameters
                trigger_url = urljoin(self.jenkins_url, f"job/{job_name}/buildWithParameters")
                response = self.session.post(trigger_url, data=build_params, timeout=30)
            else:
                response = self.session.post(trigger_url, timeout=30)

            if response.status_code in [200, 201]:
                # Get queue location
                queue_url = response.headers.get('Location')
                if queue_url:
                    return {
                        "success": True,
                        "message": f"Build triggered for job '{job_name}'",
                        "queue_url": queue_url
                    }
                else:
                    return {
                        "success": True,
                        "message": f"Build triggered for job '{job_name}'"
                    }
            else:
                return {"error": f"Failed to trigger build: HTTP {response.status_code}"}

        except Exception as e:
            return {"error": f"Failed to trigger job: {e}"}

    def _get_job_status(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get the status of a Jenkins job"""
        job_name = params.get("job_name", "")
        if not job_name:
            return {"error": "Job name not provided"}

        try:
            job_url = urljoin(self.jenkins_url, f"job/{job_name}/api/json")
            response = self.session.get(job_url, timeout=10)
            response.raise_for_status()

            job_data = response.json()

            # Get last build info
            last_build = job_data.get("lastBuild")
            if last_build:
                build_number = last_build.get("number")
                build_url = last_build.get("url")
                build_result = last_build.get("result")

                return {
                    "success": True,
                    "job_name": job_name,
                    "last_build": {
                        "number": build_number,
                        "url": build_url,
                        "result": build_result
                    },
                    "job_url": job_data.get("url"),
                    "color": job_data.get("color")  # Jenkins status color
                }
            else:
                return {
                    "success": True,
                    "job_name": job_name,
                    "message": "No builds found for this job",
                    "job_url": job_data.get("url")
                }

        except Exception as e:
            return {"error": f"Failed to get job status: {e}"}

    def _get_build_info(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get detailed information about a specific build"""
        job_name = params.get("job_name", "")
        build_number = params.get("build_number")

        if not job_name or build_number is None:
            return {"error": "Job name and build number required"}

        try:
            build_url = urljoin(self.jenkins_url, f"job/{job_name}/{build_number}/api/json")
            response = self.session.get(build_url, timeout=10)
            response.raise_for_status()

            build_data = response.json()

            return {
                "success": True,
                "job_name": job_name,
                "build_number": build_number,
                "result": build_data.get("result"),
                "building": build_data.get("building", False),
                "duration": build_data.get("duration", 0),
                "timestamp": build_data.get("timestamp"),
                "url": build_data.get("url"),
                "description": build_data.get("description"),
                "change_sets": build_data.get("changeSets", [])
            }

        except Exception as e:
            return {"error": f"Failed to get build info: {e}"}

    def _list_jobs(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """List Jenkins jobs"""
        try:
            jobs_url = urljoin(self.jenkins_url, "api/json")
            response = self.session.get(jobs_url, timeout=10)
            response.raise_for_status()

            data = response.json()
            jobs = data.get("jobs", [])

            # Extract basic job info
            job_list = []
            for job in jobs:
                job_list.append({
                    "name": job.get("name"),
                    "url": job.get("url"),
                    "color": job.get("color"),
                    "type": job.get("_class", "").split(".")[-1]
                })

            return {
                "success": True,
                "jobs": job_list,
                "total_jobs": len(job_list)
            }

        except Exception as e:
            return {"error": f"Failed to list jobs: {e}"}

    def cleanup(self):
        """Cleanup resources"""
        if self.session:
            self.session.close()
        self.session = None
        self._initialized = False


# Plugin metadata
PLUGIN_CLASS = JenkinsPlugin
PLUGIN_NAME = "jenkins"
PLUGIN_VERSION = "1.0.0"
PLUGIN_DESCRIPTION = "Integration with Jenkins CI/CD server for build management and automation"
PLUGIN_ACTIONS = ["trigger_job", "get_job_status", "get_build_info", "list_jobs"]