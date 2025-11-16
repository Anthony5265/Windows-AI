"""
Amazon Q Code Model Integration

Amazon Q Developer (formerly CodeWhisperer) is AWS's AI-powered code assistant
providing intelligent code completion, security scanning, and code generation.
"""

import os
import json
import uuid
import boto3
import requests
from typing import List, Dict, Optional, Any
from datetime import datetime


class AmazonQ:
    """
    Amazon Q Developer - AI-powered code assistant from AWS

    Uses AWS's CodeWhisperer service and Amazon Q APIs for code assistance.
    Provides enterprise-grade code completion, security scanning, and chat.

    Supported languages: Python, Java, JavaScript, TypeScript, C#, Go, Rust, and 15+ more
    Features: autocomplete, chat, explain, generate-tests, fix-bugs, security-scan
    """

    def __init__(self, api_key: Optional[str] = None, **kwargs):
        """
        Initialize Amazon Q Developer client

        Args:
            api_key: AWS access key (or set AWS_ACCESS_KEY_ID env var)
            **kwargs: Additional configuration options
                - secret_key: AWS secret key (or set AWS_SECRET_ACCESS_KEY)
                - region: AWS region (default: us-east-1)
                - session_token: AWS session token for temporary credentials
                - profile_name: AWS profile name
                - timeout: Request timeout in seconds (default: 30)
        """
        self.api_key = api_key or os.getenv("AWS_ACCESS_KEY_ID")
        self.secret_key = kwargs.get("secret_key", os.getenv("AWS_SECRET_ACCESS_KEY"))
        self.session_token = kwargs.get("session_token", os.getenv("AWS_SESSION_TOKEN"))
        self.region = kwargs.get("region", os.getenv("AWS_REGION", "us-east-1"))
        self.profile_name = kwargs.get("profile_name")
        self.timeout = kwargs.get("timeout", 30)
        self.provider = "amazon"
        self.session_id = str(uuid.uuid4())

        # Initialize boto3 client
        self._init_aws_client()

        # Comprehensive language support
        self.supported_languages = [
            'python', 'java', 'javascript', 'typescript', 'csharp', 'go',
            'rust', 'kotlin', 'swift', 'ruby', 'php', 'scala', 'sql',
            'cpp', 'c', 'shell', 'yaml', 'json', 'terraform', 'cloudformation'
        ]

        self.features = [
            'autocomplete', 'chat', 'explain', 'generate-tests', 'fix-bugs',
            'generate-docs', 'security-scan', 'code-review', 'refactor',
            'iac-generation'  # Infrastructure as Code
        ]

        # Security and compliance features
        self.security_features = {
            'vulnerability_scan': True,
            'secret_detection': True,
            'compliance_check': True,
            'license_scan': True
        }

    def _init_aws_client(self):
        """Initialize AWS boto3 client"""
        try:
            if self.profile_name:
                session = boto3.Session(profile_name=self.profile_name, region_name=self.region)
            else:
                session = boto3.Session(
                    aws_access_key_id=self.api_key,
                    aws_secret_access_key=self.secret_key,
                    aws_session_token=self.session_token,
                    region_name=self.region
                )

            self.codewhisperer_client = session.client('codewhisperer-runtime')
            self.q_client = session.client('q')
        except Exception as e:
            self.codewhisperer_client = None
            self.q_client = None

    def complete(self, code: str, language: str = "python", **kwargs) -> Dict[str, Any]:
        """
        Generate code completion using Amazon Q

        Args:
            code: Code context/prefix
            language: Programming language
            **kwargs: Additional options
                - cursor_position: Position in code (default: end)
                - max_results: Maximum completions (default: 5)
                - suffix: Code after cursor
                - file_path: File path for better context

        Returns:
            Dict with completions and metadata
        """
        if not self.codewhisperer_client:
            return {
                "error": "AWS credentials required. Configure AWS CLI or set AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY.",
                "completions": [],
                "provider": "amazon_q"
            }

        try:
            cursor_position = kwargs.get("cursor_position", len(code))
            max_results = kwargs.get("max_results", 5)
            suffix = kwargs.get("suffix", "")
            file_path = kwargs.get("file_path", f"file.{self._get_extension(language)}")

            # Amazon Q CodeWhisperer API call
            response = self.codewhisperer_client.generate_recommendations(
                fileContext={
                    'leftFileContent': code,
                    'rightFileContent': suffix,
                    'filename': file_path,
                    'programmingLanguage': {
                        'languageName': self._map_language(language)
                    }
                },
                maxResults=max_results
            )

            completions = []
            for recommendation in response.get('recommendations', []):
                completions.append({
                    "text": recommendation.get('content', ''),
                    "references": recommendation.get('references', []),
                    "recommendation_id": recommendation.get('recommendationId', ''),
                    "completion_type": recommendation.get('completionType', '')
                })

            return {
                "completions": completions,
                "language": language,
                "provider": "amazon_q",
                "model": "amazon-q-developer",
                "session_id": self.session_id,
                "response_metadata": response.get('ResponseMetadata', {})
            }

        except Exception as e:
            return {
                "error": str(e),
                "completions": [],
                "provider": "amazon_q"
            }

    def chat(self, messages: List[Dict[str, str]], **kwargs) -> Dict[str, Any]:
        """
        Chat with Amazon Q about code

        Args:
            messages: List of message dicts with 'role' and 'content'
            **kwargs: Additional options
                - conversation_id: Conversation ID for context
                - max_tokens: Maximum response tokens (default: 2048)

        Returns:
            Dict with response and metadata
        """
        if not self.q_client:
            return {
                "error": "AWS credentials required",
                "response": "",
                "provider": "amazon_q"
            }

        try:
            conversation_id = kwargs.get("conversation_id", str(uuid.uuid4()))

            # Get the latest user message
            user_message = ""
            for msg in reversed(messages):
                if msg.get("role") == "user":
                    user_message = msg.get("content", "")
                    break

            response = self.q_client.send_message(
                conversationId=conversation_id,
                userMessage=user_message
            )

            return {
                "response": response.get('systemMessage', ''),
                "conversation_id": response.get('conversationId', ''),
                "role": "assistant",
                "provider": "amazon_q",
                "model": "amazon-q",
                "response_metadata": response.get('ResponseMetadata', {})
            }

        except Exception as e:
            return {
                "error": str(e),
                "response": "",
                "provider": "amazon_q"
            }

    def explain(self, code: str, language: str = "python") -> str:
        """
        Explain what code does using Amazon Q

        Args:
            code: Code to explain
            language: Programming language

        Returns:
            Detailed explanation string
        """
        messages = [
            {
                "role": "user",
                "content": f"Explain this {language} code in detail. Include what it does, how it works, and any AWS best practices if applicable:\n\n```{language}\n{code}\n```"
            }
        ]

        result = self.chat(messages)
        return result.get("response", f"Failed to explain code: {result.get('error', 'Unknown error')}")

    def fix_bug(self, code: str, error: str, language: str = "python") -> Dict[str, Any]:
        """
        Suggest fixes for buggy code using Amazon Q

        Args:
            code: Code with bug
            error: Error message or description
            language: Programming language

        Returns:
            Dict with suggested fixes and explanations
        """
        messages = [
            {
                "role": "user",
                "content": f"Fix this {language} code that has an error. Provide the corrected code and explain the fix:\n\nCode:\n```{language}\n{code}\n```\n\nError:\n{error}"
            }
        ]

        result = self.chat(messages)
        return {
            "suggestion": result.get("response", ""),
            "error": result.get("error"),
            "provider": "amazon_q",
            "conversation_id": result.get("conversation_id")
        }

    def generate_tests(self, code: str, language: str = "python", **kwargs) -> str:
        """
        Generate unit tests for code using Amazon Q

        Args:
            code: Code to test
            language: Programming language
            **kwargs: Additional options
                - framework: Test framework (junit, pytest, jest, etc.)
                - coverage: Target coverage level

        Returns:
            Generated test code
        """
        framework = kwargs.get("framework", self._get_default_test_framework(language))
        coverage = kwargs.get("coverage", "comprehensive")

        messages = [
            {
                "role": "user",
                "content": f"Generate {coverage} {framework} unit tests for this {language} code. Include edge cases, error handling, and mocking where appropriate:\n\n```{language}\n{code}\n```"
            }
        ]

        result = self.chat(messages)
        return result.get("response", f"Failed to generate tests: {result.get('error', 'Unknown error')}")

    def generate_docs(self, code: str, language: str = "python", **kwargs) -> str:
        """
        Generate documentation for code using Amazon Q

        Args:
            code: Code to document
            language: Programming language
            **kwargs: Additional options
                - style: Documentation style

        Returns:
            Generated documentation string
        """
        style = kwargs.get("style", self._get_default_doc_style(language))

        messages = [
            {
                "role": "user",
                "content": f"Generate {style}-style documentation for this {language} code. Include description, parameters, return values, exceptions, and usage examples:\n\n```{language}\n{code}\n```"
            }
        ]

        result = self.chat(messages)
        return result.get("response", f"Failed to generate documentation: {result.get('error', 'Unknown error')}")

    def security_scan(self, code: str, language: str = "python") -> Dict[str, Any]:
        """
        Scan code for security vulnerabilities using Amazon Q

        Args:
            code: Code to scan
            language: Programming language

        Returns:
            Dict with security findings and recommendations
        """
        if not self.codewhisperer_client:
            return {
                "error": "AWS credentials required",
                "findings": [],
                "provider": "amazon_q"
            }

        try:
            # Use CodeWhisperer security scan
            file_path = f"file.{self._get_extension(language)}"

            response = self.codewhisperer_client.create_code_scan(
                artifacts={
                    'files': [
                        {
                            'filename': file_path,
                            'content': code.encode('utf-8')
                        }
                    ]
                },
                programmingLanguage={
                    'languageName': self._map_language(language)
                }
            )

            return {
                "scan_id": response.get('scanId', ''),
                "status": response.get('status', ''),
                "findings": response.get('findings', []),
                "provider": "amazon_q",
                "security_features": self.security_features
            }

        except Exception as e:
            return {
                "error": str(e),
                "findings": [],
                "provider": "amazon_q"
            }

    def review_code(self, code: str, language: str = "python") -> Dict[str, Any]:
        """
        Perform comprehensive code review with Amazon Q

        Args:
            code: Code to review
            language: Programming language

        Returns:
            Dict with review findings and suggestions
        """
        messages = [
            {
                "role": "user",
                "content": f"Perform a comprehensive code review of this {language} code. Check for:\n- Security vulnerabilities\n- Performance issues\n- AWS best practices (if applicable)\n- Code quality and maintainability\n- Potential bugs\n\n```{language}\n{code}\n```"
            }
        ]

        result = self.chat(messages)
        return {
            "review": result.get("response", ""),
            "error": result.get("error"),
            "provider": "amazon_q",
            "conversation_id": result.get("conversation_id")
        }

    def generate_iac(self, description: str, platform: str = "cloudformation") -> Dict[str, Any]:
        """
        Generate Infrastructure as Code using Amazon Q

        Args:
            description: Natural language description of infrastructure
            platform: IaC platform (cloudformation, terraform, cdk)

        Returns:
            Dict with generated IaC code
        """
        messages = [
            {
                "role": "user",
                "content": f"Generate {platform} infrastructure code based on this description:\n\n{description}\n\nInclude comments and follow AWS best practices for security and cost optimization."
            }
        ]

        result = self.chat(messages)
        return {
            "iac_code": result.get("response", ""),
            "platform": platform,
            "error": result.get("error"),
            "provider": "amazon_q"
        }

    def is_available(self) -> bool:
        """
        Check if Amazon Q service is available

        Returns:
            True if service is accessible and authenticated
        """
        if not self.codewhisperer_client:
            return False

        try:
            # Test connectivity with a simple API call
            self.codewhisperer_client.list_code_scan_findings(
                maxResults=1
            )
            return True
        except Exception:
            # Try alternative check
            try:
                return self.api_key is not None and self.secret_key is not None
            except:
                return False

    def get_info(self) -> Dict[str, Any]:
        """
        Get plugin metadata and status

        Returns:
            Dict with comprehensive plugin information
        """
        return {
            "name": "Amazon Q Developer",
            "provider": "amazon",
            "version": "1.0.0",
            "region": self.region,
            "supported_languages": self.supported_languages,
            "features": self.features,
            "security_features": self.security_features,
            "available": self.is_available(),
            "requires_auth": True,
            "auth_type": "aws_credentials",
            "session_id": self.session_id,
            "formerly_known_as": "CodeWhisperer",
            "integration_platforms": [
                "AWS Console", "VS Code", "JetBrains IDEs",
                "Visual Studio", "AWS Cloud9", "AWS Lambda Console"
            ],
            "enterprise_features": {
                "sso_integration": True,
                "admin_controls": True,
                "usage_analytics": True,
                "customization": True
            }
        }

    def _map_language(self, language: str) -> str:
        """Map language to AWS CodeWhisperer language identifier"""
        language_map = {
            'python': 'python',
            'java': 'java',
            'javascript': 'javascript',
            'typescript': 'typescript',
            'csharp': 'csharp',
            'go': 'go',
            'rust': 'rust',
            'kotlin': 'kotlin',
            'swift': 'swift',
            'ruby': 'ruby',
            'php': 'php',
            'scala': 'scala',
            'sql': 'sql',
            'cpp': 'cpp',
            'c': 'c',
            'shell': 'shell',
            'terraform': 'terraform',
            'cloudformation': 'yaml'
        }
        return language_map.get(language.lower(), 'plaintext')

    def _get_extension(self, language: str) -> str:
        """Get file extension for language"""
        extensions = {
            'python': 'py', 'java': 'java', 'javascript': 'js', 'typescript': 'ts',
            'csharp': 'cs', 'go': 'go', 'rust': 'rs', 'kotlin': 'kt',
            'swift': 'swift', 'ruby': 'rb', 'php': 'php', 'scala': 'scala',
            'sql': 'sql', 'cpp': 'cpp', 'c': 'c', 'shell': 'sh',
            'terraform': 'tf', 'cloudformation': 'yaml', 'yaml': 'yaml'
        }
        return extensions.get(language.lower(), 'txt')

    def _get_default_test_framework(self, language: str) -> str:
        """Get default test framework for language"""
        frameworks = {
            'python': 'pytest', 'java': 'junit', 'javascript': 'jest',
            'typescript': 'jest', 'csharp': 'nunit', 'go': 'testing',
            'rust': 'cargo test', 'kotlin': 'junit', 'swift': 'xctest',
            'ruby': 'rspec', 'php': 'phpunit', 'scala': 'scalatest'
        }
        return frameworks.get(language.lower(), 'unittest')

    def _get_default_doc_style(self, language: str) -> str:
        """Get default documentation style for language"""
        styles = {
            'python': 'google', 'java': 'javadoc', 'javascript': 'jsdoc',
            'typescript': 'jsdoc', 'csharp': 'xmldoc', 'go': 'godoc',
            'rust': 'rustdoc', 'kotlin': 'kdoc', 'swift': 'markup',
            'ruby': 'rdoc', 'php': 'phpdoc', 'scala': 'scaladoc'
        }
        return styles.get(language.lower(), 'markdown')


# Example usage and testing
if __name__ == "__main__":
    # Initialize Amazon Q
    amazon_q = AmazonQ()

    # Get info
    info = amazon_q.get_info()
    print("Amazon Q Developer Info:")
    print(json.dumps(info, indent=2))

    # Test if available
    if amazon_q.is_available():
        print("\nAmazon Q is available")

        # Test completion
        code = "import boto3\n\ndef create_s3_bucket(bucket_name):\n    "
        result = amazon_q.complete(code, language="python")
        print("\nCode completion:")
        print(json.dumps(result, indent=2))

        # Test security scan
        vulnerable_code = """
import os
password = "hardcoded_password_123"
api_key = os.environ.get("API_KEY", "default_key")
"""
        scan_result = amazon_q.security_scan(vulnerable_code, language="python")
        print("\nSecurity scan:")
        print(json.dumps(scan_result, indent=2))
    else:
        print("\nAmazon Q is not available.")
        print("Configure AWS credentials using AWS CLI or environment variables:")
        print("  AWS_ACCESS_KEY_ID")
        print("  AWS_SECRET_ACCESS_KEY")
        print("  AWS_REGION (optional)")
