import re

# Read the file
with open('windows_ai/plugins/builtin/audio_models/whisper_plugin.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Find the _transcribe_offline method and ensure it's used correctly
# The issue is _prepare_audio_file is being called before _transcribe_offline
# We need to call _transcribe_offline earlier when API key is missing

# Find the _transcribe method
transcribe_pattern = r'(async def _transcribe\(self, params: Dict\[str, Any\]\) -> Dict\[str, Any\]:.*?""".*?""")\s+(if not self\._api_key:.*?return await self\._transcribe_offline\(params\))\s+(audio_file = params\.get\("audio_file"\))'

def fix_transcribe(match):
    header = match.group(1)
    api_key_check = match.group(2)
    audio_file_line = match.group(3)
    
    # Reorder: check audio_file first, then API key
    return f'''{header}
        {audio_file_line}
        if not audio_file:
            return {{
                "success": False,
                "error": "audio_file parameter is required",
                "error_code": "MISSING_PARAMETER"
            }}

        {api_key_check}
'''

content = re.sub(transcribe_pattern, fix_transcribe, content, flags=re.DOTALL)

# Write back
with open('windows_ai/plugins/builtin/audio_models/whisper_plugin.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("✓ Fixed _transcribe method flow in whisper_plugin.py")