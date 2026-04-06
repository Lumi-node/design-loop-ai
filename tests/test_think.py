"""Unit tests for DesignAgent.think() method with improvement heuristics."""

import pytest
from agent_designer import DesignAgent, DesignIterationEnvironment


class TestThinkReturnStructure:
    """Tests for think() return structure."""

    def test_think_returns_dict_with_required_keys(self):
        """Verify think() returns dict with all required keys."""
        agent = DesignAgent()
        # First call observe to populate self.observations
        html = '<html><body>test</body></html>'
        agent.observe(html)

        result = agent.think()

        assert isinstance(result, dict)
        assert 'spec_modifications' in result
        assert 'reasoning' in result
        assert 'target_metrics' in result

    def test_think_spec_modifications_has_colors_and_layout(self):
        """Verify spec_modifications has both colors and layout_regions keys."""
        agent = DesignAgent()
        html = '<html><body>test</body></html>'
        agent.observe(html)

        result = agent.think()

        assert isinstance(result['spec_modifications'], dict)
        assert 'colors' in result['spec_modifications']
        assert 'layout_regions' in result['spec_modifications']
        assert isinstance(result['spec_modifications']['colors'], dict)
        assert isinstance(result['spec_modifications']['layout_regions'], dict)

    def test_think_reasoning_is_string(self):
        """Verify reasoning field is a string."""
        agent = DesignAgent()
        html = '<html><body>test</body></html>'
        agent.observe(html)

        result = agent.think()

        assert isinstance(result['reasoning'], str)

    def test_think_target_metrics_has_required_keys(self):
        """Verify target_metrics contains required keys."""
        agent = DesignAgent()
        html = '<html><body>test</body></html>'
        agent.observe(html)

        result = agent.think()

        assert 'target_metrics' in result
        assert isinstance(result['target_metrics'], dict)
        assert 'accessibility_score' in result['target_metrics']
        assert 'layout_symmetry' in result['target_metrics']


