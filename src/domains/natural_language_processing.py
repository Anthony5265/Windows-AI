"""
Natural Language Processing Module - Production Grade
NER, sentiment analysis, text classification, summarization, and Q&A
"""
from typing import Dict, Any, List, Optional, Tuple
import logging
import os
import re

logger = logging.getLogger(__name__)

# Optional dependencies
try:
    import spacy
    SPACY_AVAILABLE = True
except ImportError:
    SPACY_AVAILABLE = False

try:
    from transformers import pipeline, AutoTokenizer, AutoModelForSequenceClassification
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False


class NLPProcessor:
    """Production NLP capabilities"""

    def __init__(self):
        self.spacy_model = None
        self.pipelines = {}

    def _load_spacy_model(self, model: str = "en_core_web_sm"):
        """Load spaCy model"""
        if not SPACY_AVAILABLE:
            return False

        try:
            if self.spacy_model is None or self.spacy_model.meta.get("name") != model:
                self.spacy_model = spacy.load(model)
            return True
        except Exception as e:
            logger.error(f"Failed to load spaCy model {model}: {e}")
            return False

    async def extract_entities(self, text: str, provider: str = "spacy",
                               model: str = "en_core_web_sm") -> Dict[str, Any]:
        """
        Extract named entities from text

        Args:
            text: Input text
            provider: NER provider (spacy, huggingface, azure)
            model: Model to use

        Returns:
            Dict with entities and their types
        """
        if provider == "spacy":
            return await self._spacy_ner(text, model)
        elif provider == "huggingface":
            return await self._huggingface_ner(text, model)
        elif provider == "azure":
            return await self._azure_ner(text)
        else:
            return {"status": "error", "message": f"Unknown provider: {provider}"}

    async def _spacy_ner(self, text: str, model: str = "en_core_web_sm") -> Dict[str, Any]:
        """Named Entity Recognition using spaCy"""
        if not SPACY_AVAILABLE:
            return {"status": "error", "message": "spaCy not installed. Install with: pip install spacy"}

        try:
            if not self._load_spacy_model(model):
                return {"status": "error", "message": f"Failed to load model: {model}"}

            doc = self.spacy_model(text)
            entities = [
                {
                    "text": ent.text,
                    "label": ent.label_,
                    "start": ent.start_char,
                    "end": ent.end_char
                }
                for ent in doc.ents
            ]

            return {
                "status": "success",
                "entities": entities,
                "entity_count": len(entities)
            }
        except Exception as e:
            logger.error(f"spaCy NER error: {e}")
            return {"status": "error", "message": str(e)}

    async def _huggingface_ner(self, text: str, model: str = "dslim/bert-base-NER") -> Dict[str, Any]:
        """NER using Hugging Face Transformers"""
        if not TRANSFORMERS_AVAILABLE:
            return {"status": "error", "message": "transformers not installed"}

        try:
            if "ner" not in self.pipelines:
                self.pipelines["ner"] = pipeline("ner", model=model, aggregation_strategy="simple")

            results = self.pipelines["ner"](text)
            entities = [
                {
                    "text": r["word"],
                    "label": r["entity_group"],
                    "score": float(r["score"]),
                    "start": r["start"],
                    "end": r["end"]
                }
                for r in results
            ]

            return {
                "status": "success",
                "entities": entities,
                "entity_count": len(entities)
            }
        except Exception as e:
            logger.error(f"Hugging Face NER error: {e}")
            return {"status": "error", "message": str(e)}

    async def _azure_ner(self, text: str) -> Dict[str, Any]:
        """NER using Azure Text Analytics"""
        try:
            from azure.ai.textanalytics import TextAnalyticsClient
            from azure.core.credentials import AzureKeyCredential

            key = os.getenv("AZURE_TEXT_ANALYTICS_KEY", "")
            endpoint = os.getenv("AZURE_TEXT_ANALYTICS_ENDPOINT", "")

            if not key or not endpoint:
                return {"status": "error", "message": "Azure credentials not configured"}

            client = TextAnalyticsClient(endpoint=endpoint, credential=AzureKeyCredential(key))
            result = client.recognize_entities(documents=[text])[0]

            if result.is_error:
                return {"status": "error", "message": result.error.message}

            entities = [
                {
                    "text": entity.text,
                    "label": entity.category,
                    "subcategory": entity.subcategory,
                    "confidence": entity.confidence_score,
                    "offset": entity.offset
                }
                for entity in result.entities
            ]

            return {
                "status": "success",
                "entities": entities,
                "entity_count": len(entities)
            }
        except ImportError:
            return {"status": "error", "message": "Azure Text Analytics SDK not installed"}
        except Exception as e:
            logger.error(f"Azure NER error: {e}")
            return {"status": "error", "message": str(e)}

    async def analyze_sentiment(self, text: str, provider: str = "transformers") -> Dict[str, Any]:
        """
        Analyze sentiment of text

        Args:
            text: Input text
            provider: Sentiment provider (transformers, azure, spacy)

        Returns:
            Dict with sentiment label and scores
        """
        if provider == "transformers":
            return await self._transformers_sentiment(text)
        elif provider == "azure":
            return await self._azure_sentiment(text)
        elif provider == "spacy":
            return await self._spacy_sentiment(text)
        else:
            return {"status": "error", "message": f"Unknown provider: {provider}"}

    async def _transformers_sentiment(self, text: str,
                                      model: str = "distilbert-base-uncased-finetuned-sst-2-english") -> Dict[str, Any]:
        """Sentiment analysis using Transformers"""
        if not TRANSFORMERS_AVAILABLE:
            return {"status": "error", "message": "transformers not installed"}

        try:
            if "sentiment" not in self.pipelines:
                self.pipelines["sentiment"] = pipeline("sentiment-analysis", model=model)

            result = self.pipelines["sentiment"](text)[0]

            return {
                "status": "success",
                "label": result["label"],
                "score": float(result["score"]),
                "text": text
            }
        except Exception as e:
            logger.error(f"Transformers sentiment error: {e}")
            return {"status": "error", "message": str(e)}

    async def _azure_sentiment(self, text: str) -> Dict[str, Any]:
        """Sentiment analysis using Azure Text Analytics"""
        try:
            from azure.ai.textanalytics import TextAnalyticsClient
            from azure.core.credentials import AzureKeyCredential

            key = os.getenv("AZURE_TEXT_ANALYTICS_KEY", "")
            endpoint = os.getenv("AZURE_TEXT_ANALYTICS_ENDPOINT", "")

            if not key or not endpoint:
                return {"status": "error", "message": "Azure credentials not configured"}

            client = TextAnalyticsClient(endpoint=endpoint, credential=AzureKeyCredential(key))
            result = client.analyze_sentiment(documents=[text])[0]

            if result.is_error:
                return {"status": "error", "message": result.error.message}

            return {
                "status": "success",
                "label": result.sentiment,
                "confidence_scores": {
                    "positive": result.confidence_scores.positive,
                    "neutral": result.confidence_scores.neutral,
                    "negative": result.confidence_scores.negative
                },
                "sentences": [
                    {
                        "text": s.text,
                        "sentiment": s.sentiment,
                        "scores": {
                            "positive": s.confidence_scores.positive,
                            "neutral": s.confidence_scores.neutral,
                            "negative": s.confidence_scores.negative
                        }
                    }
                    for s in result.sentences
                ]
            }
        except ImportError:
            return {"status": "error", "message": "Azure Text Analytics SDK not installed"}
        except Exception as e:
            logger.error(f"Azure sentiment error: {e}")
            return {"status": "error", "message": str(e)}

    async def _spacy_sentiment(self, text: str) -> Dict[str, Any]:
        """Basic sentiment using spaCy with spacytextblob"""
        try:
            if not SPACY_AVAILABLE:
                return {"status": "error", "message": "spaCy not installed"}

            from spacytextblob.spacytextblob import SpacyTextBlob

            if not self._load_spacy_model():
                return {"status": "error", "message": "Failed to load spaCy model"}

            if "spacytextblob" not in self.spacy_model.pipe_names:
                self.spacy_model.add_pipe("spacytextblob")

            doc = self.spacy_model(text)
            polarity = doc._.blob.polarity
            subjectivity = doc._.blob.subjectivity

            if polarity > 0.1:
                label = "positive"
            elif polarity < -0.1:
                label = "negative"
            else:
                label = "neutral"

            return {
                "status": "success",
                "label": label,
                "polarity": polarity,
                "subjectivity": subjectivity
            }
        except ImportError:
            return {"status": "error", "message": "spacytextblob not installed"}
        except Exception as e:
            logger.error(f"spaCy sentiment error: {e}")
            return {"status": "error", "message": str(e)}

    async def classify_text(self, text: str, labels: List[str] = None,
                           provider: str = "transformers", model: str = None) -> Dict[str, Any]:
        """
        Classify text into categories

        Args:
            text: Input text
            labels: Possible labels (for zero-shot classification)
            provider: Classification provider
            model: Model to use

        Returns:
            Dict with classification results
        """
        if provider == "transformers" and labels:
            return await self._zero_shot_classification(text, labels, model)
        elif provider == "transformers":
            return await self._transformers_classification(text, model)
        else:
            return {"status": "error", "message": f"Unknown provider: {provider}"}

    async def _zero_shot_classification(self, text: str, labels: List[str],
                                       model: str = None) -> Dict[str, Any]:
        """Zero-shot classification using Transformers"""
        if not TRANSFORMERS_AVAILABLE:
            return {"status": "error", "message": "transformers not installed"}

        try:
            if "zero-shot" not in self.pipelines:
                model_name = model or "facebook/bart-large-mnli"
                self.pipelines["zero-shot"] = pipeline("zero-shot-classification", model=model_name)

            result = self.pipelines["zero-shot"](text, candidate_labels=labels)

            return {
                "status": "success",
                "labels": result["labels"],
                "scores": [float(s) for s in result["scores"]],
                "top_label": result["labels"][0],
                "top_score": float(result["scores"][0])
            }
        except Exception as e:
            logger.error(f"Zero-shot classification error: {e}")
            return {"status": "error", "message": str(e)}

    async def _transformers_classification(self, text: str, model: str = None) -> Dict[str, Any]:
        """Text classification using Transformers"""
        if not TRANSFORMERS_AVAILABLE:
            return {"status": "error", "message": "transformers not installed"}

        try:
            model_name = model or "distilbert-base-uncased"
            if "classification" not in self.pipelines:
                self.pipelines["classification"] = pipeline("text-classification", model=model_name)

            result = self.pipelines["classification"](text)[0]

            return {
                "status": "success",
                "label": result["label"],
                "score": float(result["score"])
            }
        except Exception as e:
            logger.error(f"Classification error: {e}")
            return {"status": "error", "message": str(e)}

    async def summarize(self, text: str, max_length: int = 130,
                       min_length: int = 30, provider: str = "transformers") -> Dict[str, Any]:
        """
        Summarize text

        Args:
            text: Input text
            max_length: Maximum summary length
            min_length: Minimum summary length
            provider: Summarization provider

        Returns:
            Dict with summary
        """
        if provider == "transformers":
            return await self._transformers_summarization(text, max_length, min_length)
        else:
            return {"status": "error", "message": f"Unknown provider: {provider}"}

    async def _transformers_summarization(self, text: str, max_length: int = 130,
                                         min_length: int = 30) -> Dict[str, Any]:
        """Summarization using Transformers"""
        if not TRANSFORMERS_AVAILABLE:
            return {"status": "error", "message": "transformers not installed"}

        try:
            if "summarization" not in self.pipelines:
                self.pipelines["summarization"] = pipeline("summarization", model="facebook/bart-large-cnn")

            result = self.pipelines["summarization"](
                text,
                max_length=max_length,
                min_length=min_length,
                do_sample=False
            )[0]

            return {
                "status": "success",
                "summary": result["summary_text"],
                "original_length": len(text),
                "summary_length": len(result["summary_text"])
            }
        except Exception as e:
            logger.error(f"Summarization error: {e}")
            return {"status": "error", "message": str(e)}

    async def answer_question(self, question: str, context: str,
                             provider: str = "transformers") -> Dict[str, Any]:
        """
        Answer question based on context

        Args:
            question: Question to answer
            context: Context containing the answer
            provider: QA provider

        Returns:
            Dict with answer and confidence
        """
        if provider == "transformers":
            return await self._transformers_qa(question, context)
        else:
            return {"status": "error", "message": f"Unknown provider: {provider}"}

    async def _transformers_qa(self, question: str, context: str) -> Dict[str, Any]:
        """Question answering using Transformers"""
        if not TRANSFORMERS_AVAILABLE:
            return {"status": "error", "message": "transformers not installed"}

        try:
            if "qa" not in self.pipelines:
                self.pipelines["qa"] = pipeline("question-answering", model="distilbert-base-cased-distilled-squad")

            result = self.pipelines["qa"](question=question, context=context)

            return {
                "status": "success",
                "answer": result["answer"],
                "score": float(result["score"]),
                "start": result["start"],
                "end": result["end"]
            }
        except Exception as e:
            logger.error(f"QA error: {e}")
            return {"status": "error", "message": str(e)}

    async def detect_language(self, text: str, provider: str = "spacy") -> Dict[str, Any]:
        """
        Detect language of text

        Args:
            text: Input text
            provider: Language detection provider

        Returns:
            Dict with detected language
        """
        if provider == "spacy":
            return await self._spacy_language_detection(text)
        else:
            return {"status": "error", "message": f"Unknown provider: {provider}"}

    async def _spacy_language_detection(self, text: str) -> Dict[str, Any]:
        """Language detection using spaCy"""
        try:
            from spacy_langdetect import LanguageDetector

            if not SPACY_AVAILABLE:
                return {"status": "error", "message": "spaCy not installed"}

            if not self._load_spacy_model():
                return {"status": "error", "message": "Failed to load spaCy model"}

            if "language_detector" not in self.spacy_model.pipe_names:
                self.spacy_model.add_pipe("language_detector")

            doc = self.spacy_model(text)
            language = doc._.language

            return {
                "status": "success",
                "language": language["language"],
                "score": language["score"]
            }
        except ImportError:
            return {"status": "error", "message": "spacy-langdetect not installed"}
        except Exception as e:
            logger.error(f"Language detection error: {e}")
            return {"status": "error", "message": str(e)}

    async def extract_keywords(self, text: str, top_n: int = 10) -> Dict[str, Any]:
        """
        Extract keywords from text

        Args:
            text: Input text
            top_n: Number of keywords to extract

        Returns:
            Dict with keywords
        """
        if not SPACY_AVAILABLE:
            return {"status": "error", "message": "spaCy not installed"}

        try:
            if not self._load_spacy_model():
                return {"status": "error", "message": "Failed to load spaCy model"}

            doc = self.spacy_model(text)

            # Extract keywords based on POS tags and frequency
            keywords = {}
            for token in doc:
                if token.pos_ in ["NOUN", "PROPN", "ADJ"] and not token.is_stop:
                    lemma = token.lemma_.lower()
                    keywords[lemma] = keywords.get(lemma, 0) + 1

            # Sort by frequency
            sorted_keywords = sorted(keywords.items(), key=lambda x: x[1], reverse=True)[:top_n]

            return {
                "status": "success",
                "keywords": [
                    {"word": word, "frequency": freq}
                    for word, freq in sorted_keywords
                ]
            }
        except Exception as e:
            logger.error(f"Keyword extraction error: {e}")
            return {"status": "error", "message": str(e)}

    async def dependency_parse(self, text: str) -> Dict[str, Any]:
        """
        Parse dependency structure of text

        Args:
            text: Input text

        Returns:
            Dict with dependency parse tree
        """
        if not SPACY_AVAILABLE:
            return {"status": "error", "message": "spaCy not installed"}

        try:
            if not self._load_spacy_model():
                return {"status": "error", "message": "Failed to load spaCy model"}

            doc = self.spacy_model(text)
            dependencies = [
                {
                    "text": token.text,
                    "lemma": token.lemma_,
                    "pos": token.pos_,
                    "dep": token.dep_,
                    "head": token.head.text,
                    "children": [child.text for child in token.children]
                }
                for token in doc
            ]

            return {
                "status": "success",
                "dependencies": dependencies,
                "sentence": text
            }
        except Exception as e:
            logger.error(f"Dependency parsing error: {e}")
            return {"status": "error", "message": str(e)}


# Legacy compatibility functions
def input_processor(raw_text: str) -> List[str]:
    """Legacy text input processor"""
    normalized = raw_text.strip().lower()
    tokens = re.findall(r"\b\w+\b", normalized)
    return tokens


def task_planner(processed_text: List[str]) -> Dict[str, Any]:
    """Legacy task planner"""
    if not processed_text:
        return {"plan": []}

    mode = "local" if len(processed_text) <= 5 else "remote"
    plan = {"plan": [{"type": mode, "tokens": processed_text}]}
    return plan


def executor(plan: Dict[str, Any]) -> Dict[str, Any]:
    """Legacy executor"""
    results: List[str] = []
    for task in plan.get("plan", []):
        tokens = task.get("tokens", [])
        if task.get("type") == "local":
            results.append("LOCAL:" + " ".join(tokens))
        else:
            results.append("REMOTE:" + " ".join(tokens))
    return {"results": results}


def result_aggregator(results: Dict[str, Any]) -> Dict[str, Any]:
    """Legacy result aggregator"""
    return results
