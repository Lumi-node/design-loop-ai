"""Tests for spec_initial.json - initial design specification."""

import json
import re
import os
from pathlib import Path


def load_spec():
    """Load the initial spec file."""
    spec_path = Path(__file__).parent.parent / "examples" / "spec_initial.json"
    with open(spec_path, 'r') as f:
        return json.load(f)


def hex_to_rgb(hex_color: str) -> tuple:
    """Convert hex color (#RRGGBB) to RGB tuple (0-255)."""
    hex_color = hex_color.lstrip('#')
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))


def calculate_luminance(r: int, g: int, b: int) -> float:
    """Calculate relative luminance using WCAG formula."""
    # Normalize RGB to 0-1
    r_norm = r / 255.0
    g_norm = g / 255.0
    b_norm = b / 255.0

    # Apply gamma correction
    def gamma_correct(c):
        if c <= 0.03928:
            return c / 12.92
        else:
            return ((c + 0.055) / 1.055) ** 2.4

    r_lin = gamma_correct(r_norm)
    g_lin = gamma_correct(g_norm)
    b_lin = gamma_correct(b_norm)

    # Calculate luminance
    luminance = 0.2126 * r_lin + 0.7152 * g_lin + 0.0722 * b_lin
    return luminance


def calculate_contrast_ratio(color1_hex: str, color2_hex: str) -> float:
    """Calculate WCAG contrast ratio between two hex colors."""
    rgb1 = hex_to_rgb(color1_hex)
    rgb2 = hex_to_rgb(color2_hex)

    l1 = calculate_luminance(*rgb1)
    l2 = calculate_luminance(*rgb2)

    # Contrast ratio is always (lighter + 0.05) / (darker + 0.05)
    lighter = max(l1, l2)
    darker = min(l1, l2)

    ratio = (lighter + 0.05) / (darker + 0.05)
    return ratio


class TestSpecJSONValidity:
    """Test that spec_initial.json is valid JSON."""

    def test_spec_json_valid(self):
        """Spec file should be valid JSON."""
        spec = load_spec()
        assert isinstance(spec, dict), "Spec must be a dict"

    def test_spec_file_exists(self):
        """Spec file should exist on disk."""
        spec_path = Path(__file__).parent.parent / "examples" / "spec_initial.json"
        assert spec_path.exists(), f"Spec file not found at {spec_path}"

    def test_spec_file_non_empty(self):
        """Spec file should be non-empty."""
        spec_path = Path(__file__).parent.parent / "examples" / "spec_initial.json"
        assert spec_path.stat().st_size > 0, "Spec file is empty"

    def test_spec_parseable_by_json_load(self):
        """Spec should be parseable by json.load()."""
        spec_path = Path(__file__).parent.parent / "examples" / "spec_initial.json"
        with open(spec_path, 'r') as f:
            spec = json.load(f)
        assert isinstance(spec, dict)


class TestSpecSchema:
    """Test that spec has correct structure."""

    def test_has_layout_regions_key(self):
        """Spec must have layout_regions key."""
        spec = load_spec()
        assert 'layout_regions' in spec, "Spec missing 'layout_regions' key"

    def test_has_colors_key(self):
        """Spec must have colors key."""
        spec = load_spec()
        assert 'colors' in spec, "Spec missing 'colors' key"

    def test_layout_regions_has_all_fields(self):
        """layout_regions must have all 4 required fields."""
        spec = load_spec()
        required_fields = [
            'header_height_percent',
            'content_width_percent',
            'footer_height_percent',
            'sidebar_width_percent'
        ]
        for field in required_fields:
            assert field in spec['layout_regions'], \
                f"layout_regions missing '{field}'"

    def test_colors_has_all_regions(self):
        """colors dict must have all 4 region names."""
        spec = load_spec()
        required_regions = ['header', 'sidebar', 'content', 'footer']
        for region in required_regions:
            assert region in spec['colors'], \
                f"colors missing '{region}'"


class TestLayoutRegionValues:
    """Test that layout region values are in valid range."""

    def test_layout_regions_are_integers(self):
        """All layout region values must be integers."""
        spec = load_spec()
        for region, value in spec['layout_regions'].items():
            assert isinstance(value, int), \
                f"layout_regions['{region}'] = {value} is not an integer"

    def test_layout_regions_in_range_0_to_100(self):
        """All layout region percentages must be in range [0, 100]."""
        spec = load_spec()
        for region, value in spec['layout_regions'].items():
            assert 0 <= value <= 100, \
                f"layout_regions['{region}'] = {value} is not in range [0, 100]"

    def test_header_height_percent_is_low(self):
        """Header should be ≤ 10% (imbalanced layout)."""
        spec = load_spec()
        assert spec['layout_regions']['header_height_percent'] <= 10, \
            f"Header {spec['layout_regions']['header_height_percent']}% is not imbalanced (≤ 10% expected)"

    def test_footer_height_percent_is_low(self):
        """Footer should be ≤ 10% (imbalanced layout)."""
        spec = load_spec()
        assert spec['layout_regions']['footer_height_percent'] <= 10, \
            f"Footer {spec['layout_regions']['footer_height_percent']}% is not imbalanced (≤ 10% expected)"

    def test_content_width_percent_is_high(self):
        """Content should be ≥ 65% (asymmetric regions)."""
        spec = load_spec()
        assert spec['layout_regions']['content_width_percent'] >= 65, \
            f"Content {spec['layout_regions']['content_width_percent']}% is not asymmetric (≥ 65% expected)"


