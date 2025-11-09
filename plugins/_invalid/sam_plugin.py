"""
Segment Anything Model (SAM) Plugin
Supports image segmentation and object detection using Meta's SAM model
"""

from typing import Dict, Any, Optional, List, Tuple
import os
import numpy as np
from PIL import Image
import io
import base64


class SAMPlugin:
    """Plugin for Segment Anything Model (SAM)"""
    
    name = "sam"
    version = "1.0.0"
    description = "Integration with Segment Anything Model for image segmentation"
    author = "Windows AI Team"
    
    def __init__(self):
        self.model = None
        self.predictor = None
        self.device = None
        self._initialized = False
        
    def initialize(self, config: Optional[Dict[str, Any]] = None) -> bool:
        """Initialize the SAM plugin"""
        try:
            # Try to import SAM dependencies
            try:
                from segment_anything import sam_model_registry, SamPredictor
                import torch
            except ImportError:
                print("segment-anything package not installed. Install with: pip install segment-anything")
                return False
            
            # Set device
            self.device = config.get("device", "cuda" if torch.cuda.is_available() else "cpu")
            
            # Get model type and checkpoint
            model_type = config.get("model_type", "vit_h")
            checkpoint_path = config.get("checkpoint_path")
            
            if not checkpoint_path:
                # Try to find checkpoint in common locations
                checkpoint_path = self._find_checkpoint(model_type)
                if not checkpoint_path:
                    print("SAM checkpoint not found. Please download from https://github.com/facebookresearch/segment-anything#model-checkpoints")
                    return False
            
            # Load model
            self.model = sam_model_registry[model_type](checkpoint=checkpoint_path)
            self.model.to(device=self.device)
            self.predictor = SamPredictor(self.model)
            
            self._initialized = True
            return True
            
        except Exception as e:
            print(f"Error initializing SAM plugin: {e}")
            return False
    
    def _find_checkpoint(self, model_type: str) -> Optional[str]:
        """Find SAM checkpoint in common locations"""
        checkpoint_names = {
            "vit_h": "sam_vit_h_4b8939.pth",
            "vit_l": "sam_vit_l_0b3195.pth", 
            "vit_b": "sam_vit_b_01ec64.pth"
        }
        
        checkpoint_name = checkpoint_names.get(model_type)
        if not checkpoint_name:
            return None
            
        # Common locations to check
        locations = [
            os.path.join(os.getcwd(), "models", checkpoint_name),
            os.path.join(os.path.expanduser("~"), ".sam", checkpoint_name),
            os.path.join(os.getcwd(), checkpoint_name),
            os.path.join(os.path.dirname(__file__), "..", "..", "models", checkpoint_name)
        ]
        
        for location in locations:
            if os.path.exists(location):
                return location
        
        return None
    
    def execute(self, action: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a SAM action"""
        if not self._initialized:
            return {"error": "Plugin not initialized. Please provide model checkpoint."}
        
        try:
            if action == "segment_with_points":
                return self._segment_with_points(params)
            elif action == "segment_with_box":
                return self._segment_with_box(params)
            elif action == "segment_everything":
                return self._segment_everything(params)
            elif action == "segment_with_mask":
                return self._segment_with_mask(params)
            elif action == "detect_objects":
                return self._detect_objects(params)
            elif action == "generate_masks":
                return self._generate_masks(params)
            elif action == "interactive_segment":
                return self._interactive_segment(params)
            else:
                return {"error": f"Unknown action: {action}"}
                
        except Exception as e:
            return {"error": str(e)}
    
    def _load_image(self, image_input: Any) -> np.ndarray:
        """Load image from various input formats"""
        if isinstance(image_input, str):
            # Load from file path
            image = Image.open(image_input).convert("RGB")
        elif isinstance(image_input, bytes):
            # Load from bytes
            image = Image.open(io.BytesIO(image_input)).convert("RGB")
        elif isinstance(image_input, np.ndarray):
            # Already numpy array
            return image_input
        else:
            raise ValueError("Unsupported image input format")
        
        return np.array(image)
    
    def _segment_with_points(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Segment image using point prompts"""
        image_input = params.get("image")
        point_coords = params.get("point_coords", [])
        point_labels = params.get("point_labels", [1])  # 1 for foreground, 0 for background
        multimask_output = params.get("multimask_output", True)
        
        if not image_input or not point_coords:
            return {"error": "image and point_coords required"}
        
        # Load and set image
        image = self._load_image(image_input)
        self.predictor.set_image(image)
        
        # Convert to numpy array if needed
        point_coords = np.array(point_coords)
        point_labels = np.array(point_labels)
        
        # Generate masks
        masks, scores, logits = self.predictor.predict(
            point_coords=point_coords,
            point_labels=point_labels,
            multimask_output=multimask_output
        )
        
        # Convert masks to base64 images
        mask_images = []
        for i, mask in enumerate(masks):
            mask_img = Image.fromarray((mask * 255).astype(np.uint8))
            img_byte_arr = io.BytesIO()
            mask_img.save(img_byte_arr, format='PNG')
            mask_images.append(base64.b64encode(img_byte_arr.getvalue()).decode())
        
        return {
            "masks": mask_images,
            "scores": scores.tolist(),
            "mask_count": len(masks),
            "point_coords": point_coords.tolist(),
            "point_labels": point_labels.tolist()
        }
    
    def _segment_with_box(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Segment image using bounding box prompt"""
        image_input = params.get("image")
        box = params.get("box")  # [x1, y1, x2, y2]
        multimask_output = params.get("multimask_output", True)
        
        if not image_input or not box:
            return {"error": "image and box required"}
        
        # Load and set image
        image = self._load_image(image_input)
        self.predictor.set_image(image)
        
        # Convert to numpy array
        box = np.array(box)
        
        # Generate masks
        masks, scores, logits = self.predictor.predict(
            box=box,
            multimask_output=multimask_output
        )
        
        # Convert masks to base64 images
        mask_images = []
        for i, mask in enumerate(masks):
            mask_img = Image.fromarray((mask * 255).astype(np.uint8))
            img_byte_arr = io.BytesIO()
            mask_img.save(img_byte_arr, format='PNG')
            mask_images.append(base64.b64encode(img_byte_arr.getvalue()).decode())
        
        return {
            "masks": mask_images,
            "scores": scores.tolist(),
            "mask_count": len(masks),
            "box": box.tolist()
        }
    
    def _segment_everything(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Generate masks for entire image (automatic segmentation)"""
        try:
            from segment_anything import SamAutomaticMaskGenerator
            
            image_input = params.get("image")
            points_per_side = params.get("points_per_side", 32)
            pred_iou_thresh = params.get("pred_iou_thresh", 0.86)
            stability_score_thresh = params.get("stability_score_thresh", 0.92)
            crop_n_layers = params.get("crop_n_layers", 0)
            crop_n_points_downscale_factor = params.get("crop_n_points_downscale_factor", 1)
            min_mask_region_area = params.get("min_mask_region_area", 100)
            
            if not image_input:
                return {"error": "image required"}
            
            # Load image
            image = self._load_image(image_input)
            
            # Create mask generator
            mask_generator = SamAutomaticMaskGenerator(
                model=self.model,
                points_per_side=points_per_side,
                pred_iou_thresh=pred_iou_thresh,
                stability_score_thresh=stability_score_thresh,
                crop_n_layers=crop_n_layers,
                crop_n_points_downscale_factor=crop_n_points_downscale_factor,
                min_mask_region_area=min_mask_region_area,
                device=self.device
            )
            
            # Generate masks
            masks = mask_generator.generate(image)
            
            # Convert masks to base64 images
            mask_images = []
            for mask_info in masks:
                mask = mask_info['segmentation']
                mask_img = Image.fromarray((mask * 255).astype(np.uint8))
                img_byte_arr = io.BytesIO()
                mask_img.save(img_byte_arr, format='PNG')
                mask_images.append(base64.b64encode(img_byte_arr.getvalue()).decode())
            
            return {
                "masks": mask_images,
                "mask_info": masks,
                "mask_count": len(masks),
                "image_shape": image.shape
            }
            
        except ImportError:
            return {"error": "SamAutomaticMaskGenerator not available. Update segment-anything package."}
    
    def _segment_with_mask(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Refine segmentation using mask input"""
        image_input = params.get("image")
        mask_input = params.get("mask_input")
        point_coords = params.get("point_coords", [])
        point_labels = params.get("point_labels", [1])
        multimask_output = params.get("multimask_output", True)
        
        if not image_input or not mask_input:
            return {"error": "image and mask_input required"}
        
        # Load and set image
        image = self._load_image(image_input)
        self.predictor.set_image(image)
        
        # Convert inputs to numpy arrays
        mask_input = np.array(mask_input)
        point_coords = np.array(point_coords) if point_coords else None
        point_labels = np.array(point_labels) if point_labels else None
        
        # Generate masks
        masks, scores, logits = self.predictor.predict(
            point_coords=point_coords,
            point_labels=point_labels,
            mask_input=mask_input,
            multimask_output=multimask_output
        )
        
        # Convert masks to base64 images
        mask_images = []
        for i, mask in enumerate(masks):
            mask_img = Image.fromarray((mask * 255).astype(np.uint8))
            img_byte_arr = io.BytesIO()
            mask_img.save(img_byte_arr, format='PNG')
            mask_images.append(base64.b64encode(img_byte_arr.getvalue()).decode())
        
        return {
            "masks": mask_images,
            "scores": scores.tolist(),
            "mask_count": len(masks)
        }
    
    def _detect_objects(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Detect and segment objects in image"""
        # Use segment_everything for object detection
        result = self._segment_everything(params)
        
        if "error" in result:
            return result
        
        # Extract bounding boxes from masks
        objects = []
        for i, mask_info in enumerate(result.get("mask_info", [])):
            segmentation = mask_info['segmentation']
            bbox = mask_info['bbox']  # [x, y, w, h]
            area = mask_info['area']
            predicted_iou = mask_info['predicted_iou']
            stability_score = mask_info['stability_score']
            
            objects.append({
                "id": i,
                "bbox": bbox,
                "area": area,
                "confidence": float(predicted_iou),
                "stability_score": float(stability_score),
                "mask": result["masks"][i] if i < len(result["masks"]) else None
            })
        
        return {
            "objects": objects,
            "object_count": len(objects),
            "image_shape": result.get("image_shape")
        }
    
    def _generate_masks(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Generate masks with custom parameters"""
        return self._segment_everything(params)
    
    def _interactive_segment(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Interactive segmentation with multiple prompts"""
        image_input = params.get("image")
        prompts = params.get("prompts", [])  # List of {"type": "point"/"box", "data": ...}
        
        if not image_input or not prompts:
            return {"error": "image and prompts required"}
        
        # Load and set image
        image = self._load_image(image_input)
        self.predictor.set_image(image)
        
        all_masks = []
        all_scores = []
        
        # Process each prompt
        for prompt in prompts:
            prompt_type = prompt.get("type")
            prompt_data = prompt.get("data")
            
            if prompt_type == "point":
                point_coords = np.array([prompt_data["coords"]])
                point_labels = np.array([prompt_data.get("label", 1)])
                
                masks, scores, _ = self.predictor.predict(
                    point_coords=point_coords,
                    point_labels=point_labels,
                    multimask_output=False
                )
                
            elif prompt_type == "box":
                box = np.array(prompt_data)
                masks, scores, _ = self.predictor.predict(
                    box=box,
                    multimask_output=False
                )
            
            else:
                continue
            
            if len(masks) > 0:
                all_masks.append(masks[0])
                all_scores.append(scores[0])
        
        # Convert masks to base64 images
        mask_images = []
        for mask in all_masks:
            mask_img = Image.fromarray((mask * 255).astype(np.uint8))
            img_byte_arr = io.BytesIO()
            mask_img.save(img_byte_arr, format='PNG')
            mask_images.append(base64.b64encode(img_byte_arr.getvalue()).decode())
        
        return {
            "masks": mask_images,
            "scores": all_scores,
            "mask_count": len(all_masks),
            "prompts_processed": len(prompts)
        }
    
    def cleanup(self):
        """Cleanup resources"""
        self.model = None
        self.predictor = None
        self._initialized = False


# Plugin metadata
PLUGIN_CLASS = SAMPlugin
PLUGIN_NAME = "sam"
PLUGIN_VERSION = "1.0.0"
PLUGIN_DESCRIPTION = "Integration with Segment Anything Model for image segmentation"
PLUGIN_ACTIONS = [
    "segment_with_points", "segment_with_box", "segment_everything",
    "segment_with_mask", "detect_objects", "generate_masks", "interactive_segment"
]