"""ClickHouse"""
from typing import Dict,Any
class clickhousePlugin:
    def __init__(self):self.name="ClickHouse"
    async def execute(self,**k):return {"status":"success"}
