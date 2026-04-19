# Provider Chat Examples

This page shows how to use the provider-backed integrations endpoints for direct
CLI and local-runtime execution.

## Detect available providers

```bash
curl http://127.0.0.1:8010/integrations/providers/detect
```

## Get Ollama recommendations

```bash
curl http://127.0.0.1:8010/integrations/providers/ollama/recommendations
```

## Synchronous provider chat

```bash
curl -X POST http://127.0.0.1:8010/integrations/providers/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Summarize the latest changes",
    "model": "cli:codex",
    "temperature": 0.3,
    "max_tokens": 256
  }'
```

## Streaming provider chat over NDJSON

```bash
curl -N -X POST http://127.0.0.1:8010/integrations/providers/chat/stream \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Explain this step by step",
    "model": "ollama:llama3.1:8b",
    "temperature": 0.7,
    "max_tokens": 256
  }'
```

Example output:

```json
{"type":"start","model":"ollama:llama3.1:8b","conversation_id":null}
{"type":"chunk","content":"Step 1: "}
{"type":"chunk","content":"inspect the request..."}
{"type":"complete","content":"Step 1: inspect the request...","model":"ollama:llama3.1:8b","conversation_id":null}
```

## Use `stream: true` on the main chat endpoint

The main provider chat endpoint also accepts `stream: true` and will delegate to
NDJSON streaming.

```bash
curl -N -X POST http://127.0.0.1:8010/integrations/providers/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Stream this response",
    "model": "cli:codex",
    "stream": true
  }'
```

## Include prior history

```bash
curl -X POST http://127.0.0.1:8010/integrations/providers/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Continue",
    "model": "cli:claude",
    "history": [
      {"role": "system", "content": "You are concise."},
      {"role": "user", "content": "Give me a quick summary."},
      {"role": "assistant", "content": "Here is the summary."}
    ]
  }'
```
