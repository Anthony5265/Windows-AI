import re

# Read the file
with open('windows_ai/plugins/builtin/audio_models/whisper_plugin.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Find and fix the _transcribe method - move API key check earlier
old_pattern = r'''        audio_file = params\.get\("audio_file"\)
        if not audio_file:
            return \{
                "success": False,
                "error": "audio_file parameter is required",
                "error_code": "MISSING_PARAMETER"
            \}

        if not self\._api_key:
            # Simulate transcription without API key
            return await self\._transcribe_offline\(params\)'''

new_text = '''        # Check API key first - if missing, use offline simulation
        if not self._api_key:
            # Simulate transcription without API key
            return await self._transcribe_offline(params)
        
        audio_file = params.get("audio_file")
        if not audio_file:
            return {
                "success": False,
                "error": "audio_file parameter is required",
                "error_code": "MISSING_PARAMETER"
            }'''

content = content.replace(old_pattern, new_text)

# Write back
with open('windows_ai/plugins/builtin/audio_models/whisper_plugin.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("✓ Moved API key check before file validation in whisper_plugin.py")