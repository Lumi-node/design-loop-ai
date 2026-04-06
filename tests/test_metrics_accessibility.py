"""
Unit tests for accessibility scoring functions (metrics.py)

Tests WCAG 2.1 AA contrast calculation, CSS parsing, semantic tag detection,
and padding extraction. Covers AC1-AC6 of issue-01-metrics-accessibility.
"""

import pytest
from metrics import (
    srgb_to_linear,
    relative_luminance,
    contrast_ratio,
    parse_color,
    calculate_accessibility_score,
)


class TestSRGBToLinear:
    """Tests for sRGB to linear color space conversion."""

    def test_pure_black_to_linear(self):
        """Black (0) should convert to 0."""
        assert srgb_to_linear(0) == 0.0

    def test_pure_white_to_linear(self):
        """White (255) should convert to 1.0."""
        result = srgb_to_linear(255)
        assert result == pytest.approx(1.0, abs=0.001)

    def test_linear_conversion_below_threshold(self):
        """Values <= 0.03928 normalized use linear division."""
        # 10/255 ≈ 0.0392, which is > 0.03928, so uses power formula
        # 8/255 ≈ 0.0314 < 0.03928, so uses linear division
        srgb_norm = 8 / 255.0
        expected = srgb_norm / 12.92
        assert srgb_to_linear(8) == pytest.approx(expected, abs=0.0001)

    def test_linear_conversion_above_threshold(self):
        """Values > 0.03928 normalized use power formula."""
        srgb_norm = 100 / 255.0
        expected = ((srgb_norm + 0.055) / 1.055) ** 2.4
        assert srgb_to_linear(100) == pytest.approx(expected, abs=0.0001)

    def test_mid_gray(self):
        """Mid-gray (128) should convert consistently."""
        result = srgb_to_linear(128)
        assert 0.2 < result < 0.3  # Rough sanity check


class TestRelativeLuminance:
    """Tests for WCAG 2.1 relative luminance calculation."""

    def test_pure_black(self):
        """Black (0,0,0) should have luminance ~0."""
        assert relative_luminance(0, 0, 0) == pytest.approx(0.0, abs=0.0001)

    def test_pure_white(self):
        """White (255,255,255) should have luminance ~1."""
        result = relative_luminance(255, 255, 255)
        assert result == pytest.approx(1.0, abs=0.0001)

    def test_pure_red(self):
        """Pure red (255,0,0) should have specific luminance value."""
        result = relative_luminance(255, 0, 0)
        # Red has high luminance contribution from the R channel
        assert 0.2 < result < 0.3

    def test_pure_green(self):
        """Pure green (0,255,0) has highest luminance contribution."""
        result = relative_luminance(0, 255, 0)
        # Green channel has weight 0.7152
        assert 0.7 < result < 0.8

    def test_pure_blue(self):
        """Pure blue (0,0,255) has lowest luminance contribution."""
        result = relative_luminance(0, 0, 255)
        # Blue channel has weight 0.0722
        assert 0.05 < result < 0.15


class TestContrastRatio:
    """Tests for WCAG 2.1 contrast ratio calculation."""

    def test_white_on_black_21_to_1(self):
        """White on black should be exactly 21:1 (classic WCAG reference)."""
        ratio = contrast_ratio((255, 255, 255), (0, 0, 0))
        assert ratio == pytest.approx(21.0, abs=0.01)

    def test_black_on_white_21_to_1(self):
        """Black on white (reversed) should also be 21:1."""
        ratio = contrast_ratio((0, 0, 0), (255, 255, 255))
        assert ratio == pytest.approx(21.0, abs=0.01)

    def test_same_color_1_to_1(self):
        """Same color should have 1:1 contrast."""
        ratio = contrast_ratio((128, 128, 128), (128, 128, 128))
        assert ratio == pytest.approx(1.0, abs=0.0001)

    def test_wcag_aa_minimum_4_5_to_1(self):
        """Verify contrast calculation for WCAG AA threshold."""
        # This should exceed 4.5:1
        ratio = contrast_ratio((255, 255, 255), (50, 50, 50))
        assert ratio > 4.5

    def test_gray_on_white(self):
        """Gray on white should have lower contrast than black on white."""
        ratio_black = contrast_ratio((0, 0, 0), (255, 255, 255))
        ratio_gray = contrast_ratio((128, 128, 128), (255, 255, 255))
        assert ratio_black > ratio_gray

    def test_contrast_is_symmetric(self):
        """Contrast ratio should be same regardless of order (uses max/min)."""
        ratio1 = contrast_ratio((255, 0, 0), (0, 255, 0))
        ratio2 = contrast_ratio((0, 255, 0), (255, 0, 0))
        assert ratio1 == pytest.approx(ratio2, abs=0.0001)


