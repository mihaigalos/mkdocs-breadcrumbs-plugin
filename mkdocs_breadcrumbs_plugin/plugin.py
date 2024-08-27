import os
import shutil
import logging
import fnmatch
from mkdocs.config import config_options
from mkdocs.plugins import BasePlugin
from urllib.parse import unquote
from mkdocs.structure.files import File

class BreadCrumbs(BasePlugin):

    config_scheme = (
        ('log_level', config_options.Type(str, default='INFO')),
        ('delimiter', config_options.Type(str, default=' / ')),
        ('base_url', config_options.Type(str, default='')),
        ('exclude_paths', config_options.Type(list, default=['docs/mkdocs/**', 'docs/index.md'])),
        ('additional_index_folders', config_options.Type(list, default=[])),
        ('generate_home_index', config_options.Type(bool, default=True)),
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

        try:
            # Ensure additional_index_folders are created or moved as needed
            for folder in self.additional_index_folders:
                self.logger.info(f'Handling additional folders: {folder}')
                for dirpath, dirnames, filenames in os.walk(folder):
                    if not self._is_path_excluded(dirpath):
                        self._generate_index_page(folder, dirpath)
                    self._copy_all_to_docs(folder, dirpath, files, config)

            # Generate index pages for the main docs directory with exclusions and optional home index
            for dirpath, dirnames, filenames in os.walk(self.docs_dir):
                if self._is_path_excluded(dirpath):
                    self.logger.debug(f'Skipping excluded path: {dirpath}')
                    dirnames[:] = []  # Don't traverse any subdirectories
                    continue

                # Ensure docs/index.md is handled properly
                if 'index.md' not in filenames and not self.generate_home_index:
                    self.logger.debug(f'Generating home index page for docs_dir')
                    self._generate_index_page(self.docs_dir, self.docs_dir)

                if 'index.md' not in filenames or os.path.relpath(dirpath, self.docs_dir) != '.':
                    self.logger.debug(f'Generating index page for path={dirpath}')
                    self._generate_index_page(self.docs_dir, dirpath)

            # Filter out excluded files from the files collection
            files._files = [
                file for file in files._files if not self._is_path_excluded(file.abs_src_path)
            ]

        finally:
            # Cleanup additional index folders
            for folder in self.additional_index_folders:
                self.logger.info(f'Cleaning up additional folder={folder}')
                self._cleanup_folder(folder)

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
            item_relative_path = os.path.join(relative_dir, item).replace("\\", "/")
            if os.path.isdir(item_path):
                content_lines.append(f"- [{item}]({base_url_part}/{item_relative_path}/)")
                self._generate_index_page(docs_dir, item_path)  # Recursively generate index.md
            elif item.endswith(".md") and item != "index.md":
                item_name = os.path.splitext(item)[0]
                content_lines.append(f"- [{item_name}]({base_url_part}/{item_relative_path}/)")

        content = "\n".join(content_lines)
        if not self._is_path_excluded(os.path.join(dirpath, 'index.md')):
            index_path = os.path.join(dirpath, 'index.md')
            with open(index_path, 'w') as f:
                f.write(content)
            self.logger.info(f"Generated index page: {index_path}")

    def _copy_all_to_docs(self, base_folder, dirpath, files, config):
        """Recursively copy all files and subdirectories from the base folder to the corresponding docs directory.
           Also update the files collection accordingly.
        """
        for root, dirs, files_list in os.walk(dirpath):
            if self._is_path_excluded(root):
                self.logger.debug(f'Skipping excluded path: {root}')
                dirs[:] = []  # Don't traverse any subdirectories
                continue

            relative_path = os.path.relpath(root, base_folder)
            dest_dir = os.path.join(self.docs_dir, relative_path)
            self.logger.debug(f'Copying files from {root} to {dest_dir}')

            if not os.path.exists(dest_dir):
                os.makedirs(dest_dir)

            for file in files_list:
                src_file_path = os.path.join(root, file)
                dest_file_path = os.path.join(dest_dir, file)
                if self._is_path_excluded(dest_file_path):
                    self.logger.debug(f'Skipping excluded file: {dest_file_path}')
                    continue
                if os.path.exists(src_file_path):  # Ensure the source file exists
                    shutil.copy(src_file_path, dest_file_path)
                    self.logger.debug(f'Copied {src_file_path} to {dest_file_path}')
                    if not self._is_path_excluded(dest_file_path):
                        page_file = File(
                            os.path.relpath(dest_file_path, self.docs_dir),
                            self.docs_dir,
                            config['site_dir'],
                            config['use_directory_urls']
                        )
                        files.append(page_file)

    def _cleanup_folder(self, folder):
        """Recursively delete a folder and its contents."""
        for root, dirs, files in os.walk(folder, topdown=False):
            for name in files:
                try:
                    os.remove(os.path.join(root, name))
                    self.logger.debug(f'Deleted file {os.path.join(root, name)}')
                except FileNotFoundError:
                    self.logger.debug(f'File not found during deletion: {os.path.join(root, name)}')
            for name in dirs:
                try:
                    os.rmdir(os.path.join(root, name))
                    self.logger.debug(f'Deleted directory {os.path.join(root, name)}')
                except FileNotFoundError:
                    self.logger.debug(f'Directory not found during deletion: {os.path.join(root, name)}')

    def on_page_markdown(self, markdown, page, config, files, **kwargs):
        breadcrumbs = []
        path_parts = page.url.strip("/").split("/")
        accumulated_path = []

        for part in path_parts[:-1]:
            accumulated_path.append(part)
            current_path = "/".join(accumulated_path)
            if self.base_url:
                crumb_url = f"{self.base_url}/{current_path}/"
            else:
                crumb_url = f"/{current_path}/"
            breadcrumbs.append(f"[{unquote(part)}]({crumb_url})")
            self.logger.debug(f'Added breadcrumb: {unquote(part)} with URL: {crumb_url}')

        current_page = path_parts[-1].replace('.md', '')
        if current_page:
            breadcrumbs.append(unquote(current_page))
            self.logger.debug(f'Added current page breadcrumb: {unquote(current_page)}')

        home_breadcrumb = f"[Home]({self.base_url}/)" if self.base_url else "[Home](/)"
        if breadcrumbs:
            breadcrumb_str = self.config['delimiter'].join(breadcrumbs)
            breadcrumb_str = home_breadcrumb + self.config['delimiter'] + breadcrumb_str
        else:
            breadcrumb_str = home_breadcrumb

        self.logger.info(f'Generated breadcrumb string: {breadcrumb_str}')
        return breadcrumb_str + "\n" + markdown