class TestThinkContrastHeuristic:
    """Tests for Heuristic 1: Contrast Gap Closure."""

    def test_contrast_heuristic_triggers_below_4_5(self):
        """Verify colors are modified when avg_contrast_ratio < 4.5."""
        agent = DesignAgent()

        # Create observation with low contrast (2.0 < 4.5)
        agent.observations = {
            'avg_contrast_ratio': 2.0,
            'layout_symmetry': 0.6,
            'accessibility_score': 75.0,
            'dom_depth': 5,
            'contrast_ratios': {}
        }

        result = agent.think()

        # Should have color modifications
        assert len(result['spec_modifications']['colors']) > 0
        assert 'Increased contrast' in result['reasoning'] or 'contrast' in result['reasoning'].lower()

    def test_contrast_heuristic_no_change_at_threshold(self):
        """Verify no color changes when avg_contrast_ratio == 4.5."""
        agent = DesignAgent()

        # Create observation at threshold (4.5)
        agent.observations = {
            'avg_contrast_ratio': 4.5,
            'layout_symmetry': 0.6,
            'accessibility_score': 75.0,
            'dom_depth': 5,
            'contrast_ratios': {}
        }

        result = agent.think()

        # Should have no color modifications
        assert len(result['spec_modifications']['colors']) == 0

    def test_contrast_heuristic_no_change_above_4_5(self):
        """Verify no color changes when avg_contrast_ratio > 4.5."""
        agent = DesignAgent()

        # Create observation above threshold (5.0 > 4.5)
        agent.observations = {
            'avg_contrast_ratio': 5.0,
            'layout_symmetry': 0.6,
            'accessibility_score': 75.0,
            'dom_depth': 5,
            'contrast_ratios': {}
        }

        result = agent.think()

        # Should have no color modifications
        assert len(result['spec_modifications']['colors']) == 0

    def test_contrast_heuristic_shift_toward_computation(self):
        """Verify shift_toward computation moves 15% of distance."""
        agent = DesignAgent()

        # Set observations with low contrast
        agent.observations = {
            'avg_contrast_ratio': 2.0,
            'layout_symmetry': 0.6,
            'accessibility_score': 75.0,
            'dom_depth': 5,
            'contrast_ratios': {}
        }

        # Set current spec with gray color
        agent.current_spec = {
            'layout_regions': {},
            'colors': {
                'header': ['#808080'],  # 128, 128, 128
                'sidebar': ['#888888'],
                'content': ['#FFFFFF'],
                'footer': ['#AAAAAA']
            }
        }

        result = agent.think()

        # Header color should shift
        if 'header' in result['spec_modifications']['colors']:
            new_color = result['spec_modifications']['colors']['header'][0]
            # Extract RGB from hex
            r = int(new_color[1:3], 16)
            g = int(new_color[3:5], 16)
            b = int(new_color[5:7], 16)

            # Should shift toward 255 (lighten) from 128
            # 15% of 127 = ~19, so expect ~147
            assert r > 128, f"Red should increase from 128, got {r}"
            assert r <= 128 + 25, f"Red delta should be ≤ 25, got {r - 128}"

    def test_contrast_heuristic_clamps_delta_to_25(self):
        """Verify color delta is clamped to ±25 per iteration."""
        agent = DesignAgent()

        # Set observations with very low contrast
        agent.observations = {
            'avg_contrast_ratio': 0.5,  # Very low
            'layout_symmetry': 0.6,
            'accessibility_score': 75.0,
            'dom_depth': 5,
            'contrast_ratios': {}
        }

        # Set current spec with medium gray
        agent.current_spec = {
            'layout_regions': {},
            'colors': {
                'header': ['#808080'],  # 128, 128, 128
                'sidebar': ['#888888'],
                'content': ['#FFFFFF'],
                'footer': ['#AAAAAA']
            }
        }

        result = agent.think()

        # Verify all color modifications respect ±25 delta bound
        for region, colors in result['spec_modifications']['colors'].items():
            if colors:  # If modification exists
                new_hex = colors[0]
                new_r = int(new_hex[1:3], 16)
                new_g = int(new_hex[3:5], 16)
                new_b = int(new_hex[5:7], 16)

                # Get original
                if agent.current_spec['colors'].get(region):
                    old_hex = agent.current_spec['colors'][region][0]
                    old_r = int(old_hex[1:3], 16)
                    old_g = int(old_hex[3:5], 16)
                    old_b = int(old_hex[5:7], 16)

                    # Check delta is ≤ 25
                    assert abs(new_r - old_r) <= 25, f"Red delta {abs(new_r - old_r)} > 25"
                    assert abs(new_g - old_g) <= 25, f"Green delta {abs(new_g - old_g)} > 25"
                    assert abs(new_b - old_b) <= 25, f"Blue delta {abs(new_b - old_b)} > 25"

    def test_contrast_heuristic_colors_stay_in_bounds(self):
        """Verify all color components stay 0-255."""
        agent = DesignAgent()

        agent.observations = {
            'avg_contrast_ratio': 2.0,
            'layout_symmetry': 0.6,
            'accessibility_score': 75.0,
            'dom_depth': 5,
            'contrast_ratios': {}
        }

        agent.current_spec = {
            'layout_regions': {},
            'colors': {
                'header': ['#000000'],  # Very dark
                'sidebar': ['#FFFFFF'],  # Very light
                'content': ['#FFFFFF'],
                'footer': ['#AAAAAA']
            }
        }

        result = agent.think()

        # Verify all colors are valid hex format and in bounds
        for region, colors in result['spec_modifications']['colors'].items():
            for hex_color in colors:
                assert hex_color.startswith('#'), f"Color must start with #: {hex_color}"
                assert len(hex_color) == 7, f"Color must be #RRGGBB: {hex_color}"
                r = int(hex_color[1:3], 16)
                g = int(hex_color[3:5], 16)
                b = int(hex_color[5:7], 16)
                assert 0 <= r <= 255, f"Red out of bounds: {r}"
                assert 0 <= g <= 255, f"Green out of bounds: {g}"
                assert 0 <= b <= 255, f"Blue out of bounds: {b}"


