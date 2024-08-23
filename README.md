# mkdocs-breadcrumbs-plugin

Mkdocs location-based breadcrumbs navigation.

These directly get prepended to rendered Markdown.

![screenshot](https://github.com/mihaigalos/mkdocs-breadcrumbs-plugin/raw/main/screenshots/mkdocs-breadcrumbs-plugin.png)

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

> [!IMPORTANT]  
> This plugin will recursively scan folders for the first markdown document.
> If a subpath contains no markdown, it will not contain a hyperlink in the generated breadcrumb.
