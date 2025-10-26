# Workflow Spec (YAML)
- `name`: workflow name
- `steps`: list of steps
Step types:
- `tool`: calls Actions API with `with` as params
- `llm`: calls Proxy chat completions; `with.prompt` supports `{{ steps.<id>.<field> }}`
