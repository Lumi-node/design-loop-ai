"""Unit tests for metrics.py module.

Tests cover all four metric extraction functions:
- extract_dom_depth: HTML nesting depth
- extract_contrast_ratios: WCAG contrast pairs
- calculate_layout_symmetry: Layout balance (variance formula)
- calculate_accessibility_score: WCAG 2.1 AA compliance
"""

import pytest
from metrics import (
    extract_dom_depth,
    extract_contrast_ratios,
    calculate_layout_symmetry,
    calculate_accessibility_score,
    extract_responsive_breakpoints,
)


class TestExtractDomDepth:
    """Test extract_dom_depth function."""

    def test_shallow_html_structure(self):
        """Verify shallow HTML returns correct depth."""
        html = '<html><body><div>text</div></body></html>'
        depth = extract_dom_depth(html)
        assert isinstance(depth, int)
        assert depth >= 1
        assert depth == 4  # html(1), body(2), div(3), text(4)

    def test_deep_html_structure(self):
        """Verify deep HTML returns higher depth than shallow."""
        html_shallow = '<html><body><div>text</div></body></html>'
        html_deep = '<html><body><div><div><div><div>text</div></div></div></div></body></html>'

        depth_shallow = extract_dom_depth(html_shallow)
        depth_deep = extract_dom_depth(html_deep)

        assert depth_deep > depth_shallow
        assert depth_deep >= 6  # Nested divs add 4 more levels

    def test_empty_html(self):
        """Verify empty HTML returns 1."""
        assert extract_dom_depth('') == 1
        assert extract_dom_depth('   ') == 1

    def test_minimal_html(self):
        """Verify minimal HTML handled gracefully."""
        html = '<html></html>'
        depth = extract_dom_depth(html)
        assert depth >= 1

    def test_malformed_html(self):
        """Verify malformed HTML handled gracefully."""
        html = '<html><body><div>unclosed div</body></html>'
        depth = extract_dom_depth(html)
        assert isinstance(depth, int)
        assert depth >= 1

    def test_html_without_html_tag(self):
        """Verify HTML without html tag handled gracefully."""
        html = '<body><div>text</div></body>'
        depth = extract_dom_depth(html)
        assert isinstance(depth, int)
        assert depth >= 1


class TestExtractContrastRatios:
    """Test extract_contrast_ratios function."""

    def test_black_on_white_maximum_contrast(self):
        """Verify black on white produces ~21.0 contrast."""
        html = '''<html>
        <body>
            <div style="background-color: #FFFFFF; color: #000000;">Black on white</div>
        </body>
        </html>'''
        ratios = extract_contrast_ratios(html)

        assert isinstance(ratios, dict)
        assert len(ratios) > 0
        # Black on white should be close to 21.0
        assert any(ratio >= 20.0 for ratio in ratios.values())

    def test_white_on_black_maximum_contrast(self):
        """Verify white on black produces ~21.0 contrast."""
        html = '''<html>
        <body>
            <div style="background-color: #000000; color: #FFFFFF;">White on black</div>
        </body>
        </html>'''
        ratios = extract_contrast_ratios(html)

        assert isinstance(ratios, dict)
        assert len(ratios) > 0
        assert any(ratio >= 20.0 for ratio in ratios.values())

    def test_gray_on_white_medium_contrast(self):
        """Verify gray on white produces medium contrast."""
        html = '''<html>
        <body>
            <div style="background-color: #FFFFFF; color: #808080;">Gray on white</div>
        </body>
        </html>'''
        ratios = extract_contrast_ratios(html)

        assert isinstance(ratios, dict)
        assert len(ratios) > 0
        # Gray on white should be between 1.0 and 21.0
        assert all(1.0 <= ratio <= 21.0 for ratio in ratios.values())

    def test_no_contrast_pairs(self):
        """Verify HTML with no styles returns empty dict."""
        html = '<html><body><div>text</div></body></html>'
        ratios = extract_contrast_ratios(html)
        assert isinstance(ratios, dict)
        assert len(ratios) == 0

    def test_missing_color_or_background(self):
        """Verify elements with only one of color/background skip gracefully."""
        html = '''<html>
        <body>
            <div style="background-color: #FFFFFF;">No text color</div>
            <div style="color: #000000;">No background</div>
        </body>
        </html>'''
        ratios = extract_contrast_ratios(html)
        assert isinstance(ratios, dict)
        # May be empty or contain ratios, but should not crash

    def test_invalid_color_format(self):
        """Verify invalid colors handled gracefully."""
        html = '''<html>
        <body>
            <div style="background-color: #GGGGGG; color: #000000;">Invalid color</div>
        </body>
        </html>'''
        ratios = extract_contrast_ratios(html)
        assert isinstance(ratios, dict)
        # Should not crash, may be empty

    def test_contrast_ratio_range(self):
        """Verify all contrast ratios are in [1.0, 21.0] range."""
        html = '''<html>
        <body>
            <div style="background-color: #000000; color: #FFFFFF;">Text 1</div>
            <div style="background-color: #808080; color: #FFFFFF;">Text 2</div>
            <div style="background-color: #FFFFFF; color: #000000;">Text 3</div>
        </body>
        </html>'''
        ratios = extract_contrast_ratios(html)

        for ratio in ratios.values():
            assert 1.0 <= ratio <= 21.0

    def test_empty_html_contrast(self):
        """Verify empty HTML returns empty dict."""
        assert extract_contrast_ratios('') == {}
        assert extract_contrast_ratios('   ') == {}