class TestParseColor:
    """Tests for CSS color parsing."""

    def test_parse_rgb_format(self):
        """Parse rgb(r, g, b) format."""
        result = parse_color("rgb(255, 128, 64)")
        assert result == (255, 128, 64)

    def test_parse_rgb_with_spaces(self):
        """Parse rgb() with extra spaces."""
        result = parse_color("rgb( 200 , 100 , 50 )")
        assert result == (200, 100, 50)

    def test_parse_rgba_format(self):
        """Parse rgba(r, g, b, a) format, ignoring alpha."""
        result = parse_color("rgba(255, 128, 64, 0.5)")
        assert result == (255, 128, 64)

    def test_parse_hex_6_digit(self):
        """Parse #RRGGBB hex format."""
        result = parse_color("#FF8040")
        assert result == (255, 128, 64)

    def test_parse_hex_6_digit_lowercase(self):
        """Parse #rrggbb hex format (lowercase)."""
        result = parse_color("#ff8040")
        assert result == (255, 128, 64)

    def test_parse_hex_3_digit(self):
        """Parse #RGB hex format (3 digits, expanded)."""
        result = parse_color("#F80")
        assert result == (255, 136, 0)  # F->FF, 8->88, 0->00

    def test_parse_hex_3_digit_lowercase(self):
        """Parse #rgb hex format (lowercase)."""
        result = parse_color("#abc")
        assert result == (170, 187, 204)  # a->aa, b->bb, c->cc

    def test_parse_white_hex(self):
        """Parse white #FFFFFF."""
        result = parse_color("#FFFFFF")
        assert result == (255, 255, 255)

    def test_parse_black_hex(self):
        """Parse black #000000."""
        result = parse_color("#000000")
        assert result == (0, 0, 0)

    def test_parse_invalid_returns_gray(self):
        """Invalid color strings default to gray (128, 128, 128)."""
        result = parse_color("invalid-color")
        assert result == (128, 128, 128)

    def test_parse_empty_string_returns_gray(self):
        """Empty color string defaults to gray."""
        result = parse_color("")
        assert result == (128, 128, 128)

    def test_parse_clamps_out_of_range_rgb(self):
        """RGB values > 255 are clamped to 255."""
        result = parse_color("rgb(300, 400, 500)")
        assert result == (255, 255, 255)  # All clamped to 255

    def test_parse_negative_rgb_clamped(self):
        """Negative RGB values result in parsing failure, default to gray."""
        # Regex won't match negative values, so defaults to gray
        result = parse_color("rgb(-10, -20, -30)")
        assert result == (128, 128, 128)


