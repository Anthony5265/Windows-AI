# Windows AI Actions API

The Windows AI platform exposes REST endpoints for local features. The interfaces are standardized in [openapi/windows-ai.yaml](../../../openapi/windows-ai.yaml) and are served from `http://localhost:3000`.

All endpoints accept and return JSON.

## Endpoints

### `POST /api/actions/execute`
Execute a named action on the host.

```json
{
  "action": "shell",
  "params": { "command": "echo hi" }
}
```

### `POST /api/mobile/pair`
Create a pairing token for a mobile device.

```json
{ "deviceId": "phone-1" }
```

### `POST /api/mobile/command`
Execute an action on behalf of a paired device.

```json
{ "token": "<token>", "action": "get_system_info" }
```

### `POST /api/mesh/distribute`
Distribute a task to mesh nodes.

```json
{ "task": "render frame" }
```

### `POST /api/iot/event`
Submit an IoT device event.

```json
{ "deviceId": "lamp", "event": "on" }
```

### `POST /api/search/query`
Query a set of documents and return matching ids.

```json
{
  "query": "hello world",
  "documents": { "a": "hello there", "b": "general kenobi" }
}
```

Each response contains an `ok` field and a `result` or `token` depending on the endpoint.