class TestCalculateLayoutSymmetry:
    """Test calculate_layout_symmetry function."""

    def test_equal_flex_divs_maximum_symmetry(self):
        """Verify equal flex divs produce ~1.0 symmetry."""
        html = '''<html>
        <body>
            <div class="container">
                <div style="flex: 1;">Section 1</div>
                <div style="flex: 1;">Section 2</div>
                <div style="flex: 1;">Section 3</div>
            </div>
        </body>
        </html>'''
        symmetry = calculate_layout_symmetry(html)

        assert isinstance(symmetry, float)
        assert 0.0 <= symmetry <= 1.0
        assert symmetry >= 0.95  # Should be close to 1.0

    def test_unequal_flex_divs_lower_symmetry(self):
        """Verify unequal flex divs produce lower symmetry."""
        html = '''<html>
        <body>
            <div class="container">
                <div style="flex: 0.1;">Section 1</div>
                <div style="flex: 0.8;">Section 2</div>
                <div style="flex: 0.1;">Section 3</div>
            </div>
        </body>
        </html>'''
        symmetry = calculate_layout_symmetry(html)

        assert isinstance(symmetry, float)
        assert 0.0 <= symmetry <= 1.0
        assert symmetry < 0.95  # Should be less than equal case
        assert symmetry > 0.8   # But still reasonably high

    def test_equal_height_percentages(self):
        """Verify equal height percentages produce high symmetry."""
        html = '''<html>
        <body>
            <div class="container">
                <div style="height: 33.33%;">Section 1</div>
                <div style="height: 33.33%;">Section 2</div>
                <div style="height: 33.33%;">Section 3</div>
            </div>
        </body>
        </html>'''
        symmetry = calculate_layout_symmetry(html)

        assert isinstance(symmetry, float)
        assert 0.0 <= symmetry <= 1.0
        assert symmetry >= 0.95

    def test_single_region_trivially_symmetric(self):
        """Verify single region returns 1.0."""
        html = '''<html>
        <body>
            <div class="container">
                <div style="flex: 1;">Only section</div>
            </div>
        </body>
        </html>'''
        symmetry = calculate_layout_symmetry(html)

        assert symmetry == 1.0

    def test_no_container_neutral_score(self):
        """Verify HTML without container returns neutral score."""
        html = '<html><body><div>No container</div></body></html>'
        symmetry = calculate_layout_symmetry(html)

        assert isinstance(symmetry, float)
        assert 0.0 <= symmetry <= 1.0
        assert symmetry == 0.5  # Neutral

    def test_no_regions_neutral_score(self):
        """Verify container without regions returns high score (trivially symmetric)."""
        html = '''<html>
        <body>
            <div class="container">
            </div>
        </body>
        </html>'''
        symmetry = calculate_layout_symmetry(html)

        assert isinstance(symmetry, float)
        assert symmetry == 1.0  # Trivially symmetric when no regions

    def test_empty_html_neutral_symmetry(self):
        """Verify empty HTML returns neutral score."""
        assert calculate_layout_symmetry('') == 0.5
        assert calculate_layout_symmetry('   ') == 0.5

    def test_symmetric_vs_asymmetric_comparison(self):
        """Verify symmetric layout scores higher than asymmetric."""
        html_symmetric = '''<html>
        <body>
            <div class="container">
                <div style="flex: 1;">A</div>
                <div style="flex: 1;">B</div>
                <div style="flex: 1;">C</div>
            </div>
        </body>
        </html>'''

        html_asymmetric = '''<html>
        <body>
            <div class="container">
                <div style="flex: 0.1;">A</div>
                <div style="flex: 0.8;">B</div>
                <div style="flex: 0.1;">C</div>
            </div>
        </body>
        </html>'''

        sym_score = calculate_layout_symmetry(html_symmetric)
        asym_score = calculate_layout_symmetry(html_asymmetric)

        assert sym_score > asym_score