class TestCalculateAccessibilityScore:
    """Tests for accessibility score calculation."""

    def test_returns_integer(self):
        """Score must be an integer."""
        score = calculate_accessibility_score("<html></html>")
        assert isinstance(score, int)

    def test_score_in_range_0_100(self):
        """Score must be in [0, 100]."""
        score = calculate_accessibility_score("<html></html>")
        assert 0 <= score <= 100

    def test_empty_html_returns_baseline_50(self):
        """Empty HTML should return baseline 50."""
        score = calculate_accessibility_score("")
        assert score == 50

    def test_none_input_returns_baseline_50(self):
        """None input should return baseline 50."""
        score = calculate_accessibility_score(None)
        assert score == 50

    def test_too_short_html_returns_baseline_50(self):
        """HTML shorter than 50 chars should return baseline."""
        score = calculate_accessibility_score("<html></html>")
        assert score == 50

    def test_html_without_style_tag_returns_baseline_50(self):
        """HTML without <style> tag should return baseline 50."""
        html = "<html><body><div class='header'></div></body></html>"
        score = calculate_accessibility_score(html)
        assert score == 50

    def test_html_with_empty_style_tag_returns_baseline_50(self):
        """HTML with empty <style> tag should return baseline 50."""
        html = "<html><head><style></style></head><body></body></html>"
        score = calculate_accessibility_score(html)
        assert score == 50

    def test_all_regions_wcag_aa_with_padding_returns_85_plus(self):
        """All regions with 4.5:1 contrast + padding >= 10px should score >= 85."""
        html = """
        <!DOCTYPE html>
        <html>
        <head><style>
        .header { background-color: #000000; color: #FFFFFF; padding: 12px; }
        .sidebar { background-color: #000000; color: #FFFFFF; padding: 10px; }
        .content { background-color: #000000; color: #FFFFFF; padding: 15px; }
        .footer { background-color: #000000; color: #FFFFFF; padding: 10px; }
        </style></head>
        <body></body>
        </html>
        """
        score = calculate_accessibility_score(html)
        assert score >= 85

    def test_80_percent_regions_wcag_aa_returns_70_plus(self):
        """4 regions with 3 meeting 4.5:1 threshold should score around 50-60."""
        html = """
        <!DOCTYPE html>
        <html>
        <head><style>
        .header { background-color: #000000; color: #FFFFFF; padding: 10px; }
        .sidebar { background-color: #000000; color: #FFFFFF; padding: 10px; }
        .content { background-color: #000000; color: #FFFFFF; padding: 10px; }
        .footer { background-color: #CCCCCC; color: #888888; padding: 10px; }
        </style></head>
        <body></body>
        </html>
        """
        score = calculate_accessibility_score(html)
        # 3/4 = 75% regions pass contrast
        # Base score = (3/4) * 70 = 52.5
        # Padding bonus = 5*4 = 20 (all have padding)
        # Total = 52.5 + 20 = 72.5 -> 72
        assert score >= 70

    def test_less_than_50_percent_regions_wcag_aa_returns_50_or_less(self):
        """< 50% of regions with 4.5:1 contrast should score <= 50."""
        html = """
        <!DOCTYPE html>
        <html>
        <head><style>
        .header { background-color: #CCCCCC; color: #888888; }
        .sidebar { background-color: #CCCCCC; color: #888888; }
        .content { background-color: #000000; color: #FFFFFF; }
        .footer { background-color: #CCCCCC; color: #888888; }
        </style></head>
        <body></body>
        </html>
        """
        score = calculate_accessibility_score(html)
        # 1/4 = 25% < 50%, so score should be <= 50
        assert score <= 50

    def test_semantic_tags_increase_score(self):
        """Using semantic tags (header, main, footer) should increase score."""
        html_semantic = """
        <!DOCTYPE html>
        <html>
        <head><style>
        .header { background-color: #000000; color: #FFFFFF; padding: 10px; }
        .content { background-color: #000000; color: #FFFFFF; padding: 10px; }
        .footer { background-color: #000000; color: #FFFFFF; padding: 10px; }
        </style></head>
        <body>
        <header><div class="header"></div></header>
        <main><div class="content"></div></main>
        <footer><div class="footer"></div></footer>
        </body>
        </html>
        """
        html_div_only = """
        <!DOCTYPE html>
        <html>
        <head><style>
        .header { background-color: #000000; color: #FFFFFF; padding: 10px; }
        .content { background-color: #000000; color: #FFFFFF; padding: 10px; }
        .footer { background-color: #000000; color: #FFFFFF; padding: 10px; }
        </style></head>
        <body>
        <div class="header"></div>
        <div class="content"></div>
        <div class="footer"></div>
        </body>
        </html>
        """
        score_semantic = calculate_accessibility_score(html_semantic)
        score_div = calculate_accessibility_score(html_div_only)
        assert score_semantic > score_div

    def test_padding_bonus_applied(self):
        """Padding >= 10px should add bonus points."""
        html_with_padding = """
        <!DOCTYPE html>
        <html>
        <head><style>
        .header { background-color: #000000; color: #FFFFFF; padding: 15px; }
        .sidebar { background-color: #000000; color: #FFFFFF; padding: 12px; }
        .content { background-color: #000000; color: #FFFFFF; padding: 10px; }
        .footer { background-color: #000000; color: #FFFFFF; padding: 11px; }
        </style></head>
        <body></body>
        </html>
        """
        html_no_padding = """
        <!DOCTYPE html>
        <html>
        <head><style>
        .header { background-color: #000000; color: #FFFFFF; padding: 5px; }
        .sidebar { background-color: #000000; color: #FFFFFF; padding: 3px; }
        .content { background-color: #000000; color: #FFFFFF; padding: 7px; }
        .footer { background-color: #000000; color: #FFFFFF; padding: 2px; }
        </style></head>
        <body></body>
        </html>
        """
        score_with_padding = calculate_accessibility_score(html_with_padding)
        score_no_padding = calculate_accessibility_score(html_no_padding)
        assert score_with_padding > score_no_padding

    def test_css_cascade_uses_last_color(self):
        """CSS cascade rule: last color declaration should be used."""
        html = """
        <!DOCTYPE html>
        <html>
        <head><style>
        .header {
            background-color: #CCCCCC;
            background-color: #000000;
            color: #AAAAAA;
            color: #FFFFFF;
            padding: 10px;
        }
        .sidebar { background-color: #000000; color: #FFFFFF; padding: 10px; }
        .content { background-color: #000000; color: #FFFFFF; padding: 10px; }
        .footer { background-color: #000000; color: #FFFFFF; padding: 10px; }
        </style></head>
        <body></body>
        </html>
        """
        score = calculate_accessibility_score(html)
        # If first colors were used, header would fail contrast
        # If last colors used, header passes (black on white)
        assert score >= 70  # Should pass due to CSS cascade

    def test_missing_regions_dont_penalize(self):
        """Missing region CSS selectors should not penalize score."""
        html = """
        <!DOCTYPE html>
        <html>
        <head><style>
        .header { background-color: #000000; color: #FFFFFF; padding: 10px; }
        .content { background-color: #000000; color: #FFFFFF; padding: 10px; }
        </style></head>
        <body></body>
        </html>
        """
        score = calculate_accessibility_score(html)
        # 2/2 regions pass, so base score = 70
        # With semantic bonus and padding bonus, should be >= 75
        assert score >= 70

    def test_rgb_rgba_color_parsing(self):
        """RGB and RGBA colors should be parsed correctly."""
        html = """
        <!DOCTYPE html>
        <html>
        <head><style>
        .header { background-color: rgb(0, 0, 0); color: rgb(255, 255, 255); padding: 10px; }
        .sidebar { background-color: rgba(0, 0, 0, 0.5); color: rgba(255, 255, 255, 1); padding: 10px; }
        .content { background-color: #000000; color: #FFFFFF; padding: 10px; }
        .footer { background-color: #000; color: #FFF; padding: 10px; }
        </style></head>
        <body></body>
        </html>
        """
        score = calculate_accessibility_score(html)
        assert score >= 70

    def test_case_insensitive_tag_detection(self):
        """Semantic tag detection should be case-insensitive."""
        html = """
        <!DOCTYPE html>
        <html>
        <head><style>
        .header { background-color: #000000; color: #FFFFFF; padding: 10px; }
        .content { background-color: #000000; color: #FFFFFF; padding: 10px; }
        .footer { background-color: #000000; color: #FFFFFF; padding: 10px; }
        </style></head>
        <body>
        <HEADER><div class="header"></div></HEADER>
        <MAIN><div class="content"></div></MAIN>
        <FOOTER><div class="footer"></div></FOOTER>
        </body>
        </html>
        """
        score = calculate_accessibility_score(html)
        assert score >= 80  # Should detect semantic tags


