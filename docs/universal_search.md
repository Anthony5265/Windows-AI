# Universal Search

The universal search system provides a simple token-based index that can be
used to look up local files or trigger actions from the GUI.

## Configuration

Select the backend by editing `config/search.yaml`:

```yaml
backend: local  # or "cloud"
cloud:
  endpoint: https://example.com/search
```

The local backend keeps an in-memory index. The cloud backend represents a
remote service and is intended to be replaced with a real implementation.

## Using the GUI

```python
from search import load_engine
from gui.core import GuiCore

engine = load_engine()
engine.index({"readme": "Open the README file"})

gui = GuiCore(model)
gui.enable_search(engine)
results = gui.search("readme")

# Link search results to actions

def open_readme():
    print("Opening README.md")

gui.register_search_action("readme", open_readme)
if "readme" in results:
    gui.activate_search_result("readme")
```

This example indexes a small document, queries it from the GUI and associates a
workflow with the returned result.
