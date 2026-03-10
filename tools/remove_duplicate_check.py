import re

# Read the file
with open('windows_ai/plugins/builtin/audio_models/whisper_plugin.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Remove the duplicate audio_file check
# Find the pattern where audio_file is checked twice
pattern = r'(if not self\._api_key:\s+# Simulate transcription without API key\s+return await self\._transcribe_offline\(params\))\s+if not audio_file:\s+return \{\s+"success": False,\s+"error": "audio_file parameter is required",\s+"error_code": "MISSING_PARAMETER"\s+\}'

content = re.sub(pattern, r'\1', content)

# Write back
with open('windows_ai/plugins/builtin/audio_models/whisper_plugin.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("✓ Removed duplicate audio_file check in whisper_plugin.py")