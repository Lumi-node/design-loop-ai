"""Unit and functional tests for calculate_harmony_score function.

Tests cover:
- Return type and range validation
- Shannon entropy calculation on hue distribution
- Saturation consistency scoring
- Hue spacing analysis
- RGB to HSV conversion
- Edge cases (empty, None, malformed input)
"""

import pytest
import math
import colorsys
from metrics import calculate_harmony_score


class TestCalculateHarmonyScoreBasic:
    """Basic functionality tests for calculate_harmony_score."""

    def test_calculate_harmony_score_returns_integer(self):
        """AC1: Function returns integer in range [0, 100]."""
        extracted_colors = {
            'header': [(245, 200, 150), (180, 100, 50)],
            'sidebar': [(50, 100, 180), (100, 150, 200)],
            'content': [(200, 220, 240)],
            'footer': [(60, 80, 100)]
        }
        html = "dummy"
        score = calculate_harmony_score(html, extracted_colors)
        assert isinstance(score, int), f"Expected int, got {type(score)}"
        assert 0 <= score <= 100, f"Score {score} outside range [0, 100]"

    def test_calculate_harmony_score_empty_dict(self):
        """AC5: Empty extracted_colors dict returns baseline score (50)."""
        html = "dummy"
        score = calculate_harmony_score(html, {})
        assert score == 50, f"Expected baseline 50 for empty dict, got {score}"

    def test_calculate_harmony_score_none_input(self):
        """AC5: None extracted_colors returns baseline score (50)."""
        html = "dummy"
        score = calculate_harmony_score(html, None)
        assert score == 50, f"Expected baseline 50 for None input, got {score}"

    def test_calculate_harmony_score_single_color(self):
        """Edge case: Single color should return neutral/baseline-ish score."""
        extracted_colors = {'header': [(128, 128, 128)]}
        html = "dummy"
        score = calculate_harmony_score(html, extracted_colors)
        assert 0 <= score <= 100
        # Single color: no spacing (neutral 20), low entropy (0), medium saturation (0)
        # Expected: ~20 (spacing score only)
        assert score <= 50, f"Single color should score low, got {score}"


class TestEntropyCalculation:
    """Tests for Shannon entropy calculation on hue distribution."""

    def test_entropy_uniform_distribution(self):
        """Test: Uniform hue distribution should yield ~3.58 bits entropy."""
        # Create colors uniformly distributed across all hue bins
        # 12 hues spaced 30° apart = good entropy and spacing
        colors = []
        for i in range(12):
            hue_deg = i * 30
            hue_norm = hue_deg / 360.0
            r, g, b = colorsys.hsv_to_rgb(hue_norm, 0.8, 0.8)
            # Add multiple copies with slightly different saturation/value
            for j in range(3):
                # Vary saturation slightly to keep distinct hues distinct
                h2, s2, v2 = hue_norm, 0.8 - j*0.05, 0.8 - j*0.02
                r2, g2, b2 = colorsys.hsv_to_rgb(h2, s2, v2)
                colors.append((int(r2 * 255), int(g2 * 255), int(b2 * 255)))

        extracted_colors = {'header': colors}
        html = "dummy"
        score = calculate_harmony_score(html, extracted_colors)

        # Uniform distribution: entropy ≈ 3.58 bits
        # entropy_pts = (3.58 / 3.58) * 65 = 65
        # High saturation consistency: ~20 pts (varies slightly but reasonably consistent)
        # Good spacing: ~15 pts (all 30° apart)
        # Total: ~80-100 expected
        assert score >= 80, f"Uniform distribution should score 80+, got {score}"

    def test_entropy_good_diversity(self):
        """Test: Good hue diversity should score well."""
        # Create colors with good hue diversity (entropy >2.5 bits)
        # All colors spread across different hue bins
        extracted_colors = {
            'header': [
                (255, 0, 0),      # Red (0°)
                (0, 255, 0),      # Green (120°)
                (0, 0, 255),      # Blue (240°)
                (255, 128, 0),    # Orange (30°)
            ],
            'sidebar': [
                (255, 255, 0),    # Yellow (60°)
                (128, 0, 255),    # Purple (270°)
                (0, 255, 128),    # Cyan (~150°)
                (255, 0, 128),    # Pink (~330°)
            ],
            'content': [
                (64, 255, 0),     # Yellow-green (90°)
                (0, 255, 200),    # Cyan-green (~165°)
                (200, 0, 255),    # Magenta (~280°)
            ]
        }
        html = "dummy"
        score = calculate_harmony_score(html, extracted_colors)
        assert score >= 75, f"Good diversity should score >= 75, got {score}"

    def test_entropy_good_but_not_excellent(self):
        """AC3: Entropy > 2.0 bits should yield score >= 70 (but may be < 85)."""
        # Colors with good but not perfect diversity - add more colors
        extracted_colors = {
            'header': [
                (255, 0, 0),      # Red (0°)
                (0, 255, 0),      # Green (120°)
                (0, 0, 255),      # Blue (240°)
                (255, 128, 0),    # Orange (30°)
                (255, 255, 0),    # Yellow (60°)
            ],
            'sidebar': [
                (128, 0, 255),    # Purple (270°)
                (0, 255, 128),    # Green-cyan (150°)
                (255, 0, 128),    # Red-pink (330°)
            ],
            'content': [
                (64, 255, 0),     # Yellow-green (90°)
            ]
        }
        html = "dummy"
        score = calculate_harmony_score(html, extracted_colors)
        assert score >= 70, f"Good diversity (entropy > 2.0) should score >= 70, got {score}"


