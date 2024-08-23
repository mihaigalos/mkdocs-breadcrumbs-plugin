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
        self.logger = logging.getLogger('mkdocs.plugins.issues')
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

    def _get_first_document(self, config, ref_location):
        ref_path = os.path.join(config['docs_dir'], ref_location)
        if os.path.isdir(ref_path):
            first_md_file = self._get_first_markdown_file(ref_path)
            if first_md_file:
                ref_location = os.path.relpath(first_md_file, config['docs_dir']).replace('\\', '/')
                ref_location = os.path.splitext(ref_location)[0]
        return ref_location

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

    def on_page_markdown(self, markdown, page, config, files, **kwargs):
        slashes = page.url.count("/")
        breadcrumbs = []
        pos_start_substring = 0

        while slashes > 0:
            pos_slash = page.url.find("/", pos_start_substring + 1)
            ref_name = page.url[pos_start_substring:pos_slash]
            ref_location = page.url[:pos_slash]

            if pos_slash != -1:
                ref_location = self._get_first_document(config, ref_location)
            else:
                ref_location = page.url

            self.logger.debug(f"page.url: {page.url} ref_name: {ref_name} ref_location: {ref_location}, slashes: {slashes}")

            if ref_name:
                if self.base_url:
                    crumb = f"[{ref_name}](/{self.base_url}/{ref_location}/)"
                else:
                    crumb = f"[{ref_name}](/{ref_location}/)"
                breadcrumbs.append(crumb)

            pos_start_substring = pos_slash + 1
            slashes -= 1

        if page.url:
            current_page = page.url.split("/")[-1]
            if current_page:
                breadcrumbs.append(current_page)

        breadcrumb_str = self.config['delimiter'].join(breadcrumbs)
        home_breadcrumb = f"[Home](/{self.base_url}/)" if self.base_url else "[Home](/)"

        breadcrumb_str = home_breadcrumb + (self.config['delimiter'] + breadcrumb_str if breadcrumb_str else "")

        return breadcrumb_str + "\n" + markdown

