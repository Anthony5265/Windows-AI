# Provider Integrations API

Provider integrations are exposed through the integrations router and cover three areas:

- provider discovery
- local hardware and Ollama recommendations
- provider-backed chat execution

## Supported provider chat targets

Windows AI currently supports these provider-backed target formats:

- `cli:gemini`
- `cli:codex`
- `cli:claude`
- `cli:grok`
- `ollama:<model>`

## Discovery and setup endpoints

### `GET /integrations/providers/definitions`
Returns the known provider definitions, including install URLs, auth hints, and capability flags.

### `GET /integrations/providers/detect`
Detects all supported provider CLIs and local runtimes on the current machine.

### `GET /integrations/providers/detect/{provider_id}`
Detects a single provider. Valid ids are `gemini`, `codex`, `claude`, `grok`, and `ollama`.

### `GET /integrations/providers/hardware`
Returns a lightweight hardware profile used for local model recommendations.

### `GET /integrations/providers/ollama/recommendations`
Returns recommended Ollama models based on detected hardware.

### `GET /integrations/providers/setup-plan`
Returns a combined setup plan including detection results and installer actions.

## Provider-backed chat

### `POST /integrations/providers/chat`
Executes a provider-backed chat request and returns the final normalized response.

Example request:

```json
{
  "message": "Summarize the latest changes",
  "conversation_id": "optional-id",
  "model": "cli:codex",
  "temperature": 0.7,
  "max_tokens": 512,
  "history": [
    {"role": "system", "content": "You are concise."},
    {"role": "assistant", "content": "Ready."}
  ]
}
```

Example response:

```json
{
  "status": "success",
  "conversation_id": "optional-id",
  "provider_result": {
    "model": "cli:codex",
    "provider_id": "codex",
    "content": "Here is a concise summary...",
    "backend": "provider-cli",
    "metadata": {
      "temperature": 0.7,
      "max_tokens": 512,
      "auth_configured": true,
      "attempt_count": 4
    }
  },
  "message": {
    "role": "assistant",
    "content": "Here is a concise summary...",
    "model": "cli:codex"
  }
}
```

### `POST /integrations/providers/chat/stream`
Streams a provider-backed chat request as newline-delimited JSON with these event types:

- `start`
- `chunk`
- `complete`
- `error`

Example request:

```json
{
  "message": "Stream the explanation",
  "conversation_id": "optional-id",
  "model": "ollama:llama3.1:8b",
  "temperature": 0.7,
  "max_tokens": 256,
  "history": []
}
```

Example stream:

```json
{"type":"start","model":"ollama:llama3.1:8b","conversation_id":"optional-id"}
{"type":"chunk","content":"Hello"}
{"type":"chunk","content":" world"}
{"type":"complete","content":"Hello world","model":"ollama:llama3.1:8b","conversation_id":"optional-id"}
```
