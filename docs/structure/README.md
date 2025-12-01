# Repository Organization Toolkit

This directory centralizes the resources that explain how Windows AI is laid out.  It introduces the
curated categories that group every top-level folder and file, and it stores a machine-readable manifest
that other tooling can consume.

## Key Components

| File | Purpose |
| --- | --- |
| [`catalog_config.yaml`](catalog_config.yaml) | Source of truth that maps every path in the repository to an organizational category. |
| [`manifest.json`](manifest.json) | Generated inventory describing each category, including directory trees. |
| [`overview.md`](overview.md) | Human-friendly summary of the categories and the assets they contain. |
| [`../../scripts/generate_repo_manifest.py`](../../scripts/generate_repo_manifest.py) | Script that produces the manifest from the YAML configuration. |

## Generating the Manifest

Run the helper script from the repository root any time files move or new directories appear:

```bash
python scripts/generate_repo_manifest.py --pretty
```

The command validates that every top-level path is accounted for.  If anything is missing, it halts with
an error listing the paths that need to be assigned to a category.  The `--pretty` flag is optional and
simply formats the JSON for easier manual inspection.

## Updating the Catalog

1. Edit [`catalog_config.yaml`](catalog_config.yaml) to add, remove, or adjust entries.
2. Regenerate the manifest using the script above.
3. Commit both the YAML and JSON files together so the documentation and tooling stay in sync.

Each catalog entry supports:

- `path`: relative path from the repository root to the directory or file.
- `description`: short summary that appears in the manifest and in the overview table.
- `kind`: set to `file` to indicate that the path should not be expanded into a tree (defaults to `directory`).
- `max_depth`: optional limit for how deep the directory tree should be expanded in the manifest.
- `collapsed`: when `true`, the manifest records the entry but intentionally avoids traversing children (useful for vendor directories such as `node_modules`).

## Staying Organized

The organization toolkit works best when changes to the repository include updated catalog metadata.  A
quick checklist before opening a pull request:

- [ ] Did any new top-level directories or files appear?  If so, add them to the catalog.
- [ ] Did any paths move?  Update their catalog entries and regenerate the manifest.
- [ ] Are large vendor or build directories still marked as `collapsed` to keep the manifest manageable?

Following these steps keeps the documentation navigable and ensures new contributors can quickly locate
code, tooling, and assets across the Windows AI monorepo.
