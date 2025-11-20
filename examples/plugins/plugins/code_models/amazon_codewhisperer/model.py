"""
Amazon CodeWhisperer Code Model Integration

Amazon CodeWhisperer is an AI-powered code generator that provides real-time
code suggestions, security scanning, and reference tracking.
"""

import os
import json
import boto3
import time
from typing import List, Dict, Optional, Any
from botocore.exceptions import ClientError, NoCredentialsError


class AmazonCodeWhisperer:
    """
    Amazon CodeWhisperer - AI code companion

    Uses AWS CodeWhisperer API for intelligent code generation and suggestions.
    Requires AWS credentials with CodeWhisperer permissions.

    Supported languages: Python, Java, JavaScript, TypeScript, C#, Go, Rust, Ruby, SQL, and more
    Features: autocomplete, security-scan, reference-tracking, code-generation
    """

    def __init__(self, api_key: Optional[str] = None, **kwargs):
        """
        Initialize Amazon CodeWhisperer client

        Args:
            api_key: Not used (AWS uses boto3 credential chain)
            **kwargs: Additional configuration options
                - region: AWS region (default: us-east-1)
                - profile: AWS profile name
                - access_key_id: AWS access key ID
                - secret_access_key: AWS secret access key
                - session_token: AWS session token (optional)
        """
        self.region = kwargs.get("region", os.getenv("AWS_REGION", "us-east-1"))
        self.profile = kwargs.get("profile", os.getenv("AWS_PROFILE"))
        self.provider = "amazon"

        # Supported languages
        self.supported_languages = [
            'python', 'java', 'javascript', 'typescript', 'csharp', 'go',
            'rust', 'ruby', 'php', 'cpp', 'c', 'sql', 'shell', 'kotlin',
            'scala', 'json', 'yaml', 'terraform', 'cloudformation'
        ]

        self.features = [
            'autocomplete', 'security-scan', 'reference-tracking',
            'code-generation', 'explain', 'fix-bugs'
        ]

        # Initialize boto3 client
        try:
            session_kwargs = {"region_name": self.region}

            if self.profile:
                session_kwargs["profile_name"] = self.profile

            # Create session
            session = boto3.Session(**session_kwargs)

            # Try to create client
            self.client = session.client('codewhisperer')
            self._authenticated = True

        except (ClientError, NoCredentialsError) as e:
            self.client = None
            self._authenticated = False

    def complete(self, code: str, language: str = "python", **kwargs) -> Dict[str, Any]:
        """
        Generate code completion

        Args:
            code: Code context/prefix
            language: Programming language
            **kwargs: Additional options
                - file_path: Path to file being edited
                - max_results: Maximum number of suggestions (default: 5)

        Returns:
            Dict with completions and metadata
        """
        if not self._authenticated or not self.client:
            return {
                "error": "Not authenticated with AWS CodeWhisperer",
                "completions": [],
                "provider": "amazon_codewhisperer"
            }

        try:
            file_path = kwargs.get("file_path", f"untitled.{self._get_extension(language)}")
            max_results = kwargs.get("max_results", 5)

            response = self.client.generate_recommendations(
                fileContext={
                    'filename': file_path,
                    'programmingLanguage': {
                        'languageName': language
                    },
                    'leftFileContent': code,
                    'rightFileContent': kwargs.get("suffix", "")
                },
                maxResults=max_results
            )

            completions = []
            for rec in response.get('recommendations', []):
                completions.append({
                    "text": rec.get('content', ''),
                    "references": rec.get('references', []),
                    "most_relevant_missing_imports": rec.get('mostRelevantMissingImports', [])
                })

            return {
                "completions": completions,
                "language": language,
                "provider": "amazon_codewhisperer",
                "request_id": response.get('ResponseMetadata', {}).get('RequestId')
            }

        except ClientError as e:
            return {
                "error": f"AWS API error: {e.response['Error']['Message']}",
                "completions": [],
                "provider": "amazon_codewhisperer"
            }
        except Exception as e:
            return {
                "error": str(e),
                "completions": [],
                "provider": "amazon_codewhisperer"
            }

    def chat(self, messages: List[Dict[str, str]], **kwargs) -> Dict[str, Any]:
        """
        Chat about code (not directly supported by CodeWhisperer)

        This method provides a basic implementation using code generation
        capabilities for code-related questions.

        Args:
            messages: List of message dicts with 'role' and 'content'
            **kwargs: Additional options

        Returns:
            Dict with response and metadata
        """
        # CodeWhisperer doesn't have a direct chat API
        # We simulate it using code generation
        last_message = messages[-1].get("content", "") if messages else ""

        return {
            "response": "CodeWhisperer doesn't support direct chat. Use complete() for code suggestions.",
            "note": "For chat capabilities, consider using Amazon Q Developer",
            "provider": "amazon_codewhisperer"
        }

    def explain(self, code: str, language: str = "python") -> str:
        """
        Explain what code does

        Args:
            code: Code to explain
            language: Programming language

        Returns:
            Explanation string
        """
        # CodeWhisperer doesn't have built-in explain
        # Suggest using Amazon Q or other services
        return (
            f"CodeWhisperer focuses on code generation and suggestions.\n"
            f"For code explanation, consider using Amazon Q Developer or other AI services.\n"
            f"Code to explain:\n{code}"
        )

    def suggest_fix(self, code: str, error: str, language: str = "python") -> Dict[str, Any]:
        """
        Suggest fixes for buggy code

        Args:
            code: Code with bug
            error: Error message or description
            language: Programming language

        Returns:
            Dict with suggested fixes
        """
        # Use code completion to suggest fixes
        prompt = f"{code}\n# Fix for error: {error}\n"

        result = self.complete(prompt, language=language, max_results=3)

        return {
            "suggestions": result.get("completions", []),
            "error": result.get("error"),
            "provider": "amazon_codewhisperer"
        }

    def generate_docs(self, code: str, language: str = "python", **kwargs) -> str:
        """
        Generate documentation for code

        Args:
            code: Code to document
            language: Programming language
            **kwargs: Additional options

        Returns:
            Generated documentation string
        """
        # Use completion to generate docstrings
        if language == "python":
            prompt = f'{code}\n    """\n    '
        elif language in ["javascript", "typescript"]:
            prompt = f'{code}\n/**\n * '
        else:
            prompt = f'{code}\n// Documentation:\n// '

        result = self.complete(prompt, language=language, max_results=1)

        if result.get("completions"):
            return result["completions"][0].get("text", "")

        return "Failed to generate documentation"

    def scan_security(self, code: str, language: str = "python", **kwargs) -> Dict[str, Any]:
        """
        Scan code for security vulnerabilities

        Args:
            code: Code to scan
            language: Programming language
            **kwargs: Additional options
                - file_path: Path to file

        Returns:
            Dict with security findings
        """
        if not self._authenticated or not self.client:
            return {
                "error": "Not authenticated with AWS CodeWhisperer",
                "findings": [],
                "provider": "amazon_codewhisperer"
            }

        try:
            file_path = kwargs.get("file_path", f"untitled.{self._get_extension(language)}")

            # Create code scan
            response = self.client.create_code_scan(
                programmingLanguage={
                    'languageName': language
                },
                codeContext={
                    'filename': file_path,
                    'content': code
                }
            )

            scan_id = response.get('jobId')

            # Wait for scan to complete
            max_wait = 30
            for _ in range(max_wait):
                status_response = self.client.get_code_scan(
                    jobId=scan_id
                )

                status = status_response.get('status')
                if status == 'Completed':
                    findings = status_response.get('findings', [])
                    return {
                        "findings": findings,
                        "scan_id": scan_id,
                        "provider": "amazon_codewhisperer"
                    }
                elif status == 'Failed':
                    return {
                        "error": "Security scan failed",
                        "findings": [],
                        "provider": "amazon_codewhisperer"
                    }

                time.sleep(1)

            return {
                "error": "Security scan timed out",
                "scan_id": scan_id,
                "provider": "amazon_codewhisperer"
            }

        except ClientError as e:
            return {
                "error": f"AWS API error: {e.response['Error']['Message']}",
                "findings": [],
                "provider": "amazon_codewhisperer"
            }
        except Exception as e:
            return {
                "error": str(e),
                "findings": [],
                "provider": "amazon_codewhisperer"
            }

    def is_available(self) -> bool:
        """
        Check if Amazon CodeWhisperer service is available

        Returns:
            True if service is accessible
        """
        if not self._authenticated or not self.client:
            return False

        try:
            # Try a simple API call
            self.client.list_available_customizations()
            return True
        except Exception:
            return False

    def get_info(self) -> Dict[str, Any]:
        """
        Get plugin metadata and status

        Returns:
            Dict with plugin information
        """
        return {
            "name": "Amazon CodeWhisperer",
            "provider": "amazon",
            "region": self.region,
            "supported_languages": self.supported_languages,
            "features": self.features,
            "available": self.is_available(),
            "authenticated": self._authenticated,
            "requires_auth": True,
            "auth_type": "aws_credentials",
            "note": "Requires AWS credentials with CodeWhisperer permissions"
        }

    def _get_extension(self, language: str) -> str:
        """Get file extension for language"""
        extensions = {
            'python': 'py',
            'java': 'java',
            'javascript': 'js',
            'typescript': 'ts',
            'csharp': 'cs',
            'go': 'go',
            'rust': 'rs',
            'ruby': 'rb',
            'php': 'php',
            'cpp': 'cpp',
            'c': 'c',
            'sql': 'sql',
            'shell': 'sh',
            'kotlin': 'kt',
            'scala': 'scala'
        }
        return extensions.get(language, 'txt')


# Example usage and testing
if __name__ == "__main__":
    # Initialize CodeWhisperer
    codewhisperer = AmazonCodeWhisperer()

    # Get info
    info = codewhisperer.get_info()
    print("Amazon CodeWhisperer Info:")
    print(json.dumps(info, indent=2))

    # Test if available
    if codewhisperer.is_available():
        print("\nAmazon CodeWhisperer is available")

        # Test completion
        code = "def calculate_fibonacci(n):\n    "
        result = codewhisperer.complete(code, language="python")
        print("\nCode completion:")
        print(json.dumps(result, indent=2))

        # Test security scan
        test_code = """
import subprocess
user_input = input("Enter command: ")
subprocess.call(user_input, shell=True)  # Security vulnerability
"""
        scan_result = codewhisperer.scan_security(test_code, language="python")
        print("\nSecurity scan:")
        print(json.dumps(scan_result, indent=2))
    else:
        print("\nAmazon CodeWhisperer is not available.")
        print("Configure AWS credentials with CodeWhisperer permissions.")
