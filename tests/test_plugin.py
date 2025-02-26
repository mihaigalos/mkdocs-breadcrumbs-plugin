from mkdocs_breadcrumbs_plugin.plugin import BreadCrumbs
import os
import sys
import unittest
import logging
from unittest import mock
from copy import deepcopy

# Modify path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import after path modification


class TestBreadcrumbsPlugin(unittest.TestCase):
    def setUp(self):
        """Set up test fixtures before each test method."""
        self.plugin = BreadCrumbs()

        # Mock MkDocs config
        self.mkdocs_config = {
            "site_name": "Test Site",
            "site_url": "http://example.com/",
            "docs_dir": "docs",
        }

        # Default plugin config - adjusted to match actual plugin options
        self.default_config = {
            "home_text": "Home",
            "delimiter": " / ",
            "base_url": "",
            "exclude_paths": ["docs/mkdocs/**", "docs/index.md"],
            "additional_index_folders": [],
            "generate_home_index": True,
            "use_page_titles": False,
            "log_level": "INFO",
        }

        # Create a mock page
        self.page = mock.MagicMock()
        self.page.title = "Test Page"
        self.page.url = "test-page/"
        self.page.file.src_path = "test-page.md"
        self.page.is_homepage = False
        self.page.is_page = True
        self.page.is_section = False
        self.page.parent = None

        # Suppress actual logging during tests
        logging.disable(logging.CRITICAL)

    def tearDown(self):
        # Re-enable logging
        logging.disable(logging.NOTSET)

    def test_on_page_markdown(self):
        """Test plugin behavior with default configuration."""
        # Configure the plugin with defaults
        self.plugin.config = deepcopy(self.default_config)
        self.plugin.on_config(self.mkdocs_config)

        # Test the breadcrumbs generation
        markdown = "# Test Content"
        result = self.plugin.on_page_markdown(
            markdown, self.page, self.mkdocs_config, None
        )

        # Should contain home link and page link
        self.assertIn("[Home](/)", result)
        self.assertIn("[test-page](/test-page)", result)
        self.assertIn(self.default_config["delimiter"], result)
        self.assertIn(markdown, result)

    def test_custom_home_text(self):
        """Test plugin with custom home text."""
        # Configure with custom home text
        custom_config = deepcopy(self.default_config)
        custom_config["home_text"] = "Start"
        self.plugin.config = custom_config
        self.plugin.on_config(self.mkdocs_config)

        # Test the breadcrumbs generation
        markdown = "# Test Content"
        result = self.plugin.on_page_markdown(
            markdown, self.page, self.mkdocs_config, None
        )

        # Should contain custom home text
        self.assertIn("[Start](/)", result)

    def test_with_page_titles(self):
        """Test plugin with use_page_titles=True."""
        # Configure with use_page_titles=True
        custom_config = deepcopy(self.default_config)
        custom_config["use_page_titles"] = True
        self.plugin.config = custom_config
        self.plugin.on_config(self.mkdocs_config)

        # Create a mock page hierarchy
        parent_page = mock.MagicMock()
        parent_page.title = "Parent Section"
        parent_page.url = "parent-section/"
        parent_page.is_homepage = False
        parent_page.is_page = True
        parent_page.is_section = False
        parent_page.parent = None

        self.page.parent = parent_page

        # Test the breadcrumbs generation
        markdown = "# Test Content"
        result = self.plugin.on_page_markdown(
            markdown, self.page, self.mkdocs_config, None
        )

        # Should contain home link and parent page title
        self.assertIn("[Home](/)", result)
        self.assertIn("[Parent Section](/parent-section/)", result)

    def test_is_path_excluded(self):
        """Test path exclusion functionality."""
        self.plugin.config = deepcopy(self.default_config)
        self.plugin.on_config(self.mkdocs_config)

        # Test excluded paths
        self.plugin.exclude_paths = ["test_dir/**"]
        self.plugin.docs_dir = "/tmp/docs"

        # Should be excluded
        self.assertTrue(self.plugin._is_path_excluded("/tmp/docs/test_dir/file.md"))
        self.assertTrue(
            self.plugin._is_path_excluded("/tmp/docs/test_dir/subdir/file.md")
        )

        # Should not be excluded
        self.assertFalse(self.plugin._is_path_excluded("/tmp/docs/other_dir/file.md"))

    def test_custom_delimiter(self):
        """Test plugin with custom delimiter."""
        custom_config = deepcopy(self.default_config)
        custom_config["delimiter"] = " > "
        self.plugin.config = custom_config
        self.plugin.on_config(self.mkdocs_config)

        markdown = "# Test Content"
        result = self.plugin.on_page_markdown(
            markdown, self.page, self.mkdocs_config, None
        )

        self.assertIn("[Home](/)", result)
        self.assertIn(" > ", result)  # Custom delimiter
        self.assertNotIn(" / ", result)  # Default delimiter should not be present

    def test_base_url(self):
        """Test plugin with custom base_url."""
        custom_config = deepcopy(self.default_config)
        custom_config["base_url"] = "/docs"
        self.plugin.config = custom_config
        self.plugin.on_config(self.mkdocs_config)
        self.plugin.base_url = "/docs"  # Manually set as it's usually done in on_config

        markdown = "# Test Content"
        result = self.plugin.on_page_markdown(
            markdown, self.page, self.mkdocs_config, None
        )

        self.assertIn("[Home](/docs/)", result)
        self.assertIn("[test-page](/docs/test-page)", result)

    def test_homepage_handling(self):
        """Test plugin behavior with homepage."""
        self.plugin.config = deepcopy(self.default_config)
        self.plugin.on_config(self.mkdocs_config)

        # Set up a homepage mock
        homepage = mock.MagicMock()
        homepage.title = "Home Page"
        homepage.url = ""
        homepage.file.src_path = "index.md"
        homepage.is_homepage = True
        homepage.is_page = True
        homepage.is_section = False
        homepage.parent = None

        markdown = "# Homepage Content"
        result = self.plugin.on_page_markdown(
            markdown, homepage, self.mkdocs_config, None
        )

        # Should contain only the home link without additional breadcrumbs
        self.assertIn("[Home](/)", result)

        # Verify no delimiter or additional breadcrumbs are present
        self.assertNotIn(" / ", result)

        # Verify exact structure
        expected_structure = "[Home](/)\n# Homepage Content"
        self.assertEqual(result, expected_structure)

    def test_section_page_with_titles(self):
        """Test plugin with a section page using page titles."""
        custom_config = deepcopy(self.default_config)
        custom_config["use_page_titles"] = True
        self.plugin.config = custom_config
        self.plugin.on_config(self.mkdocs_config)

        # Create a section page
        section_page = mock.MagicMock()
        section_page.title = "Section Title"
        section_page.url = "section/"
        section_page.file.src_path = "section/index.md"
        section_page.is_homepage = False
        section_page.is_page = False  # Not a regular page
        section_page.is_section = True  # It's a section
        section_page.parent = None

        markdown = "# Section Content"
        result = self.plugin.on_page_markdown(
            markdown, section_page, self.mkdocs_config, None
        )

        self.assertIn("[Home](/)", result)
        # Check if section is rendered correctly based on implementation
        # This depends on how sections are handled in _generate_breadcrumbs_from_page_titles

    def test_nested_pages_url_based(self):
        """Test plugin with nested pages using URL-based breadcrumbs."""
        self.plugin.config = deepcopy(self.default_config)
        self.plugin.config["use_page_titles"] = False  # Ensure URL-based
        self.plugin.on_config(self.mkdocs_config)

        # Create a page with a nested URL
        nested_page = mock.MagicMock()
        nested_page.title = "Nested Page"
        nested_page.url = "parent/child/nested-page/"
        nested_page.file.src_path = "parent/child/nested-page.md"
        nested_page.is_homepage = False
        nested_page.is_page = True
        nested_page.is_section = False
        nested_page.parent = None

        markdown = "# Nested Content"
        result = self.plugin.on_page_markdown(
            markdown, nested_page, self.mkdocs_config, None
        )

        self.assertIn("[Home](/)", result)
        self.assertIn("[parent](/parent)", result)
        self.assertIn("[child](/parent/child)", result)
        self.assertIn("[nested-page](/parent/child/nested-page)", result)


if __name__ == "__main__":
    unittest.main()
