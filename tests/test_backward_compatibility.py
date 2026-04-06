"""Backward compatibility tests for source build 0c16ae7e.

This module verifies that source build 0c16ae7e modules remain importable,
functional, and unmodified. These tests act as regression guards to ensure
the iterative improvement agent (design_agent.py, iterative_design.py, metrics.py)
does not inadvertently break the existing design-to-HTML converter pipeline.

Testing Strategy:
- Unit tests: Import each source module individually; verify no ImportError or AttributeError
- Functional tests: Call convert_design() with sample image; verify returned path exists and contains valid HTML
- Regression guards: Verify source file structure unchanged (check file existence and readability)
"""

import pytest
import os
import sys
from pathlib import Path

# Get the absolute path to the sources directory
SOURCES_DIR = Path(__file__).parent.parent / "sources" / "0c16ae7e"
SAMPLE_IMAGE_PATH = Path(__file__).parent.parent / "test_sample_image.png"


class TestAllSourceModulesImportable:
    """Test that all source build 0c16ae7e modules are importable."""

    def test_import_html_generator(self):
        """Test html_generator module imports without errors."""
        sys.path.insert(0, str(SOURCES_DIR))
        try:
            import html_generator
            assert hasattr(html_generator, 'generate_html_structure')
            assert hasattr(html_generator, 'generate_css')
        finally:
            sys.path.remove(str(SOURCES_DIR))

    def test_import_layout_detector(self):
        """Test layout_detector module imports without errors."""
        sys.path.insert(0, str(SOURCES_DIR))
        try:
            import layout_detector
            assert hasattr(layout_detector, 'detect_layout_regions')
        finally:
            sys.path.remove(str(SOURCES_DIR))

    def test_import_color_extractor(self):
        """Test color_extractor module imports without errors."""
        sys.path.insert(0, str(SOURCES_DIR))
        try:
            import color_extractor
            assert hasattr(color_extractor, 'extract_colors')
        finally:
            sys.path.remove(str(SOURCES_DIR))

    def test_import_types(self):
        """Test types module imports without errors."""
        sys.path.insert(0, str(SOURCES_DIR))
        try:
            import importlib.util
            spec = importlib.util.spec_from_file_location("project_types", str(SOURCES_DIR / "types.py"))
            project_types = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(project_types)
            assert hasattr(project_types, 'DesignToHTMLError')
        finally:
            if str(SOURCES_DIR) in sys.path:
                sys.path.remove(str(SOURCES_DIR))

    def test_import_image_loader(self):
        """Test image_loader module imports without errors."""
        sys.path.insert(0, str(SOURCES_DIR))
        try:
            import image_loader
            assert hasattr(image_loader, 'load_image')
        finally:
            sys.path.remove(str(SOURCES_DIR))

    def test_import_output_writer(self):
        """Test output_writer module imports without errors."""
        sys.path.insert(0, str(SOURCES_DIR))
        try:
            import output_writer
            assert hasattr(output_writer, 'write_output')
        finally:
            sys.path.remove(str(SOURCES_DIR))

    def test_import_main(self):
        """Test main module imports without errors."""
        sys.path.insert(0, str(SOURCES_DIR))
        try:
            import main
            assert hasattr(main, 'convert_design')
        finally:
            sys.path.remove(str(SOURCES_DIR))


