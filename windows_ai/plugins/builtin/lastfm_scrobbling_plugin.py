"""Last.fm scrobbling"""
from typing import Dict,Any
class lastfm_scrobblingPlugin:
    def __init__(self):self.name="Last.fm scrobbling"
    async def execute(self,**k):return {"status":"success"}
