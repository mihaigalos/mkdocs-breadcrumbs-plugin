# mkdocs-breadcrumbs-plugin

Experimental mkdocs location-based breadcrumbs navigation.

These directly get prepended to rendered Markdown.

![screenshot](https://github.com/mihaigalos/mkdocs-breadcrumbs-plugin/raw/main/screenshots/mkdocs-breadcrumbs-plugin.png)

## Setup

Install the plugin using pip:

```bash
pip install mkdocs-breadcrumbs-plugin
```

Activate the plugin in `mkdocs.yml`:
```yaml
plugins:
  - search
  - mkdocs-breadcrumbs-plugin:
      log_level: "DEBUG"  # "DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"
      delimiter: " / "  # separator between sections
```
