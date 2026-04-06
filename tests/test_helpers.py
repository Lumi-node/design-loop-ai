"""Unit tests for DesignAgent helper methods."""

import pytest
import os
import tempfile
from pathlib import Path

# Add the parent directory to the path so we can import agent_designer
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agent_designer import DesignAgent


class TestSpecToRegions:
    """Tests for _spec_to_regions conversion."""

    def test_basic_layout_conversion(self):
        """Test basic percentage to pixel conversion with standard values."""
        agent = DesignAgent()
        spec = {
            'layout_regions': {
                'header_height_percent': 10,
                'sidebar_width_percent': 20,
                'footer_height_percent': 10,
                'content_width_percent': 80
            },
            'colors': {}
        }

        regions = agent._spec_to_regions(spec)

        # Header: 10% of 600 = 60
        assert regions['header']['height'] == 60
        assert regions['header']['width'] == 800
        assert regions['header']['x'] == 0
        assert regions['header']['y'] == 0

        # Footer: 10% of 600 = 60
        assert regions['footer']['height'] == 60
        assert regions['footer']['width'] == 800
        assert regions['footer']['x'] == 0
        assert regions['footer']['y'] == 540  # 10 + (600-10-10) = 540

        # Sidebar: 20% of 800 = 160
        assert regions['sidebar']['width'] == 160
        assert regions['sidebar']['x'] == 0
        assert regions['sidebar']['y'] == 60
        assert regions['sidebar']['height'] == 480  # 600 - 60 - 60

        # Content: 80% of 800 = 640, but x starts at 160
        assert regions['content']['width'] == 640
        assert regions['content']['x'] == 160
        assert regions['content']['y'] == 60
        assert regions['content']['height'] == 480

    def test_50_percent_header(self):
        """Test header taking 50% of canvas height."""
        agent = DesignAgent()
        spec = {
            'layout_regions': {
                'header_height_percent': 50,
                'sidebar_width_percent': 0,
                'footer_height_percent': 0,
                'content_width_percent': 100
            },
            'colors': {}
        }

        regions = agent._spec_to_regions(spec)

        # Header: 50% of 600 = 300
        assert regions['header']['height'] == 300

    def test_zero_percent_regions(self):
        """Test zero percent regions return None."""
        agent = DesignAgent()
        spec = {
            'layout_regions': {
                'header_height_percent': 0,
                'sidebar_width_percent': 0,
                'footer_height_percent': 0,
                'content_width_percent': 100
            },
            'colors': {}
        }

        regions = agent._spec_to_regions(spec)

        # Zero regions should be None
        assert regions['header'] is None
        assert regions['sidebar'] is None
        assert regions['footer'] is None

    def test_100_percent_header(self):
        """Test header taking 100% of canvas height."""
        agent = DesignAgent()
        spec = {
            'layout_regions': {
                'header_height_percent': 100,
                'sidebar_width_percent': 0,
                'footer_height_percent': 0,
                'content_width_percent': 100
            },
            'colors': {}
        }

        regions = agent._spec_to_regions(spec)

        # Header: 100% of 600 = 600
        assert regions['header']['height'] == 600

    def test_sidebar_width_calculation(self):
        """Test sidebar width is calculated as percentage of 800."""
        agent = DesignAgent()
        spec = {
            'layout_regions': {
                'header_height_percent': 0,
                'sidebar_width_percent': 25,
                'footer_height_percent': 0,
                'content_width_percent': 75
            },
            'colors': {}
        }

        regions = agent._spec_to_regions(spec)

        # Sidebar: 25% of 800 = 200
        assert regions['sidebar']['width'] == 200
        # Content: 800 - 200 = 600
        assert regions['content']['width'] == 600