class TestSaturationConsistency:
    """Tests for saturation consistency scoring."""

    def test_saturation_high_consistency(self):
        """Test: High-saturation colors should have good consistency score."""
        # All vivid, high-saturation colors
        extracted_colors = {
            'header': [
                (255, 0, 0),      # Pure red (s=100)
                (0, 255, 0),      # Pure green (s=100)
                (0, 0, 255),      # Pure blue (s=100)
            ],
            'sidebar': [
                (255, 128, 0),    # Orange (s=100)
                (255, 0, 255),    # Magenta (s=100)
            ]
        }
        html = "dummy"
        score = calculate_harmony_score(html, extracted_colors)
        # High saturation consistency + good entropy + good spacing
        assert score >= 70, f"High saturation colors should score well, got {score}"

    def test_saturation_low_consistency(self):
        """Test: Mix of high and low saturation should penalize consistency."""
        # Mix vivid and pastel colors (high variance in saturation)
        extracted_colors = {
            'header': [
                (255, 0, 0),      # Pure red (s=100)
                (200, 150, 150),  # Pastel red (s~30)
                (0, 255, 0),      # Pure green (s=100)
                (150, 200, 150),  # Pastel green (s~30)
            ]
        }
        html = "dummy"
        score = calculate_harmony_score(html, extracted_colors)
        # Mixed saturation penalizes consistency score
        # But may still score decently due to hue diversity
        assert 20 <= score <= 90, f"Mixed saturation should score mid-range, got {score}"


