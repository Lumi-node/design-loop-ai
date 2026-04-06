"""Tests for main.py module - initial HTML generation functionality.

Tests the generate_initial_html() function with spec_initial.json to verify:
- Function creates iteration_0.html at expected location
- Generated HTML contains valid structure (html, body tags)
- CSS is properly embedded in head section
- Colors and layout from spec are reflected in output
"""

import os
import json
import pytest
from pathlib import Path
from bs4 import BeautifulSoup

# Import functions to test
from main import generate_initial_html, load_initial_spec


class TestGenerateInitialHtml:
    """Test suite for generate_initial_html() function."""

    @pytest.fixture
    def spec_dict(self):
        """Fixture providing a valid design spec."""
        return {
            'layout_regions': {
                'header_height_percent': 8,
                'content_width_percent': 70,
                'footer_height_percent': 8,
                'sidebar_width_percent': 30
            },
            'colors': {
                'header': ['#AAAAAA'],
                'sidebar': ['#888888'],
                'content': ['#FFFFFF'],
                'footer': ['#AAAAAA']
            }
        }

    @pytest.fixture
    def cleanup_iteration_0(self):
        """Fixture to clean up iteration_0.html after test."""
        yield
        # Cleanup after test
        iteration_0_path = os.path.join('examples', 'iteration_0.html')
        if os.path.exists(iteration_0_path):
            os.remove(iteration_0_path)

    def test_generate_initial_html_returns_string(self, spec_dict, cleanup_iteration_0):
        """Test that generate_initial_html returns a string path."""
        result = generate_initial_html(spec_dict)
        assert isinstance(result, str), "generate_initial_html must return a string"

    def test_generate_initial_html_returns_correct_path(self, spec_dict, cleanup_iteration_0):
        """Test that function returns path to iteration_0.html."""
        result = generate_initial_html(spec_dict)
        assert result.endswith('iteration_0.html'), \
            "Path must end with 'iteration_0.html'"
        assert 'examples' in result, "Path must contain 'examples' directory"

    def test_generate_initial_html_creates_file(self, spec_dict, cleanup_iteration_0):
        """Test that iteration_0.html is created on disk."""
        path = generate_initial_html(spec_dict)
        assert os.path.exists(path), f"File must exist at {path}"

    def test_generate_initial_html_file_is_readable(self, spec_dict, cleanup_iteration_0):
        """Test that created iteration_0.html is readable."""
        path = generate_initial_html(spec_dict)
        assert os.access(path, os.R_OK), f"File must be readable: {path}"

    def test_generate_initial_html_file_is_not_empty(self, spec_dict, cleanup_iteration_0):
        """Test that iteration_0.html contains content."""
        path = generate_initial_html(spec_dict)
        file_size = os.path.getsize(path)
        assert file_size > 0, f"File must not be empty (size: {file_size})"

    def test_generate_initial_html_contains_html_tag(self, spec_dict, cleanup_iteration_0):
        """Test that generated HTML contains <html> and </html> tags."""
        path = generate_initial_html(spec_dict)
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()

        assert '<html>' in content.lower(), "HTML must contain <html> tag"
        assert '</html>' in content.lower(), "HTML must contain </html> tag"

    def test_generate_initial_html_contains_body_tag(self, spec_dict, cleanup_iteration_0):
        """Test that generated HTML contains <body> tags."""
        path = generate_initial_html(spec_dict)
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()

        assert '<body' in content.lower(), "HTML must contain <body> tag"
        assert '</body>' in content.lower(), "HTML must contain closing </body> tag"

    def test_generate_initial_html_contains_style_in_head(self, spec_dict, cleanup_iteration_0):
        """Test that CSS is embedded in <head> section."""
        path = generate_initial_html(spec_dict)
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Parse HTML
        soup = BeautifulSoup(content, 'html.parser')

        # Check for style tag in head
        head = soup.find('head')
        assert head is not None, "HTML must have <head> section"

        style_tag = head.find('style')
        assert style_tag is not None, "<head> must contain <style> tag"

        # Verify style tag has content
        style_content = style_tag.string
        assert style_content is not None, "<style> tag must have content"
        assert len(style_content.strip()) > 0, "<style> tag must not be empty"

    def test_generate_initial_html_contains_color_from_spec(self, spec_dict, cleanup_iteration_0):
        """Test that colors from spec appear in generated HTML."""
        path = generate_initial_html(spec_dict)
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Check that colors from spec are mentioned in CSS
        # The colors appear in background-color properties
        for region, color_list in spec_dict['colors'].items():
            for color in color_list:
                # Convert hex to rgb() format (what generate_css produces)
                hex_color = color.lstrip('#')
                r = int(hex_color[0:2], 16)
                g = int(hex_color[2:4], 16)
                b = int(hex_color[4:6], 16)
                rgb_string = f'rgb({r}, {g}, {b})'

                assert rgb_string in content, \
                    f"Generated HTML must contain color {rgb_string} from spec"

    def test_generate_initial_html_contains_layout_regions(self, spec_dict, cleanup_iteration_0):
        """Test that layout regions from spec are reflected in HTML."""
        path = generate_initial_html(spec_dict)
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()

        soup = BeautifulSoup(content, 'html.parser')

        # Verify region classes are present
        for region_class in ['header', 'sidebar', 'content', 'footer']:
            element = soup.find(class_=region_class)
            assert element is not None, \
                f"HTML must contain div with class='{region_class}'"

    def test_generate_initial_html_with_invalid_spec_raises_error(self, cleanup_iteration_0):
        """Test that invalid spec raises ValueError."""
        # Missing layout_regions
        bad_spec1 = {'colors': {}}
        with pytest.raises(ValueError):
            generate_initial_html(bad_spec1)

        # Missing colors
        bad_spec2 = {'layout_regions': {}}
        with pytest.raises(ValueError):
            generate_initial_html(bad_spec2)

        # Not a dict
        with pytest.raises(ValueError):
            generate_initial_html("not a dict")

    def test_generate_initial_html_with_complex_spec(self, cleanup_iteration_0):
        """Test with different color values."""
        spec = {
            'layout_regions': {
                'header_height_percent': 10,
                'content_width_percent': 75,
                'footer_height_percent': 10,
                'sidebar_width_percent': 25
            },
            'colors': {
                'header': ['#FF0000'],  # Red
                'sidebar': ['#00FF00'],  # Green
                'content': ['#0000FF'],  # Blue
                'footer': ['#FFFF00']    # Yellow
            }
        }

        path = generate_initial_html(spec)
        assert os.path.exists(path), "File must be created"

        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Verify colors are in RGB format
        assert 'rgb(255, 0, 0)' in content  # Red
        assert 'rgb(0, 255, 0)' in content  # Green
        assert 'rgb(0, 0, 255)' in content  # Blue
        assert 'rgb(255, 255, 0)' in content  # Yellow

    def test_generate_initial_html_with_spec_initial_json(self, cleanup_iteration_0):
        """Test with actual spec_initial.json file."""
        try:
            spec = load_initial_spec('examples/spec_initial.json')
            path = generate_initial_html(spec)

            assert os.path.exists(path), "File must be created from spec_initial.json"
            assert os.path.getsize(path) > 0, "File must not be empty"

            with open(path, 'r', encoding='utf-8') as f:
                content = f.read()

            # Basic validation
            assert '<html>' in content.lower()
            assert '<body' in content.lower()
            assert '<style>' in content.lower()
        except FileNotFoundError:
            # Skip if spec_initial.json doesn't exist yet
            pytest.skip("spec_initial.json not found")

    def test_generate_initial_html_file_is_absolute_path(self, spec_dict, cleanup_iteration_0):
        """Test that returned path is absolute."""
        path = generate_initial_html(spec_dict)
        assert os.path.isabs(path), "Returned path must be absolute"

    def test_generate_initial_html_creates_valid_structure(self, spec_dict, cleanup_iteration_0):
        """Test that HTML structure is valid and parseable."""
        path = generate_initial_html(spec_dict)
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Parse with BeautifulSoup to verify validity
        soup = BeautifulSoup(content, 'html.parser')

        # Verify basic structure
        assert soup.find('html') is not None
        assert soup.find('head') is not None
        assert soup.find('body') is not None
        assert soup.find('style') is not None