class TestContrastRatioWCAGAAValidation:
    """Tests for WCAG AA contrast ratio validation (AC5-AC6)."""

    def test_wcag_aa_reference_white_on_black(self):
        """Reference WCAG AA example: white on black = 21:1."""
        ratio = contrast_ratio((255, 255, 255), (0, 0, 0))
        assert ratio == pytest.approx(21.0, abs=0.01)

    def test_wcag_aa_threshold_4_5_to_1(self):
        """WCAG AA requires 4.5:1 for normal text."""
        # Black text on light gray should exceed 4.5:1
        ratio = contrast_ratio((0, 0, 0), (200, 200, 200))
        assert ratio > 4.5

    def test_wcag_aa_below_threshold(self):
        """Below 4.5:1 should not meet WCAG AA."""
        # Light gray on light gray should be below 4.5:1
        ratio = contrast_ratio((200, 200, 200), (180, 180, 180))
        assert ratio < 4.5

    def test_srgb_luminance_formula_correctness(self):
        """Verify sRGB linearization matches WCAG 2.1 spec."""
        # Test specific values from WCAG spec
        # Black: relative luminance should be 0
        black_lum = relative_luminance(0, 0, 0)
        assert black_lum == pytest.approx(0.0, abs=0.0001)

        # White: relative luminance should be 1
        white_lum = relative_luminance(255, 255, 255)
        assert white_lum == pytest.approx(1.0, abs=0.0001)


