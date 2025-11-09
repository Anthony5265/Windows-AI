"""Taskbar context menu"""
from typing import Dict,Any
import logging
logger=logging.getLogger(__name__)
class taskbar_context_menuPlugin:
    def __init__(self):self.name="Taskbar context menu";self.version="1.0.0"
    async def execute(self,**k):return {"status":"success","plugin":self.name}
