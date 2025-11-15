"""
Azure Speech - SPEECH-TO-TEXT
"""

class AzureSpeech:
    def __init__(self, api_key=None):
        self.api_key = api_key
        self.name = "Azure Speech"
        self.model_type = "speech-to-text"
    
    def transcribe(self, audio_path: str) -> str:
        return f"Transcription from {self.name}"
    
    def synthesize(self, text: str) -> bytes:
        return b"audio_data"
    
    def detect_language(self, audio_path: str) -> str:
        return "en"