class TestThinkLayoutHeuristic:
    """Tests for Heuristic 2: Layout Symmetry Balance."""

    def test_layout_heuristic_triggers_below_0_5(self):
        """Verify layout adjustments when layout_symmetry < 0.5."""
        agent = DesignAgent()

        agent.observations = {
            'avg_contrast_ratio': 5.0,
            'layout_symmetry': 0.3,  # Below 0.5
            'accessibility_score': 75.0,
            'dom_depth': 5,
            'contrast_ratios': {}
        }

        result = agent.think()

        # Should have layout modifications
        assert len(result['spec_modifications']['layout_regions']) > 0
        assert 'layout' in result['reasoning'].lower() or 'balance' in result['reasoning'].lower() or 'symm' in result['reasoning'].lower()

    def test_layout_heuristic_no_change_at_threshold(self):
        """Verify no layout changes when layout_symmetry == 0.5."""
        agent = DesignAgent()

        agent.observations = {
            'avg_contrast_ratio': 5.0,
            'layout_symmetry': 0.5,  # At threshold
            'accessibility_score': 75.0,
            'dom_depth': 5,
            'contrast_ratios': {}
        }

        result = agent.think()

        # Should have no layout modifications
        assert len(result['spec_modifications']['layout_regions']) == 0

    def test_layout_heuristic_no_change_above_0_5(self):
        """Verify no layout changes when layout_symmetry > 0.5."""
        agent = DesignAgent()

        agent.observations = {
            'avg_contrast_ratio': 5.0,
            'layout_symmetry': 0.8,  # Above 0.5
            'accessibility_score': 75.0,
            'dom_depth': 5,
            'contrast_ratios': {}
        }

        result = agent.think()

        # Should have no layout modifications
        assert len(result['spec_modifications']['layout_regions']) == 0

    def test_layout_heuristic_adjusts_toward_mean(self):
        """Verify layout adjustments move toward mean by 5 percentage points."""
        agent = DesignAgent()

        agent.observations = {
            'avg_contrast_ratio': 5.0,
            'layout_symmetry': 0.3,
            'accessibility_score': 75.0,
            'dom_depth': 5,
            'contrast_ratios': {}
        }

        agent.current_spec = {
            'layout_regions': {
                'header_height_percent': 8,
                'content_width_percent': 70,
                'footer_height_percent': 8,
                'sidebar_width_percent': 30
            },
            'colors': {}
        }

        result = agent.think()

        # Calculate mean of height percentages: (8 + 8) / 2 = 8
        # Or if considering all layout regions...
        # The adjustments should move toward a more balanced state
        if 'header_height_percent' in result['spec_modifications']['layout_regions']:
            new_val = result['spec_modifications']['layout_regions']['header_height_percent']
            # Should increase by at most 5
            assert new_val <= 8 + 5, f"Adjustment > 5 points: {new_val - 8}"
            assert new_val >= 8 - 5, f"Adjustment < -5 points: {new_val - 8}"

    def test_layout_heuristic_clamps_to_0_100(self):
        """Verify layout adjustments stay within 0-100 percentage range."""
        agent = DesignAgent()

        agent.observations = {
            'avg_contrast_ratio': 5.0,
            'layout_symmetry': 0.3,
            'accessibility_score': 75.0,
            'dom_depth': 5,
            'contrast_ratios': {}
        }

        agent.current_spec = {
            'layout_regions': {
                'header_height_percent': 2,  # Very small, should increase
                'content_width_percent': 70,
                'footer_height_percent': 2,
                'sidebar_width_percent': 30
            },
            'colors': {}
        }

        result = agent.think()

        # Verify all layout values stay 0-100
        for field, value in result['spec_modifications']['layout_regions'].items():
            assert 0 <= value <= 100, f"{field} out of bounds: {value}"

    def test_layout_heuristic_max_adjustment_10_points(self):
        """Verify layout adjustments are clamped to ±10 percentage points per iteration."""
        agent = DesignAgent()

        agent.observations = {
            'avg_contrast_ratio': 5.0,
            'layout_symmetry': 0.1,  # Very low symmetry
            'accessibility_score': 75.0,
            'dom_depth': 5,
            'contrast_ratios': {}
        }

        agent.current_spec = {
            'layout_regions': {
                'header_height_percent': 5,
                'content_width_percent': 70,
                'footer_height_percent': 5,
                'sidebar_width_percent': 30
            },
            'colors': {}
        }

        result = agent.think()

        # Verify all adjustments respect ±10 point bound
        for field, new_val in result['spec_modifications']['layout_regions'].items():
            if field in agent.current_spec['layout_regions']:
                old_val = agent.current_spec['layout_regions'][field]
                delta = abs(new_val - old_val)
                assert delta <= 10, f"{field} delta {delta} exceeds ±10 bound"


