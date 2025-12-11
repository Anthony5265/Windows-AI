"""
Document Processing Manager - 20+ Services
OCR, PDF extraction, document understanding
"""

import asyncio
import logging
import os
from typing import Dict, List, Any, Optional
from windows_ai.config.unified_config import WindowsAIConfig

import asyncio
import base64
import logging
import os
from typing import Dict, List, Any, Optional
from pathlib import Path
from enum import Enum

logger = logging.getLogger(__name__)

class OCRProvider(Enum):
    GOOGLE = "google"
    AZURE = "azure"
    AWS = "aws"
    MISTRAL = "mistral"
    TESSERACT = "tesseract"
    PADDLEOCR = "paddleocr"
    EASYOCR = "easyocr"

class DocumentProcessingManager:
    """Manages document processing across 20+ providers"""

    def __init__(self):
        self._config: Optional[WindowsAIConfig] = None
        self._initialized = False
        self.output_dir = Path.home() / ".windowsai" / "documents"

    async def initialize(self, config: Optional[WindowsAIConfig] = None):
        """Initialize document processing"""
        if self._initialized:
            return
        
        self._config = config
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self._initialized = True
        logger.info("Document Processing Manager initialized")

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

    async def ocr(
        self,
        provider: OCRProvider,
        image_path: str,
        language: str = "en",
        **kwargs
    ) -> Dict[str, Any]:
        """Perform OCR on an image"""

        if provider == OCRProvider.TESSERACT:
            return await self._tesseract_ocr(image_path, language)
        elif provider == OCRProvider.EASYOCR:
            return await self._easyocr_ocr(image_path, language)
        elif provider == OCRProvider.PADDLEOCR:
            return await self._paddleocr_ocr(image_path, language)
        elif provider == OCRProvider.GOOGLE:
            return await self._google_ocr(image_path)
        elif provider == OCRProvider.AZURE:
            return await self._azure_ocr(image_path)
        elif provider == OCRProvider.AWS:
            return await self._aws_ocr(image_path)
        elif provider == OCRProvider.MISTRAL:
            return await self._mistral_ocr(image_path, **kwargs)
        else:
            raise ValueError(f"Unsupported OCR provider: {provider}")

    async def _tesseract_ocr(self, image_path, language):
        """Tesseract OCR"""
        import pytesseract
        from PIL import Image

        image = Image.open(image_path)
        text = pytesseract.image_to_string(image, lang=language)
        data = pytesseract.image_to_data(image, lang=language, output_type=pytesseract.Output.DICT)

        return {
            "text": text,
            "provider": "tesseract",
            "words": data
        }

    async def _easyocr_ocr(self, image_path, language):
        """EasyOCR"""
        import easyocr

        reader = easyocr.Reader([language])
        result = reader.readtext(image_path)

        text = " ".join([item[1] for item in result])
        words = [{"text": item[1], "confidence": item[2], "bbox": item[0]} for item in result]

        return {
            "text": text,
            "provider": "easyocr",
            "words": words
        }

    async def _paddleocr_ocr(self, image_path, language):
        """PaddleOCR"""
        from paddleocr import PaddleOCR

        ocr = PaddleOCR(use_angle_cls=True, lang=language)
        result = ocr.ocr(image_path, cls=True)

        text_parts = []
        words = []
        for line in result[0]:
            text_parts.append(line[1][0])
            words.append({
                "text": line[1][0],
                "confidence": line[1][1],
                "bbox": line[0]
            })

        return {
            "text": " ".join(text_parts),
            "provider": "paddleocr",
            "words": words
        }

    async def _google_ocr(self, image_path):
        """Google Cloud Vision OCR"""
        from google.cloud import vision

        client = vision.ImageAnnotatorClient()

        with open(image_path, "rb") as f:
            content = f.read()

        image = vision.Image(content=content)
        response = await asyncio.get_event_loop().run_in_executor(
            None, lambda: client.text_detection(image=image)
        )

        texts = response.text_annotations
        if texts:
            return {
                "text": texts[0].description,
                "provider": "google",
                "words": [{"text": t.description, "bbox": [(v.x, v.y) for v in t.bounding_poly.vertices]} for t in texts[1:]]
            }

        return {"text": "", "provider": "google", "words": []}

    async def _azure_ocr(self, image_path):
        """Azure Computer Vision OCR"""
        import aiohttp

        api_key = os.environ.get("AZURE_VISION_KEY")
        endpoint = os.environ.get("AZURE_VISION_ENDPOINT")

        with open(image_path, "rb") as f:
            image_data = f.read()

        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{endpoint}/vision/v3.2/ocr",
                headers={
                    "Ocp-Apim-Subscription-Key": api_key,
                    "Content-Type": "application/octet-stream"
                },
                data=image_data
            ) as response:
                data = await response.json()

                text_parts = []
                words = []
                for region in data.get("regions", []):
                    for line in region.get("lines", []):
                        line_text = " ".join([w["text"] for w in line.get("words", [])])
                        text_parts.append(line_text)
                        words.extend(line.get("words", []))

                return {
                    "text": "\n".join(text_parts),
                    "provider": "azure",
                    "words": words
                }

    async def _aws_ocr(self, image_path):
        """AWS Textract OCR"""
        import boto3

        client = boto3.client("textract")

        with open(image_path, "rb") as f:
            image_bytes = f.read()

        response = client.detect_document_text(
            Document={"Bytes": image_bytes}
        )

        text_parts = []
        words = []
        for block in response.get("Blocks", []):
            if block["BlockType"] == "LINE":
                text_parts.append(block["Text"])
            elif block["BlockType"] == "WORD":
                words.append({
                    "text": block["Text"],
                    "confidence": block["Confidence"],
                    "bbox": block.get("Geometry", {}).get("BoundingBox")
                })

        return {
            "text": "\n".join(text_parts),
            "provider": "aws",
            "words": words
        }

    async def _mistral_ocr(self, image_path, **kwargs):
        """Mistral OCR API"""
        import aiohttp

        api_key = os.environ.get("MISTRAL_API_KEY")

        with open(image_path, "rb") as f:
            image_data = base64.b64encode(f.read()).decode()

        async with aiohttp.ClientSession() as session:
            async with session.post(
                "https://api.mistral.ai/v1/ocr",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "mistral-ocr-latest",
                    "document": {
                        "type": "image_url",
                        "image_url": f"data:image/jpeg;base64,{image_data}"
                    }
                }
            ) as response:
                data = await response.json()

                return {
                    "text": data.get("text", ""),
                    "provider": "mistral",
                    "pages": data.get("pages", [])
                }

    # ==================== PDF PROCESSING ====================

    async def extract_pdf_text(self, pdf_path: str) -> Dict[str, Any]:
        """Extract text from PDF"""
        import pypdf

        reader = pypdf.PdfReader(pdf_path)
        pages = []

        for i, page in enumerate(reader.pages):
            text = page.extract_text()
            pages.append({
                "page": i + 1,
                "text": text
            })

        return {
            "total_pages": len(pages),
            "pages": pages,
            "full_text": "\n\n".join([p["text"] for p in pages])
        }

    async def extract_pdf_tables(self, pdf_path: str) -> List[List[List[str]]]:
        """Extract tables from PDF"""
        import tabula

        tables = tabula.read_pdf(pdf_path, pages="all")
        return [table.values.tolist() for table in tables]

    async def extract_pdf_images(self, pdf_path: str, output_dir: str = None) -> List[str]:
        """Extract images from PDF"""
        import fitz  # PyMuPDF

        output_dir = output_dir or str(self.output_dir / "pdf_images")
        Path(output_dir).mkdir(parents=True, exist_ok=True)

        doc = fitz.open(pdf_path)
        image_paths = []

        for page_num in range(len(doc)):
            page = doc[page_num]
            images = page.get_images()

            for img_idx, img in enumerate(images):
                xref = img[0]
                base_image = doc.extract_image(xref)
                image_bytes = base_image["image"]

                image_path = os.path.join(output_dir, f"page{page_num + 1}_img{img_idx + 1}.{base_image['ext']}")
                with open(image_path, "wb") as f:
                    f.write(image_bytes)

                image_paths.append(image_path)

        return image_paths

    async def pdf_to_markdown(self, pdf_path: str) -> str:
        """Convert PDF to Markdown"""
        try:
            from marker.converters.pdf import PdfConverter
            from marker.models import create_model_dict

            converter = PdfConverter(artifact_dict=create_model_dict())
            rendered = converter(pdf_path)
            return rendered.markdown

        except ImportError:
            # Fallback to basic extraction
            result = await self.extract_pdf_text(pdf_path)
            return result["full_text"]

    async def merge_pdfs(self, pdf_paths: List[str], output_path: str) -> str:
        """Merge multiple PDFs"""
        import pypdf

        merger = pypdf.PdfMerger()

        for pdf_path in pdf_paths:
            merger.append(pdf_path)

        merger.write(output_path)
        merger.close()

        return output_path

    async def split_pdf(self, pdf_path: str, output_dir: str = None) -> List[str]:
        """Split PDF into individual pages"""
        import pypdf

        output_dir = output_dir or str(self.output_dir / "split_pdfs")
        Path(output_dir).mkdir(parents=True, exist_ok=True)

        reader = pypdf.PdfReader(pdf_path)
        output_paths = []

        for i, page in enumerate(reader.pages):
            writer = pypdf.PdfWriter()
            writer.add_page(page)

            output_path = os.path.join(output_dir, f"page_{i + 1}.pdf")
            with open(output_path, "wb") as f:
                writer.write(f)

            output_paths.append(output_path)

        return output_paths

    # ==================== DOCUMENT UNDERSTANDING ====================

    async def analyze_document(
        self,
        file_path: str,
        llm_provider: str = "openai"
    ) -> Dict[str, Any]:
        """Analyze document with AI"""
        from windows_ai.integrations.ai_providers import AIProvidersManager, Provider

        # Extract text based on file type
        ext = Path(file_path).suffix.lower()

        if ext == ".pdf":
            result = await self.extract_pdf_text(file_path)
            text = result["full_text"]
        elif ext in [".png", ".jpg", ".jpeg", ".webp"]:
            result = await self.ocr(OCRProvider.TESSERACT, file_path)
            text = result["text"]
        else:
            with open(file_path, "r", encoding="utf-8") as f:
                text = f.read()

        # Analyze with AI
        ai = AIProvidersManager()
        await ai.initialize()

        messages = [
            {"role": "system", "content": "You are a document analysis assistant. Analyze the document and provide: 1) Summary 2) Key points 3) Named entities 4) Document type classification"},
            {"role": "user", "content": f"Analyze this document:\n\n{text[:10000]}"}
        ]

        provider = Provider(llm_provider)
        response = await ai.chat(provider, messages)

        return {
            "analysis": response["content"],
            "text_length": len(text),
            "file_type": ext
        }

    async def extract_structured_data(
        self,
        file_path: str,
        schema: Dict[str, Any],
        llm_provider: str = "openai"
    ) -> Dict[str, Any]:
        """Extract structured data from document based on schema"""
        from windows_ai.integrations.ai_providers import AIProvidersManager, Provider
        import json

        # Extract text
        ext = Path(file_path).suffix.lower()
        if ext == ".pdf":
            result = await self.extract_pdf_text(file_path)
            text = result["full_text"]
        else:
            result = await self.ocr(OCRProvider.TESSERACT, file_path)
            text = result["text"]

        # Extract with AI
        ai = AIProvidersManager()
        await ai.initialize()

        messages = [
            {"role": "system", "content": f"Extract structured data from the document according to this schema: {json.dumps(schema)}. Return valid JSON."},
            {"role": "user", "content": f"Document:\n\n{text[:8000]}"}
        ]

        provider = Provider(llm_provider)
        response = await ai.chat(provider, messages)

        try:
            return json.loads(response["content"])
        except json.JSONDecodeError:
            return {"raw_response": response["content"]}

    def list_ocr_providers(self) -> List[str]:
        """List available OCR providers"""
        return [p.value for p in OCRProvider]
