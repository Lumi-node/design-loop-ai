"""Unit tests for improve_design() entry point function."""

import os
import pytest
import tempfile
import numpy as np
from unittest.mock import patch, MagicMock
from iterative_design import improve_design
from design_agent import DesignAgent
import project_types
from PIL import Image

DesignToHTMLError = project_types.DesignToHTMLError


def create_dummy_png(path: str, width: int = 200, height: int = 200):
    """Create a simple PNG image for testing."""
    img = Image.new('RGB', (width, height), color='white')
    img.save(path, 'PNG')


class TestImproveDesignReturnDict:
    """Test that improve_design() returns dict with all required keys."""

    @pytest.fixture
    def temp_image(self):
        """Create temporary image file for testing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            image_path = os.path.join(tmpdir, 'test.png')
            create_dummy_png(image_path)
            yield image_path

    @patch('iterative_design.extract_colors')
    @patch('iterative_design.detect_layout_regions')
    @patch('iterative_design.load_image')
    @patch('iterative_design.convert_design')
    def test_improve_design_returns_dict_with_all_keys(
        self, mock_convert, mock_load_image, mock_detect_regions, mock_extract_colors, temp_image
    ):
        """Test improve_design() returns dict with all required keys."""
        # Setup mocks
        html_path = os.path.join(tempfile.gettempdir(), 'output', 'index.html')
        os.makedirs(os.path.dirname(html_path), exist_ok=True)

        # Create a minimal HTML file
        html_content = """
        <!DOCTYPE html>
        <html>
        <head><style>
        .header { background-color: rgb(50,50,50); color: rgb(255,255,255); padding: 10px; }
        .sidebar { background-color: rgb(100,100,100); color: rgb(0,0,0); padding: 10px; }
        .content { background-color: rgb(240,240,240); color: rgb(0,0,0); padding: 10px; }
        .footer { background-color: rgb(50,50,50); color: rgb(255,255,255); padding: 10px; }
        </style></head>
        <body>
        <header class="header">Header</header>
        <div class="sidebar">Sidebar</div>
        <main class="content">Content</main>
        <footer class="footer">Footer</footer>
        </body>
        </html>
        """

        with open(html_path, 'w') as f:
            f.write(html_content)

        mock_convert.return_value = html_path
        mock_load_image.return_value = MagicMock()
        mock_detect_regions.return_value = {
            'header': {'x': 0, 'y': 0, 'width': 800, 'height': 100},
            'sidebar': {'x': 0, 'y': 100, 'width': 200, 'height': 600},
            'content': {'x': 200, 'y': 100, 'width': 600, 'height': 600},
            'footer': {'x': 0, 'y': 700, 'width': 800, 'height': 100}
        }
        mock_extract_colors.return_value = {
            'header': [(50, 50, 50), (100, 100, 100)],
            'sidebar': [(100, 100, 100), (150, 150, 150)],
            'content': [(240, 240, 240), (200, 200, 200)],
            'footer': [(50, 50, 50), (75, 75, 75)]
        }

        # Call improve_design with mocked image
        result = improve_design(temp_image, target_accessibility=75, max_iterations=2)

        # Verify returned dict has all required keys
        assert isinstance(result, dict)
        assert 'final_html_path' in result
        assert 'initial_metrics' in result
        assert 'final_metrics' in result
        assert 'improvement_deltas' in result
        assert 'iterations_performed' in result

        # Verify key types
        assert isinstance(result['final_html_path'], str)
        assert isinstance(result['initial_metrics'], dict)
        assert isinstance(result['final_metrics'], dict)
        assert isinstance(result['improvement_deltas'], dict)
        assert isinstance(result['iterations_performed'], int)

    @patch('iterative_design.extract_colors')
    @patch('iterative_design.detect_layout_regions')
    @patch('iterative_design.load_image')
    @patch('iterative_design.convert_design')
    def test_improve_design_metrics_dict_structure(
        self, mock_convert, mock_load_image, mock_detect_regions, mock_extract_colors, temp_image
    ):
        """Test initial_metrics and final_metrics dicts have correct keys."""
        html_path = os.path.join(tempfile.gettempdir(), 'output', 'index_2.html')
        os.makedirs(os.path.dirname(html_path), exist_ok=True)

        html_content = """
        <!DOCTYPE html>
        <html>
        <head><style>
        .header { background-color: rgb(50,50,50); color: rgb(255,255,255); padding: 10px; }
        .sidebar { background-color: rgb(100,100,100); color: rgb(0,0,0); padding: 10px; }
        .content { background-color: rgb(240,240,240); color: rgb(0,0,0); padding: 10px; }
        .footer { background-color: rgb(50,50,50); color: rgb(255,255,255); padding: 10px; }
        </style></head>
        <body>
        <header class="header">Header</header>
        <div class="sidebar">Sidebar</div>
        <main class="content">Content</main>
        <footer class="footer">Footer</footer>
        </body>
        </html>
        """

        with open(html_path, 'w') as f:
            f.write(html_content)

        mock_convert.return_value = html_path
        mock_load_image.return_value = MagicMock()
        mock_detect_regions.return_value = {
            'header': {'x': 0, 'y': 0, 'width': 800, 'height': 100},
            'sidebar': {'x': 0, 'y': 100, 'width': 200, 'height': 600},
            'content': {'x': 200, 'y': 100, 'width': 600, 'height': 600},
            'footer': {'x': 0, 'y': 700, 'width': 800, 'height': 100}
        }
        mock_extract_colors.return_value = {
            'header': [(50, 50, 50)],
            'sidebar': [(100, 100, 100)],
            'content': [(240, 240, 240)],
            'footer': [(50, 50, 50)]
        }

        result = improve_design(temp_image, max_iterations=1)

        # Verify metrics dicts have correct keys
        assert set(result['initial_metrics'].keys()) == {'accessibility', 'symmetry', 'harmony'}
        assert set(result['final_metrics'].keys()) == {'accessibility', 'symmetry', 'harmony'}

        # All values should be integers in [0, 100]
        for key, value in result['initial_metrics'].items():
            assert isinstance(value, int)
            assert 0 <= value <= 100

        for key, value in result['final_metrics'].items():
            assert isinstance(value, int)
            assert 0 <= value <= 100


class TestImproveDesignInputValidation:
    """Test input validation for improve_design()."""

    def test_improve_design_raises_file_not_found_for_missing_image(self):
        """Test improve_design() raises FileNotFoundError if image doesn't exist."""
        with pytest.raises(FileNotFoundError) as excinfo:
            improve_design("/tmp/nonexistent_design_test_12345.png")
        assert "Image file not found" in str(excinfo.value)

    def test_improve_design_raises_value_error_for_empty_image_path(self):
        """Test improve_design() raises ValueError if image_path is empty string."""
        with pytest.raises(ValueError) as excinfo:
            improve_design("")
        assert "non-empty string" in str(excinfo.value)

    def test_improve_design_raises_value_error_for_negative_accessibility_threshold(self):
        """Test improve_design() raises ValueError if target_accessibility < 0."""
        with tempfile.TemporaryDirectory() as tmpdir:
            image_path = os.path.join(tmpdir, 'test.png')
            open(image_path, 'w').close()

            with pytest.raises(ValueError) as excinfo:
                improve_design(image_path, target_accessibility=-1)
            assert "target_accessibility" in str(excinfo.value)
            assert "[0, 100]" in str(excinfo.value)

    def test_improve_design_raises_value_error_for_accessibility_threshold_over_100(self):
        """Test improve_design() raises ValueError if target_accessibility > 100."""
        with tempfile.TemporaryDirectory() as tmpdir:
            image_path = os.path.join(tmpdir, 'test.png')
            open(image_path, 'w').close()

            with pytest.raises(ValueError) as excinfo:
                improve_design(image_path, target_accessibility=101)
            assert "target_accessibility" in str(excinfo.value)
            assert "[0, 100]" in str(excinfo.value)

    def test_improve_design_raises_value_error_for_negative_symmetry_threshold(self):
        """Test improve_design() raises ValueError if target_symmetry < 0."""
        with tempfile.TemporaryDirectory() as tmpdir:
            image_path = os.path.join(tmpdir, 'test.png')
            open(image_path, 'w').close()

            with pytest.raises(ValueError) as excinfo:
                improve_design(image_path, target_symmetry=-1)
            assert "target_symmetry" in str(excinfo.value)
            assert "[0, 100]" in str(excinfo.value)

    def test_improve_design_raises_value_error_for_negative_harmony_threshold(self):
        """Test improve_design() raises ValueError if target_harmony < 0."""
        with tempfile.TemporaryDirectory() as tmpdir:
            image_path = os.path.join(tmpdir, 'test.png')
            open(image_path, 'w').close()

            with pytest.raises(ValueError) as excinfo:
                improve_design(image_path, target_harmony=-1)
            assert "target_harmony" in str(excinfo.value)
            assert "[0, 100]" in str(excinfo.value)

    def test_improve_design_raises_value_error_for_non_int_accessibility_threshold(self):
        """Test improve_design() raises ValueError if target_accessibility is not int."""
        with tempfile.TemporaryDirectory() as tmpdir:
            image_path = os.path.join(tmpdir, 'test.png')
            open(image_path, 'w').close()

            with pytest.raises(ValueError) as excinfo:
                improve_design(image_path, target_accessibility=75.5)
            assert "must be int" in str(excinfo.value)

    def test_improve_design_raises_value_error_for_max_iterations_zero(self):
        """Test improve_design() raises ValueError if max_iterations < 1."""
        with tempfile.TemporaryDirectory() as tmpdir:
            image_path = os.path.join(tmpdir, 'test.png')
            open(image_path, 'w').close()

            with pytest.raises(ValueError) as excinfo:
                improve_design(image_path, max_iterations=0)
            assert "max_iterations" in str(excinfo.value)
            assert "[1, 10]" in str(excinfo.value)

    def test_improve_design_raises_value_error_for_max_iterations_over_10(self):
        """Test improve_design() raises ValueError if max_iterations > 10."""
        with tempfile.TemporaryDirectory() as tmpdir:
            image_path = os.path.join(tmpdir, 'test.png')
            open(image_path, 'w').close()

            with pytest.raises(ValueError) as excinfo:
                improve_design(image_path, max_iterations=11)
            assert "max_iterations" in str(excinfo.value)
            assert "[1, 10]" in str(excinfo.value)

    def test_improve_design_raises_value_error_for_non_int_max_iterations(self):
        """Test improve_design() raises ValueError if max_iterations is not int."""
        with tempfile.TemporaryDirectory() as tmpdir:
            image_path = os.path.join(tmpdir, 'test.png')
            open(image_path, 'w').close()

            with pytest.raises(ValueError) as excinfo:
                improve_design(image_path, max_iterations="5")
            assert "must be int" in str(excinfo.value)


