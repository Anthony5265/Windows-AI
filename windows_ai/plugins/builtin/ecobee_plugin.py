"""Ecobee"""
from typing import Dict,Any
class ecobeePlugin:
    def __init__(self):self.name="Ecobee"
    async def execute(self,**k):return {"status":"success"}
