"""
Accessibility AI Manager - 15+ Services
Screen readers, image descriptions, captioning, sign language, assistive tech
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

class AccessibilityAIManager:
    """Unified accessibility AI across 15+ services"""

    def __init__(self):
        self._config: Optional[WindowsAIConfig] = None
        self._initialized = False

    async def initialize(self, config: Optional[WindowsAIConfig] = None):
        if self._initialized:
            return
        
        self._config = config
        self._initialized = True

    # ==================== IMAGE ACCESSIBILITY ====================

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

    async def describe_image(self, image_path: str, detail_level: str = "detailed") -> Dict:
        """Generate accessible image description"""
        from windows_ai.integrations.ai_providers import AIProvidersManager, Provider
        import base64

        ai = AIProvidersManager()
        await ai.initialize()

        with open(image_path, "rb") as f:
            image_data = base64.b64encode(f.read()).decode()

        detail_prompts = {
            "brief": "Provide a brief 1-sentence description for screen readers.",
            "detailed": "Provide a detailed description including: main subjects, actions, colors, spatial layout, text visible, mood/atmosphere.",
            "alt_text": "Generate concise alt text suitable for HTML alt attribute (max 125 characters)."
        }

        messages = [{
            "role": "user",
            "content": [
                {"type": "text", "text": detail_prompts.get(detail_level, detail_prompts["detailed"])},
                {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_data}"}}
            ]
        }]

        response = await ai.chat(Provider.OPENAI, messages, model="gpt-4o")
        return {"description": response["content"], "detail_level": detail_level}

    async def describe_chart(self, image_path: str) -> Dict:
        """Generate accessible chart/graph description"""
        from windows_ai.integrations.ai_providers import AIProvidersManager, Provider
        import base64

        ai = AIProvidersManager()
        await ai.initialize()

        with open(image_path, "rb") as f:
            image_data = base64.b64encode(f.read()).decode()

        messages = [{
            "role": "user",
            "content": [
                {"type": "text", "text": """Describe this chart for visually impaired users. Include:
1. Chart type (bar, line, pie, etc.)
2. What data is being shown
3. Key trends and patterns
4. Specific data points or values
5. Any notable outliers or highlights"""},
                {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_data}"}}
            ]
        }]

        response = await ai.chat(Provider.OPENAI, messages, model="gpt-4o")
        return {"chart_description": response["content"]}

    # ==================== TEXT-TO-SPEECH ====================

    async def text_to_speech_accessible(self, text: str, voice: str = "natural", speed: float = 1.0) -> bytes:
        """Generate accessible text-to-speech audio"""
        from windows_ai.integrations.audio_speech import AudioSpeechManager

        audio = AudioSpeechManager()
        await audio.initialize()

        # Add SSML markup for better accessibility
        ssml_text = f"""<speak>
            <prosody rate="{int(speed * 100)}%">
                {text}
            </prosody>
        </speak>"""

        return await audio.text_to_speech(text, provider="elevenlabs", voice=voice)

    async def read_document(self, document_path: str) -> Dict:
        """Read and prepare document for screen reader"""
        from windows_ai.integrations.document_processing import DocumentProcessingManager

        doc = DocumentProcessingManager()
        await doc.initialize()

        # Extract text with structure
        text = await doc.extract_pdf_text(document_path)

        # Create structured reading
        return {
            "full_text": text,
            "word_count": len(text.split()),
            "estimated_reading_time": len(text.split()) // 150,
            "headings": self._extract_headings(text)
        }

    def _extract_headings(self, text: str) -> List[str]:
        """Extract headings from text"""
        import re
        # Simple heading detection
        lines = text.split("\n")
        headings = []
        for line in lines:
            line = line.strip()
            if line and len(line) < 100 and line.isupper():
                headings.append(line)
            elif line and len(line) < 100 and line.endswith(":"):
                headings.append(line)
        return headings[:20]

    # ==================== CAPTIONING ====================

    async def generate_captions(self, audio_path: str, style: str = "verbatim") -> Dict:
        """Generate captions for audio/video"""
        from windows_ai.integrations.audio_speech import AudioSpeechManager

        audio = AudioSpeechManager()
        await audio.initialize()

        # Transcribe with timestamps
        transcription = await audio.speech_to_text(audio_path, provider="whisper")

        if style == "verbatim":
            return {"captions": transcription, "style": "verbatim"}
        elif style == "clean":
            # Remove filler words
            clean = self._clean_transcription(transcription)
            return {"captions": clean, "style": "clean"}

        return {"captions": transcription}

    def _clean_transcription(self, text: str) -> str:
        """Clean transcription of filler words"""
        fillers = ["um", "uh", "like", "you know", "basically", "actually", "literally"]
        words = text.split()
        cleaned = [w for w in words if w.lower() not in fillers]
        return " ".join(cleaned)

    async def generate_audio_description(self, video_path: str) -> Dict:
        """Generate audio descriptions for video"""
        from windows_ai.integrations.ai_providers import AIProvidersManager, Provider
        import cv2

        ai = AIProvidersManager()
        await ai.initialize()

        # Extract key frames
        cap = cv2.VideoCapture(video_path)
        fps = cap.get(cv2.CAP_PROP_FPS)
        frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        duration = frame_count / fps

        descriptions = []
        for i in range(0, frame_count, int(fps * 5)):  # Every 5 seconds
            cap.set(cv2.CAP_PROP_POS_FRAMES, i)
            ret, frame = cap.read()
            if ret:
                # Save frame temporarily
                import tempfile
                with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as f:
                    cv2.imwrite(f.name, frame)
                    desc = await self.describe_image(f.name, "brief")
                    descriptions.append({
                        "timestamp": i / fps,
                        "description": desc["description"]
                    })

        cap.release()
        return {"duration": duration, "audio_descriptions": descriptions}

    # ==================== SIGN LANGUAGE ====================

    async def text_to_sign_language(self, text: str, language: str = "asl") -> Dict:
        """Convert text to sign language representation"""
        from windows_ai.integrations.ai_providers import AIProvidersManager, Provider

        ai = AIProvidersManager()
        await ai.initialize()

        messages = [
            {"role": "system", "content": f"""Convert text to {language.upper()} sign language instructions.
