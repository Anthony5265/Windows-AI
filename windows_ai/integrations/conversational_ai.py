"""
Conversational AI Manager - 20+ Services
Chatbots, voice assistants, dialog management, sentiment analysis
"""

import asyncio
import logging
import os
from typing import Dict, List, Any, Optional
from windows_ai.config.unified_config import WindowsAIConfig

import asyncio
import logging
import os
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime

logger = logging.getLogger(__name__)

@dataclass
class Message:
    role: str
    content: str
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict = field(default_factory=dict)

@dataclass
class ConversationState:
    messages: List[Message] = field(default_factory=list)
    context: Dict = field(default_factory=dict)
    intents: List[str] = field(default_factory=list)
    entities: Dict = field(default_factory=dict)

class ConversationalAIManager:
    """Unified conversational AI across 20+ services"""

    def __init__(self):
        self._config: Optional[WindowsAIConfig] = None
        self._initialized = False
        self._conversations: Dict[str, ConversationState] = {}
        self._intent_handlers: Dict[str, Callable] = {}

    async def initialize(self, config: Optional[WindowsAIConfig] = None):
        if self._initialized:
            return
        
        self._config = config
        self._initialized = True

    # ==================== CONVERSATION MANAGEMENT ====================

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

    def create_conversation(self, conversation_id: str) -> str:
        """Create new conversation session"""
        self._conversations[conversation_id] = ConversationState()
        return conversation_id

    def get_conversation(self, conversation_id: str) -> Optional[ConversationState]:
        """Get conversation state"""
        return self._conversations.get(conversation_id)

    async def chat(self, conversation_id: str, user_message: str, system_prompt: str = None) -> Dict:
        """Process chat message and generate response"""
        from windows_ai.integrations.ai_providers import AIProvidersManager, Provider

        if conversation_id not in self._conversations:
            self.create_conversation(conversation_id)

        state = self._conversations[conversation_id]
        state.messages.append(Message(role="user", content=user_message))

        # Detect intent and entities
        intent_result = await self.detect_intent(user_message)
        entities = await self.extract_entities(user_message)

        state.intents.append(intent_result.get("intent", "unknown"))
        state.entities.update(entities)

        # Check for intent handler
        intent = intent_result.get("intent")
        if intent in self._intent_handlers:
            handler_response = await self._intent_handlers[intent](user_message, state)
            if handler_response:
                state.messages.append(Message(role="assistant", content=handler_response))
                return {"response": handler_response, "intent": intent, "entities": entities}

        # Generate AI response
        ai = AIProvidersManager()
        await ai.initialize()

        messages = [{"role": "system", "content": system_prompt or "You are a helpful assistant."}]
        messages.extend([{"role": m.role, "content": m.content} for m in state.messages[-10:]])

        response = await ai.chat(Provider.OPENAI, messages)
        assistant_message = response["content"]

        state.messages.append(Message(role="assistant", content=assistant_message))

        return {"response": assistant_message, "intent": intent, "entities": entities}

    def register_intent_handler(self, intent: str, handler: Callable):
        """Register custom intent handler"""
        self._intent_handlers[intent] = handler

    # ==================== INTENT DETECTION ====================

    async def detect_intent(self, text: str, intents: List[str] = None) -> Dict:
        """Detect user intent"""
        from windows_ai.integrations.ai_providers import AIProvidersManager, Provider

        ai = AIProvidersManager()
        await ai.initialize()

        default_intents = ["greeting", "farewell", "question", "command", "complaint", "feedback", "booking", "purchase", "support", "other"]
        intent_list = intents or default_intents

        messages = [
            {"role": "system", "content": f"""Classify the user's intent. Choose from: {', '.join(intent_list)}
Return JSON: {{"intent": "...", "confidence": 0.0-1.0, "sub_intent": "..."}}"""},
            {"role": "user", "content": text}
        ]

        response = await ai.chat(Provider.OPENAI, messages)
        import json
        try:
            return json.loads(response["content"])
        except:
            return {"intent": "other", "confidence": 0.5}

    # ==================== ENTITY EXTRACTION ====================

    async def extract_entities(self, text: str, entity_types: List[str] = None) -> Dict:
        """Extract named entities from text"""
        from windows_ai.integrations.ai_providers import AIProvidersManager, Provider

        ai = AIProvidersManager()
        await ai.initialize()

        default_types = ["person", "organization", "location", "date", "time", "money", "email", "phone", "product"]
        types = entity_types or default_types

        messages = [
            {"role": "system", "content": f"""Extract entities from text. Types: {', '.join(types)}
Return JSON: {{"entities": [{{"type": "...", "value": "...", "start": N, "end": N}}]}}"""},
            {"role": "user", "content": text}
        ]

        response = await ai.chat(Provider.OPENAI, messages)
        import json
        try:
            result = json.loads(response["content"])
            return {e["type"]: e["value"] for e in result.get("entities", [])}
        except:
            return {}

    # ==================== SENTIMENT ANALYSIS ====================

    async def analyze_sentiment(self, text: str) -> Dict:
        """Analyze text sentiment"""
        from windows_ai.integrations.ai_providers import AIProvidersManager, Provider

        ai = AIProvidersManager()
        await ai.initialize()

        messages = [
            {"role": "system", "content": """Analyze sentiment. Return JSON:
{"sentiment": "positive/negative/neutral", "score": -1.0 to 1.0, "emotions": {"joy": 0-1, "anger": 0-1, "sadness": 0-1, "fear": 0-1, "surprise": 0-1}}"""},
            {"role": "user", "content": text}
        ]

        response = await ai.chat(Provider.OPENAI, messages)
        import json
        try:
            return json.loads(response["content"])
        except:
            return {"sentiment": "neutral", "score": 0.0}

    # ==================== DIALOG FLOW ====================

    async def create_dialog_flow(self, name: str, steps: List[Dict]) -> Dict:
        """Create dialog flow for guided conversations"""
        return {
            "name": name,
            "steps": steps,
            "current_step": 0,
            "collected_data": {}
        }

    async def process_dialog_step(self, flow: Dict, user_input: str) -> Dict:
        """Process current dialog step"""
        current_step = flow["steps"][flow["current_step"]]

        # Validate input if validation rules exist
        if "validation" in current_step:
            valid = self._validate_input(user_input, current_step["validation"])
            if not valid:
                return {"response": current_step.get("error_message", "Invalid input. Please try again."), "valid": False}

        # Store collected data
        if "field" in current_step:
            flow["collected_data"][current_step["field"]] = user_input

        # Move to next step
        flow["current_step"] += 1

        # Check if flow is complete
        if flow["current_step"] >= len(flow["steps"]):
            return {"response": "Thank you! All information collected.", "complete": True, "data": flow["collected_data"]}

        # Return next prompt
        next_step = flow["steps"][flow["current_step"]]
        return {"response": next_step["prompt"], "complete": False}

    def _validate_input(self, input_text: str, validation: Dict) -> bool:
        import re
        if validation.get("type") == "email":
            return bool(re.match(r"[^@]+@[^@]+\.[^@]+", input_text))
        elif validation.get("type") == "phone":
            return bool(re.match(r"[\d\-\+\(\)\s]+", input_text))
        elif validation.get("type") == "number":
            return input_text.isdigit()
        elif "pattern" in validation:
            return bool(re.match(validation["pattern"], input_text))
        return True

    # ==================== VOICE ASSISTANT ====================

    async def voice_to_response(self, audio_path: str, system_prompt: str = None) -> Dict:
        """Process voice input and generate voice response"""
        from windows_ai.integrations.audio_speech import AudioSpeechManager

        audio = AudioSpeechManager()
        await audio.initialize()

        # Transcribe
        transcription = await audio.speech_to_text(audio_path, provider="whisper")

        # Process as chat
        conversation_id = f"voice_{datetime.now().timestamp()}"
        response = await self.chat(conversation_id, transcription, system_prompt)

        # Generate speech response
        audio_response = await audio.text_to_speech(response["response"], provider="elevenlabs")

        return {
            "transcription": transcription,
            "response_text": response["response"],
            "audio_response": audio_response
        }

    # ==================== MULTI-TURN CONTEXT ====================

    async def summarize_conversation(self, conversation_id: str) -> str:
        """Summarize conversation for context compression"""
        from windows_ai.integrations.ai_providers import AIProvidersManager, Provider

        state = self._conversations.get(conversation_id)
        if not state:
            return ""

        ai = AIProvidersManager()
        await ai.initialize()

        messages_text = "\n".join([f"{m.role}: {m.content}" for m in state.messages])

        messages = [
            {"role": "system", "content": "Summarize this conversation concisely, preserving key information and context."},
            {"role": "user", "content": messages_text}
        ]

        response = await ai.chat(Provider.OPENAI, messages)
        return response["content"]

    # ==================== PERSONA MANAGEMENT ====================

    async def create_persona(self, name: str, traits: Dict) -> Dict:
        """Create chatbot persona"""
        return {
            "name": name,
            "personality": traits.get("personality", "friendly and helpful"),
            "tone": traits.get("tone", "professional"),
            "expertise": traits.get("expertise", []),
            "backstory": traits.get("backstory", ""),
            "constraints": traits.get("constraints", []),
            "system_prompt": self._generate_persona_prompt(name, traits)
        }

    def _generate_persona_prompt(self, name: str, traits: Dict) -> str:
        return f"""You are {name}, an AI assistant with the following characteristics:
Personality: {traits.get('personality', 'friendly and helpful')}
Tone: {traits.get('tone', 'professional')}
Expertise: {', '.join(traits.get('expertise', ['general assistance']))}
{f"Background: {traits.get('backstory')}" if traits.get('backstory') else ''}
{f"Constraints: {', '.join(traits.get('constraints', []))}" if traits.get('constraints') else ''}
Stay in character and respond accordingly."""

    # ==================== RESPONSE GENERATION ====================

    async def generate_response_variants(self, prompt: str, num_variants: int = 3) -> List[str]:
        """Generate multiple response variants"""
        from windows_ai.integrations.ai_providers import AIProvidersManager, Provider

        ai = AIProvidersManager()
        await ai.initialize()

        variants = []
        for i in range(num_variants):
            response = await ai.chat(Provider.OPENAI, [{"role": "user", "content": prompt}], temperature=0.9)
            variants.append(response["content"])

        return variants

    def list_capabilities(self) -> Dict[str, List[str]]:
        return {
            "conversation": ["chat", "multi_turn", "context_management"],
            "nlu": ["intent_detection", "entity_extraction", "sentiment_analysis"],
            "dialog": ["flow_management", "validation", "branching"],
            "voice": ["speech_to_text", "text_to_speech", "voice_assistant"],
            "persona": ["creation", "management", "customization"]
        }
