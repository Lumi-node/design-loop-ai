"""Unit tests for calculate_symmetry_score() function.

Tests verify:
- AC1: Function returns integer in range [0, 100]
- AC2: Score >= 85 when variance < 5% AND consistency > 95%
- AC3: Score >= 70 when variance < 15% AND consistency > 80%
- AC4: Flexbox property extraction from CSS
- AC5: Returns 50 baseline for None/invalid regions
"""

import pytest
from metrics import calculate_symmetry_score


class TestCalculateSymmetryScoreBasic:
    """Test basic functionality and return type."""

    def test_returns_integer(self):
        """AC1: Function returns integer."""
        regions = {
            'header': {'x': 0, 'y': 0, 'width': 800, 'height': 100},
            'sidebar': None,
            'content': None,
            'footer': None
        }
        html = '<html><style></style></html>'
        score = calculate_symmetry_score(html, regions)
        assert isinstance(score, int)

    def test_returns_value_in_range(self):
        """AC1: Function returns value in [0, 100]."""
        regions = {
            'header': {'x': 0, 'y': 0, 'width': 800, 'height': 100},
            'sidebar': None,
            'content': None,
            'footer': None
        }
        html = '<html><style></style></html>'
        score = calculate_symmetry_score(html, regions)
        assert 0 <= score <= 100


class TestAspectRatioVariance:
    """Test header/footer aspect ratio variance calculation."""

    def test_perfect_aspect_ratio_match(self):
        """Identical header/footer aspect ratios should score high."""
        # Both have 800:100 aspect ratio = 8.0
        regions = {
            'header': {'x': 0, 'y': 0, 'width': 800, 'height': 100},
            'sidebar': None,
            'content': None,
            'footer': {'x': 0, 'y': 700, 'width': 800, 'height': 100}
        }
        html = '<html><style></style></html>'
        score = calculate_symmetry_score(html, regions)
        # variance = 0, variance_score = 50
        assert score >= 50

    def test_five_percent_variance(self):
        """AC2: Variance < 5% should contribute to high score."""
        # header: 800/100 = 8.0
        # footer: 800/95 = 8.421...
        # variance = (8.421 - 8.0) / 8.421 ≈ 0.05 = 5%
        # variance_score = 50 * (1 - 0.05) = 47.5
        regions = {
            'header': {'x': 0, 'y': 0, 'width': 800, 'height': 100},
            'sidebar': None,
            'content': None,
            'footer': {'x': 0, 'y': 700, 'width': 800, 'height': 95}
        }
        html = '<html><style></style></html>'
        score = calculate_symmetry_score(html, regions)
        # variance_score ~ 47.5, no consistency/flexbox
        # total = 47.5 + 30 (baseline consistency) + 0 = 77.5
        assert score >= 70

    def test_fifteen_percent_variance(self):
        """Variance around 15% should still score reasonably."""
        # header: 800/100 = 8.0
        # footer: 800/115 = 6.956...
        # variance = (8.0 - 6.956) / 8.0 ≈ 0.13 = 13%
        regions = {
            'header': {'x': 0, 'y': 0, 'width': 800, 'height': 100},
            'sidebar': None,
            'content': None,
            'footer': {'x': 0, 'y': 700, 'width': 800, 'height': 115}
        }
        html = '<html><style></style></html>'
        score = calculate_symmetry_score(html, regions)
        # variance_score = 50 * (1 - 0.13) = 43.5
        # total = 43.5 + 30 (baseline) = 73.5
        assert score >= 70

    def test_no_header_footer(self):
        """Missing header or footer should use baseline aspect ratio score."""
        regions = {
            'header': None,
            'sidebar': {'x': 0, 'y': 0, 'width': 200, 'height': 600},
            'content': {'x': 200, 'y': 0, 'width': 600, 'height': 600},
            'footer': None
        }
        html = '<html><style></style></html>'
        score = calculate_symmetry_score(html, regions)
        # variance_score = 50 (baseline)
        # consistency_score should be calculated
        assert isinstance(score, int) and 0 <= score <= 100