class TestColorFormat:
    """Test that all colors are in valid #RRGGBB hex format."""

    def test_color_lists_not_empty(self):
        """Each region's color list must be non-empty."""
        spec = load_spec()
        for region, color_list in spec['colors'].items():
            assert isinstance(color_list, list), \
                f"colors['{region}'] must be a list"
            assert len(color_list) > 0, \
                f"colors['{region}'] is empty"

    def test_all_colors_are_strings(self):
        """All colors must be strings."""
        spec = load_spec()
        for region, color_list in spec['colors'].items():
            for i, color in enumerate(color_list):
                assert isinstance(color, str), \
                    f"colors['{region}'][{i}] is not a string: {color}"

    def test_all_colors_match_hex_format(self):
        """All colors must match #RRGGBB format (7 chars, valid hex)."""
        spec = load_spec()
        hex_pattern = re.compile(r'^#[0-9A-Fa-f]{6}$')

        for region, color_list in spec['colors'].items():
            for i, color in enumerate(color_list):
                assert hex_pattern.match(color), \
                    f"colors['{region}'][{i}] = '{color}' is not valid #RRGGBB format"


class TestColorContrast:
    """Test that colors are intentionally low contrast."""

    def test_has_low_contrast_pair(self):
        """Spec should have at least one color pair with contrast < 4.5 (WCAG AA threshold)."""
        spec = load_spec()

        # Get all colors
        all_colors = []
        for region, color_list in spec['colors'].items():
            all_colors.extend(color_list)

        # Remove duplicates while preserving order
        unique_colors = []
        for color in all_colors:
            if color not in unique_colors:
                unique_colors.append(color)

        # Check all pairs
        low_contrast_pairs = []
        for i, color1 in enumerate(unique_colors):
            for color2 in unique_colors[i+1:]:
                ratio = calculate_contrast_ratio(color1, color2)
                if ratio < 4.5:
                    low_contrast_pairs.append((color1, color2, ratio))

        assert len(low_contrast_pairs) > 0, \
            f"Spec should have at least one low-contrast pair (< 4.5). " \
            f"All pairs have contrast >= 4.5, which is not poor quality."

    def test_medium_gray_to_white_low_contrast(self):
        """#AAAAAA (medium gray) on #FFFFFF should have low contrast."""
        # This is the intentional low-contrast pair in the spec
        ratio = calculate_contrast_ratio('#AAAAAA', '#FFFFFF')
        assert ratio < 4.5, \
            f"Medium gray (#AAAAAA) to white (#FFFFFF) should be low contrast, " \
            f"but ratio is {ratio:.2f} >= 4.5"

    def test_spec_colors_include_low_contrast_combinations(self):
        """The spec colors should be selected to produce low contrast."""
        spec = load_spec()

        # Check specific known low-contrast combinations in the spec
        # Header (#AAAAAA) on content (#FFFFFF) = low contrast
        # Sidebar (#888888) on content (#FFFFFF) = low contrast

        header_color = spec['colors']['header'][0]
        sidebar_color = spec['colors']['sidebar'][0]
        content_color = spec['colors']['content'][0]
        footer_color = spec['colors']['footer'][0]

        # At least some of these pairs should be low contrast
        pairs_to_check = [
            (header_color, content_color),
            (sidebar_color, content_color),
            (footer_color, content_color),
        ]

        has_low_contrast = False
        for color1, color2 in pairs_to_check:
            ratio = calculate_contrast_ratio(color1, color2)
            if ratio < 4.5:
                has_low_contrast = True
                break

        assert has_low_contrast, \
            "Spec colors should include at least one low-contrast pair for demonstrating improvement"


class TestSpecConsistency:
    """Test internal consistency of spec values."""

    def test_region_names_match_between_sections(self):
        """Region names in colors should match expected set."""
        spec = load_spec()
        expected_regions = {'header', 'sidebar', 'content', 'footer'}
        actual_regions = set(spec['colors'].keys())
        assert actual_regions == expected_regions, \
            f"Color regions {actual_regions} don't match expected {expected_regions}"

    def test_no_extra_keys_in_spec(self):
        """Spec should only have layout_regions and colors at top level."""
        spec = load_spec()
        allowed_keys = {'layout_regions', 'colors'}
        actual_keys = set(spec.keys())
        assert actual_keys == allowed_keys, \
            f"Spec has unexpected keys: {actual_keys - allowed_keys}"