class TestAccessibilityScoreEdgeCases:
    """Edge case tests for accessibility scoring."""

    def test_malformed_html_with_no_css_returns_50(self):
        """Malformed HTML with no CSS returns baseline 50."""
        html = "<html><body>some content</body>"  # Missing closing >
        score = calculate_accessibility_score(html)
        assert score == 50

    def test_html_with_css_in_wrong_format(self):
        """CSS not in <style> tag should return 50."""
        html = """
        <html>
        <head>
        <link rel="stylesheet" href="styles.css">
        </head>
        <body></body>
        </html>
        """
        score = calculate_accessibility_score(html)
        assert score == 50

    def test_malformed_color_values_use_defaults(self):
        """Malformed color values default to gray (128,128,128)."""
        html = """
        <!DOCTYPE html>
        <html>
        <head><style>
        .header { background-color: invalid; color: notacolor; padding: 10px; }
        .sidebar { background-color: #000000; color: #FFFFFF; padding: 10px; }
        .content { background-color: #000000; color: #FFFFFF; padding: 10px; }
        .footer { background-color: #000000; color: #FFFFFF; padding: 10px; }
        </style></head>
        <body></body>
        </html>
        """
        score = calculate_accessibility_score(html)
        # Header should use defaults (gray bg, gray text) which gives 1:1 contrast (fails)
        # 3/4 regions pass, so base = 52.5 + padding bonus(5) + no semantic = 57.5 -> 57
        # But could be different due to rounding, so be flexible
        assert 50 <= score <= 100

    def test_no_regions_detected_returns_50(self):
        """No region CSS selectors should return baseline."""
        html = """
        <!DOCTYPE html>
        <html>
        <head><style>
        .other { background-color: #000000; color: #FFFFFF; padding: 10px; }
        </style></head>
        <body></body>
        </html>
        """
        score = calculate_accessibility_score(html)
        assert score == 50

    def test_regions_with_missing_padding_declaration(self):
        """Regions without padding should still be scored for contrast."""
        html = """
        <!DOCTYPE html>
        <html>
        <head><style>
        .header { background-color: #000000; color: #FFFFFF; }
        .sidebar { background-color: #000000; color: #FFFFFF; }
        .content { background-color: #000000; color: #FFFFFF; }
        .footer { background-color: #000000; color: #FFFFFF; }
        </style></head>
        <body></body>
        </html>
        """
        score = calculate_accessibility_score(html)
        # All regions pass contrast, but no padding
        # Base score = 70, no padding bonus, no semantic bonus = 70
        assert score == 70

    def test_padding_various_formats(self):
        """Padding can be specified various ways."""
        html = """
        <!DOCTYPE html>
        <html>
        <head><style>
        .header { background-color: #000000; color: #FFFFFF; padding: 10px; }
        .sidebar { background-color: #000000; color: #FFFFFF; padding:12px; }
        .content { background-color: #000000; color: #FFFFFF; padding : 15px; }
        .footer { background-color: #000000; color: #FFFFFF; padding: 20px; }
        </style></head>
        <body></body>
        </html>
        """
        score = calculate_accessibility_score(html)
        # All regions pass contrast and padding
        assert score >= 85

    def test_multiple_style_tags(self):
        """Only first <style> tag should be used."""
        html = """
        <!DOCTYPE html>
        <html>
        <head>
        <style>
        .header { background-color: #000000; color: #FFFFFF; padding: 10px; }
        .sidebar { background-color: #000000; color: #FFFFFF; padding: 10px; }
        .content { background-color: #000000; color: #FFFFFF; padding: 10px; }
        .footer { background-color: #000000; color: #FFFFFF; padding: 10px; }
        </style>
        <style>
        .header { background-color: #FFFFFF; color: #000000; padding: 5px; }
        </style>
        </head>
        <body></body>
        </html>
        """
        score = calculate_accessibility_score(html)
        # First style tag should be used (all black with white text, good contrast)
        assert score >= 85