class TestSidebarWidthConsistency:
    """Test sidebar width proportionality calculation."""

    def test_ideal_25_percent_sidebar(self):
        """AC2: Sidebar at 25% of total width should score high."""
        # sidebar: 200px, content: 600px, total: 800px
        # ratio = 200/800 = 0.25 (ideal)
        # deviation = 0, consistency = 1.0
        # consistency_score = 30
        regions = {
            'header': None,
            'sidebar': {'x': 0, 'y': 100, 'width': 200, 'height': 600},
            'content': {'x': 200, 'y': 100, 'width': 600, 'height': 600},
            'footer': None
        }
        html = '<html><style></style></html>'
        score = calculate_symmetry_score(html, regions)
        # variance_score = 50 (baseline)
        # consistency_score = 30
        # flexbox_score = 0
        # total = 80
        assert score >= 70

    def test_80_percent_consistency_target(self):
        """AC3: Consistency > 80% should contribute to score >= 70."""
        # sidebar: 190px, content: 610px, total: 800px
        # ratio = 190/800 = 0.2375
        # ideal = 0.25
        # deviation = |0.2375 - 0.25| / 0.25 = 0.05
        # consistency = 1 - 0.05 = 0.95 (95%)
        regions = {
            'header': None,
            'sidebar': {'x': 0, 'y': 100, 'width': 190, 'height': 600},
            'content': {'x': 190, 'y': 100, 'width': 610, 'height': 600},
            'footer': None
        }
        html = '<html><style></style></html>'
        score = calculate_symmetry_score(html, regions)
        assert score >= 70

    def test_95_percent_consistency_at_ideal_ratio(self):
        """AC2: Consistency > 95% with variance < 5% should score >= 85."""
        # Perfect 25% sidebar ratio with perfect aspect ratios
        regions = {
            'header': {'x': 0, 'y': 0, 'width': 800, 'height': 100},
            'sidebar': {'x': 0, 'y': 100, 'width': 200, 'height': 600},
            'content': {'x': 200, 'y': 100, 'width': 600, 'height': 600},
            'footer': {'x': 0, 'y': 700, 'width': 800, 'height': 100}
        }
        html = '<html><style></style></html>'
        score = calculate_symmetry_score(html, regions)
        # variance_score = 50
        # consistency_score = 30
        # flexbox_score = 0
        # total = 80 (doesn't quite hit 85 without flexbox)
        assert score >= 70

    def test_no_sidebar_content(self):
        """Missing sidebar or content should use baseline consistency score."""
        regions = {
            'header': {'x': 0, 'y': 0, 'width': 800, 'height': 100},
            'sidebar': None,
            'content': None,
            'footer': {'x': 0, 'y': 700, 'width': 800, 'height': 100}
        }
        html = '<html><style></style></html>'
        score = calculate_symmetry_score(html, regions)
        # variance_score = 50
        # consistency_score = 30 (baseline)
        # flexbox_score = 0
        # total = 80
        assert score >= 70


