import os
import logging
from mkdocs.config import config_options
from mkdocs.plugins import BasePlugin

class BreadCrumbs(BasePlugin):

    config_scheme = (
        ('log_level', config_options.Type(str, default='INFO')),
        ('delimiter', config_options.Type(str, default=' / ')),
        ('base_url', config_options.Type(str, default='')),
    )

    def _setup_logger(self):
        self.logger = logging.getLogger('mkdocs.plugins.breadcrumbs')
        log_level = self.config['log_level'].upper()
        numeric_level = getattr(logging, log_level, None)
        if not isinstance(numeric_level, int):
            raise ValueError(f'Invalid log level: {log_level}')
        logging.basicConfig(level=numeric_level)
        self.logger.setLevel(numeric_level)
        self.logger.info(f'Log level set to {log_level}')

    def _get_base_url(self, config):
        site_url = config.get('site_url', '').rstrip('/')
        base_url = ""

        if site_url:
            parsed_url = site_url.split('//', 1)[-1]
            if "/" in parsed_url:
                base_url = parsed_url.split('/', 1)[1]

        return base_url

    def on_config(self, config, **kwargs):
        self._setup_logger()
        self.base_url = self._get_base_url(config)

    def on_files(self, files, config, **kwargs):
        docs_dir = config['docs_dir']
        for dirpath, _, filenames in os.walk(docs_dir):
            if 'index.md' not in filenames:
                self._generate_index_page(docs_dir, dirpath)

    def _generate_index_page(self, docs_dir, dirpath):
        # Construct the index.md content
        relative_dir = os.path.relpath(dirpath, docs_dir)
        content_lines = [f"# Index of {relative_dir}", ""]
        base_url_part = f"/{self.base_url}/".rstrip('/') if self.base_url else ""

        for item in sorted(os.listdir(dirpath)):
            item_path = os.path.join(dirpath, item)
            if os.path.isdir(item_path):
                # Link to the directory URL without index.md
                relative_item_path = os.path.join(relative_dir, item).replace("\\", "/")
                content_lines.append(f"- [{item}]({base_url_part}/{relative_item_path}/)")
            elif item.endswith(".md") and item != "index.md":
                item_name = os.path.splitext(item)[0]
                # Link directly to the .md file without 'index.md'
                relative_item_path = os.path.join(relative_dir, item_name).replace("\\", "/")
                content_lines.append(f"- [{item_name}]({base_url_part}/{relative_item_path})")

        content = "\n".join(content_lines)
        index_path = os.path.join(dirpath, 'index.md')
        with open(index_path, 'w') as f:
            f.write(content)

        self.logger.info(f"Generated index page: {index_path}")

    def on_page_markdown(self, markdown, page, config, files, **kwargs):
        breadcrumbs = []
        path_parts = page.url.strip("/").split("/")
        accumulated_path = []

        for i, part in enumerate(path_parts[:-1]):
            accumulated_path.append(part)
            current_path = "/".join(accumulated_path)
            if self.base_url:
                crumb_url = f"/{self.base_url}/{current_path}/"
            else:
                crumb_url = f"/{current_path}/"
            breadcrumbs.append(f"[{part}]({crumb_url})")

        current_page = path_parts[-1].replace('.md', '')
        if current_page:
            breadcrumbs.append(current_page)

        home_breadcrumb = f"[Home]({self.base_url}/)" if self.base_url else "[Home](/)"
        if breadcrumbs:
            breadcrumb_str = self.config['delimiter'].join(breadcrumbs)
            breadcrumb_str = home_breadcrumb + self.config['delimiter'] + breadcrumb_str
        else:
            breadcrumb_str = home_breadcrumb

        return breadcrumb_str + "\n" + markdown