class TestCalculateAccessibilityScore:
    """Test calculate_accessibility_score function."""

    def test_well_formed_html_high_score(self):
        """Verify well-formed HTML with semantics scores high."""
        html = '''<html>
        <head>
            <title>Page Title</title>
        </head>
        <body>
            <h1>Main Heading</h1>
            <nav>Navigation</nav>
            <main>
                <p>Content</p>
            </main>
            <footer>Footer</footer>
        </body>
        </html>'''
        score = calculate_accessibility_score(html)

        assert isinstance(score, (int, float))
        assert 0 <= score <= 100
        assert score >= 50  # Should be reasonably high

    def test_poorly_formed_html_low_score(self):
        """Verify poorly-formed HTML scores lower."""
        html = '<body style="background: #CCCCCC; color: #999999;"><div>Low contrast text</div></body>'
        score = calculate_accessibility_score(html)

        assert isinstance(score, (int, float))
        assert 0 <= score <= 100
        assert score < 50  # Should be relatively low

    def test_well_formed_vs_poorly_formed(self):
        """Verify well-formed scores higher than poorly-formed."""
        html_good = '''<html>
        <head><title>Good</title></head>
        <body>
            <h1>Title</h1>
            <p style="background-color: #FFFFFF; color: #000000;">Good contrast</p>
        </body>
        </html>'''

        html_poor = '''<html>
        <body>
            <div style="background-color: #CCCCCC; color: #999999;">Poor contrast</div>
        </body>
        </html>'''

        score_good = calculate_accessibility_score(html_good)
        score_poor = calculate_accessibility_score(html_poor)

        assert score_good > score_poor

    def test_score_with_image_alt_text(self):
        """Verify images with alt text improve score."""
        html_no_alt = '<html><body><img src="test.jpg"></body></html>'
        html_with_alt = '<html><body><img src="test.jpg" alt="Test image"></body></html>'

        score_no_alt = calculate_accessibility_score(html_no_alt)
        score_with_alt = calculate_accessibility_score(html_with_alt)

        assert score_with_alt >= score_no_alt

    def test_score_with_form_labels(self):
        """Verify form labels improve score."""
        html_no_label = '<html><body><input type="text"></body></html>'
        html_with_label = '<html><body><label>Name</label><input type="text"></body></html>'

        score_no_label = calculate_accessibility_score(html_no_label)
        score_with_label = calculate_accessibility_score(html_with_label)

        assert score_with_label >= score_no_label

    def test_empty_html_very_low_score(self):
        """Verify empty HTML has very low score."""
        assert calculate_accessibility_score('') == 0.0
        assert calculate_accessibility_score('   ') == 0.0

    def test_minimal_html_low_score(self):
        """Verify minimal HTML without semantics has low score."""
        html = '<html><body><div>text</div></body></html>'
        score = calculate_accessibility_score(html)

        assert isinstance(score, (int, float))
        assert 0 <= score <= 100
        assert score >= 20  # At least has required elements (html, body)

    def test_heading_hierarchy(self):
        """Verify proper heading hierarchy improves score."""
        html_no_h1 = '<html><body><h2>Title</h2></body></html>'
        html_with_h1 = '<html><body><h1>Title</h1><h2>Subtitle</h2></body></html>'

        score_no_h1 = calculate_accessibility_score(html_no_h1)
        score_with_h1 = calculate_accessibility_score(html_with_h1)

        assert score_with_h1 >= score_no_h1

    def test_contrast_score_contribution(self):
        """Verify good contrast contributes positively."""
        html_good_contrast = '''<html>
        <body>
            <div style="background-color: #000000; color: #FFFFFF;">High contrast</div>
        </body>
        </html>'''

        html_poor_contrast = '''<html>
        <body>
            <div style="background-color: #CCCCCC; color: #999999;">Low contrast</div>
        </body>
        </html>'''

        score_good = calculate_accessibility_score(html_good_contrast)
        score_poor = calculate_accessibility_score(html_poor_contrast)

        assert score_good > score_poor

    def test_score_range(self):
        """Verify accessibility score always in [0, 100] range."""
        test_htmls = [
            '',
            '<html></html>',
            '<body>text</body>',
            '<html><head><title>T</title></head><body><h1>H1</h1><p>P</p></body></html>',
            '<div style="background: #000; color: #FFF; margin: -1000px;">extreme</div>' * 100,
        ]

        for html in test_htmls:
            score = calculate_accessibility_score(html)
            assert 0 <= score <= 100