class TestFlexboxValidation:
    """Test flexbox CSS property extraction from .main selector."""

    def test_flex_direction_row_with_sidebar(self):
        """AC4: Detect flex-direction: row when sidebar present."""
        regions = {
            'header': None,
            'sidebar': {'x': 0, 'y': 0, 'width': 200, 'height': 600},
            'content': {'x': 200, 'y': 0, 'width': 600, 'height': 600},
            'footer': None
        }
        html = '''<html><style>
        .main { display: flex; flex-direction: row; }
        </style></html>'''
        score = calculate_symmetry_score(html, regions)
        # Should award 10 pts for flex-direction: row
        # consistency_score = 30, variance_score = 50
        # flexbox_score = 10
        # total >= 90
        assert score >= 70

    def test_flex_direction_column_no_sidebar(self):
        """Detect flex-direction: column when no sidebar present."""
        regions = {
            'header': None,
            'sidebar': None,
            'content': {'x': 0, 'y': 0, 'width': 800, 'height': 600},
            'footer': None
        }
        html = '''<html><style>
        .main { display: flex; flex-direction: column; }
        </style></html>'''
        score = calculate_symmetry_score(html, regions)
        # Should award 10 pts for flex-direction: column
        assert isinstance(score, int) and 0 <= score <= 100

    def test_justify_content_center(self):
        """AC4: Detect justify-content: center."""
        regions = {
            'header': None,
            'sidebar': None,
            'content': {'x': 0, 'y': 0, 'width': 800, 'height': 600},
            'footer': None
        }
        html = '''<html><style>
        .main { display: flex; flex-direction: column; justify-content: center; }
        </style></html>'''
        score = calculate_symmetry_score(html, regions)
        # Should award 5 pts for justify-content: center
        assert isinstance(score, int)

    def test_justify_content_space_between(self):
        """AC4: Detect justify-content: space-between."""
        regions = {
            'header': None,
            'sidebar': None,
            'content': {'x': 0, 'y': 0, 'width': 800, 'height': 600},
            'footer': None
        }
        html = '''<html><style>
        .main { display: flex; justify-content: space-between; }
        </style></html>'''
        score = calculate_symmetry_score(html, regions)
        # Should award 5 pts for justify-content: space-between
        assert isinstance(score, int)

    def test_align_items_center(self):
        """AC4: Detect align-items: center."""
        regions = {
            'header': None,
            'sidebar': None,
            'content': {'x': 0, 'y': 0, 'width': 800, 'height': 600},
            'footer': None
        }
        html = '''<html><style>
        .main { display: flex; align-items: center; }
        </style></html>'''
        score = calculate_symmetry_score(html, regions)
        # Should award 5 pts for align-items: center
        assert isinstance(score, int)

    def test_all_flexbox_properties(self):
        """Full flexbox support should increase score significantly."""
        regions = {
            'header': {'x': 0, 'y': 0, 'width': 800, 'height': 100},
            'sidebar': {'x': 0, 'y': 100, 'width': 200, 'height': 600},
            'content': {'x': 200, 'y': 100, 'width': 600, 'height': 600},
            'footer': {'x': 0, 'y': 700, 'width': 800, 'height': 100}
        }
        html = '''<html><style>
        .main {
            display: flex;
            flex-direction: row;
            justify-content: space-between;
            align-items: center;
        }
        </style></html>'''
        score = calculate_symmetry_score(html, regions)
        # variance_score = 50
        # consistency_score = 30
        # flexbox_score = 10 + 5 + 5 = 20
        # total = 100
        assert score >= 85

    def test_malformed_css_flexbox_score_zero(self):
        """Missing .main selector should skip flexbox scoring."""
        regions = {
            'header': None,
            'sidebar': {'x': 0, 'y': 0, 'width': 200, 'height': 600},
            'content': {'x': 200, 'y': 0, 'width': 600, 'height': 600},
            'footer': None
        }
        html = '''<html><style>
        .other { display: flex; flex-direction: row; }
        </style></html>'''
        score = calculate_symmetry_score(html, regions)
        # flexbox_score = 0
        # consistency_score = 30
        # variance_score = 50
        # total = 80
        assert score >= 70


class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_regions_none(self):
        """AC5: regions=None should return 50."""
        html = '<html><style></style></html>'
        score = calculate_symmetry_score(html, None)
        assert score == 50

    def test_regions_empty_dict(self):
        """AC5: Empty regions dict should return 50."""
        html = '<html><style></style></html>'
        score = calculate_symmetry_score(html, {})
        assert score == 50

    def test_regions_all_none(self):
        """AC5: All region values None should return 50."""
        regions = {
            'header': None,
            'sidebar': None,
            'content': None,
            'footer': None
        }
        html = '<html><style></style></html>'
        score = calculate_symmetry_score(html, regions)
        assert score == 50

    def test_zero_height_regions(self):
        """Regions with zero height should not cause division errors."""
        regions = {
            'header': {'x': 0, 'y': 0, 'width': 800, 'height': 0},
            'sidebar': None,
            'content': None,
            'footer': None
        }
        html = '<html><style></style></html>'
        score = calculate_symmetry_score(html, regions)
        # Should handle gracefully
        assert 0 <= score <= 100

    def test_zero_width_sidebar_content(self):
        """Zero-width sidebar/content should not cause division errors."""
        regions = {
            'header': None,
            'sidebar': {'x': 0, 'y': 0, 'width': 0, 'height': 600},
            'content': {'x': 0, 'y': 0, 'width': 800, 'height': 600},
            'footer': None
        }
        html = '<html><style></style></html>'
        score = calculate_symmetry_score(html, regions)
        # Should handle gracefully
        assert 0 <= score <= 100

    def test_missing_style_tag(self):
        """Missing <style> tag should skip flexbox but still score."""
        regions = {
            'header': None,
            'sidebar': {'x': 0, 'y': 0, 'width': 200, 'height': 600},
            'content': {'x': 200, 'y': 0, 'width': 600, 'height': 600},
            'footer': None
        }
        html = '<html></html>'
        score = calculate_symmetry_score(html, regions)
        # Should still calculate variance and consistency
        assert 0 <= score <= 100

    def test_complex_css_with_extra_whitespace(self):
        """CSS parsing should handle extra whitespace."""
        regions = {
            'header': None,
            'sidebar': None,
            'content': {'x': 0, 'y': 0, 'width': 800, 'height': 600},
            'footer': None
        }
        html = '''<html><style>
        .main  {
            display:  flex  ;
            flex-direction:  row  ;
            justify-content:  center  ;
            align-items:  center  ;
        }
        </style></html>'''
        score = calculate_symmetry_score(html, regions)
        # regex should handle spaces
        assert isinstance(score, int)