class TestThinkAccessibilityHeuristic:
    """Tests for Heuristic 3: Accessibility Score Gap."""

    def test_accessibility_heuristic_low_score_triggers_contrast(self):
        """Verify accessibility < 70 triggers contrast improvement."""
        agent = DesignAgent()

        agent.observations = {
            'avg_contrast_ratio': 2.0,  # Low contrast triggers heuristic 1
            'layout_symmetry': 0.6,
            'accessibility_score': 60.0,  # Below 70
            'dom_depth': 5,
            'contrast_ratios': {}
        }

        agent.current_spec = {
            'layout_regions': {},
            'colors': {
                'header': ['#808080'],
                'sidebar': ['#888888'],
                'content': ['#FFFFFF'],
                'footer': ['#AAAAAA']
            }
        }

        result = agent.think()

        # Should apply contrast improvement
        assert len(result['spec_modifications']['colors']) > 0

    def test_accessibility_heuristic_no_change_at_70(self):
        """Verify no additional changes when accessibility_score == 70."""
        agent = DesignAgent()

        agent.observations = {
            'avg_contrast_ratio': 5.0,  # Good contrast
            'layout_symmetry': 0.6,
            'accessibility_score': 70.0,  # At threshold
            'dom_depth': 5,
            'contrast_ratios': {}
        }

        result = agent.think()

        # Should have no modifications (all heuristics satisfied)
        assert len(result['spec_modifications']['colors']) == 0
        assert len(result['spec_modifications']['layout_regions']) == 0

    def test_accessibility_heuristic_no_change_above_70(self):
        """Verify no changes when accessibility_score > 70 and contrast good."""
        agent = DesignAgent()

        agent.observations = {
            'avg_contrast_ratio': 5.0,
            'layout_symmetry': 0.6,
            'accessibility_score': 80.0,  # Above 70
            'dom_depth': 5,
            'contrast_ratios': {}
        }

        result = agent.think()

        # Should have no modifications
        assert len(result['spec_modifications']['colors']) == 0
        assert len(result['spec_modifications']['layout_regions']) == 0


class TestThinkPreconditions:
    """Tests for preconditions and error handling."""

    def test_think_raises_error_before_observe(self):
        """Verify think() raises ValueError if observe() not called first."""
        agent = DesignAgent()
        # Don't call observe()

        with pytest.raises(ValueError):
            agent.think()

    def test_think_raises_error_with_empty_observations(self):
        """Verify think() raises ValueError if observations empty."""
        agent = DesignAgent()
        agent.observations = {}  # Empty

        with pytest.raises(ValueError):
            agent.think()

    def test_think_raises_error_with_none_observations(self):
        """Verify think() raises ValueError if observations is None."""
        agent = DesignAgent()
        agent.observations = None

        with pytest.raises(ValueError):
            agent.think()

    def test_think_works_after_observe(self):
        """Verify think() works correctly after observe() is called."""
        agent = DesignAgent()
        html = '<html><body>test</body></html>'
        agent.observe(html)

        # Should not raise error
        result = agent.think()
        assert isinstance(result, dict)


