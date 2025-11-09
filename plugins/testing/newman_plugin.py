"""Newman API Testing Plugin"""
from typing import Dict,Any,Optional
import subprocess
class NewmanPlugin:
    name="newman";version="1.0.0";description="Newman Postman CLI runner";author="Windows AI Team"
    def __init__(self):self._initialized=False
    def initialize(self,config:Optional[Dict[str,Any]]=None)->bool:self._initialized=True;return True
    def execute(self,action:str,params:Dict[str,Any])->Dict[str,Any]:
        if not self._initialized:return{"success":False}
        if action=="run":coll=params.get("collection","");subprocess.run(["newman","run",coll]);return{"success":True}
        return{"success":False}
    def shutdown(self)->bool:self._initialized=False;return True
