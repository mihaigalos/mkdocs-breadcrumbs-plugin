import os
import logging
from mkdocs.config import config_options
from mkdocs.plugins import BasePlugin

class BreadCrumbs(BasePlugin):

    config_scheme = (
        ('log_level', config_options.Type(str, default='INFO')),
        ('delimiter', config_options.Type(str, default=' / ')),
        ('base_url', config_options.Type(str, default='')),
        ('tooltip_message', config_options.Type(str, default="Is a folder in the hierarchy - no page to navigate to.")),
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

            if self._is_valid_markdown_file(config, ref_location + ".md"):
                if self.base_url:
                    crumb = f"[{ref_name}](/{self.base_url}/{ref_location}/)"
                else:
                    crumb = f"[{ref_name}](/{ref_location}/)"
            else:
                # Tooltip for non-clickable segment using the user-defined message from config
                tooltip_message = self.config['tooltip_message']
                crumb = f'<span title="{tooltip_message}">{ref_name}</span>'

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

