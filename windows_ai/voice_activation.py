"""
Voice Activation and Speech Processing System
Wake word detection, speech-to-text, and voice command processing
"""
import logging
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime
from dataclasses import dataclass, asdict
from pathlib import Path
import json
import threading
import queue

logger = logging.getLogger(__name__)


@dataclass
class VoiceCommand:
    """Processed voice command"""
    command_id: str
    text: str
    confidence: float
    intent: Optional[str]
    entities: Dict[str, Any]
    timestamp: str
    language: str = "en-US"


@dataclass
class WakeWordDetection:
    """Wake word detection event"""
    detected: bool
    confidence: float
    timestamp: str
    wake_word: str


class VoiceActivationSystem:
    """
    Voice Activation and Speech Processing System

    Features:
    - Wake word detection ("Hey Windows AI", "Computer", etc.)
    - Real-time speech-to-text
    - Voice command intent recognition
    - Multi-language support
    - Noise cancellation and audio preprocessing
    - Voice activity detection
    - Speaker recognition (optional)
    - Voice command history
    """

    def __init__(self, data_dir: Path):
        self.data_dir = data_dir
        self.data_dir.mkdir(parents=True, exist_ok=True)

        self.config_file = data_dir / "voice_config.json"
        self.history_file = data_dir / "voice_history.json"

        # Configuration
        self.wake_words = ["hey windows ai", "computer", "assistant"]
        self.language = "en-US"
        self.enabled = False
        self.use_local_model = True  # Use local STT vs cloud

        # State
        self.listening = False
        self.wake_word_detected = False

        # Command history
        self.command_history: List[VoiceCommand] = []

        # Command callbacks
        self.command_callbacks: List[Callable] = []

        # Audio processing
        self.audio_queue: queue.Queue = queue.Queue()

        # Threads
        self._listen_thread: Optional[threading.Thread] = None
        self._process_thread: Optional[threading.Thread] = None

        # STT/TTS engines (will be initialized on start)
        self.stt_engine = None
        self.tts_engine = None
        self.wake_word_detector = None

        # Load configuration
        self._load_config()

    def initialize_engines(self):
        """Initialize speech recognition engines"""
        try:
            # Try to use speech_recognition library
            import speech_recognition as sr
            self.stt_engine = sr.Recognizer()
            logger.info("Initialized speech recognition engine")

            # Try to initialize wake word detector (porcupine)
            try:
                import pvporcupine
                # Would need API key for production
                self.wake_word_detector = "porcupine"
                logger.info("Porcupine wake word detector available")
            except ImportError:
                logger.warning("Porcupine not available. Using simple audio detection.")
                self.wake_word_detector = "simple"

            # Try to initialize TTS
            try:
                import pyttsx3
                self.tts_engine = pyttsx3.init()
                self.tts_engine.setProperty('rate', 175)  # Speed
                self.tts_engine.setProperty('volume', 0.9)
                logger.info("Initialized text-to-speech engine")
            except Exception as e:
                logger.warning(f"TTS not available: {e}")

            return True

        except ImportError as e:
            logger.error(f"Speech recognition libraries not available: {e}")
            logger.info("Install with: pip install SpeechRecognition pyaudio pyttsx3")
            return False

    def start_listening(self):
        """Start voice activation listening"""
        if self.listening:
            logger.warning("Voice activation already listening")
            return

        # Initialize engines if not done
        if not self.stt_engine:
            if not self.initialize_engines():
                logger.error("Failed to initialize speech engines")
                return

        self.listening = True

        # Start listening thread
        self._listen_thread = threading.Thread(
            target=self._listen_loop,
            daemon=True
        )
        self._listen_thread.start()

        # Start processing thread
        self._process_thread = threading.Thread(
            target=self._process_loop,
            daemon=True
        )
        self._process_thread.start()

        logger.info("Started voice activation system")

    def stop_listening(self):
        """Stop voice activation"""
        self.listening = False

        if self._listen_thread:
            self._listen_thread.join(timeout=2)

        if self._process_thread:
            self._process_thread.join(timeout=2)

        logger.info("Stopped voice activation system")

    def _listen_loop(self):
        """Background loop for audio listening"""
        try:
            import speech_recognition as sr

            with sr.Microphone() as source:
                # Adjust for ambient noise
                logger.info("Adjusting for ambient noise...")
                self.stt_engine.adjust_for_ambient_noise(source, duration=1)
                logger.info("Listening for wake word...")

                while self.listening:
                    try:
                        # Listen for audio
                        audio = self.stt_engine.listen(source, timeout=1, phrase_time_limit=5)

                        # Add to queue for processing
                        self.audio_queue.put(audio)

                    except sr.WaitTimeoutError:
                        # No speech detected, continue
                        continue
                    except Exception as e:
                        logger.error(f"Error in listen loop: {e}")
                        continue

        except Exception as e:
            logger.error(f"Fatal error in listen loop: {e}")

    def _process_loop(self):
        """Background loop for audio processing"""
        import speech_recognition as sr

        while self.listening:
            try:
                # Get audio from queue (with timeout)
                try:
                    audio = self.audio_queue.get(timeout=0.5)
                except queue.Empty:
                    continue

                # Convert audio to text
                try:
                    if self.use_local_model:
                        # Use local model (Sphinx)
                        text = self.stt_engine.recognize_sphinx(audio)
                    else:
                        # Use Google Speech Recognition (requires internet)
                        text = self.stt_engine.recognize_google(audio, language=self.language)

                    text = text.lower().strip()
                    logger.debug(f"Recognized: {text}")

                    # Check for wake word
                    if not self.wake_word_detected:
                        if any(wake_word in text for wake_word in self.wake_words):
                            self.wake_word_detected = True
                            logger.info(f"Wake word detected: {text}")

                            # Speak confirmation
                            self.speak("Yes?")

                            continue

                    # If wake word was detected, process as command
                    if self.wake_word_detected:
                        self._process_command(text)

                        # Reset wake word detection
                        self.wake_word_detected = False

                except sr.UnknownValueError:
                    # Speech not recognized
                    logger.debug("Could not understand audio")
                except sr.RequestError as e:
                    logger.error(f"Speech recognition error: {e}")

            except Exception as e:
                logger.error(f"Error in process loop: {e}")

    def _process_command(self, text: str):
        """Process voice command"""
        import uuid

        # Parse intent and entities
        intent, entities = self._parse_intent(text)

        # Create command object
        command = VoiceCommand(
            command_id=str(uuid.uuid4()),
            text=text,
            confidence=0.8,  # Would come from STT
            intent=intent,
            entities=entities,
            timestamp=datetime.now().isoformat(),
            language=self.language
        )

        # Add to history
        self.command_history.append(command)

        logger.info(f"Voice command: {text} [intent: {intent}]")

        # Execute callbacks
        for callback in self.command_callbacks:
            try:
                callback(command)
            except Exception as e:
                logger.error(f"Error in command callback: {e}")

        # Execute built-in commands
        self._execute_builtin_command(command)

    def _parse_intent(self, text: str) -> tuple[Optional[str], Dict[str, Any]]:
        """Parse intent from command text"""
        text_lower = text.lower()

        # Simple intent classification (would use NLU model in production)
        if any(word in text_lower for word in ['open', 'launch', 'start']):
            # Extract application name
            for word in ['open', 'launch', 'start']:
                if word in text_lower:
                    app_name = text_lower.split(word, 1)[1].strip()
                    return 'open_application', {'app_name': app_name}

        elif any(word in text_lower for word in ['search', 'find', 'look for']):
            for word in ['search', 'find', 'look for']:
                if word in text_lower:
                    query = text_lower.split(word, 1)[1].strip()
                    return 'search', {'query': query}

        elif any(word in text_lower for word in ['close', 'quit', 'exit']):
            return 'close_application', {}

        elif any(word in text_lower for word in ['what', 'when', 'where', 'who', 'how']):
            return 'question', {'question': text}

        elif any(word in text_lower for word in ['remind', 'reminder']):
            return 'set_reminder', {'text': text}

        elif 'weather' in text_lower:
            return 'get_weather', {}

        elif 'time' in text_lower:
            return 'get_time', {}

        elif any(word in text_lower for word in ['stop', 'cancel']):
            return 'cancel', {}

        else:
            return 'unknown', {'text': text}

    def _execute_builtin_command(self, command: VoiceCommand):
        """Execute built-in voice commands"""
        intent = command.intent

        if intent == 'get_time':
            current_time = datetime.now().strftime("%I:%M %p")
            self.speak(f"The time is {current_time}")

        elif intent == 'get_weather':
            # Would integrate with weather API
            self.speak("I cannot check the weather right now.")

        elif intent == 'cancel':
            self.speak("Cancelling")
            self.wake_word_detected = False

        elif intent == 'unknown':
            self.speak("I didn't understand that command.")

    def speak(self, text: str):
        """Speak text using TTS"""
        try:
            if self.tts_engine:
                logger.info(f"Speaking: {text}")
                self.tts_engine.say(text)
                self.tts_engine.runAndWait()
            else:
                logger.info(f"Would speak: {text}")
        except Exception as e:
            logger.error(f"Error speaking: {e}")

    def register_command_callback(self, callback: Callable):
        """Register callback for voice commands"""
        self.command_callbacks.append(callback)
        logger.info("Registered voice command callback")

    def set_wake_words(self, wake_words: List[str]):
        """Set custom wake words"""
        self.wake_words = [w.lower() for w in wake_words]
        self._save_config()
        logger.info(f"Updated wake words: {self.wake_words}")

    def set_language(self, language: str):
        """Set recognition language"""
        self.language = language
        self._save_config()
        logger.info(f"Set language to: {language}")

    def get_command_history(self, limit: int = 50) -> List[Dict]:
        """Get recent voice commands"""
        return [asdict(cmd) for cmd in self.command_history[-limit:]]

    def get_status(self) -> Dict[str, Any]:
        """Get voice activation status"""
        return {
            'enabled': self.enabled,
            'listening': self.listening,
            'wake_word_detected': self.wake_word_detected,
            'wake_words': self.wake_words,
            'language': self.language,
            'engines': {
                'stt': 'initialized' if self.stt_engine else 'not initialized',
                'tts': 'initialized' if self.tts_engine else 'not initialized',
                'wake_word': self.wake_word_detector or 'not initialized'
            },
            'commands_processed': len(self.command_history)
        }

    def _save_config(self):
        """Save configuration"""
        try:
            config = {
                'wake_words': self.wake_words,
                'language': self.language,
                'enabled': self.enabled,
                'use_local_model': self.use_local_model
            }
            with open(self.config_file, 'w') as f:
                json.dump(config, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving config: {e}")

    def _load_config(self):
        """Load configuration"""
        try:
            if self.config_file.exists():
                with open(self.config_file, 'r') as f:
                    config = json.load(f)
                    self.wake_words = config.get('wake_words', self.wake_words)
                    self.language = config.get('language', self.language)
                    self.enabled = config.get('enabled', self.enabled)
                    self.use_local_model = config.get('use_local_model', self.use_local_model)
                logger.info("Loaded voice configuration")
        except Exception as e:
            logger.error(f"Error loading config: {e}")


# Global instance
_voice_system: Optional[VoiceActivationSystem] = None


def get_voice_system(data_dir: Path = None) -> VoiceActivationSystem:
    """Get or create global voice system"""
    global _voice_system

    if _voice_system is None:
        if data_dir is None:
            data_dir = Path.home() / ".windows-ai" / "voice"
        _voice_system = VoiceActivationSystem(data_dir)

    return _voice_system


def initialize_voice_system(data_dir: Path = None, start_listening: bool = False):
    """Initialize the voice activation system"""
    system = get_voice_system(data_dir)

    # Only start if explicitly requested (requires microphone)
    if start_listening:
        system.start_listening()

    logger.info("Voice activation system initialized")
    return system