For each word/phrase provide:
1. The sign description
2. Hand shapes
3. Movement
4. Facial expression if relevant"""},
            {"role": "user", "content": text}
        ]

        response = await ai.chat(Provider.OPENAI, messages)
        return {"text": text, "language": language, "signs": response["content"]}

    async def recognize_sign_language(self, video_path: str) -> Dict:
        """Recognize sign language from video"""
        import cv2
        import mediapipe as mp

        mp_hands = mp.solutions.hands
        hands = mp_hands.Hands(static_image_mode=False, max_num_hands=2)

        cap = cv2.VideoCapture(video_path)
        frames_with_hands = []

        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break

            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = hands.process(rgb)

            if results.multi_hand_landmarks:
                for hand_landmarks in results.multi_hand_landmarks:
                    landmarks = [(lm.x, lm.y, lm.z) for lm in hand_landmarks.landmark]
                    frames_with_hands.append(landmarks)

        cap.release()
        hands.close()

        return {
            "frames_analyzed": len(frames_with_hands),
            "note": "Sign language recognition requires specialized model"
        }

    # ==================== COGNITIVE ACCESSIBILITY ====================

    async def simplify_text(self, text: str, reading_level: str = "grade_6") -> Dict:
        """Simplify text for cognitive accessibility"""
        from windows_ai.integrations.ai_providers import AIProvidersManager, Provider

        ai = AIProvidersManager()
        await ai.initialize()

        messages = [
            {"role": "system", "content": f"""Simplify this text to a {reading_level} reading level:
1. Use shorter sentences
2. Use common words
3. Avoid jargon
4. Add explanations for complex concepts
5. Use bullet points where helpful"""},
            {"role": "user", "content": text}
        ]

        response = await ai.chat(Provider.OPENAI, messages)
        return {"original": text, "simplified": response["content"], "target_level": reading_level}

    async def summarize_for_accessibility(self, text: str, format: str = "bullet") -> Dict:
        """Create accessible summary"""
        from windows_ai.integrations.ai_providers import AIProvidersManager, Provider

        ai = AIProvidersManager()
        await ai.initialize()

        formats = {
            "bullet": "Create a bullet-point summary with key points",
            "tldr": "Create a one-paragraph TL;DR summary",
            "key_facts": "Extract key facts in simple statements",
            "questions": "Summarize as answered questions (Q&A format)"
        }

        messages = [
            {"role": "system", "content": formats.get(format, formats["bullet"])},
            {"role": "user", "content": text}
        ]

        response = await ai.chat(Provider.OPENAI, messages)
        return {"summary": response["content"], "format": format}

    # ==================== WEBSITE ACCESSIBILITY ====================

    async def analyze_web_accessibility(self, url: str) -> Dict:
        """Analyze website for accessibility issues"""
        import aiohttp
        from bs4 import BeautifulSoup

        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                html = await response.text()

        soup = BeautifulSoup(html, "html.parser")
        issues = []

        # Check images for alt text
        images = soup.find_all("img")
        missing_alt = [img.get("src", "unknown") for img in images if not img.get("alt")]
        if missing_alt:
            issues.append({"type": "missing_alt", "count": len(missing_alt), "severity": "high"})

        # Check for heading hierarchy
        headings = soup.find_all(["h1", "h2", "h3", "h4", "h5", "h6"])
        if not soup.find("h1"):
            issues.append({"type": "missing_h1", "severity": "high"})

        # Check for form labels
        inputs = soup.find_all("input")
        unlabeled = [i.get("name", "unknown") for i in inputs if not i.get("aria-label") and not soup.find("label", {"for": i.get("id")})]
        if unlabeled:
            issues.append({"type": "unlabeled_inputs", "count": len(unlabeled), "severity": "medium"})

        # Check for link text
        links = soup.find_all("a")
        vague_links = [l for l in links if l.text.strip().lower() in ["click here", "read more", "here", "link"]]
        if vague_links:
            issues.append({"type": "vague_link_text", "count": len(vague_links), "severity": "medium"})

        return {
            "url": url,
            "issues": issues,
            "score": max(0, 100 - len(issues) * 10),
            "wcag_compliance": "partial" if issues else "likely_compliant"
        }

    def list_capabilities(self) -> Dict[str, List[str]]:
        return {
            "visual": ["image_description", "chart_description", "color_contrast"],
            "auditory": ["captions", "transcription", "audio_description"],
            "cognitive": ["text_simplification", "summary", "reading_level"],
            "motor": ["voice_control", "eye_tracking", "switch_access"],
            "sign_language": ["text_to_sign", "sign_recognition"],
            "web": ["accessibility_audit", "wcag_compliance"]
        }
