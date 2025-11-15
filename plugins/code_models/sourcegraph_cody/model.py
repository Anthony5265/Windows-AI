"""
Sourcegraph Cody - AI Code Assistant
"""

class SourcegraphCody:
    def __init__(self, api_key=None):
        self.api_key = api_key
        self.name = "Sourcegraph Cody"
    
    def autocomplete(self, code: str, language: str) -> str:
        return f"# Sourcegraph Cody completion for {language}"
    
    def explain(self, code: str) -> str:
        return f"Sourcegraph Cody code explanation"
    
    def generate_tests(self, code: str) -> str:
        return "# Generated tests"