class TestColorsSpecToDict:
    """Tests for _colors_spec_to_dict color conversion."""

    def test_red_color(self):
        """Test pure red conversion."""
        agent = DesignAgent()
        spec = {
            'colors': {
                'header': ['#FF0000']
            }
        }

        colors = agent._colors_spec_to_dict(spec)

        assert colors['header'][0] == (255, 0, 0)

    def test_pure_black(self):
        """Test pure black conversion."""
        agent = DesignAgent()
        spec = {
            'colors': {
                'sidebar': ['#000000']
            }
        }

        colors = agent._colors_spec_to_dict(spec)

        assert colors['sidebar'][0] == (0, 0, 0)

    def test_pure_white(self):
        """Test pure white conversion."""
        agent = DesignAgent()
        spec = {
            'colors': {
                'content': ['#FFFFFF']
            }
        }

        colors = agent._colors_spec_to_dict(spec)

        assert colors['content'][0] == (255, 255, 255)

    def test_medium_gray(self):
        """Test medium gray conversion."""
        agent = DesignAgent()
        spec = {
            'colors': {
                'footer': ['#808080']
            }
        }

        colors = agent._colors_spec_to_dict(spec)

        assert colors['footer'][0] == (128, 128, 128)

    def test_multiple_colors_per_region(self):
        """Test multiple colors in a single region."""
        agent = DesignAgent()
        spec = {
            'colors': {
                'header': ['#FF0000', '#00FF00', '#0000FF']
            }
        }

        colors = agent._colors_spec_to_dict(spec)

        assert len(colors['header']) == 3
        assert colors['header'][0] == (255, 0, 0)
        assert colors['header'][1] == (0, 255, 0)
        assert colors['header'][2] == (0, 0, 255)

    def test_multiple_regions(self):
        """Test multiple regions with different colors."""
        agent = DesignAgent()
        spec = {
            'colors': {
                'header': ['#FF0000'],
                'sidebar': ['#00FF00'],
                'content': ['#0000FF'],
                'footer': ['#FFFFFF']
            }
        }

        colors = agent._colors_spec_to_dict(spec)

        assert colors['header'][0] == (255, 0, 0)
        assert colors['sidebar'][0] == (0, 255, 0)
        assert colors['content'][0] == (0, 0, 255)
        assert colors['footer'][0] == (255, 255, 255)

    def test_arbitrary_hex_colors(self):
        """Test arbitrary hex color values."""
        agent = DesignAgent()
        spec = {
            'colors': {
                'header': ['#1A2B3C'],
                'sidebar': ['#AA55FF'],
                'content': ['#12AB34']
            }
        }

        colors = agent._colors_spec_to_dict(spec)

        assert colors['header'][0] == (26, 43, 60)
        assert colors['sidebar'][0] == (170, 85, 255)
        assert colors['content'][0] == (18, 171, 52)


class TestInsertCssIntoHtml:
    """Tests for _insert_css_into_html CSS embedding."""

    def test_basic_css_insertion(self):
        """Test basic CSS insertion into HTML head."""
        agent = DesignAgent()
        html = '<html><head></head><body></body></html>'
        css = 'body { color: red; }'

        result = agent._insert_css_into_html(html, css)

        assert '<style>' in result
        assert 'body { color: red; }' in result
        assert '</style>' in result
        # Should have style before </head>
        assert '<style>body { color: red; }</style></head>' in result

    def test_css_in_head_not_body(self):
        """Test CSS is inserted in <head> not <body>."""
        agent = DesignAgent()
        html = '<html><head></head><body></body></html>'
        css = '.container { display: flex; }'

        result = agent._insert_css_into_html(html, css)

        # CSS should be in head (before </head>)
        head_end = result.index('</head>')
        style_start = result.index('<style>')
        style_end = result.index('</style>')
        body_start = result.index('<body>')

        # Style tag should be before </head>
        assert style_start < head_end
        assert style_end < head_end
        # Style tag should come before <body>
        assert style_end < body_start

    def test_complex_css_insertion(self):
        """Test insertion of complex CSS."""
        agent = DesignAgent()
        html = '<html><head><title>Test</title></head><body></body></html>'
        css = '''
        .header { width: 100%; height: 50px; }
        .content { flex: 1; }
        .footer { width: 100%; height: 30px; }
        '''

        result = agent._insert_css_into_html(html, css)

        assert '<style>' in result
        assert '.header' in result
        assert '.content' in result
        assert '.footer' in result
        assert result.count('</head>') == 1

    def test_case_insensitive_head_tag(self):
        """Test that </head> tag detection is case-insensitive."""
        agent = DesignAgent()
        html = '<html><HEAD></HEAD><body></body></html>'
        css = 'body { color: blue; }'

        result = agent._insert_css_into_html(html, css)

        assert '<style>' in result
        assert 'body { color: blue; }' in result

    def test_html_with_existing_style_in_body(self):
        """Test HTML that already has inline styles in body."""
        agent = DesignAgent()
        html = '<html><head></head><body><div style="color: green;">Test</div></body></html>'
        css = '.container { width: 800px; }'

        result = agent._insert_css_into_html(html, css)

        assert '<style>.container { width: 800px; }</style>' in result
        assert 'style="color: green;"' in result

    def test_preserved_html_structure(self):
        """Test that HTML structure is preserved."""
        agent = DesignAgent()
        html = '''<html>
<head>
    <title>Test Page</title>
</head>
<body>
    <div class="container">
        <header>Header</header>
        <main>Content</main>
    </div>
</body>
</html>'''
        css = 'body { font-family: Arial; }'

        result = agent._insert_css_into_html(html, css)

        assert '<title>Test Page</title>' in result
        assert '<header>Header</header>' in result
        assert '<main>Content</main>' in result
        assert '<style>body { font-family: Arial; }</style>' in result


