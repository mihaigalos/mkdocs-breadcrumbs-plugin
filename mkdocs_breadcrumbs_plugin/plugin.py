import os
import sys
from timeit import default_timer as timer
from datetime import datetime, timedelta
import logging

from mkdocs import utils as mkdocs_utils
from mkdocs.config import config_options, Config
from mkdocs.plugins import BasePlugin
from mkdocs.structure.nav import get_navigation


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

    def _get_first_document(self, config, ref_location):
        ref_path = os.path.join(config['docs_dir'], ref_location)
        if os.path.isdir(ref_path):
            for file in os.listdir(ref_path):
                if file.endswith(".md"):
                    ref_location = f"{ref_location}/{file[:-3]}"
                    break
        return ref_location

    def _get_base_url(self, config):
        site_url = config.get('site_url', '').rstrip('/')
        base_url = ""

        if site_url:
            print(site_url)
            temp = site_url.replace('http://', '').replace('https://', '')
            if "/" in temp:
                base_url = temp.split('/', 1)[1]

        return base_url

    def on_config(self, config, **kwargs):
        self._setup_logger()
        self.base_url = self._get_base_url(config)

    def on_page_markdown(self, markdown, page, config, files, **kwargs):
        slashes = page.url.count("/")
        pos_start_substring = 0
        breadcrumbs = ""
        depth = 0

        while slashes > 0:
            pos_slash = page.url.find("/", pos_start_substring+1)
            ref_name = page.url[pos_start_substring:pos_slash]
            ref_location = page.url[:pos_slash]


            ref_location = self._get_first_document(config, ref_location)
            self.logger.debug(f"page.url: {page.url} ref_name: {ref_name} ref_location: {ref_location} depth: {depth}, slashes: {slashes}")

            if len(breadcrumbs) > 0:
                breadcrumbs += self.config['delimiter']
            if depth > 0:
                if self.base_url:
                    breadcrumbs = breadcrumbs + f"[{ref_name}](/{self.base_url}/{ref_location}/)"
                else:
                    breadcrumbs = breadcrumbs + f"[{ref_name}](/{ref_location}/)"

            pos_start_substring = pos_slash + 1
            slashes -= 1
            depth += 1
        return breadcrumbs + "\n" + markdown

