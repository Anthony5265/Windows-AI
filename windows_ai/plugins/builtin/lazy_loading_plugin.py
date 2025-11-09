"""Lazy loading"""
from typing import Dict,Any
class lazy_loadingPlugin:
    def __init__(self):self.name="Lazy loading"
    async def execute(self,**k):return {"status":"success"}
