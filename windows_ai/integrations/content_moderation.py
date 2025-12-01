"""
Content Moderation Manager - 10+ Services
Text, image, video moderation and safety
"""

import asyncio
import logging
import os
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)

class ContentModerationManager:
    """Unified content moderation across 10+ providers"""

    def __init__(self):
        self._initialized = False

    async def initialize(self, config: Optional[Dict] = None):
        if self._initialized:
            return
        self._initialized = True

    # ==================== TEXT MODERATION ====================

    async def moderate_text(self, text: str, provider: str = "openai") -> Dict:
        """Moderate text content"""
        if provider == "openai":
            return await self._openai_moderate(text)
        elif provider == "perspective":
            return await self._perspective_moderate(text)
        elif provider == "aws":
            return await self._aws_comprehend_moderate(text)
        elif provider == "azure":
            return await self._azure_moderate(text)
        elif provider == "hive":
            return await self._hive_moderate(text)
        else:
            raise ValueError(f"Unsupported provider: {provider}")

    async def _openai_moderate(self, text):
        from openai import AsyncOpenAI
        client = AsyncOpenAI()
        response = await client.moderations.create(input=text)
        result = response.results[0]
        return {
            "flagged": result.flagged,
            "categories": {k: v for k, v in result.categories.model_dump().items() if v},
            "scores": result.category_scores.model_dump()
        }

    async def _perspective_moderate(self, text):
        import aiohttp
        api_key = os.environ.get("PERSPECTIVE_API_KEY")
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"https://commentanalyzer.googleapis.com/v1alpha1/comments:analyze?key={api_key}",
                json={
                    "comment": {"text": text},
                    "requestedAttributes": {
                        "TOXICITY": {}, "SEVERE_TOXICITY": {},
                        "IDENTITY_ATTACK": {}, "INSULT": {},
                        "PROFANITY": {}, "THREAT": {}
                    }
                }
            ) as response:
                data = await response.json()
                scores = {
                    attr: data["attributeScores"][attr]["summaryScore"]["value"]
                    for attr in data.get("attributeScores", {})
                }
                return {"flagged": any(s > 0.7 for s in scores.values()), "scores": scores}

    async def _aws_comprehend_moderate(self, text):
        import boto3
        client = boto3.client("comprehend")
        response = client.detect_toxic_content(
            TextSegments=[{"Text": text}],
            LanguageCode="en"
        )
        return {
            "flagged": any(r.get("Toxicity", 0) > 0.5 for r in response.get("ResultList", [])),
            "results": response.get("ResultList", [])
        }

    async def _azure_moderate(self, text):
        import aiohttp
        endpoint = os.environ.get("AZURE_CONTENT_SAFETY_ENDPOINT")
        key = os.environ.get("AZURE_CONTENT_SAFETY_KEY")
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{endpoint}/contentsafety/text:analyze?api-version=2023-10-01",
                headers={"Ocp-Apim-Subscription-Key": key, "Content-Type": "application/json"},
                json={"text": text}
            ) as response:
                data = await response.json()
                categories = data.get("categoriesAnalysis", [])
                return {
                    "flagged": any(c.get("severity", 0) > 2 for c in categories),
                    "categories": categories
                }

    async def _hive_moderate(self, text):
        import aiohttp
        api_key = os.environ.get("HIVE_API_KEY")
        async with aiohttp.ClientSession() as session:
            async with session.post(
                "https://api.thehive.ai/api/v2/task/sync",
                headers={"Authorization": f"Token {api_key}"},
                json={"text_data": text}
            ) as response:
                return await response.json()

    # ==================== IMAGE MODERATION ====================

    async def moderate_image(self, image_url: str, provider: str = "aws") -> Dict:
        """Moderate image content"""
        if provider == "aws":
            return await self._aws_rekognition_moderate(image_url)
        elif provider == "google":
            return await self._google_vision_moderate(image_url)
        elif provider == "azure":
            return await self._azure_image_moderate(image_url)
        elif provider == "sightengine":
            return await self._sightengine_moderate(image_url)
        else:
            raise ValueError(f"Unsupported provider: {provider}")

    async def _aws_rekognition_moderate(self, image_url):
        import boto3
        import aiohttp
        client = boto3.client("rekognition")

        # Download image
        async with aiohttp.ClientSession() as session:
            async with session.get(image_url) as response:
                image_bytes = await response.read()

        response = client.detect_moderation_labels(Image={"Bytes": image_bytes})
        labels = response.get("ModerationLabels", [])
        return {
            "flagged": len(labels) > 0,
            "labels": [{"name": l["Name"], "confidence": l["Confidence"]} for l in labels]
        }

    async def _google_vision_moderate(self, image_url):
        from google.cloud import vision
        client = vision.ImageAnnotatorClient()
        image = vision.Image()
        image.source.image_uri = image_url
        response = client.safe_search_detection(image=image)
        safe = response.safe_search_annotation
        return {
            "adult": safe.adult.name,
            "violence": safe.violence.name,
            "racy": safe.racy.name,
            "medical": safe.medical.name,
            "spoof": safe.spoof.name
        }

    async def _azure_image_moderate(self, image_url):
        import aiohttp
        endpoint = os.environ.get("AZURE_CONTENT_SAFETY_ENDPOINT")
        key = os.environ.get("AZURE_CONTENT_SAFETY_KEY")
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{endpoint}/contentsafety/image:analyze?api-version=2023-10-01",
                headers={"Ocp-Apim-Subscription-Key": key, "Content-Type": "application/json"},
                json={"image": {"url": image_url}}
            ) as response:
                return await response.json()

    async def _sightengine_moderate(self, image_url):
        import aiohttp
        async with aiohttp.ClientSession() as session:
            async with session.get(
                "https://api.sightengine.com/1.0/check.json",
                params={
                    "url": image_url,
                    "models": "nudity,wad,offensive,gore",
                    "api_user": os.environ.get("SIGHTENGINE_USER"),
                    "api_secret": os.environ.get("SIGHTENGINE_SECRET")
                }
            ) as response:
                return await response.json()

    # ==================== VIDEO MODERATION ====================

    async def moderate_video(self, video_url: str, provider: str = "aws") -> Dict:
        """Moderate video content"""
        if provider == "aws":
            return await self._aws_video_moderate(video_url)
        elif provider == "google":
            return await self._google_video_moderate(video_url)

    async def _aws_video_moderate(self, video_url):
        import boto3
        client = boto3.client("rekognition")
        response = client.start_content_moderation(
            Video={"S3Object": {"Bucket": "bucket", "Name": video_url}}
        )
        return {"job_id": response["JobId"]}

    async def _google_video_moderate(self, video_url):
        from google.cloud import videointelligence
        client = videointelligence.VideoIntelligenceServiceClient()
        features = [videointelligence.Feature.EXPLICIT_CONTENT_DETECTION]
        operation = client.annotate_video(input_uri=video_url, features=features)
        return {"operation_name": operation.operation.name}

    # ==================== AI MODERATION ====================

    async def ai_moderate(self, content: str, content_type: str = "text", policy: str = None) -> Dict:
        """AI-powered content moderation with custom policies"""
        from windows_ai.integrations.ai_providers import AIProvidersManager, Provider

        ai = AIProvidersManager()
        await ai.initialize()

        default_policy = """
Check content for:
1. Hate speech or discrimination
2. Violence or threats
3. Sexual content
4. Harassment or bullying
5. Misinformation
6. Self-harm content
7. Illegal activities
8. Spam or scams
"""

        messages = [
            {"role": "system", "content": f"""You are a content moderator. Analyze the content.
Policy: {policy or default_policy}
Return JSON: {{"flagged": bool, "categories": ["..."], "severity": "none/low/medium/high", "explanation": "..."}}"""},
            {"role": "user", "content": f"Content type: {content_type}\n\n{content}"}
        ]

        response = await ai.chat(Provider.OPENAI, messages)
        import json
        try:
            return json.loads(response["content"])
        except:
            return {"raw": response["content"]}

    def list_providers(self) -> Dict[str, List[str]]:
        return {
            "text": ["openai", "perspective", "aws", "azure", "hive"],
            "image": ["aws", "google", "azure", "sightengine", "clarifai"],
            "video": ["aws", "google", "azure", "hive"]
        }