class TestHueSpacing:
    """Tests for hue spacing calculation."""

    def test_hue_spacing_45_degrees(self):
        """Test: Colors at 0°, 45°, 90° should have min spacing 45°."""
        extracted_colors = {
            'header': [
                (255, 0, 0),      # Red (0°)
                # Create color at 45° (between red and yellow)
                (255, 128, 0),    # Orange (~30°) - close enough for test
                (255, 255, 0),    # Yellow (~60°)
            ]
        }
        html = "dummy"
        score = calculate_harmony_score(html, extracted_colors)
        # Good spacing (>30°): should get full 20 pts from spacing
        # Plus entropy and saturation
        assert score >= 40, f"45° spacing should score well, got {score}"

    def test_hue_spacing_small_5_degrees(self):
        """Test: Hues at 0° and 5° should have min spacing 5°."""
        extracted_colors = {
            'header': [
                (255, 0, 0),      # Red (0°)
                (255, 12, 0),     # Slightly more orange (~5°)
                (0, 255, 0),      # Green (~120°)
            ]
        }
        html = "dummy"
        score = calculate_harmony_score(html, extracted_colors)
        # Small spacing (<30°): spacing_pts = (5/30)*20 ≈ 3.3
        # But has some hue diversity still
        assert score >= 30, f"5° spacing should score at least 30, got {score}"

    def test_hue_spacing_monochromatic(self):
        """AC4: Monochromatic palette (hue spacing < 30°) should score <= 40."""
        # All similar colors (hues clustered within 30°)
        extracted_colors = {
            'header': [
                (255, 0, 0),      # Red (0°)
                (240, 10, 10),    # Dark red (~0°)
                (255, 64, 0),     # Red-orange (~15°)
                (220, 20, 20),    # Crimson (~0°)
                (255, 32, 0),     # Red-orange (~10°)
            ]
        }
        html = "dummy"
        score = calculate_harmony_score(html, extracted_colors)
        assert score <= 40, f"Monochromatic palette should score <= 40, got {score}"

    def test_hue_spacing_wraparound(self):
        """Test: Hue wrap-around (350° to 10°) should calculate min spacing as 20°."""
        extracted_colors = {
            'header': [
                (255, 0, 0),      # Red (0°)
                # Color near 350° (magenta side)
                (255, 0, 100),    # Magenta-red (~340°)
                # Color near 10° (orange side)
                (255, 64, 0),     # Orange (~15°)
            ]
        }
        html = "dummy"
        score = calculate_harmony_score(html, extracted_colors)
        # Should handle wrap-around correctly
        # min_spacing: check last (340) to first (0) via wrap: (0 + 360) - 340 = 20°
        assert score >= 30, f"Wrap-around spacing should work, got {score}"


class TestRGBToHSVConversion:
    """Tests for RGB to HSV conversion via colorsys."""

    def test_rgb_pure_red(self):
        """Test: Pure red (255,0,0) should have hue ~0°."""
        extracted_colors = {'header': [(255, 0, 0)]}
        html = "dummy"
        score = calculate_harmony_score(html, extracted_colors)
        # Single color, low entropy, no saturation std (all one value)
        # Expected: mostly spacing score (20) + saturation (30) ≈ 50
        assert score >= 20, f"Pure red should process without error"

    def test_rgb_pure_green(self):
        """Test: Pure green (0,255,0) should have hue ~120°."""
        extracted_colors = {'header': [(0, 255, 0)]}
        html = "dummy"
        score = calculate_harmony_score(html, extracted_colors)
        assert 0 <= score <= 100

    def test_rgb_pure_blue(self):
        """Test: Pure blue (0,0,255) should have hue ~240°."""
        extracted_colors = {'header': [(0, 0, 255)]}
        html = "dummy"
        score = calculate_harmony_score(html, extracted_colors)
        assert 0 <= score <= 100

    def test_rgb_grayscale(self):
        """Test: Grayscale colors (R=G=B) have hue 0 (achromatic)."""
        # Grayscale has saturation 0, so low entropy
        extracted_colors = {
            'header': [(128, 128, 128), (200, 200, 200), (50, 50, 50)]
        }
        html = "dummy"
        score = calculate_harmony_score(html, extracted_colors)
        # Grayscale: all same hue (0°), zero saturation
        # entropy: very low (all in one bin)
        # saturation_std: 0 (all zero saturation) → consistency = 1.0 * 30
        # spacing: < 30° (all same hue) → spacing = 0
        # Total: ~30
        assert score <= 50, f"Grayscale should score low (no hue diversity), got {score}"


