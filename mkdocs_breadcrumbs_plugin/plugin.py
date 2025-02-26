import os
import shutil
import logging
import fnmatch
from mkdocs.config import config_options
from mkdocs.plugins import BasePlugin
from urllib.parse import unquote


class BreadCrumbs(BasePlugin):

    config_scheme = (
        ("log_level", config_options.Type(str, default="INFO")),
        ("delimiter", config_options.Type(str, default=" / ")),
        ("base_url", config_options.Type(str, default="")),
        (
            "exclude_paths",
            config_options.Type(list, default=["docs/mkdocs/**", "docs/index.md"]),
        ),
        ("additional_index_folders", config_options.Type(list, default=[])),
        ("generate_home_index", config_options.Type(bool, default=True)),
        ("use_page_titles", config_options.Type(bool, default=False)),
        ("home_text", config_options.Type(str, default="Home")),
    )

    def _setup_logger(self):
        self.logger = logging.getLogger("mkdocs.plugins.breadcrumbs")
        log_level = self.config["log_level"].upper()
        numeric_level = getattr(logging, log_level, None)
        if not isinstance(numeric_level, int):
            raise ValueError(f"Invalid log level: {log_level}")
        self.logger.setLevel(numeric_level)
        handler = logging.StreamHandler()
        handler.setLevel(numeric_level)
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)
        self.logger.info(f"Log level set to {log_level}")

    def _get_base_url(self, config):
        site_url = config.get("site_url", "").rstrip("/")
        if not site_url:
            return ""
        parsed_url = site_url.split("//", 1)[-1]
        base_url = "/" + parsed_url.split("/", 1)[1] if "/" in parsed_url else ""
        return base_url.rstrip("/")

    def on_config(self, config, **kwargs):
        self._setup_logger()
        self.base_url = self._get_base_url(config)
        self.docs_dir = config["docs_dir"]
        self.additional_index_folders = self.config["additional_index_folders"]
        self.exclude_paths = self.config["exclude_paths"]
        self.generate_home_index = self.config["generate_home_index"]
        self.logger.info(
            f"Configuration: base_url={self.base_url}, "
            f"additional_index_folders={self.additional_index_folders}, "
            f"exclude_paths={self.exclude_paths}, "
            f"generate_home_index={self.generate_home_index}"
        )

    def on_files(self, files, config, **kwargs):
        self.logger.info(f"Generating index pages for docs_dir={self.docs_dir}")
        self._generate_index_pages(self.docs_dir)
        for folder in self.additional_index_folders:
            self.logger.info(f"Generating index pages for additional folder={folder}")
            self._generate_index_pages(folder, move_to_docs=True)

    def _generate_index_pages(self, base_folder, move_to_docs=False):
        for dirpath, dirnames, filenames in os.walk(base_folder):
            if self._is_path_excluded(dirpath):
                self.logger.debug(f"Skipping excluded path: {dirpath}")
                dirnames[:] = []  # Don't traverse any subdirectories
                continue

            if "index.md" not in filenames:
                self.logger.debug(f"Generating index page for path={dirpath}")
                self._generate_index_page(base_folder, dirpath)
                if move_to_docs:
                    self._copy_all_to_docs(base_folder, dirpath)

    def _is_path_excluded(self, path):
        relative_path = os.path.relpath(path, self.docs_dir).replace(os.sep, "/")
        self.logger.debug(
            f"Checking if path is excluded: relative_path={relative_path}"
        )
        for pattern in self.exclude_paths:
            normalized_pattern = (
                pattern.replace("docs/", "", 1)
                if pattern.startswith("docs/")
                else pattern
            )
            if fnmatch.fnmatch(relative_path, normalized_pattern):
                self.logger.debug(
                    f"Excluding path={relative_path} based on pattern={pattern}"
                )
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
                content_lines.append(
                    f"- [{item}]({base_url_part}/{relative_item_path}/)"
                )
                # Recursively generate index.md
                self._generate_index_page(docs_dir, item_path)
            elif item.endswith(".md") and item != "index.md":
                item_name = os.path.splitext(item)[0]
                relative_item_path = os.path.join(relative_dir, item_name).replace(
                    "\\", "/"
                )
                content_lines.append(
                    f"- [{item_name}]({base_url_part}/{relative_item_path}/)"
                )

        content = "\n".join(content_lines)
        index_path = os.path.join(dirpath, "index.md")
        with open(index_path, "w") as f:
            f.write(content)

        self.logger.info(f"Generated index page: {index_path}")

    def _copy_all_to_docs(self, base_folder, dirpath):
        """Recursively copy all files and subdirectories from the base folder to
        the corresponding docs directory."""
        for root, dirs, files in os.walk(dirpath):
            if self._is_path_excluded(root):
                self.logger.debug(f"Skipping excluded path: {root}")
                dirs[:] = []  # Don't traverse any subdirectories
                continue

            relative_path = os.path.relpath(root, base_folder)
            dest_dir = os.path.join(self.docs_dir, relative_path)
            self.logger.debug(f"Copying files from {root} to {dest_dir}")

            if not os.path.exists(dest_dir):
                os.makedirs(dest_dir)

            for file in files:
                src_file_path = os.path.join(root, file)
                dest_file_path = os.path.join(dest_dir, file)
                if self._is_path_excluded(dest_file_path):
                    self.logger.debug(f"Skipping excluded file: {dest_file_path}")
                    continue
                if os.path.exists(dest_file_path):
                    self.logger.debug(
                        f"Skipping already present file: {dest_file_path}"
                    )
                else:
                    shutil.copy(src_file_path, dest_file_path)
                    self.logger.debug(f"Copied {src_file_path} to {dest_file_path}")

    def _cleanup_folder(self, folder):
        """Recursively delete a folder and its contents."""
        for root, dirs, files in os.walk(folder, topdown=False):
            for name in files:
                os.remove(os.path.join(root, name))
                self.logger.debug(f"Deleted file {os.path.join(root, name)}")
            for name in dirs:
                os.rmdir(os.path.join(root, name))
                self.logger.debug(f"Deleted directory {os.path.join(root, name)}")

    def on_page_markdown(self, markdown, page, config, files, **kwargs):
        home_breadcrumb = (
            f"[{self.config['home_text']}]({self.base_url}/)"
            if self.base_url
            else f"[{self.config['home_text']}](/)"
        )

        # For homepage, only include the home link without additional breadcrumbs
        if getattr(page, "is_homepage", False):
            breadcrumb_str = home_breadcrumb
        else:
            # For other pages, generate and include additional breadcrumbs
            breadcrumbs = self._generate_breadcrumbs(page)
            breadcrumb_str = home_breadcrumb + (
                self.config["delimiter"] + self.config["delimiter"].join(breadcrumbs)
                if breadcrumbs
                else ""
            )

        self.logger.info(f"Generated breadcrumb string: {breadcrumb_str}")
        return breadcrumb_str + "\n" + markdown

    def _generate_breadcrumbs(self, page):
        if self.config["use_page_titles"]:
            return self._generate_breadcrumbs_from_page_titles(page)
        return self._generate_breadcrumbs_from_url(page)

    def _generate_breadcrumbs_from_page_titles(self, page):
        breadcrumbs = []
        accumulated_path = []

        current_page = page
        while current_page and getattr(current_page, "is_homepage", False) is False:
            accumulated_path.insert(0, current_page)
            current_page = current_page.parent

        if not accumulated_path:
            return []

        for i, part_page in enumerate(accumulated_path):
            is_last = i == len(accumulated_path) - 1
            if is_last and part_page.is_page:
                continue
            if part_page.is_page:
                crumb_url = (
                    f"{self.base_url}/{part_page.url}"
                    if self.base_url
                    else f"/{part_page.url}"
                )
                breadcrumbs.append(f"[{part_page.title}]({crumb_url})")
            elif part_page.is_section:
                breadcrumbs.append(part_page.title)
        return breadcrumbs

    def _generate_breadcrumbs_from_url(self, page):
        breadcrumbs = []
        accumulated_path = []

        path_parts = page.url.strip("/").split("/")
        for part in path_parts:
            accumulated_path.append(part)
            current_path = "/".join(accumulated_path)
            crumb_url = (
                f"{self.base_url}/{current_path}"
                if self.base_url
                else f"/{current_path}"
            )
            title = unquote(part)
            breadcrumbs.append(f"[{title}]({crumb_url})")
            self.logger.debug(f"Added breadcrumb: {title} with URL: {crumb_url}")
        return breadcrumbs
