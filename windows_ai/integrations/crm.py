"""
CRM Manager - 10+ Platforms
Salesforce, HubSpot, Pipedrive, Zoho, etc.
"""

import asyncio
import logging
import os
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)

class CRMManager:
    """Unified CRM operations across 10+ platforms"""

    def __init__(self):
        self._initialized = False

    async def initialize(self, config: Optional[Dict] = None):
        if self._initialized:
            return
        self._initialized = True

    # ==================== HUBSPOT ====================

    async def hubspot_create_contact(self, email: str, firstname: str = None, lastname: str = None, properties: Dict = None) -> Dict:
        """Create HubSpot contact"""
        import aiohttp

        api_key = os.environ.get("HUBSPOT_API_KEY")

        props = {"email": email}
        if firstname:
            props["firstname"] = firstname
        if lastname:
            props["lastname"] = lastname
        props.update(properties or {})

        async with aiohttp.ClientSession() as session:
            async with session.post(
                "https://api.hubapi.com/crm/v3/objects/contacts",
                headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
                json={"properties": props}
            ) as response:
                return await response.json()

    async def hubspot_get_contacts(self, limit: int = 10, properties: List[str] = None) -> List[Dict]:
        """Get HubSpot contacts"""
        import aiohttp

        api_key = os.environ.get("HUBSPOT_API_KEY")
        props = properties or ["email", "firstname", "lastname"]

        async with aiohttp.ClientSession() as session:
            async with session.get(
                "https://api.hubapi.com/crm/v3/objects/contacts",
                headers={"Authorization": f"Bearer {api_key}"},
                params={"limit": limit, "properties": ",".join(props)}
            ) as response:
                data = await response.json()
                return [{"id": c["id"], **c.get("properties", {})} for c in data.get("results", [])]

    async def hubspot_create_deal(self, dealname: str, amount: float = None, pipeline: str = "default", properties: Dict = None) -> Dict:
        """Create HubSpot deal"""
        import aiohttp

        api_key = os.environ.get("HUBSPOT_API_KEY")

        props = {"dealname": dealname, "pipeline": pipeline}
        if amount:
            props["amount"] = str(amount)
        props.update(properties or {})

        async with aiohttp.ClientSession() as session:
            async with session.post(
                "https://api.hubapi.com/crm/v3/objects/deals",
                headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
                json={"properties": props}
            ) as response:
                return await response.json()

    async def hubspot_search(self, object_type: str, filters: List[Dict], properties: List[str] = None) -> List[Dict]:
        """Search HubSpot objects"""
        import aiohttp

        api_key = os.environ.get("HUBSPOT_API_KEY")

        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"https://api.hubapi.com/crm/v3/objects/{object_type}/search",
                headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
                json={"filterGroups": [{"filters": filters}], "properties": properties or []}
            ) as response:
                data = await response.json()
                return data.get("results", [])

    # ==================== SALESFORCE ====================

    async def salesforce_create_lead(self, lastname: str, company: str, email: str = None, **kwargs) -> Dict:
        """Create Salesforce lead"""
        from simple_salesforce import Salesforce

        sf = Salesforce(
            username=os.environ.get("SALESFORCE_USERNAME"),
            password=os.environ.get("SALESFORCE_PASSWORD"),
            security_token=os.environ.get("SALESFORCE_TOKEN")
        )

        lead_data = {"LastName": lastname, "Company": company}
        if email:
            lead_data["Email"] = email
        lead_data.update(kwargs)

        result = sf.Lead.create(lead_data)
        return {"id": result["id"], "success": result["success"]}

    async def salesforce_query(self, soql: str) -> List[Dict]:
        """Execute Salesforce SOQL query"""
        from simple_salesforce import Salesforce

        sf = Salesforce(
            username=os.environ.get("SALESFORCE_USERNAME"),
            password=os.environ.get("SALESFORCE_PASSWORD"),
            security_token=os.environ.get("SALESFORCE_TOKEN")
        )

        result = sf.query(soql)
        return result.get("records", [])

    async def salesforce_create_opportunity(self, name: str, stage: str, close_date: str, amount: float = None) -> Dict:
        """Create Salesforce opportunity"""
        from simple_salesforce import Salesforce

        sf = Salesforce(
            username=os.environ.get("SALESFORCE_USERNAME"),
            password=os.environ.get("SALESFORCE_PASSWORD"),
            security_token=os.environ.get("SALESFORCE_TOKEN")
        )

        opp_data = {"Name": name, "StageName": stage, "CloseDate": close_date}
        if amount:
            opp_data["Amount"] = amount

        result = sf.Opportunity.create(opp_data)
        return {"id": result["id"], "success": result["success"]}

    # ==================== PIPEDRIVE ====================

    async def pipedrive_create_person(self, name: str, email: str = None, phone: str = None) -> Dict:
        """Create Pipedrive person"""
        import aiohttp

        api_token = os.environ.get("PIPEDRIVE_API_TOKEN")

        async with aiohttp.ClientSession() as session:
            async with session.post(
                "https://api.pipedrive.com/v1/persons",
                params={"api_token": api_token},
                json={"name": name, "email": email, "phone": phone}
            ) as response:
                return await response.json()

    async def pipedrive_create_deal(self, title: str, person_id: int = None, value: float = None) -> Dict:
        """Create Pipedrive deal"""
        import aiohttp

        api_token = os.environ.get("PIPEDRIVE_API_TOKEN")

        async with aiohttp.ClientSession() as session:
            async with session.post(
                "https://api.pipedrive.com/v1/deals",
                params={"api_token": api_token},
                json={"title": title, "person_id": person_id, "value": value}
            ) as response:
                return await response.json()

    async def pipedrive_get_deals(self, status: str = "open", limit: int = 10) -> List[Dict]:
        """Get Pipedrive deals"""
        import aiohttp

        api_token = os.environ.get("PIPEDRIVE_API_TOKEN")

        async with aiohttp.ClientSession() as session:
            async with session.get(
                "https://api.pipedrive.com/v1/deals",
                params={"api_token": api_token, "status": status, "limit": limit}
            ) as response:
                data = await response.json()
                return data.get("data", [])

    # ==================== ZOHO CRM ====================

    async def zoho_create_lead(self, last_name: str, company: str, email: str = None, **kwargs) -> Dict:
        """Create Zoho CRM lead"""
        import aiohttp

        access_token = os.environ.get("ZOHO_ACCESS_TOKEN")

        lead_data = {"Last_Name": last_name, "Company": company}
        if email:
            lead_data["Email"] = email
        lead_data.update(kwargs)

        async with aiohttp.ClientSession() as session:
            async with session.post(
                "https://www.zohoapis.com/crm/v3/Leads",
                headers={"Authorization": f"Zoho-oauthtoken {access_token}", "Content-Type": "application/json"},
                json={"data": [lead_data]}
            ) as response:
                return await response.json()

    async def zoho_get_records(self, module: str, limit: int = 10) -> List[Dict]:
        """Get Zoho CRM records"""
        import aiohttp

        access_token = os.environ.get("ZOHO_ACCESS_TOKEN")

        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"https://www.zohoapis.com/crm/v3/{module}",
                headers={"Authorization": f"Zoho-oauthtoken {access_token}"},
                params={"per_page": limit}
            ) as response:
                data = await response.json()
                return data.get("data", [])

    # ==================== CLOSE.COM ====================

    async def close_create_lead(self, name: str, contacts: List[Dict] = None) -> Dict:
        """Create Close.com lead"""
        import aiohttp

        api_key = os.environ.get("CLOSE_API_KEY")

        async with aiohttp.ClientSession() as session:
            async with session.post(
                "https://api.close.com/api/v1/lead/",
                auth=aiohttp.BasicAuth(api_key, ""),
                json={"name": name, "contacts": contacts or []}
            ) as response:
                return await response.json()

    async def close_get_leads(self, limit: int = 10) -> List[Dict]:
        """Get Close.com leads"""
        import aiohttp

        api_key = os.environ.get("CLOSE_API_KEY")

        async with aiohttp.ClientSession() as session:
            async with session.get(
                "https://api.close.com/api/v1/lead/",
                auth=aiohttp.BasicAuth(api_key, ""),
                params={"_limit": limit}
            ) as response:
                data = await response.json()
                return data.get("data", [])

    # ==================== FRESHSALES ====================

    async def freshsales_create_contact(self, email: str, first_name: str = None, last_name: str = None) -> Dict:
        """Create Freshsales contact"""
        import aiohttp

        api_key = os.environ.get("FRESHSALES_API_KEY")
        domain = os.environ.get("FRESHSALES_DOMAIN")

        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"https://{domain}.freshsales.io/api/contacts",
                headers={"Authorization": f"Token token={api_key}", "Content-Type": "application/json"},
                json={"contact": {"email": email, "first_name": first_name, "last_name": last_name}}
            ) as response:
                return await response.json()

    # ==================== ATTIO ====================

    async def attio_create_record(self, object_slug: str, data: Dict) -> Dict:
        """Create Attio record"""
        import aiohttp

        api_key = os.environ.get("ATTIO_API_KEY")

        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"https://api.attio.com/v2/objects/{object_slug}/records",
                headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
                json={"data": data}
            ) as response:
                return await response.json()

    # ==================== AI CRM ASSISTANT ====================

    async def ai_analyze_lead(self, lead_data: Dict) -> Dict:
        """AI-powered lead analysis"""
        from windows_ai.integrations.ai_providers import AIProvidersManager, Provider

        ai = AIProvidersManager()
        await ai.initialize()

        messages = [
            {"role": "system", "content": """Analyze the lead and provide:
1. Lead score (0-100)
2. Qualification status (hot/warm/cold)
3. Recommended next action
4. Key insights
Return JSON: {"score": N, "status": "...", "next_action": "...", "insights": [...]}"""},
            {"role": "user", "content": str(lead_data)}
        ]

        response = await ai.chat(Provider.OPENAI, messages)
        import json
        try:
            return json.loads(response["content"])
        except:
            return {"analysis": response["content"]}

    async def ai_draft_followup(self, contact: Dict, context: str) -> str:
        """AI-powered follow-up email draft"""
        from windows_ai.integrations.ai_providers import AIProvidersManager, Provider

        ai = AIProvidersManager()
        await ai.initialize()

        messages = [
            {"role": "system", "content": "Draft a professional follow-up email for this contact."},
            {"role": "user", "content": f"Contact: {contact}\nContext: {context}"}
        ]

        response = await ai.chat(Provider.OPENAI, messages)
        return response["content"]

    def list_providers(self) -> List[str]:
        return ["hubspot", "salesforce", "pipedrive", "zoho", "close", "freshsales",
                "attio", "copper", "insightly", "monday_crm", "airtable"]
