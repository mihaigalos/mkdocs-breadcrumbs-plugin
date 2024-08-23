# mkdocs-breadcrumbs-plugin

Experimental mkdocs location-based breadcrumbs navigation.

These directly get prepended to rendered Markdown.

![example](screenshots/breadcrumbs.png)

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
      start_depth: 2
```

## Config

* `start_depth` - An int representing at which depth the plugin is running the logic. The depth represents the number of slashes in a URL path (i.e.: /home/ has depth 2). 

