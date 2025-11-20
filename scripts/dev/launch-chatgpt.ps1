$ErrorActionPreference="Stop"
$context = Get-Content "docs/context-snapshot.txt" -Raw
$encoded = [System.Web.HttpUtility]::UrlEncode($context)
$chatUrl = "https://chat.openai.com/?q=$encoded"
Start-Process $chatUrl
