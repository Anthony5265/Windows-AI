# Ab Test Runner Plugin

A/B testing and experimentation

## Installation

```bash
pip install windows-ai-ab_test_runner
```

## Usage

```python
from marketplace.ab_test_runner import AbTestRunnerPlugin

plugin = AbTestRunnerPlugin(config={})
result = plugin.execute()
```

## Configuration

Configure this plugin via the `config` parameter or environment variables.

## API Reference

### AbTestRunnerPlugin

Main plugin class.

- `execute(*args, **kwargs)` - Execute the plugin logic
- `validate()` - Validate plugin configuration
- `initialize()` - Initialize resources
- `shutdown()` - Clean up resources

## License

MIT License
