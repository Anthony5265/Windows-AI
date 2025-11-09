"""Loggly"""
from typing import Dict,Any
class logglyPlugin:
    def __init__(self):self.name="Loggly"
    async def execute(self,**k):return {"status":"success"}
