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

    def _get_first_markdown_file(self, dir_path):
        for root, _, files in os.walk(dir_path):
            for file in sorted(files):
                if file.endswith(".md"):
                    return os.path.join(root, file)
        return None

    def _is_valid_markdown_file(self, config, ref_location):
        ref_path = os.path.join(config['docs_dir'], ref_location)
        return os.path.isfile(ref_path) and ref_path.endswith(".md")

    def _get_base_url(self, config):
        site_url = config.get('site_url', '').rstrip('/')
        base_url = ""

        if site_url:
            temp = site_url.replace('http://', '').replace('https://', '')
            if "/" in temp:
                base_url = temp.split('/', 1)[1]

        return base_url

    def on_config(self, config, **kwargs):
        self._setup_logger()
        self.base_url = self._get_base_url(config)

    def on_files(self, files, config, **kwargs):
        docs_dir = config['docs_dir']
        for dirpath, _, filenames in os.walk(docs_dir):
            index_path = os.path.join(dirpath, 'index.md')
            if 'index.md' not in filenames:
                self._generate_index_page(docs_dir, dirpath)

    def _generate_index_page(self, docs_dir, dirpath):
        # Construct the index.md content
        relative_dir = os.path.relpath(dirpath, docs_dir)
        content_lines = [f"# Index of {relative_dir}", ""]
        base_url_part = f"/{self.base_url}/" if self.base_url else "/"

        for item in sorted(os.listdir(dirpath)):
            item_path = os.path.join(dirpath, item)
            if os.path.isdir(item_path):
                content_lines.append(f"- [{item}]({base_url_part}{os.path.join(relative_dir, item)}/index.md)")
            elif item.endswith(".md") and item != "index.md":
                item_name = os.path.splitext(item)[0]
                content_lines.append(f"- [{item_name}]({base_url_part}{os.path.join(relative_dir, item)})")

        content = "\n".join(content_lines)
        index_path = os.path.join(dirpath, 'index.md')
        with open(index_path, 'w') as f:
            f.write(content)

        self.logger.info(f"Generated index page: {index_path}")

    def on_page_markdown(self, markdown, page, config, files, **kwargs):
        slashes = page.url.count("/")
        breadcrumbs = []
        pos_start_substring = 0

        while slashes >= 0:
            pos_slash = page.url.find("/", pos_start_substring + 1)
            if pos_slash == -1:
                pos_slash = len(page.url)
            ref_name = page.url[pos_start_substring:pos_slash]
            ref_location = page.url[:pos_slash]

            if self.base_url:
                crumb = f"[{ref_name}](/{self.base_url}/{ref_location}/)"
            else:
                crumb = f"[{ref_name}](/{ref_location}/)"

            self.logger.debug(f"page.url: {page.url} ref_name: {ref_name} ref_location: {ref_location}, slashes: {slashes}")

            if ref_name:
                breadcrumbs.append(crumb)

            pos_start_substring = pos_slash + 1
            slashes -= 1

        current_page = page.url.split("/")[-1].replace('.md', '')
        if current_page:
            breadcrumbs.append(current_page)

        # Join the breadcrumbs with the delimiter
        home_breadcrumb = f"[Home](/{self.base_url}/)" if self.base_url else "[Home](/)"
        if breadcrumbs:
            breadcrumb_str = self.config['delimiter'].join(breadcrumbs)
            breadcrumb_str = home_breadcrumb + self.config['delimiter'] + breadcrumb_str
        else:
            breadcrumb_str = home_breadcrumb

        return breadcrumb_str + "\n" + markdown