class TestThinkReasoningOutput:
    """Tests for reasoning field content."""

    def test_reasoning_empty_when_no_improvements(self):
        """Verify reasoning is appropriate when no improvements needed."""
        agent = DesignAgent()

        agent.observations = {
            'avg_contrast_ratio': 5.0,  # Good
            'layout_symmetry': 0.8,  # Good
            'accessibility_score': 80.0,  # Good
            'dom_depth': 5,
            'contrast_ratios': {}
        }

        result = agent.think()

        # Reasoning should indicate no changes needed or be empty
        assert isinstance(result['reasoning'], str)

    def test_reasoning_includes_contrast_improvement(self):
        """Verify reasoning mentions contrast when improving."""
        agent = DesignAgent()

        agent.observations = {
            'avg_contrast_ratio': 2.0,
            'layout_symmetry': 0.6,
            'accessibility_score': 75.0,
            'dom_depth': 5,
            'contrast_ratios': {}
        }

        result = agent.think()

        # Should mention contrast or improvement
        reasoning_lower = result['reasoning'].lower()
        assert 'contrast' in reasoning_lower or 'improved' in reasoning_lower or 'chang' in reasoning_lower

    def test_reasoning_includes_layout_improvement(self):
        """Verify reasoning mentions layout when improving."""
        agent = DesignAgent()

        agent.observations = {
            'avg_contrast_ratio': 5.0,
            'layout_symmetry': 0.3,
            'accessibility_score': 75.0,
            'dom_depth': 5,
            'contrast_ratios': {}
        }

        result = agent.think()

        # Should mention layout or balance or symmetry
        reasoning_lower = result['reasoning'].lower()
        assert 'layout' in reasoning_lower or 'balanc' in reasoning_lower or 'symm' in reasoning_lower


class TestThinkMultipleHeuristics:
    """Tests combining multiple heuristics."""

    def test_think_applies_both_contrast_and_layout(self):
        """Verify both heuristics applied when both conditions met."""
        agent = DesignAgent()

        agent.observations = {
            'avg_contrast_ratio': 2.0,  # Triggers contrast
            'layout_symmetry': 0.3,  # Triggers layout
            'accessibility_score': 75.0,
            'dom_depth': 5,
            'contrast_ratios': {}
        }

        agent.current_spec = {
            'layout_regions': {
                'header_height_percent': 8,
                'content_width_percent': 70,
                'footer_height_percent': 8,
                'sidebar_width_percent': 30
            },
            'colors': {
                'header': ['#808080'],
                'sidebar': ['#888888'],
                'content': ['#FFFFFF'],
                'footer': ['#AAAAAA']
            }
        }

        result = agent.think()

        # Should have both types of modifications
        assert len(result['spec_modifications']['colors']) > 0
        assert len(result['spec_modifications']['layout_regions']) > 0

    def test_think_target_metrics_reasonable(self):
        """Verify target_metrics are reasonable improvements."""
        agent = DesignAgent()

        agent.observations = {
            'avg_contrast_ratio': 2.0,
            'layout_symmetry': 0.3,
            'accessibility_score': 60.0,
            'dom_depth': 5,
            'contrast_ratios': {}
        }

        result = agent.think()

        # Target metrics should be improvements
        target_acc = result['target_metrics']['accessibility_score']
        target_sym = result['target_metrics']['layout_symmetry']

        # Should target higher values
        assert target_acc >= agent.observations['accessibility_score']
        assert target_sym >= agent.observations['layout_symmetry']
        # But not exceed max
        assert target_acc <= 100.0
        assert target_sym <= 1.0


class TestThinkCurrentSpecTracking:
    """Tests for self.current_spec tracking."""

    def test_think_initializes_current_spec_from_observations(self):
        """Verify think() initializes current_spec if empty."""
        agent = DesignAgent()
        agent.observations = {
            'avg_contrast_ratio': 5.0,
            'layout_symmetry': 0.6,
            'accessibility_score': 75.0,
            'dom_depth': 5,
            'contrast_ratios': {}
        }

        # Without setting current_spec, should still work
        result = agent.think()
        assert isinstance(result, dict)
