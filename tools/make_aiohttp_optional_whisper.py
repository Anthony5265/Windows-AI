import re

# Read the file
with open('windows_ai/plugins/builtin/audio_models/whisper_plugin.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Replace import aiohttp with optional import
import_pattern = r'import aiohttp'
import_replacement = '''try:
    import aiohttp
    AIOHTTP_AVAILABLE = True
except ImportError:
    AIOHTTP_AVAILABLE = False
    aiohttp = None'''

content = content.replace('import aiohttp', import_replacement)

# Replace session creation
session_pattern = r'(\s+)# Create HTTP session with custom timeout\s+timeout = aiohttp\.ClientTimeout\(total=self\._request_timeout\)\s+self\.session = aiohttp\.ClientSession\(timeout=timeout\)'
session_replacement = r'\1# Create HTTP session with custom timeout (if aiohttp available)\n\1if AIOHTTP_AVAILABLE:\n\1    timeout = aiohttp.ClientTimeout(total=self._request_timeout)\n\1    self.session = aiohttp.ClientSession(timeout=timeout)\n\1else:\n\1    self.session = None'

content = re.sub(session_pattern, session_replacement, content)

# Write back
with open('windows_ai/plugins/builtin/audio_models/whisper_plugin.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("✓ Made aiohttp optional in whisper_plugin.py")