"""Welcome messages"""
from typing import Dict,Any
class welcome_messagesPlugin:
    def __init__(self):self.name="Welcome messages"
    async def execute(self,**k):return {"status":"success"}
