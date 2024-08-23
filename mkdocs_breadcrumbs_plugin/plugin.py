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
        ('start_depth', config_options.Type(int, default=2)),
        ('log_level', config_options.Type(str, default='INFO')),


    )

    def setup_logger(self):
        self.logger = logging.getLogger('mkdocs.plugins.issues')
        log_level = self.config['log_level'].upper()
        numeric_level = getattr(logging, log_level, None)
        if not isinstance(numeric_level, int):
            raise ValueError(f'Invalid log level: {log_level}')
        logging.basicConfig(level=numeric_level)
        self.logger.setLevel(numeric_level)
        self.logger.info(f'Log level set to {log_level}')

    def on_config(self, config, **kwargs):
        self.setup_logger()

    def on_page_markdown(self, markdown, page, config, files, **kwargs):
        slashes = page.url.count("/")
        pos_start_substring = 0
        breadcrumbs = ""
        depth = 0
        while slashes > 0:
            pos_slash = page.url.find("/", pos_start_substring+1)
            ref_name  = page.url[pos_start_substring:pos_slash]
            ref_location  = page.url[:pos_slash]

            self.logger.debug(f"page.url: {page.url} ref_name: {ref_name} ref_location: {ref_location} depth: {depth}, slashes: {slashes}")

            if len(breadcrumbs) > 0:
                breadcrumbs += " > "
            if depth > 0:
                breadcrumbs = breadcrumbs + f"[{ref_name}](/{ref_location}/)"
            pos_start_substring = pos_slash + 1
            slashes -= 1
            depth += 1
        return breadcrumbs + "\n" + markdown