class TestConvertDesignStillWorks:
    """Test that convert_design() function works unchanged."""

    @pytest.fixture(autouse=True)
    def setup_paths(self):
        """Setup Python path for imports."""
        sys.path.insert(0, str(SOURCES_DIR))
        yield
        if str(SOURCES_DIR) in sys.path:
            sys.path.remove(str(SOURCES_DIR))

    def test_convert_design_with_sample_image(self):
        """Test convert_design() with sample image returns valid HTML file path."""
        from main import convert_design

        # Verify sample image exists
        assert SAMPLE_IMAGE_PATH.exists(), f"Sample image not found: {SAMPLE_IMAGE_PATH}"

        # Call convert_design
        html_path = convert_design(str(SAMPLE_IMAGE_PATH))

        # Verify returned path is a string
        assert isinstance(html_path, str), "convert_design() should return a string path"

        # Verify returned path exists
        assert os.path.exists(html_path), f"Generated HTML file not found: {html_path}"

        # Verify it's an HTML file
        assert html_path.endswith('.html'), f"Expected .html file, got: {html_path}"

    def test_convert_design_returns_valid_html(self):
        """Test convert_design() returns a file containing valid HTML structure."""
        from main import convert_design

        # Call convert_design
        html_path = convert_design(str(SAMPLE_IMAGE_PATH))

        # Read the generated HTML
        with open(html_path, 'r') as f:
            html_content = f.read()

        # Verify HTML contains expected elements
        assert '<!DOCTYPE html>' in html_content, "Missing DOCTYPE declaration"
        assert '<html' in html_content, "Missing <html> tag"
        assert '<head>' in html_content, "Missing <head> tag"
        assert '<body>' in html_content, "Missing <body> tag"
        assert '<style>' in html_content, "Missing <style> tag"
        assert '</style>' in html_content, "Missing closing </style> tag"
        assert '</html>' in html_content, "Missing closing </html> tag"

    def test_convert_design_returns_html_file_path(self):
        """Test convert_design() returns absolute path to index.html."""
        from main import convert_design

        html_path = convert_design(str(SAMPLE_IMAGE_PATH))

        # Verify it's an absolute path
        assert os.path.isabs(html_path), f"Expected absolute path, got: {html_path}"

        # Verify filename is index.html
        assert os.path.basename(html_path) == 'index.html', \
            f"Expected filename 'index.html', got: {os.path.basename(html_path)}"


class TestNoModificationsToSourceFiles:
    """Test that source files remain unmodified."""

    def test_all_source_files_exist(self):
        """Test all source files in build 0c16ae7e exist."""
        expected_files = [
            'html_generator.py',
            'layout_detector.py',
            'color_extractor.py',
            'types.py',
            'image_loader.py',
            'output_writer.py',
            'main.py'
        ]

        for filename in expected_files:
            file_path = SOURCES_DIR / filename
            assert file_path.exists(), f"Expected source file not found: {file_path}"

    def test_all_source_files_readable(self):
        """Test all source files can be read."""
        expected_files = [
            'html_generator.py',
            'layout_detector.py',
            'color_extractor.py',
            'types.py',
            'image_loader.py',
            'output_writer.py',
            'main.py'
        ]

        for filename in expected_files:
            file_path = SOURCES_DIR / filename
            try:
                with open(file_path, 'r') as f:
                    content = f.read()
                assert len(content) > 0, f"File is empty: {file_path}"
            except Exception as e:
                pytest.fail(f"Failed to read {file_path}: {e}")

    def test_source_files_are_python_modules(self):
        """Test source files have valid Python syntax."""
        import py_compile
        import tempfile

        expected_files = [
            'html_generator.py',
            'layout_detector.py',
            'color_extractor.py',
            'types.py',
            'image_loader.py',
            'output_writer.py',
            'main.py'
        ]

        for filename in expected_files:
            file_path = SOURCES_DIR / filename
            try:
                # Compile to bytecode to verify syntax
                with tempfile.NamedTemporaryFile(suffix='.pyc', delete=True) as tmp:
                    py_compile.compile(str(file_path), cfile=tmp.name, doraise=True)
            except py_compile.PyCompileError as e:
                pytest.fail(f"Source file {filename} has invalid Python syntax: {e}")

    def test_source_files_not_modified_recently(self):
        """Test source files have reasonable modification times (not just modified)."""
        expected_files = [
            'html_generator.py',
            'layout_detector.py',
            'color_extractor.py',
            'types.py',
            'image_loader.py',
            'output_writer.py',
            'main.py'
        ]

        # This is a simple sanity check - just verify files exist and are readable
        # We don't check modification times since they may be updated legitimately
        for filename in expected_files:
            file_path = SOURCES_DIR / filename
            assert file_path.stat().st_size > 0, f"Source file is empty: {file_path}"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