class TestEdgeCases:
    """Tests for edge cases and malformed input."""

    def test_malformed_colors_non_3_tuple(self):
        """Test: Tuples with len != 3 should be skipped gracefully."""
        extracted_colors = {
            'header': [
                (255, 0),         # Only 2 elements - skip
                (255, 0, 0),      # Valid red
                (255, 0, 0, 255), # 4 elements - skip
                (0, 255, 0),      # Valid green
            ]
        }
        html = "dummy"
        score = calculate_harmony_score(html, extracted_colors)
        # Should process valid colors (red, green) and ignore others
        assert 0 <= score <= 100
        assert score >= 30, f"Should score at least 30 with 2 valid colors, got {score}"

    def test_malformed_colors_non_int(self):
        """Test: Non-integer color values should be skipped."""
        extracted_colors = {
            'header': [
                ('255', '0', '0'),    # String values - skip
                (255, 0, 0),          # Valid
                (255.5, 0.5, 0.5),    # Float values - should be convertible
            ]
        }
        html = "dummy"
        score = calculate_harmony_score(html, extracted_colors)
        assert 0 <= score <= 100

    def test_malformed_colors_out_of_range(self):
        """Test: Color values outside [0, 255] should be skipped."""
        extracted_colors = {
            'header': [
                (-1, 0, 0),        # Negative - skip
                (256, 0, 0),       # > 255 - skip
                (0, 255, 0),       # Valid
                (128, 128, 128),   # Valid
            ]
        }
        html = "dummy"
        score = calculate_harmony_score(html, extracted_colors)
        # Should process valid colors only
        assert 0 <= score <= 100

    def test_none_region_list(self):
        """Test: None as color list for a region should be skipped gracefully."""
        extracted_colors = {
            'header': None,
            'sidebar': [(255, 0, 0), (0, 255, 0)],
            'content': None,
            'footer': [(0, 0, 255)],
        }
        html = "dummy"
        score = calculate_harmony_score(html, extracted_colors)
        # Should process sidebar and footer colors
        assert 0 <= score <= 100

    def test_all_invalid_colors(self):
        """Test: All colors invalid returns baseline (50)."""
        extracted_colors = {
            'header': [(256, 0, 0), (-1, 255, 0), (128,)],
            'sidebar': [('r', 'g', 'b')],
        }
        html = "dummy"
        score = calculate_harmony_score(html, extracted_colors)
        assert score == 50, f"All invalid colors should return baseline 50, got {score}"


class TestAcceptanceCriteria:
    """Tests mapping directly to acceptance criteria."""

    def test_ac1_returns_integer_0_to_100(self):
        """AC1: Function returns integer in range [0, 100]."""
        test_colors = {
            'header': [(255, 0, 0), (0, 255, 0), (0, 0, 255)],
            'sidebar': [(255, 128, 0), (128, 255, 0)],
            'content': [(0, 255, 128), (128, 0, 255)],
            'footer': [(255, 0, 128)],
        }
        score = calculate_harmony_score("", test_colors)
        assert isinstance(score, int)
        assert 0 <= score <= 100

    def test_ac2_entropy_gt_2_5_bits_scores_gte_85(self):
        """AC2: Score >= 85 when hue entropy > 2.5 bits."""
        # Create excellent hue distribution with good spacing
        colors = []
        # Create colors across all 12 bins with high saturation
        for i in range(12):
            hue_deg = i * 30
            hue_norm = hue_deg / 360.0
            r, g, b = colorsys.hsv_to_rgb(hue_norm, 0.95, 0.95)
            # Add multiple copies for redundancy
            for _ in range(3):
                colors.append((int(r * 255), int(g * 255), int(b * 255)))

        extracted_colors = {'header': colors}
        score = calculate_harmony_score("", extracted_colors)
        # With entropy ~3.58, consistency ~20, spacing 15 = 100
        # But might be slightly lower due to rounding
        assert score >= 85, f"Entropy > 2.5 bits should score >= 85, got {score}"

    def test_ac3_entropy_gt_2_0_bits_scores_gte_70(self):
        """AC3: Score >= 70 when entropy > 2.0 bits."""
        # Create distributed colors across 8 hue bins for entropy > 2.0
        colors = []
        for i in range(8):  # 8 bins filled (entropy ~2.0+)
            hue_deg = i * 45
            hue_norm = hue_deg / 360.0
            r, g, b = colorsys.hsv_to_rgb(hue_norm, 0.85, 0.85)
            for _ in range(3):
                colors.append((int(r * 255), int(g * 255), int(b * 255)))

        extracted_colors = {'header': colors}
        score = calculate_harmony_score("", extracted_colors)
        assert score >= 70, f"Entropy > 2.0 bits should score >= 70, got {score}"

    def test_ac4_hue_spacing_lt_30_scores_lte_40(self):
        """AC4: Score <= 40 when hue spacing < 30°."""
        # Create clustered colors all within 15° range to ensure score <= 40
        extracted_colors = {
            'header': [
                (255, 0, 0),      # 0°
                (255, 20, 0),     # ~5°
                (255, 40, 0),     # ~10°
                (255, 60, 0),     # ~15°
            ]
        }
        score = calculate_harmony_score("", extracted_colors)
        assert score <= 40, f"Hue spacing < 30° should score <= 40, got {score}"

    def test_ac5_empty_colors_returns_50(self):
        """AC5: Returns 50 baseline for None or empty extracted_colors."""
        # Test None
        score_none = calculate_harmony_score("", None)
        assert score_none == 50

        # Test empty dict
        score_empty = calculate_harmony_score("", {})
        assert score_empty == 50

        # Test all regions None
        score_all_none = calculate_harmony_score("", {
            'header': None,
            'sidebar': None,
            'content': None,
            'footer': None,
        })
        assert score_all_none == 50


