import os
import shutil
import logging
import fnmatch
from mkdocs.config import config_options
from mkdocs.plugins import BasePlugin
from urllib.parse import unquote

class BreadCrumbs(BasePlugin):

    config_scheme = (
        ('log_level', config_options.Type(str, default='INFO')),
        ('delimiter', config_options.Type(str, default=' / ')),
        ('base_url', config_options.Type(str, default='')),
        ('exclude_paths', config_options.Type(list, default=['docs/mkdocs/**', 'docs/index.md'])),
        ('additional_index_folders', config_options.Type(list, default=[])),
        ('generate_home_index', config_options.Type(bool, default=True)),
        ('use_page_titles', config_options.Type(bool, default=False)),
        ('home_text', config_options.Type(str, default='Home')),
    )

    def _setup_logger(self):
        self.logger = logging.getLogger('mkdocs.plugins.breadcrumbs')
        log_level = self.config['log_level'].upper()
        numeric_level = getattr(logging, log_level, None)
        if not isinstance(numeric_level, int):
            raise ValueError(f'Invalid log level: {log_level}')
        self.logger.setLevel(numeric_level)
        handler = logging.StreamHandler()
        handler.setLevel(numeric_level)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)
        self.logger.info(f'Log level set to {log_level}')

    def _get_base_url(self, config):
        site_url = config.get('site_url', '')
        if not site_url:
            return ""
        site_url = site_url.rstrip('/')
        base_url = ""

        if site_url:
            parsed_url = site_url.split('//', 1)[-1]
            if "/" in parsed_url:
                base_url = "/" + parsed_url.split('/', 1)[1]

        return base_url.rstrip('/')

    def on_config(self, config, **kwargs):
        self._setup_logger()
        self.base_url = self._get_base_url(config)
        self.docs_dir = config['docs_dir']
        self.additional_index_folders = self.config['additional_index_folders']
        self.exclude_paths = self.config['exclude_paths']
        self.generate_home_index = self.config['generate_home_index']
        self.logger.info(f'Configuration: base_url={self.base_url}, additional_index_folders={self.additional_index_folders}, exclude_paths={self.exclude_paths}, generate_home_index={self.generate_home_index}')

    def on_files(self, files, config, **kwargs):
        self.logger.info(f'Generating index pages for docs_dir={self.docs_dir}')

        # Generate index pages for the main docs directory with exclusions and optional home index
        for dirpath, dirnames, filenames in os.walk(self.docs_dir):
            if self._is_path_excluded(dirpath):
                self.logger.debug(f'Skipping excluded path: {dirpath}')
                dirnames[:] = []  # Don't traverse any subdirectories
                continue

            if 'index.md' not in filenames:
                if self.generate_home_index or os.path.relpath(dirpath, self.docs_dir) != '.':
                    self.logger.debug(f'Generating index page for path={dirpath}')
                    self._generate_index_page(self.docs_dir, dirpath)

        # Generate index pages for specified additional index folders and move them to the docs directory
        for folder in self.additional_index_folders:
            self.logger.info(f'Generating index pages for additional folder={folder}')
            for dirpath, dirnames, filenames in os.walk(folder):
                if self._is_path_excluded(dirpath):
                    self.logger.debug(f'Skipping excluded path: {dirpath}')
                    dirnames[:] = []  # Don't traverse any subdirectories
                    continue

                if 'index.md' not in filenames:
                    self.logger.debug(f'Generating index page for additional folder path={dirpath}')
                    self._generate_index_page(folder, dirpath)
                    self._copy_all_to_docs(folder, dirpath)

    def _is_path_excluded(self, path):
        relative_path = os.path.relpath(path, self.docs_dir).replace(os.sep, '/')
        self.logger.debug(f'Checking if path is excluded: relative_path={relative_path}')
        for pattern in self.exclude_paths:
            normalized_pattern = pattern.replace('docs/', '', 1) if pattern.startswith('docs/') else pattern
            if fnmatch.fnmatch(relative_path, normalized_pattern):
                self.logger.debug(f'Excluding path={relative_path} based on pattern={pattern}')
                return True
        return False

    def _generate_index_page(self, docs_dir, dirpath):
        if self._is_path_excluded(dirpath):
            return
        relative_dir = os.path.relpath(dirpath, docs_dir)
        content_lines = [f"# Index of {relative_dir}", ""]
        base_url_part = f"{self.base_url}"

        for item in sorted(os.listdir(dirpath)):
            item_path = os.path.join(dirpath, item)
            if os.path.isdir(item_path):
                relative_item_path = os.path.join(relative_dir, item).replace("\\", "/")
                content_lines.append(f"- [{item}]({base_url_part}/{relative_item_path}/)")
                self._generate_index_page(docs_dir, item_path)  # Recursively generate index.md
            elif item.endswith(".md") and item != "index.md":
                item_name = os.path.splitext(item)[0]
                relative_item_path = os.path.join(relative_dir, item_name).replace("\\", "/")
                content_lines.append(f"- [{item_name}]({base_url_part}/{relative_item_path}/)")

        content = "\n".join(content_lines)
        index_path = os.path.join(dirpath, 'index.md')
        with open(index_path, 'w') as f:
            f.write(content)

        self.logger.info(f"Generated index page: {index_path}")

    def _copy_all_to_docs(self, base_folder, dirpath):
        """Recursively copy all files and subdirectories from the base folder to the corresponding docs directory."""
        for root, dirs, files in os.walk(dirpath):
            if self._is_path_excluded(root):
                self.logger.debug(f'Skipping excluded path: {root}')
                dirs[:] = []  # Don't traverse any subdirectories
                continue

            relative_path = os.path.relpath(root, base_folder)
            dest_dir = os.path.join(self.docs_dir, relative_path)
            self.logger.debug(f'Copying files from {root} to {dest_dir}')

            if not os.path.exists(dest_dir):
                os.makedirs(dest_dir)

            for file in files:
                src_file_path = os.path.join(root, file)
                dest_file_path = os.path.join(dest_dir, file)
                if self._is_path_excluded(dest_file_path):
                    self.logger.debug(f'Skipping excluded file: {dest_file_path}')
                    continue
                if os.path.exists(dest_file_path):
                    self.logger.debug(f'Skipping already present file: {dest_file_path}')
                else:
                    shutil.copy(src_file_path, dest_file_path)
                    self.logger.debug(f'Copied {src_file_path} to {dest_file_path}')

    def _cleanup_folder(self, folder):
        """Recursively delete a folder and its contents."""
        for root, dirs, files in os.walk(folder, topdown=False):
            for name in files:
                os.remove(os.path.join(root, name))
                self.logger.debug(f'Deleted file {os.path.join(root, name)}')
            for name in dirs:
                os.rmdir(os.path.join(root, name))
                self.logger.debug(f'Deleted directory {os.path.join(root, name)}')

    def on_page_markdown(self, markdown, page, config, files, **kwargs):
        breadcrumbs = []

        if self.config['use_page_titles']:
            breadcrumbs = self._generate_breadcrumbs_from_page_titles(page)
        else:
            breadcrumbs = self._generate_breadcrumbs_from_url(page)

        # Always prepend "Home" crumb
        home_breadcrumb = (
            f"[{self.config['home_text']}]({self.base_url}/)"
            if self.base_url else f"[{self.config['home_text']}](/)"
        )

        if breadcrumbs:
            breadcrumb_str = self.config['delimiter'].join(breadcrumbs)
            breadcrumb_str = home_breadcrumb + self.config['delimiter'] + breadcrumb_str
        else:
            breadcrumb_str = home_breadcrumb

        self.logger.info(f'Generated breadcrumb string: {breadcrumb_str}')
        return breadcrumb_str + "\n" + markdown

    def _generate_breadcrumbs_from_page_titles(self, page):
        breadcrumbs = []
        accumulated_path = []

        # Collect this page and all parents up to (but not including) the homepage
        current_page = page
        while current_page and getattr(current_page, 'is_homepage', False) is False:
            accumulated_path.insert(0, current_page)
            current_page = current_page.parent

        # If there is nothing but the homepage, just return normal markdown
        if not accumulated_path:
            home_breadcrumb = f"[{self.config['home_text']}]({self.base_url}/)" if self.base_url else f"[{self.config['home_text']}](/)"
            return [home_breadcrumb]

        # We’ll iterate through all items in the chain,
        # but handle the last item carefully.
        for i, part_page in enumerate(accumulated_path):
            is_last = (i == len(accumulated_path) - 1)

            # If it's the last item AND it's the actual page, skip adding it
            # because you only want up to the parent section in the breadcrumb.
            if is_last and part_page.is_page:
                continue

            # If it's a page, add it as a link
            if part_page.is_page:
                crumb_url = (f"{self.base_url}/{part_page.url}"
                            if self.base_url else f"/{part_page.url}")
                breadcrumbs.append(f"[{part_page.title}]({crumb_url})")

            # If it's a section, add it as plain text (no link)
            elif part_page.is_section:
                breadcrumbs.append(part_page.title)
        return breadcrumbs

    def _generate_breadcrumbs_from_url(self, page):
        breadcrumbs = []
        accumulated_path = []

        # Show/link to the URL path splits
        path_parts = page.url.strip("/").split("/")
        for part in path_parts[:-1]:
            accumulated_path.append(part)
            current_path = "/".join(accumulated_path)
            if self.base_url:
                crumb_url = f"{self.base_url}/{current_path}/"
            else:
                crumb_url = f"/{current_path}/"
            
            title = unquote(part)
            breadcrumbs.append(f"[{title}]({crumb_url})")
            self.logger.debug(f'Added breadcrumb: {title} with URL: {crumb_url}')
        return breadcrumbs
