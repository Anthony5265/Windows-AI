"""Tado"""
from typing import Dict,Any
class tadoPlugin:
    def __init__(self):self.name="Tado"
    async def execute(self,**k):return {"status":"success"}