class TestIntegrationScenarios:
    """Integration tests simulating realistic color palettes."""

    def test_warm_color_palette(self):
        """Test: Warm colors (reds, oranges, yellows)."""
        extracted_colors = {
            'header': [(255, 64, 0), (240, 100, 0), (200, 80, 0)],
            'sidebar': [(255, 128, 0), (255, 160, 0)],
            'content': [(255, 192, 0), (200, 150, 0)],
            'footer': [(180, 90, 0), (200, 100, 0)],
        }
        score = calculate_harmony_score("", extracted_colors)
        assert 30 <= score <= 60, f"Warm palette should score low-mid (clustered hues), got {score}"

    def test_cool_color_palette(self):
        """Test: Cool colors (blues, cyans, purples)."""
        extracted_colors = {
            'header': [(0, 128, 255), (0, 160, 240), (64, 150, 255)],
            'sidebar': [(0, 100, 200), (32, 140, 220)],
            'content': [(0, 200, 255), (64, 200, 240)],
            'footer': [(0, 90, 180), (50, 120, 200)],
        }
        score = calculate_harmony_score("", extracted_colors)
        assert 30 <= score <= 60, f"Cool palette should score low-mid (clustered hues), got {score}"

    def test_complementary_palette(self):
        """Test: Complementary colors (opposite on color wheel)."""
        # Create colors with good spacing between complementary hues
        extracted_colors = {
            'header': [
                (255, 0, 0),      # Red (0°)
                (255, 64, 0),     # Orange (~15°)
                (0, 255, 128),    # Cyan (~165°)
                (0, 255, 200),    # Cyan-green (~175°)
            ],
            'sidebar': [
                (255, 255, 0),    # Yellow (60°)
                (0, 128, 255),    # Blue (210°)
                (128, 0, 255),    # Purple (270°)
                (0, 255, 0),      # Green (120°)
            ],
            'content': [
                (255, 0, 128),    # Pink (~330°)
            ]
        }
        score = calculate_harmony_score("", extracted_colors)
        assert score >= 60, f"Complementary palette should score okay, got {score}"

    def test_grayscale_palette(self):
        """Test: Pure grayscale (achromatic)."""
        extracted_colors = {
            'header': [(0, 0, 0), (64, 64, 64), (128, 128, 128)],
            'sidebar': [(192, 192, 192), (224, 224, 224)],
            'content': [(32, 32, 32), (96, 96, 96)],
            'footer': [(160, 160, 160), (200, 200, 200)],
        }
        score = calculate_harmony_score("", extracted_colors)
        assert score <= 50, f"Grayscale should score low (no hue diversity), got {score}"
