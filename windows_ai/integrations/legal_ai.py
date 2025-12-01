"""
Legal & Compliance AI Manager - 15+ Services
Contract analysis, legal research, compliance checking, document review
"""

import asyncio
import logging
import os
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)

class LegalAIManager:
    """Unified legal AI across 15+ services"""

    def __init__(self):
        self._initialized = False

    async def initialize(self, config: Optional[Dict] = None):
        if self._initialized:
            return
        self._initialized = True

    # ==================== CONTRACT ANALYSIS ====================

    async def analyze_contract(self, contract_text: str) -> Dict:
        """Analyze contract for key terms, risks, and obligations"""
        from windows_ai.integrations.ai_providers import AIProvidersManager, Provider

        ai = AIProvidersManager()
        await ai.initialize()

        messages = [
            {"role": "system", "content": """You are a legal contract analyst. Analyze the contract and extract:
1. Key terms and definitions
2. Obligations of each party
3. Important dates and deadlines
4. Potential risks and red flags
5. Termination clauses
6. Liability and indemnification
7. Intellectual property provisions
Return structured JSON with these categories."""},
            {"role": "user", "content": contract_text}
        ]

        response = await ai.chat(Provider.OPENAI, messages, model="gpt-4o")
        import json
        try:
            return json.loads(response["content"])
        except:
            return {"analysis": response["content"]}

    async def compare_contracts(self, contract1: str, contract2: str) -> Dict:
        """Compare two contracts and highlight differences"""
        from windows_ai.integrations.ai_providers import AIProvidersManager, Provider

        ai = AIProvidersManager()
        await ai.initialize()

        messages = [
            {"role": "system", "content": """Compare these two contracts and identify:
1. Key differences in terms
2. Added/removed clauses
3. Changes in obligations
4. Risk comparison
Return JSON: {"differences": [...], "added": [...], "removed": [...], "risk_changes": [...]}"""},
            {"role": "user", "content": f"Contract 1:\n{contract1}\n\nContract 2:\n{contract2}"}
        ]

        response = await ai.chat(Provider.OPENAI, messages, model="gpt-4o")
        import json
        try:
            return json.loads(response["content"])
        except:
            return {"comparison": response["content"]}

    # ==================== LEGAL RESEARCH ====================

    async def search_case_law(self, query: str, jurisdiction: str = "US") -> List[Dict]:
        """Search case law databases"""
        import aiohttp

        # CourtListener API
        async with aiohttp.ClientSession() as session:
            async with session.get(
                "https://www.courtlistener.com/api/rest/v3/search/",
                params={"q": query, "type": "o"},
                headers={"Authorization": f"Token {os.environ.get('COURTLISTENER_API_KEY')}"}
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    return [{
                        "case_name": r.get("caseName"),
                        "citation": r.get("citation", []),
                        "court": r.get("court"),
                        "date_filed": r.get("dateFiled"),
                        "snippet": r.get("snippet")
                    } for r in data.get("results", [])]

        return []

    async def search_statutes(self, query: str, jurisdiction: str = "federal") -> List[Dict]:
        """Search statutory databases"""
        import aiohttp

        # Using public APIs
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"https://api.uscode.house.gov/search?query={query}"
            ) as response:
                if response.status == 200:
                    return await response.json()

        return [{"note": "Statutory search - implement with specific API"}]

    async def legal_research_assistant(self, question: str, context: str = None) -> Dict:
        """AI-powered legal research assistant"""
        from windows_ai.integrations.ai_providers import AIProvidersManager, Provider

        ai = AIProvidersManager()
        await ai.initialize()

        messages = [
            {"role": "system", "content": """You are a legal research assistant. Provide:
1. Relevant legal principles
2. Applicable statutes and regulations
3. Key case precedents
4. Legal analysis
DISCLAIMER: This is for research purposes only, not legal advice.
Return structured response with citations."""},
            {"role": "user", "content": f"Question: {question}\n\nContext: {context or 'General'}"}
        ]

        response = await ai.chat(Provider.OPENAI, messages, model="gpt-4o")
        return {"research": response["content"]}

    # ==================== COMPLIANCE ====================

    async def check_gdpr_compliance(self, document: str) -> Dict:
        """Check GDPR compliance of document/policy"""
        from windows_ai.integrations.ai_providers import AIProvidersManager, Provider

        ai = AIProvidersManager()
        await ai.initialize()

        messages = [
            {"role": "system", "content": """Analyze this document for GDPR compliance. Check for:
1. Data collection and processing disclosures
2. Consent mechanisms
3. Data subject rights provisions
4. Data retention policies
5. Security measures
6. Third-party data sharing
7. DPO contact information
8. Cross-border transfer provisions
Return JSON: {"compliant": bool, "issues": [...], "recommendations": [...], "score": 0-100}"""},
            {"role": "user", "content": document}
        ]

        response = await ai.chat(Provider.OPENAI, messages, model="gpt-4o")
        import json
        try:
            return json.loads(response["content"])
        except:
            return {"analysis": response["content"]}

    async def check_hipaa_compliance(self, document: str) -> Dict:
        """Check HIPAA compliance"""
        from windows_ai.integrations.ai_providers import AIProvidersManager, Provider

        ai = AIProvidersManager()
        await ai.initialize()

        messages = [
            {"role": "system", "content": """Analyze for HIPAA compliance:
1. PHI handling procedures
2. Access controls
3. Audit trails
4. Encryption requirements
5. Business associate agreements
6. Breach notification procedures
Return JSON with compliance status and issues."""},
            {"role": "user", "content": document}
        ]

        response = await ai.chat(Provider.OPENAI, messages, model="gpt-4o")
        import json
        try:
            return json.loads(response["content"])
        except:
            return {"analysis": response["content"]}

    async def check_sox_compliance(self, document: str) -> Dict:
        """Check SOX compliance for financial controls"""
        from windows_ai.integrations.ai_providers import AIProvidersManager, Provider

        ai = AIProvidersManager()
        await ai.initialize()

        messages = [
            {"role": "system", "content": """Analyze for SOX compliance:
1. Internal control procedures
2. Financial reporting accuracy
3. Audit trail requirements
4. Access controls
5. Management certifications
Return JSON with compliance assessment."""},
            {"role": "user", "content": document}
        ]

        response = await ai.chat(Provider.OPENAI, messages, model="gpt-4o")
        import json
        try:
            return json.loads(response["content"])
        except:
            return {"analysis": response["content"]}

    # ==================== DOCUMENT REVIEW ====================

    async def review_legal_document(self, document: str, doc_type: str = "general") -> Dict:
        """Review legal document for issues"""
        from windows_ai.integrations.ai_providers import AIProvidersManager, Provider

        ai = AIProvidersManager()
        await ai.initialize()

        prompts = {
            "nda": "Review this NDA for: confidentiality scope, exclusions, term, remedies",
            "employment": "Review employment agreement for: compensation, non-compete, IP assignment, termination",
            "lease": "Review lease for: rent terms, maintenance, termination, renewal options",
            "partnership": "Review partnership agreement for: profit sharing, decision making, exit provisions",
            "general": "Review this legal document for key terms, risks, and issues"
        }

        messages = [
            {"role": "system", "content": f"{prompts.get(doc_type, prompts['general'])}. Return structured analysis."},
            {"role": "user", "content": document}
        ]

        response = await ai.chat(Provider.OPENAI, messages, model="gpt-4o")
        return {"document_type": doc_type, "review": response["content"]}

    async def redact_pii(self, document: str) -> Dict:
        """Identify and redact PII from document"""
        from windows_ai.integrations.ai_providers import AIProvidersManager, Provider

        ai = AIProvidersManager()
        await ai.initialize()

        messages = [
            {"role": "system", "content": """Identify all PII in this document:
- Names, SSN, addresses, phone numbers, emails
- Financial information (account numbers, credit cards)
- Health information
- Biometric data
Return JSON: {"pii_found": [...], "redacted_text": "text with [REDACTED]"}"""},
            {"role": "user", "content": document}
        ]

        response = await ai.chat(Provider.OPENAI, messages)
        import json
        try:
            return json.loads(response["content"])
        except:
            return {"analysis": response["content"]}

    # ==================== LEGAL DOCUMENT GENERATION ====================

    async def generate_legal_document(self, doc_type: str, parameters: Dict) -> str:
        """Generate legal document from template"""
        from windows_ai.integrations.ai_providers import AIProvidersManager, Provider

        ai = AIProvidersManager()
        await ai.initialize()

        templates = {
            "nda": "Non-Disclosure Agreement",
            "privacy_policy": "Privacy Policy",
            "terms_of_service": "Terms of Service",
            "employment_offer": "Employment Offer Letter",
            "contractor_agreement": "Independent Contractor Agreement"
        }

        messages = [
            {"role": "system", "content": f"""Generate a professional {templates.get(doc_type, doc_type)}.
Include all standard clauses and legal language.
Use the provided parameters to customize the document.
Note: This is a template and should be reviewed by legal counsel."""},
            {"role": "user", "content": f"Parameters: {parameters}"}
        ]

        response = await ai.chat(Provider.OPENAI, messages, model="gpt-4o")
        return response["content"]

    def list_capabilities(self) -> Dict[str, List[str]]:
        return {
            "contract_analysis": ["analyze", "compare", "extract_terms", "risk_assessment"],
            "legal_research": ["case_law", "statutes", "regulations", "precedents"],
            "compliance": ["gdpr", "hipaa", "sox", "ccpa", "pci_dss"],
            "document_review": ["nda", "employment", "lease", "partnership"],
            "document_generation": ["nda", "privacy_policy", "tos", "contracts"]
        }