class TestGetIterationOutputPath:
    """Tests for _get_iteration_output_path path generation."""

    def test_iteration_zero_path(self):
        """Test path for iteration 0."""
        agent = DesignAgent()
        path = agent._get_iteration_output_path(0)

        assert 'iteration_0.html' in path
        assert path.endswith('iteration_0.html')

    def test_iteration_one_path(self):
        """Test path for iteration 1."""
        agent = DesignAgent()
        path = agent._get_iteration_output_path(1)

        assert 'iteration_1.html' in path
        assert path.endswith('iteration_1.html')

    def test_iteration_ten_path(self):
        """Test path for iteration 10."""
        agent = DesignAgent()
        path = agent._get_iteration_output_path(10)

        assert 'iteration_10.html' in path
        assert path.endswith('iteration_10.html')

    def test_path_contains_examples_dir(self):
        """Test path contains examples directory."""
        agent = DesignAgent()
        path = agent._get_iteration_output_path(5)

        assert 'examples' in path
        assert 'iteration_5.html' in path

    def test_path_format(self):
        """Test path format is correct."""
        agent = DesignAgent()
        path = agent._get_iteration_output_path(3)

        # Should contain cwd prefix
        cwd = os.getcwd()
        assert path.startswith(cwd)

        # Should end with iteration_3.html
        assert path.endswith('iteration_3.html')

        # Should contain examples
        assert os.path.sep + 'examples' + os.path.sep in path


class TestIntegration:
    """Integration tests combining multiple helpers."""

    def test_full_spec_to_html_conversion_path(self):
        """Test the full conversion path from spec to regions and colors."""
        agent = DesignAgent()
        spec = {
            'layout_regions': {
                'header_height_percent': 15,
                'sidebar_width_percent': 30,
                'footer_height_percent': 10,
                'content_width_percent': 70
            },
            'colors': {
                'header': ['#FF5733'],
                'sidebar': ['#33FF57'],
                'content': ['#3357FF'],
                'footer': ['#FFFF33']
            }
        }

        regions = agent._spec_to_regions(spec)
        colors = agent._colors_spec_to_dict(spec)

        # Verify regions are converted
        assert regions['header']['height'] == 90  # 15% of 600
        assert regions['sidebar']['width'] == 240  # 30% of 800
        assert regions['footer']['height'] == 60  # 10% of 600

        # Verify colors are converted
        assert colors['header'][0] == (255, 87, 51)
        assert colors['sidebar'][0] == (51, 255, 87)
        assert colors['content'][0] == (51, 87, 255)
        assert colors['footer'][0] == (255, 255, 51)

    def test_css_insertion_with_generated_style(self):
        """Test CSS insertion with realistic generated CSS."""
        agent = DesignAgent()
        html = '<html><head><meta charset="UTF-8"></head><body><div class="container"></div></body></html>'
        css = '''.header { width: 800px; height: 90px; background-color: rgb(255, 87, 51); }
.footer { width: 800px; height: 60px; background-color: rgb(255, 255, 51); }'''

        result = agent._insert_css_into_html(html, css)

        assert '<style>' in result
        assert 'rgb(255, 87, 51)' in result
        assert 'rgb(255, 255, 51)' in result
        assert '<meta charset="UTF-8">' in result
        assert '<div class="container"></div>' in result
