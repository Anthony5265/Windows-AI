"""
TASK-002: AWS CodeWhisperer Plugin - Production Implementation
IAM authentication, security scanning, and code recommendations
"""
from typing import Dict, Any, List, Optional
import os
import logging
import boto3
from botocore.exceptions import ClientError, BotoCoreError
import json
from datetime import datetime

from windows_ai.plugins.base import IntegrationPlugin, PluginMetadata, PluginType

logger = logging.getLogger(__name__)


class AWSCodeWhispererPlugin(IntegrationPlugin):
    """
    Production-ready AWS CodeWhisperer integration with:
    - IAM authentication
    - Real-time code suggestions
    - Security vulnerability scanning
    - Reference tracking
    - Multi-language support
    """

    def __init__(self):
        metadata = PluginMetadata(
            id="aws_codewhisperer",
            name="AWS CodeWhisperer",
            description="AI-powered code generator with built-in security scanning",
            version="2.0.0",
            author="Windows AI Team",
            plugin_type=PluginType.INTEGRATION,
            tags=["code", "aws", "security", "completion", "ai"],
            requirements=["boto3>=1.26.0", "botocore>=1.29.0"]
        )
        super().__init__(metadata)

        self.aws_access_key = os.getenv("AWS_ACCESS_KEY_ID", "")
        self.aws_secret_key = os.getenv("AWS_SECRET_ACCESS_KEY", "")
        self.aws_region = os.getenv("AWS_REGION", "us-east-1")
        self.codewhisperer_client = None
        self.connected = False

        # Supported languages
        self.supported_languages = [
            "python", "java", "javascript", "typescript", "csharp",
            "ruby", "go", "php", "cpp", "c", "shell", "sql", "rust", "kotlin", "scala"
        ]

    async def initialize(self) -> bool:
        """Initialize AWS session"""
        try:
            if not self.aws_access_key or not self.aws_secret_key:
                logger.error("AWS credentials not configured")
                return False

            self._initialized = True
            logger.info("AWS CodeWhisperer plugin initialized")
            return True
        except Exception as e:
            logger.error(f"Initialization failed: {e}")
            return False

    async def connect(self, credentials: Dict[str, str]) -> bool:
        """Connect to AWS CodeWhisperer"""
        try:
            aws_access_key = credentials.get("aws_access_key_id", self.aws_access_key)
            aws_secret_key = credentials.get("aws_secret_access_key", self.aws_secret_key)
            aws_region = credentials.get("aws_region", self.aws_region)

            # Create boto3 session
            session = boto3.Session(
                aws_access_key_id=aws_access_key,
                aws_secret_access_key=aws_secret_key,
                region_name=aws_region
            )

            # Create CodeWhisperer client
            self.codewhisperer_client = session.client('codewhisperer')

            # Verify connection
            try:
                # Test API call
                response = self.codewhisperer_client.list_recommendations(
                    fileContext={'leftFileContent': '', 'rightFileContent': '', 'filename': 'test.py'},
                    maxResults=1
                )
                self.connected = True
                logger.info("Connected to AWS CodeWhisperer successfully")
                return True
            except ClientError as e:
                logger.error(f"AWS API verification failed: {e}")
                return False

        except Exception as e:
            logger.error(f"Connection error: {e}")
            return False

    async def disconnect(self) -> bool:
        """Disconnect from AWS"""
        self.codewhisperer_client = None
        self.connected = False
        return True

    async def execute(self, action: str, parameters: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        """
        Execute CodeWhisperer actions

        Actions:
        - generate: Generate code recommendations
        - scan: Security vulnerability scan
        - explain: Explain code
        - optimize: Optimize code for AWS services
        - complete: Code completion
        """
        if not self.connected:
            return {"success": False, "error": "Not connected to AWS CodeWhisperer"}

        action_map = {
            "generate": self._generate_recommendations,
            "scan": self._security_scan,
            "explain": self._explain_code,
            "optimize": self._optimize_for_aws,
            "complete": self._code_completion
        }

        handler = action_map.get(action)
        if not handler:
            return {"success": False, "error": f"Unknown action: {action}"}

        try:
            result = await handler(parameters)
            return {"success": True, "result": result}
        except Exception as e:
            logger.error(f"Action '{action}' failed: {e}")
            return {"success": False, "error": str(e)}

    async def _generate_recommendations(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Generate code recommendations"""
        try:
            code_before = params.get("code_before", "")
            code_after = params.get("code_after", "")
            filename = params.get("filename", "code.py")
            max_results = params.get("max_results", 5)

            response = self.codewhisperer_client.list_recommendations(
                fileContext={
                    'leftFileContent': code_before,
                    'rightFileContent': code_after,
                    'filename': filename
                },
                maxResults=max_results
            )

            recommendations = []
            for rec in response.get('recommendations', []):
                recommendations.append({
                    "content": rec.get('content', ''),
                    "references": rec.get('references', []),
                    "recommendation_id": rec.get('recommendationId', '')
                })

            return {
                "recommendations": recommendations,
                "count": len(recommendations),
                "timestamp": datetime.now().isoformat()
            }
        except ClientError as e:
            raise Exception(f"AWS API error: {e}")

    async def _security_scan(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Perform security vulnerability scanning"""
        try:
            code = params.get("code", "")
            filename = params.get("filename", "code.py")
            language = params.get("language", "python")

            # Create code scan
            response = self.codewhisperer_client.create_code_scan(
                artifacts={
                    'sourceCode': code.encode('utf-8')
                },
                language=language.upper()
            )

            job_id = response.get('jobId', '')

            # Get scan results
            scan_results = self.codewhisperer_client.get_code_scan(
                jobId=job_id
            )

            findings = []
            for finding in scan_results.get('findings', []):
                findings.append({
                    "title": finding.get('title', ''),
                    "description": finding.get('description', ''),
                    "severity": finding.get('severity', ''),
                    "recommendation": finding.get('recommendation', ''),
                    "line_number": finding.get('startLine', 0),
                    "category": finding.get('category', '')
                })

            return {
                "findings": findings,
                "total_findings": len(findings),
                "scan_status": scan_results.get('status', ''),
                "job_id": job_id
            }
        except ClientError as e:
            raise Exception(f"Security scan failed: {e}")

    async def _explain_code(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Explain code using CodeWhisperer"""
        code = params.get("code", "")
        language = params.get("language", "python")

        # Use recommendations API to get explanation
        explanation_prompt = f"# Explain this {language} code:\n{code}\n# Explanation:\n"

        rec_result = await self._generate_recommendations({
            "code_before": explanation_prompt,
            "code_after": "",
            "filename": f"explain.{language}",
            "max_results": 1
        })

        recommendations = rec_result.get("recommendations", [])
        explanation = recommendations[0].get("content", "") if recommendations else "No explanation available"

        return {
            "explanation": explanation,
            "language": language
        }

    async def _optimize_for_aws(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Optimize code for AWS services"""
        code = params.get("code", "")
        service = params.get("aws_service", "lambda")  # lambda, ec2, s3, dynamodb, etc.
        language = params.get("language", "python")

        optimization_prompt = f"""# Optimize this {language} code for AWS {service}:
{code}
# Optimized version:
"""

        rec_result = await self._generate_recommendations({
            "code_before": optimization_prompt,
            "code_after": "",
            "filename": f"optimize.{language}",
            "max_results": 3
        })

        return {
            "optimizations": rec_result.get("recommendations", []),
            "target_service": service,
            "language": language
        }

    async def _code_completion(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get code completions"""
        code = params.get("code", "")
        cursor_position = params.get("cursor_position", len(code))
        filename = params.get("filename", "code.py")

        code_before = code[:cursor_position]
        code_after = code[cursor_position:]

        return await self._generate_recommendations({
            "code_before": code_before,
            "code_after": code_after,
            "filename": filename,
            "max_results": params.get("max_results", 5)
        })

    async def shutdown(self):
        """Cleanup"""
        await self.disconnect()
        self._initialized = False

    def get_schema(self) -> Dict[str, Any]:
        """Return schema"""
        return {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "enum": ["generate", "scan", "explain", "optimize", "complete"]
                },
                "code": {"type": "string"},
                "language": {"type": "string"},
                "filename": {"type": "string"}
            },
            "required": ["action"]
        }


plugin = AWSCodeWhispererPlugin()
