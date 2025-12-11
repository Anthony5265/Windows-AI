"""
Batch update all 43 managers to use WindowsAIConfig instead of Dict
This script automates the repetitive work of updating manager initialization signatures
"""

import re
from pathlib import Path

# List of all manager files in integrations directory
MANAGER_FILES = [
    "ai_providers.py",  # ✅ DONE
    "image_generation.py",  # ✅ DONE  
    "video_generation.py",  # ✅ DONE
    "audio_speech.py",
    "document_processing.py",
    "windows_automation.py",
    "browser_automation.py",
    "productivity.py",
    "data_analysis.py",
    "code_assistants.py",
    "translation.py",
    "search_engines.py",
    "knowledge_graph.py",
    "threed_generation.py",
    "music_generation.py",
    "embeddings.py",
    "vector_stores.py",
    "workflow_automation.py",
    "email_services.py",
    "notifications.py",
    "cloud_storage.py",
    "database.py",
    "monitoring.py",
    "ai_agents.py",
    "security_scanning.py",
    "content_moderation.py",
    "rag_pipeline.py",
    "mlops.py",
    "payments.py",
    "social_media.py",
    "scheduling.py",
    "crm.py",
    "iot_hardware.py",
    "computer_vision.py",
    "healthcare_ai.py",
    "legal_ai.py",
    "education_ai.py",
    "finance_ai.py",
    "scientific_ai.py",
    "accessibility_ai.py",
    "realestate_ai.py",
    "gaming_ai.py",
    "conversational_ai.py",
    "automation_robotics.py",
    "biometrics_identity.py",
]

INTEGRATIONS_DIR = Path("windows_ai/integrations")

def update_manager_file(filepath: Path) -> bool:
    """
    Update a manager file to use WindowsAIConfig
    
    Changes:
    1. Add import: from windows_ai.config.unified_config import WindowsAIConfig
    2. Change initialize signature: Dict -> WindowsAIConfig
    3. Add type hint to __init__ if needed
    
    Returns:
        True if file was modified, False otherwise
    """
    if not filepath.exists():
        print(f"❌ File not found: {filepath}")
        return False
    
    content = filepath.read_text(encoding='utf-8')
    original_content = content
    modified = False
    
    # Step 1: Add import if not present
    if "from windows_ai.config.unified_config import WindowsAIConfig" not in content:
        # Find the import section (after docstring, before first class/function)
        import_pattern = r'("""[\s\S]*?""")\s*(import\s+\w+)'
        match = re.search(import_pattern, content)
        
        if match:
            # Insert after docstring, before first import
            insert_pos = match.end(1)
            content = (
                content[:insert_pos] + 
                "\n\nimport asyncio\nimport logging\nimport os\nfrom typing import Dict, List, Any, Optional\nfrom windows_ai.config.unified_config import WindowsAIConfig" +
                content[insert_pos:]
            )
            # Clean up duplicate imports later
            modified = True
            print(f"  ✅ Added WindowsAIConfig import")
    
    # Step 2: Update initialize method signature
    # Pattern: async def initialize(self, config: Optional[Dict] = None):
    initialize_pattern = r'async def initialize\(self, config: Optional\[Dict\] = None\):'
    
    if re.search(initialize_pattern, content):
        content = re.sub(
            initialize_pattern,
            'async def initialize(self, config: Optional[WindowsAIConfig] = None):',
            content
        )
        modified = True
        print(f"  ✅ Updated initialize() signature to use WindowsAIConfig")
    
    # Step 3: Add _config attribute to __init__ if not present
    # Find __init__ method and add self._config: Optional[WindowsAIConfig] = None
    init_pattern = r'(def __init__\(self\):[\s\S]*?)(async def initialize)'
    
    if re.search(init_pattern, content):
        if "self._config" not in content:
            content = re.sub(
                r'(def __init__\(self\):)',
                r'\1\n        self._config: Optional[WindowsAIConfig] = None',
                content,
                count=1
            )
            modified = True
            print(f"  ✅ Added self._config attribute to __init__")
    
    # Step 4: Add config assignment in initialize if not present
    if "self._config = config" not in content and modified:
        # Insert after "if self._initialized:" check
        content = re.sub(
            r'(async def initialize\(self, config: Optional\[WindowsAIConfig\] = None\):[\s\S]*?if self\._initialized:[\s\S]*?return)',
            r'\1\n        \n        self._config = config',
            content,
            count=1
        )
        print(f"  ✅ Added self._config = config assignment")
    
    if modified:
        filepath.write_text(content, encoding='utf-8')
        print(f"✅ Updated: {filepath.name}")
        return True
    else:
        print(f"⏭️  Skipped: {filepath.name} (already updated or no changes needed)")
        return False

def main():
    """Update all manager files"""
    print("🔧 Updating all 43 managers to use WindowsAIConfig...")
    print("=" * 60)
    
    updated_count = 0
    skipped_count = 0
    error_count = 0
    
    for manager_file in MANAGER_FILES:
        filepath = INTEGRATIONS_DIR / manager_file
        print(f"\n📄 Processing: {manager_file}")
        
        try:
            if update_manager_file(filepath):
                updated_count += 1
            else:
                skipped_count += 1
        except Exception as e:
            print(f"❌ Error updating {manager_file}: {e}")
            error_count += 1
    
    print("\n" + "=" * 60)
    print(f"✅ Updated: {updated_count} files")
    print(f"⏭️  Skipped: {skipped_count} files")
    print(f"❌ Errors: {error_count} files")
    print(f"📊 Total: {updated_count + skipped_count + error_count}/{len(MANAGER_FILES)}")

if __name__ == "__main__":
    main()
