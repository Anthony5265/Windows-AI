"""Guest mode"""
from typing import Dict,Any
class guest_modePlugin:
    def __init__(self):self.name="Guest mode"
    async def execute(self,**k):return {"status":"success"}
