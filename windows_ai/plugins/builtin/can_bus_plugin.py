"""CAN bus"""
from typing import Dict,Any
class can_busPlugin:
    def __init__(self):self.name="CAN bus"
    async def execute(self,**k):return {"status":"success"}
