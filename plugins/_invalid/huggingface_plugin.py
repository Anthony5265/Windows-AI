"""
Hugging Face Inference API Plugin
Supports 100,000+ models from Hugging Face Hub
"""

from typing import Dict, Any, Optional, List
import os


class HuggingFacePlugin:
    """Plugin for Hugging Face Inference API"""
    
    name = "huggingface"
    version = "1.0.0"
    description = "Integration with Hugging Face Inference API"
    author = "Windows AI Team"
    
    def __init__(self):
        self.api_key: Optional[str] = None
        self.client = None
        self._initialized = False
        
    def initialize(self, config: Optional[Dict[str, Any]] = None) -> bool:
        """Initialize the Hugging Face plugin"""
        try:
            from huggingface_hub import InferenceClient
            
            # Get API key from config or environment
            self.api_key = (
                config.get("api_key") if config 
                else os.getenv("HUGGINGFACE_API_KEY") or os.getenv("HF_TOKEN")
            )
            
            if not self.api_key:
                return False
            
            self.client = InferenceClient(token=self.api_key)
            self._initialized = True
            return True
            
        except ImportError:
            print("huggingface_hub package not installed. Install with: pip install huggingface_hub")
            return False
        except Exception as e:
            print(f"Error initializing Hugging Face plugin: {e}")
            return False
    
    def execute(self, action: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a Hugging Face action"""
        if not self._initialized:
            return {"error": "Plugin not initialized. Please provide API key."}
        
        try:
            if action == "text_generation":
                return self._text_generation(params)
            elif action == "chat":
                return self._chat(params)
            elif action == "text_to_image":
                return self._text_to_image(params)
            elif action == "image_to_text":
                return self._image_to_text(params)
            elif action == "embedding":
                return self._embedding(params)
            elif action == "translation":
                return self._translation(params)
            elif action == "summarization":
                return self._summarization(params)
            elif action == "question_answering":
                return self._question_answering(params)
            elif action == "text_classification":
                return self._text_classification(params)
            elif action == "zero_shot_classification":
                return self._zero_shot_classification(params)
            else:
                return {"error": f"Unknown action: {action}"}
                
        except Exception as e:
            return {"error": str(e)}
    
    def _text_generation(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Generate text"""
        prompt = params.get("prompt", "")
        model = params.get("model", "meta-llama/Llama-2-7b-chat-hf")
        max_tokens = params.get("max_tokens", 500)
        temperature = params.get("temperature", 0.7)
        
        result = self.client.text_generation(
            prompt=prompt,
            model=model,
            max_new_tokens=max_tokens,
            temperature=temperature
        )
        
        return {
            "text": result,
            "model": model
        }
    
    def _chat(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Chat completion"""
        messages = params.get("messages", [])
        model = params.get("model", "meta-llama/Llama-2-70b-chat-hf")
        max_tokens = params.get("max_tokens", 500)
        temperature = params.get("temperature", 0.7)
        
        response = self.client.chat_completion(
            messages=messages,
            model=model,
            max_tokens=max_tokens,
            temperature=temperature
        )
        
        return {
            "response": response.choices[0].message.content,
            "model": model,
            "usage": {
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens,
                "total_tokens": response.usage.total_tokens
            }
        }
    
    def _text_to_image(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Generate image from text"""
        prompt = params.get("prompt", "")
        model = params.get("model", "stabilityai/stable-diffusion-xl-base-1.0")
        
        image = self.client.text_to_image(prompt=prompt, model=model)
        
        # Save image to bytes
        import io
        img_byte_arr = io.BytesIO()
        image.save(img_byte_arr, format='PNG')
        img_byte_arr.seek(0)
        
        return {
            "image_data": img_byte_arr.getvalue(),
            "model": model,
            "format": "PNG"
        }
    
    def _image_to_text(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Generate text from image"""
        image_path = params.get("image_path")
        model = params.get("model", "Salesforce/blip-image-captioning-large")
        
        if not image_path:
            return {"error": "image_path required"}
        
        result = self.client.image_to_text(image=image_path, model=model)
        
        return {
            "text": result,
            "model": model
        }
    
    def _embedding(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Generate embeddings"""
        text = params.get("text", "")
        model = params.get("model", "sentence-transformers/all-MiniLM-L6-v2")
        
        embedding = self.client.feature_extraction(text=text, model=model)
        
        return {
            "embedding": embedding,
            "model": model,
            "dimensions": len(embedding) if isinstance(embedding, list) else None
        }
    
    def _translation(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Translate text"""
        text = params.get("text", "")
        model = params.get("model", "facebook/mbart-large-50-many-to-many-mmt")
        
        result = self.client.translation(text=text, model=model)
        
        return {
            "translated_text": result.translation_text,
            "model": model
        }
    
    def _summarization(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Summarize text"""
        text = params.get("text", "")
        model = params.get("model", "facebook/bart-large-cnn")
        
        result = self.client.summarization(text=text, model=model)
        
        return {
            "summary": result.summary_text,
            "model": model
        }
    
    def _question_answering(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Answer questions"""
        question = params.get("question", "")
        context = params.get("context", "")
        model = params.get("model", "deepset/roberta-base-squad2")
        
        result = self.client.question_answering(
            question=question,
            context=context,
            model=model
        )
        
        return {
            "answer": result.answer,
            "score": result.score,
            "model": model
        }
    
    def _text_classification(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Classify text"""
        text = params.get("text", "")
        model = params.get("model", "distilbert-base-uncased-finetuned-sst-2-english")
        
        result = self.client.text_classification(text=text, model=model)
        
        return {
            "label": result[0].label,
            "score": result[0].score,
            "all_results": [{"label": r.label, "score": r.score} for r in result],
            "model": model
        }
    
    def _zero_shot_classification(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Zero-shot classification"""
        text = params.get("text", "")
        labels = params.get("labels", [])
        model = params.get("model", "facebook/bart-large-mnli")
        
        result = self.client.zero_shot_classification(
            text=text,
            labels=labels,
            model=model
        )
        
        return {
            "labels": result.labels,
            "scores": result.scores,
            "model": model
        }
    
    def cleanup(self):
        """Cleanup resources"""
        self.client = None
        self._initialized = False


# Plugin metadata
PLUGIN_CLASS = HuggingFacePlugin
PLUGIN_NAME = "huggingface"
PLUGIN_VERSION = "1.0.0"
PLUGIN_DESCRIPTION = "Integration with Hugging Face Inference API"
PLUGIN_ACTIONS = [
    "text_generation", "chat", "text_to_image", "image_to_text",
    "embedding", "translation", "summarization", "question_answering",
    "text_classification", "zero_shot_classification"
]
