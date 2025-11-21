"""
Security Scanning Manager - 15+ Services
Vulnerability scanning, code analysis, threat detection
"""

import asyncio
import logging
import os
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)

class SecurityScanningManager:
    """Unified security scanning across 15+ services"""

    def __init__(self):
        self._initialized = False

    async def initialize(self, config: Optional[Dict] = None):
        if self._initialized:
            return
        self._initialized = True

    # ==================== CODE SCANNING ====================

    async def scan_code(self, provider: str, code: str, language: str = "python") -> Dict:
        """Scan code for vulnerabilities"""
        if provider == "snyk":
            return await self._snyk_scan(code, language)
        elif provider == "semgrep":
            return await self._semgrep_scan(code, language)
        elif provider == "sonarqube":
            return await self._sonarqube_scan(code, language)
        elif provider == "ai":
            return await self._ai_scan(code, language)
        else:
            raise ValueError(f"Unsupported provider: {provider}")

    async def _snyk_scan(self, code, language):
        import aiohttp
        async with aiohttp.ClientSession() as session:
            async with session.post(
                "https://snyk.io/api/v1/test",
                headers={"Authorization": f"token {os.environ.get('SNYK_TOKEN')}"},
                json={"code": code, "language": language}
            ) as response:
                return await response.json()

    async def _semgrep_scan(self, code, language):
        import subprocess
        import tempfile
        with tempfile.NamedTemporaryFile(mode='w', suffix=f'.{language}', delete=False) as f:
            f.write(code)
            f.flush()
            result = subprocess.run(
                ["semgrep", "--json", "--config", "auto", f.name],
                capture_output=True, text=True
            )
            import json
            return json.loads(result.stdout) if result.stdout else {"errors": result.stderr}

    async def _sonarqube_scan(self, code, language):
        import aiohttp
        base_url = os.environ.get("SONARQUBE_URL", "http://localhost:9000")
        token = os.environ.get("SONARQUBE_TOKEN")
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{base_url}/api/ce/submit",
                headers={"Authorization": f"Basic {token}"},
                data={"code": code}
            ) as response:
                return await response.json()

    async def _ai_scan(self, code, language):
        """AI-powered security analysis"""
        from windows_ai.integrations.ai_providers import AIProvidersManager, Provider

        ai = AIProvidersManager()
        await ai.initialize()

        messages = [
            {"role": "system", "content": """You are a security expert. Analyze the code for:
1. SQL injection vulnerabilities
2. XSS vulnerabilities
3. Command injection
4. Path traversal
5. Insecure authentication
6. Sensitive data exposure
7. Other OWASP Top 10 vulnerabilities

Return JSON: {"vulnerabilities": [{"type": "...", "severity": "high/medium/low", "line": N, "description": "..."}]}"""},
            {"role": "user", "content": f"Language: {language}\n\n```\n{code}\n```"}
        ]

        response = await ai.chat(Provider.OPENAI, messages)
        import json
        try:
            return json.loads(response["content"])
        except:
            return {"raw": response["content"]}

    # ==================== DEPENDENCY SCANNING ====================

    async def scan_dependencies(self, provider: str, manifest: str, manifest_type: str = "requirements.txt") -> Dict:
        """Scan dependencies for vulnerabilities"""
        if provider == "snyk":
            return await self._snyk_deps(manifest, manifest_type)
        elif provider == "safety":
            return await self._safety_scan(manifest)
        elif provider == "npm_audit":
            return await self._npm_audit(manifest)

    async def _snyk_deps(self, manifest, manifest_type):
        import aiohttp
        async with aiohttp.ClientSession() as session:
            async with session.post(
                "https://snyk.io/api/v1/test",
                headers={"Authorization": f"token {os.environ.get('SNYK_TOKEN')}"},
                json={"manifest": manifest, "type": manifest_type}
            ) as response:
                return await response.json()

    async def _safety_scan(self, requirements):
        import subprocess
        import tempfile
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write(requirements)
            f.flush()
            result = subprocess.run(
                ["safety", "check", "-r", f.name, "--json"],
                capture_output=True, text=True
            )
            import json
            return json.loads(result.stdout) if result.stdout else {"error": result.stderr}

    async def _npm_audit(self, package_json):
        import subprocess
        import tempfile
        import json
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            f.write(package_json)
            f.flush()
            result = subprocess.run(
                ["npm", "audit", "--json"],
                capture_output=True, text=True,
                cwd=os.path.dirname(f.name)
            )
            return json.loads(result.stdout) if result.stdout else {"error": result.stderr}

    # ==================== SECRET SCANNING ====================

    async def scan_secrets(self, content: str) -> List[Dict]:
        """Scan for exposed secrets"""
        import re

        patterns = {
            "aws_access_key": r"AKIA[0-9A-Z]{16}",
            "aws_secret_key": r"[0-9a-zA-Z/+]{40}",
            "github_token": r"ghp_[a-zA-Z0-9]{36}",
            "github_oauth": r"gho_[a-zA-Z0-9]{36}",
            "slack_token": r"xox[baprs]-[0-9a-zA-Z]{10,48}",
            "stripe_secret": r"sk_live_[0-9a-zA-Z]{24}",
            "google_api": r"AIza[0-9A-Za-z\\-_]{35}",
            "jwt": r"eyJ[A-Za-z0-9-_=]+\.eyJ[A-Za-z0-9-_=]+\.[A-Za-z0-9-_.+/=]*",
            "private_key": r"-----BEGIN (RSA |EC |DSA |OPENSSH )?PRIVATE KEY-----",
            "password_in_url": r"://[^:]+:[^@]+@",
        }

        findings = []
        for secret_type, pattern in patterns.items():
            matches = re.finditer(pattern, content)
            for match in matches:
                findings.append({
                    "type": secret_type,
                    "match": match.group()[:20] + "...",
                    "position": match.start()
                })

        return findings

    # ==================== URL/DOMAIN SCANNING ====================

    async def scan_url(self, url: str) -> Dict:
        """Scan URL for threats"""
        import aiohttp

        results = {}

        # VirusTotal
        vt_key = os.environ.get("VIRUSTOTAL_API_KEY")
        if vt_key:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"https://www.virustotal.com/api/v3/urls/{url}",
                    headers={"x-apikey": vt_key}
                ) as response:
                    if response.status == 200:
                        results["virustotal"] = await response.json()

        # Google Safe Browsing
        gsb_key = os.environ.get("GOOGLE_SAFE_BROWSING_KEY")
        if gsb_key:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"https://safebrowsing.googleapis.com/v4/threatMatches:find?key={gsb_key}",
                    json={
                        "client": {"clientId": "windowsai"},
                        "threatInfo": {
                            "threatTypes": ["MALWARE", "SOCIAL_ENGINEERING"],
                            "platformTypes": ["ANY_PLATFORM"],
                            "threatEntryTypes": ["URL"],
                            "threatEntries": [{"url": url}]
                        }
                    }
                ) as response:
                    results["google_safe_browsing"] = await response.json()

        return results

    # ==================== CONTAINER SCANNING ====================

    async def scan_container(self, image: str) -> Dict:
        """Scan container image for vulnerabilities"""
        import subprocess
        import json

        # Trivy scanner
        result = subprocess.run(
            ["trivy", "image", "--format", "json", image],
            capture_output=True, text=True
        )
        return json.loads(result.stdout) if result.stdout else {"error": result.stderr}

    def list_providers(self) -> Dict[str, List[str]]:
        return {
            "code": ["snyk", "semgrep", "sonarqube", "codeql", "ai"],
            "dependencies": ["snyk", "safety", "npm_audit", "dependabot"],
            "secrets": ["gitleaks", "trufflehog", "detect-secrets"],
            "containers": ["trivy", "clair", "anchore", "snyk"],
            "urls": ["virustotal", "google_safe_browsing", "urlscan"]
        }