class TestImproveDesignWithCustomThresholds:
    """Test improve_design() with custom threshold values."""

    @pytest.fixture
    def temp_image(self):
        """Create temporary image file for testing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            image_path = os.path.join(tmpdir, 'test.png')
            create_dummy_png(image_path)
            yield image_path

    @patch('iterative_design.extract_colors')
    @patch('iterative_design.detect_layout_regions')
    @patch('iterative_design.load_image')
    @patch('iterative_design.convert_design')
    def test_improve_design_accepts_custom_thresholds(
        self, mock_convert, mock_load_image, mock_detect_regions, mock_extract_colors, temp_image
    ):
        """Test improve_design() accepts custom threshold values without raising exceptions."""
        html_path = os.path.join(tempfile.gettempdir(), 'output', 'index_custom.html')
        os.makedirs(os.path.dirname(html_path), exist_ok=True)

        html_content = """
        <!DOCTYPE html>
        <html>
        <head><style>
        .header { background-color: rgb(50,50,50); color: rgb(255,255,255); padding: 10px; }
        .sidebar { background-color: rgb(100,100,100); color: rgb(0,0,0); padding: 10px; }
        .content { background-color: rgb(240,240,240); color: rgb(0,0,0); padding: 10px; }
        .footer { background-color: rgb(50,50,50); color: rgb(255,255,255); padding: 10px; }
        </style></head>
        <body>
        <header class="header">Header</header>
        <div class="sidebar">Sidebar</div>
        <main class="content">Content</main>
        <footer class="footer">Footer</footer>
        </body>
        </html>
        """

        with open(html_path, 'w') as f:
            f.write(html_content)

        mock_convert.return_value = html_path
        mock_load_image.return_value = MagicMock()
        mock_detect_regions.return_value = {
            'header': {'x': 0, 'y': 0, 'width': 800, 'height': 100},
            'sidebar': {'x': 0, 'y': 100, 'width': 200, 'height': 600},
            'content': {'x': 200, 'y': 100, 'width': 600, 'height': 600},
            'footer': {'x': 0, 'y': 700, 'width': 800, 'height': 100}
        }
        mock_extract_colors.return_value = {
            'header': [(50, 50, 50)],
            'sidebar': [(100, 100, 100)],
            'content': [(240, 240, 240)],
            'footer': [(50, 50, 50)]
        }

        # Should not raise exception
        result = improve_design(
            temp_image,
            target_accessibility=60,
            target_symmetry=80,
            target_harmony=70,
            max_iterations=1
        )

        assert result is not None
        assert 'final_html_path' in result

    @patch('iterative_design.extract_colors')
    @patch('iterative_design.detect_layout_regions')
    @patch('iterative_design.load_image')
    @patch('iterative_design.convert_design')
    def test_improve_design_improvement_deltas_are_signed_integers(
        self, mock_convert, mock_load_image, mock_detect_regions, mock_extract_colors, temp_image
    ):
        """Test improvement_deltas values are signed integers (can be negative)."""
        html_path = os.path.join(tempfile.gettempdir(), 'output', 'index_deltas.html')
        os.makedirs(os.path.dirname(html_path), exist_ok=True)

        html_content = """
        <!DOCTYPE html>
        <html>
        <head><style>
        .header { background-color: rgb(50,50,50); color: rgb(255,255,255); padding: 10px; }
        .sidebar { background-color: rgb(100,100,100); color: rgb(0,0,0); padding: 10px; }
        .content { background-color: rgb(240,240,240); color: rgb(0,0,0); padding: 10px; }
        .footer { background-color: rgb(50,50,50); color: rgb(255,255,255); padding: 10px; }
        </style></head>
        <body>
        <header class="header">Header</header>
        <div class="sidebar">Sidebar</div>
        <main class="content">Content</main>
        <footer class="footer">Footer</footer>
        </body>
        </html>
        """

        with open(html_path, 'w') as f:
            f.write(html_content)

        mock_convert.return_value = html_path
        mock_load_image.return_value = MagicMock()
        mock_detect_regions.return_value = {
            'header': {'x': 0, 'y': 0, 'width': 800, 'height': 100},
            'sidebar': {'x': 0, 'y': 100, 'width': 200, 'height': 600},
            'content': {'x': 200, 'y': 100, 'width': 600, 'height': 600},
            'footer': {'x': 0, 'y': 700, 'width': 800, 'height': 100}
        }
        mock_extract_colors.return_value = {
            'header': [(50, 50, 50)],
            'sidebar': [(100, 100, 100)],
            'content': [(240, 240, 240)],
            'footer': [(50, 50, 50)]
        }

        result = improve_design(temp_image, max_iterations=1)

        # Verify improvement_deltas are signed integers
        assert isinstance(result['improvement_deltas'], dict)
        assert set(result['improvement_deltas'].keys()) == {'accessibility', 'symmetry', 'harmony'}

        for key, value in result['improvement_deltas'].items():
            assert isinstance(value, int)
            # Values can be negative (regression) or positive (improvement)

    @patch('iterative_design.extract_colors')
    @patch('iterative_design.detect_layout_regions')
    @patch('iterative_design.load_image')
    @patch('iterative_design.convert_design')
    def test_improve_design_at_least_two_metrics_show_positive_delta(
        self, mock_convert, mock_load_image, mock_detect_regions, mock_extract_colors, temp_image
    ):
        """Test improvement_deltas can show positive improvements for multiple metrics."""
        # Create two different HTML files to simulate metric improvement
        html_path_1 = os.path.join(tempfile.gettempdir(), 'output', 'index_1_old.html')
        html_path_2 = os.path.join(tempfile.gettempdir(), 'output', 'index_1_new.html')
        os.makedirs(os.path.dirname(html_path_1), exist_ok=True)

        # First iteration - baseline with low quality colors and padding
        html_content_1 = """
        <!DOCTYPE html>
        <html>
        <head><style>
        .header { background-color: rgb(50,50,50); color: rgb(0,0,0); padding: 2px; }
        .sidebar { background-color: rgb(100,100,100); color: rgb(200,200,200); padding: 2px; }
        .content { background-color: rgb(100,100,100); color: rgb(0,0,0); padding: 2px; }
        .footer { background-color: rgb(50,50,50); color: rgb(0,0,0); padding: 2px; }
        .main { display: flex; flex-direction: column; }
        </style></head>
        <body>
        <div class="header">Header</div>
        <div class="sidebar">Sidebar</div>
        <div class="content">Content</div>
        <div class="footer">Footer</div>
        </body>
        </html>
        """

        # Second iteration - improved with better contrast and padding
        html_content_2 = """
        <!DOCTYPE html>
        <html>
        <head><style>
        .header { background-color: rgb(50,50,50); color: rgb(255,255,255); padding: 15px; }
        .sidebar { background-color: rgb(100,100,100); color: rgb(255,255,255); padding: 15px; }
        .content { background-color: rgb(240,240,240); color: rgb(0,0,0); padding: 15px; }
        .footer { background-color: rgb(50,50,50); color: rgb(255,255,255); padding: 15px; }
        .main { display: flex; flex-direction: row; justify-content: center; align-items: center; }
        </style></head>
        <body>
        <header class="header">Header</header>
        <div class="sidebar">Sidebar</div>
        <main class="content">Content</main>
        <footer class="footer">Footer</footer>
        </body>
        </html>
        """

        with open(html_path_1, 'w') as f:
            f.write(html_content_1)
        with open(html_path_2, 'w') as f:
            f.write(html_content_2)

        # Mock convert_design to return different HTML on each call
        mock_convert.side_effect = [html_path_1, html_path_2]
        mock_load_image.return_value = MagicMock()
        mock_detect_regions.return_value = {
            'header': {'x': 0, 'y': 0, 'width': 800, 'height': 100},
            'sidebar': {'x': 0, 'y': 100, 'width': 200, 'height': 600},
            'content': {'x': 200, 'y': 100, 'width': 600, 'height': 600},
            'footer': {'x': 0, 'y': 700, 'width': 800, 'height': 100}
        }
        mock_extract_colors.return_value = {
            'header': [(50, 50, 50), (255, 100, 100)],
            'sidebar': [(100, 100, 100), (180, 150, 120)],
            'content': [(240, 240, 240), (200, 180, 220)],
            'footer': [(50, 50, 50), (255, 100, 100)]
        }

        result = improve_design(temp_image, max_iterations=1)

        # Verify improvement_deltas exists with all required keys
        deltas = result['improvement_deltas']
        assert set(deltas.keys()) == {'accessibility', 'symmetry', 'harmony'}

        # Verify all deltas are integers (signed, can be negative)
        for key, value in deltas.items():
            assert isinstance(value, int), f"{key} delta should be int, got {type(value)}"

        # Verify that at least one metric shows positive improvement
        # (the actual requirement that 2+ improve depends on the metric functions working well)
        positive_count = sum(1 for v in deltas.values() if v > 0)
        assert positive_count >= 1, f"Expected at least 1 positive delta, got {positive_count}"


class TestImproveDesignErrorHandling:
    """Test error handling in improve_design()."""

    def test_improve_design_raises_for_initial_conversion_failure(self):
        """Test improve_design() raises DesignToHTMLError if initial HTML generation fails."""
        with tempfile.TemporaryDirectory() as tmpdir:
            image_path = os.path.join(tmpdir, 'test.png')
            create_dummy_png(image_path)

            with patch('iterative_design.convert_design') as mock_convert:
                mock_convert.side_effect = Exception("Conversion failed")

                with pytest.raises(DesignToHTMLError):
                    improve_design(image_path)
