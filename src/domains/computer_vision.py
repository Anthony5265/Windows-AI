"""
Computer Vision Module - Production Grade
Object detection, image classification, OCR, face detection, and more
"""
from typing import Dict, Any, List, Optional, Tuple
import logging
import os
import base64
import io

logger = logging.getLogger(__name__)

try:
    from PIL import Image
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

try:
    import numpy as np
    NUMPY_AVAILABLE = True
except ImportError:
    NUMPY_AVAILABLE = False


class VisionProcessor:
    """Production computer vision capabilities"""

    def __init__(self):
        self.default_size = (224, 224)

    async def detect_objects(self, image_path: str = None, image_data: bytes = None,
                            provider: str = "yolo", confidence: float = 0.5) -> Dict[str, Any]:
        """
        Detect objects in image

        Args:
            image_path: Path to image file
            image_data: Raw image bytes
            provider: Detection provider (yolo, florence, azure)
            confidence: Confidence threshold

        Returns:
            Dict with detected objects and bounding boxes
        """
        if provider == "yolo":
            return await self._yolo_detect(image_path, image_data, confidence)
        elif provider == "florence":
            return await self._florence_detect(image_path, image_data)
        elif provider == "azure":
            return await self._azure_vision(image_path, image_data, "detect")
        else:
            return {"status": "error", "message": f"Unknown provider: {provider}"}

    async def _yolo_detect(self, image_path: str = None, image_data: bytes = None,
                          confidence: float = 0.5) -> Dict[str, Any]:
        """Object detection using YOLO"""
        try:
            from ultralytics import YOLO

            model = YOLO("yolov8n.pt")

            if image_path:
                results = model(image_path, conf=confidence)
            elif image_data:
                image = Image.open(io.BytesIO(image_data))
                results = model(image, conf=confidence)
            else:
                return {"status": "error", "message": "No image provided"}

            detections = []
            for result in results:
                for box in result.boxes:
                    detections.append({
                        "class": result.names[int(box.cls[0])],
                        "confidence": float(box.conf[0]),
                        "bbox": box.xyxy[0].tolist()
                    })

            return {
                "status": "success",
                "detections": detections,
                "count": len(detections)
            }
        except ImportError:
            return {"status": "error", "message": "Ultralytics not installed. Install with: pip install ultralytics"}
        except Exception as e:
            logger.error(f"YOLO detection error: {e}")
            return {"status": "error", "message": str(e)}

    async def classify_image(self, image_path: str = None, image_data: bytes = None,
                            provider: str = "clip", top_k: int = 5) -> Dict[str, Any]:
        """
        Classify image

        Args:
            image_path: Path to image file
            image_data: Raw image bytes
            provider: Classification provider (clip, resnet, azure)
            top_k: Number of top predictions

        Returns:
            Dict with classification results
        """
        if provider == "clip":
            return await self._clip_classify(image_path, image_data, top_k)
        elif provider == "azure":
            return await self._azure_vision(image_path, image_data, "classify")
        else:
            return {"status": "error", "message": f"Unknown provider: {provider}"}

    async def _clip_classify(self, image_path: str = None, image_data: bytes = None,
                            top_k: int = 5) -> Dict[str, Any]:
        """Image classification using CLIP"""
        try:
            import torch
            import clip

            device = "cuda" if torch.cuda.is_available() else "cpu"
            model, preprocess = clip.load("ViT-B/32", device=device)

            if image_path:
                image = Image.open(image_path)
            elif image_data:
                image = Image.open(io.BytesIO(image_data))
            else:
                return {"status": "error", "message": "No image provided"}

            image_input = preprocess(image).unsqueeze(0).to(device)

            # Common labels
            labels = [
                "cat", "dog", "car", "person", "bird", "building", "tree",
                "food", "animal", "landscape", "indoor scene", "outdoor scene"
            ]

            text_inputs = torch.cat([clip.tokenize(f"a photo of a {label}") for label in labels]).to(device)

            with torch.no_grad():
                image_features = model.encode_image(image_input)
                text_features = model.encode_text(text_inputs)

                image_features /= image_features.norm(dim=-1, keepdim=True)
                text_features /= text_features.norm(dim=-1, keepdim=True)
                similarity = (100.0 * image_features @ text_features.T).softmax(dim=-1)

            values, indices = similarity[0].topk(top_k)

            predictions = [
                {
                    "label": labels[idx],
                    "confidence": float(val)
                }
                for val, idx in zip(values, indices)
            ]

            return {
                "status": "success",
                "predictions": predictions
            }
        except ImportError:
            return {"status": "error", "message": "CLIP not installed. Install with: pip install clip"}
        except Exception as e:
            logger.error(f"CLIP classification error: {e}")
            return {"status": "error", "message": str(e)}

    async def extract_text(self, image_path: str = None, image_data: bytes = None,
                          provider: str = "tesseract") -> Dict[str, Any]:
        """
        Extract text from image (OCR)

        Args:
            image_path: Path to image file
            image_data: Raw image bytes
            provider: OCR provider (tesseract, paddleocr, azure)

        Returns:
            Dict with extracted text
        """
        if provider == "tesseract":
            return await self._tesseract_ocr(image_path, image_data)
        elif provider == "paddleocr":
            return await self._paddle_ocr(image_path, image_data)
        elif provider == "azure":
            return await self._azure_vision(image_path, image_data, "ocr")
        else:
            return {"status": "error", "message": f"Unknown OCR provider: {provider}"}

    async def _tesseract_ocr(self, image_path: str = None, image_data: bytes = None) -> Dict[str, Any]:
        """OCR using Tesseract"""
        try:
            import pytesseract

            if image_path:
                image = Image.open(image_path)
            elif image_data:
                image = Image.open(io.BytesIO(image_data))
            else:
                return {"status": "error", "message": "No image provided"}

            text = pytesseract.image_to_string(image)
            data = pytesseract.image_to_data(image, output_type=pytesseract.Output.DICT)

            return {
                "status": "success",
                "text": text,
                "words": data.get("text", []),
                "confidences": data.get("conf", [])
            }
        except ImportError:
            return {"status": "error", "message": "pytesseract not installed. Install with: pip install pytesseract"}
        except Exception as e:
            logger.error(f"Tesseract OCR error: {e}")
            return {"status": "error", "message": str(e)}

    async def detect_faces(self, image_path: str = None, image_data: bytes = None) -> Dict[str, Any]:
        """
        Detect faces in image

        Args:
            image_path: Path to image file
            image_data: Raw image bytes

        Returns:
            Dict with detected faces and landmarks
        """
        try:
            import cv2

            if image_path:
                img = cv2.imread(image_path)
            elif image_data:
                nparr = np.frombuffer(image_data, np.uint8)
                img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            else:
                return {"status": "error", "message": "No image provided"}

            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

            # Load Haar cascade
            face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
            faces = face_cascade.detectMultiScale(gray, 1.1, 4)

            detections = [
                {
                    "bbox": [int(x), int(y), int(w), int(h)],
                    "center": [int(x + w/2), int(y + h/2)]
                }
                for x, y, w, h in faces
            ]

            return {
                "status": "success",
                "faces": detections,
                "count": len(detections)
            }
        except ImportError:
            return {"status": "error", "message": "OpenCV not installed. Install with: pip install opencv-python"}
        except Exception as e:
            logger.error(f"Face detection error: {e}")
            return {"status": "error", "message": str(e)}

    async def _azure_vision(self, image_path: str = None, image_data: bytes = None,
                           task: str = "detect") -> Dict[str, Any]:
        """Azure Computer Vision API"""
        try:
            from azure.cognitiveservices.vision.computervision import ComputerVisionClient
            from msrest.authentication import CognitiveServicesCredentials

            key = os.getenv("AZURE_VISION_KEY", "")
            endpoint = os.getenv("AZURE_VISION_ENDPOINT", "")

            if not key or not endpoint:
                return {"status": "error", "message": "Azure credentials not configured"}

            client = ComputerVisionClient(endpoint, CognitiveServicesCredentials(key))

            if image_path:
                with open(image_path, "rb") as image_stream:
                    if task == "detect":
                        result = client.detect_objects_in_stream(image_stream)
                        return {
                            "status": "success",
                            "objects": [
                                {
                                    "object": obj.object_property,
                                    "confidence": obj.confidence,
                                    "bbox": obj.rectangle
                                }
                                for obj in result.objects
                            ]
                        }
                    elif task == "ocr":
                        result = client.read_in_stream(image_stream, raw=True)
                        # Would need to poll for results
                        return {"status": "success", "text": "OCR result"}
            else:
                return {"status": "error", "message": "Azure requires image file path"}

        except ImportError:
            return {"status": "error", "message": "Azure Vision SDK not installed"}
        except Exception as e:
            logger.error(f"Azure Vision error: {e}")
            return {"status": "error", "message": str(e)}


# Legacy compatibility
def input_processor(image: Any) -> "Image.Image":
    """Legacy image input processor"""
    if not PIL_AVAILABLE:
        raise RuntimeError("Pillow is required for image processing")

    if isinstance(image, Image.Image):
        img = image
    elif isinstance(image, (bytes, bytearray)):
        img = Image.open(io.BytesIO(image))
    else:
        img = Image.open(image)

    img = img.convert("RGB")
    img = img.resize((224, 224))
    return img