class TestLoadInitialSpec:
    """Test suite for load_initial_spec() helper function."""

    def test_load_initial_spec_from_examples(self):
        """Test loading spec_initial.json from examples directory."""
        try:
            spec = load_initial_spec('examples/spec_initial.json')
            assert isinstance(spec, dict)
            assert 'layout_regions' in spec
            assert 'colors' in spec
        except FileNotFoundError:
            pytest.skip("spec_initial.json not found")

    def test_load_initial_spec_raises_on_missing_file(self):
        """Test that missing spec file raises FileNotFoundError."""
        with pytest.raises(FileNotFoundError):
            load_initial_spec('nonexistent/spec.json')

    def test_load_initial_spec_raises_on_invalid_json(self, tmp_path):
        """Test that invalid JSON raises JSONDecodeError."""
        invalid_json_file = tmp_path / "invalid.json"
        invalid_json_file.write_text("{invalid json content")

        with pytest.raises(json.JSONDecodeError):
            load_initial_spec(str(invalid_json_file))

    def test_load_initial_spec_validates_structure(self, tmp_path):
        """Test that missing required keys raises ValueError."""
        incomplete_spec_file = tmp_path / "incomplete.json"
        incomplete_spec_file.write_text('{"layout_regions": {}}')

        with pytest.raises(ValueError):
            load_initial_spec(str(incomplete_spec_file))
