# mkdocs-breadcrumbs-plugin

Mkdocs location-based breadcrumbs navigation.

These directly get prepended to rendered Markdown.

![example](screenshots/breadcrumbs.png)

## Setup

Install the plugin using pip:

```bash
pip install mkdocs-breadcrumbs-plugin
```

Activate the plugin in `mkdocs.yaml`:
```yaml
plugins:
  - search
  - mkdocs-breadcrumbs-plugin:
      log_level: "DEBUG"  # "DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"
      delimiter: " / "  # separator between sections
```