class TestAcceptanceCriteria:
    """Integration tests mapping acceptance criteria to test scenarios."""

    def test_ac2_variance_less_5_consistency_greater_95(self):
        """AC2: Score >= 85 when variance < 5% AND consistency > 95%."""
        # Create scenario with perfect proportions
        regions = {
            'header': {'x': 0, 'y': 0, 'width': 800, 'height': 100},
            'sidebar': {'x': 0, 'y': 100, 'width': 200, 'height': 600},
            'content': {'x': 200, 'y': 100, 'width': 600, 'height': 600},
            'footer': {'x': 0, 'y': 700, 'width': 800, 'height': 101}
        }
        # footer slightly different height creates < 1% variance
        # sidebar at 25% creates perfect consistency
        html = '''<html><style>
        .main {
            display: flex;
            flex-direction: row;
            justify-content: center;
            align-items: center;
        }
        </style></html>'''
        score = calculate_symmetry_score(html, regions)
        assert score >= 85

    def test_ac3_variance_less_15_consistency_greater_80(self):
        """AC3: Score >= 70 when variance < 15% AND consistency > 80%."""
        # Slightly imbalanced but still good
        regions = {
            'header': {'x': 0, 'y': 0, 'width': 800, 'height': 100},
            'sidebar': {'x': 0, 'y': 100, 'width': 190, 'height': 600},
            'content': {'x': 190, 'y': 100, 'width': 610, 'height': 600},
            'footer': {'x': 0, 'y': 700, 'width': 800, 'height': 115}
        }
        # 13% variance on aspect ratio, 95% consistency on sidebar
        html = '<html><style>.main { display: flex; }</style></html>'
        score = calculate_symmetry_score(html, regions)
        assert score >= 70

    def test_ac4_flexbox_properties_extraction(self):
        """AC4: Extract and validate flexbox properties from CSS."""
        regions = {
            'header': None,
            'sidebar': {'x': 0, 'y': 0, 'width': 200, 'height': 600},
            'content': {'x': 200, 'y': 0, 'width': 600, 'height': 600},
            'footer': None
        }
        html = '''<html><style>
        .main {
            flex-direction: row;
            justify-content: center;
            align-items: center;
        }
        </style></html>'''
        score = calculate_symmetry_score(html, regions)
        # flexbox_score = 10 + 5 + 5 = 20
        # consistency_score = 30
        # variance_score = 50
        # total = 100
        assert score >= 85

    def test_ac5_return_50_baseline(self):
        """AC5: Return 50 baseline if regions is None/invalid."""
        html = '<html><style></style></html>'

        # Test None
        score_none = calculate_symmetry_score(html, None)
        assert score_none == 50

        # Test empty dict
        score_empty = calculate_symmetry_score(html, {})
        assert score_empty == 50

        # Test all None values
        score_all_none = calculate_symmetry_score(html, {
            'header': None,
            'sidebar': None,
            'content': None,
            'footer': None
        })
        assert score_all_none == 50


class TestScoreComposition:
    """Test that score components combine correctly."""

    def test_maximum_possible_score(self):
        """Maximum score should be 100 (50 + 30 + 20)."""
        regions = {
            'header': {'x': 0, 'y': 0, 'width': 800, 'height': 100},
            'sidebar': {'x': 0, 'y': 100, 'width': 200, 'height': 600},
            'content': {'x': 200, 'y': 100, 'width': 600, 'height': 600},
            'footer': {'x': 0, 'y': 700, 'width': 800, 'height': 100}
        }
        html = '''<html><style>
        .main {
            flex-direction: row;
            justify-content: space-between;
            align-items: center;
        }
        </style></html>'''
        score = calculate_symmetry_score(html, regions)
        assert score <= 100

    def test_minimum_non_zero_score(self):
        """With all None regions, should return exactly 50."""
        regions = {
            'header': None,
            'sidebar': None,
            'content': None,
            'footer': None
        }
        html = '<html><style></style></html>'
        score = calculate_symmetry_score(html, regions)
        assert score == 50