class TestExtractResponsiveBreakpoints:
    """Test extract_responsive_breakpoints function."""

    def test_extract_min_width_breakpoint(self):
        """Verify extraction of min-width breakpoint."""
        html = '''<html>
        <head>
            <style>
                @media (min-width: 768px) { .container { width: 750px; } }
            </style>
        </head>
        </html>'''
        breakpoints = extract_responsive_breakpoints(html)

        assert isinstance(breakpoints, list)
        assert 768 in breakpoints

    def test_extract_max_width_breakpoint(self):
        """Verify extraction of max-width breakpoint."""
        html = '''<html>
        <head>
            <style>
                @media (max-width: 1024px) { .container { width: 960px; } }
            </style>
        </head>
        </html>'''
        breakpoints = extract_responsive_breakpoints(html)

        assert isinstance(breakpoints, list)
        assert 1024 in breakpoints

    def test_multiple_breakpoints(self):
        """Verify extraction of multiple breakpoints."""
        html = '''<html>
        <head>
            <style>
                @media (min-width: 480px) { }
                @media (min-width: 768px) { }
                @media (min-width: 1024px) { }
            </style>
        </head>
        </html>'''
        breakpoints = extract_responsive_breakpoints(html)

        assert isinstance(breakpoints, list)
        assert len(breakpoints) >= 3
        assert 480 in breakpoints
        assert 768 in breakpoints
        assert 1024 in breakpoints

    def test_no_breakpoints(self):
        """Verify no breakpoints returns empty list."""
        html = '<html><body>No breakpoints</body></html>'
        breakpoints = extract_responsive_breakpoints(html)

        assert isinstance(breakpoints, list)
        assert len(breakpoints) == 0

    def test_empty_html_no_breakpoints(self):
        """Verify empty HTML returns empty list."""
        assert extract_responsive_breakpoints('') == []
        assert extract_responsive_breakpoints('   ') == []

    def test_sorted_breakpoints(self):
        """Verify breakpoints are returned in sorted order."""
        html = '''<html>
        <head>
            <style>
                @media (min-width: 1024px) { }
                @media (min-width: 480px) { }
                @media (min-width: 768px) { }
            </style>
        </head>
        </html>'''
        breakpoints = extract_responsive_breakpoints(html)

        assert breakpoints == sorted(breakpoints)


class TestEdgeCasesAndDeterminism:
    """Test edge cases and verify determinism."""

    def test_determinism_dom_depth(self):
        """Verify extract_dom_depth is deterministic."""
        html = '<html><body><div><span>text</span></div></body></html>'
        depth1 = extract_dom_depth(html)
        depth2 = extract_dom_depth(html)
        depth3 = extract_dom_depth(html)

        assert depth1 == depth2 == depth3

    def test_determinism_contrast_ratios(self):
        """Verify extract_contrast_ratios is deterministic."""
        html = '<html><body><div style="background-color: #000000; color: #FFFFFF;">Text</div></body></html>'
        ratios1 = extract_contrast_ratios(html)
        ratios2 = extract_contrast_ratios(html)
        ratios3 = extract_contrast_ratios(html)

        assert ratios1 == ratios2 == ratios3

    def test_determinism_layout_symmetry(self):
        """Verify calculate_layout_symmetry is deterministic."""
        html = '''<html>
        <body>
            <div class="container">
                <div style="flex: 1;">A</div>
                <div style="flex: 2;">B</div>
                <div style="flex: 1;">C</div>
            </div>
        </body>
        </html>'''
        sym1 = calculate_layout_symmetry(html)
        sym2 = calculate_layout_symmetry(html)
        sym3 = calculate_layout_symmetry(html)

        assert sym1 == sym2 == sym3

    def test_determinism_accessibility_score(self):
        """Verify calculate_accessibility_score is deterministic."""
        html = '<html><head><title>T</title></head><body><h1>H</h1><p>P</p></body></html>'
        score1 = calculate_accessibility_score(html)
        score2 = calculate_accessibility_score(html)
        score3 = calculate_accessibility_score(html)

        assert score1 == score2 == score3

    def test_no_crash_on_very_malformed_html(self):
        """Verify functions don't crash on very malformed HTML."""
        malformed_htmls = [
            '<html>>><<<>>',
            '<<<HTML>>></div></div>',
            '<div style="background: #!!!; color: @@@;">',
            '<<h1>Heading</>>',
            '\n' * 1000,
        ]

        for html in malformed_htmls:
            # Should not raise exception
            assert isinstance(extract_dom_depth(html), int)
            assert isinstance(extract_contrast_ratios(html), dict)
            assert isinstance(calculate_layout_symmetry(html), float)
            assert isinstance(calculate_accessibility_score(html), (int, float))

    def test_unicode_handling(self):
        """Verify functions handle Unicode gracefully."""
        html = '<html><body><h1>Héllo Wørld</h1><p>日本語テキスト</p></body></html>'

        depth = extract_dom_depth(html)
        assert isinstance(depth, int)
        assert depth >= 1

        symmetry = calculate_layout_symmetry(html)
        assert isinstance(symmetry, float)

        score = calculate_accessibility_score(html)
        assert isinstance(score, (int, float))


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
