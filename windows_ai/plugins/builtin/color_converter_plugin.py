"""
Color Converter Plugin - Utility
Convert between color formats (HEX, RGB, HSL)
"""
from typing import Dict, Any, Tuple
import logging
import re

logger = logging.getLogger(__name__)

class Plugin:
    """Utility plugin for Color Converter functionality"""
    
    def __init__(self):
        self.name = "Color Converter"
        self.version = "2.0.0"
        self.description = "Convert between color formats"
    
    async def execute(self, **kwargs) -> Dict[str, Any]:
        """Execute utility function"""
        try:
            input_data = kwargs.get("input")
            to_format = kwargs.get("to_format", "all")
            
            if input_data is None:
                return {"status": "error", "message": "No input provided"}
            
            result = await self._convert(input_data, to_format, **kwargs)
            return {"status": "success", "result": result}
            
        except Exception as e:
            logger.error(f"{self.name} error: {str(e)}")
            return {"status": "error", "message": str(e)}
    
    async def _convert(self, color: str, to_format: str, **kwargs) -> Dict[str, Any]:
        """Convert color to specified format"""
        try:
            # Detect input format
            if color.startswith('#'):
                rgb = self._hex_to_rgb(color)
            elif color.startswith('rgb'):
                rgb = self._parse_rgb(color)
            elif color.startswith('hsl'):
                hsl = self._parse_hsl(color)
                rgb = self._hsl_to_rgb(hsl)
            else:
                raise ValueError("Unknown color format")
            
            # Convert to requested format
            result = {
                "input": color,
                "rgb": f"rgb({rgb[0]}, {rgb[1]}, {rgb[2]})",
                "hex": self._rgb_to_hex(rgb),
                "hsl": self._rgb_to_hsl(rgb)
            }
            
            return result
        except Exception as e:
            raise Exception(f"Color conversion failed: {str(e)}")
    
    def _hex_to_rgb(self, hex_color: str) -> Tuple[int, int, int]:
        """Convert HEX to RGB"""
        hex_color = hex_color.lstrip('#')
        return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
    
    def _rgb_to_hex(self, rgb: Tuple[int, int, int]) -> str:
        """Convert RGB to HEX"""
        return '#{:02x}{:02x}{:02x}'.format(*rgb)
    
    def _parse_rgb(self, rgb_str: str) -> Tuple[int, int, int]:
        """Parse RGB string"""
        match = re.search(r'rgb\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*\)', rgb_str)
        if match:
            return tuple(int(x) for x in match.groups())
        raise ValueError("Invalid RGB format")
    
    def _parse_hsl(self, hsl_str: str) -> Tuple[float, float, float]:
        """Parse HSL string"""
        match = re.search(r'hsl\(\s*([\d.]+)\s*,\s*([\d.]+)%\s*,\s*([\d.]+)%\s*\)', hsl_str)
        if match:
            return tuple(float(x) for x in match.groups())
        raise ValueError("Invalid HSL format")
    
    def _rgb_to_hsl(self, rgb: Tuple[int, int, int]) -> str:
        """Convert RGB to HSL"""
        r, g, b = [x / 255.0 for x in rgb]
        max_c = max(r, g, b)
        min_c = min(r, g, b)
        l = (max_c + min_c) / 2
        
        if max_c == min_c:
            h = s = 0
        else:
            d = max_c - min_c
            s = d / (2 - max_c - min_c) if l > 0.5 else d / (max_c + min_c)
            
            if max_c == r:
                h = (g - b) / d + (6 if g < b else 0)
            elif max_c == g:
                h = (b - r) / d + 2
            else:
                h = (r - g) / d + 4
            h /= 6
        
        return f"hsl({int(h * 360)}, {int(s * 100)}%, {int(l * 100)}%)"
    
    def _hsl_to_rgb(self, hsl: Tuple[float, float, float]) -> Tuple[int, int, int]:
        """Convert HSL to RGB"""
        h, s, l = hsl[0] / 360, hsl[1] / 100, hsl[2] / 100
        
        def hue_to_rgb(p, q, t):
            if t < 0: t += 1
            if t > 1: t -= 1
            if t < 1/6: return p + (q - p) * 6 * t
            if t < 1/2: return q
            if t < 2/3: return p + (q - p) * (2/3 - t) * 6
            return p
        
        if s == 0:
            r = g = b = l
        else:
            q = l * (1 + s) if l < 0.5 else l + s - l * s
            p = 2 * l - q
            r = hue_to_rgb(p, q, h + 1/3)
            g = hue_to_rgb(p, q, h)
            b = hue_to_rgb(p, q, h - 1/3)
        
        return (int(r * 255), int(g * 255), int(b * 255))
