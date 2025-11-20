if (-not $env:OPENAI_API_KEY) {
    Write-Host "❌ OPENAI_API_KEY is not set in the environment." -ForegroundColor Red
    exit 1
}
if ($env:OPENAI_API_KEY -notmatch "^sk-") {
    Write-Host "⚠️ OPENAI_API_KEY is set but doesn't look like an OpenAI key." -ForegroundColor Yellow
} else {
    Write-Host "✅ OPENAI_API_KEY is set and looks valid." -ForegroundColor Green
}
