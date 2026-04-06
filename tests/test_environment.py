"""Unit tests for DesignIterationEnvironment class."""

import pytest
from agent_designer import DesignIterationEnvironment


class TestDesignIterationEnvironmentInit:
    """Tests for __init__ method."""

    def test_init_with_none_uses_default_spec(self):
        """Verify constructor creates valid default spec."""
        env = DesignIterationEnvironment(initial_spec=None)
        assert env.spec is not None
        assert 'layout_regions' in env.spec
        assert 'colors' in env.spec
        assert env.iteration_count == 0
        assert env.metrics_history == []

    def test_init_with_custom_spec(self):
        """Verify constructor accepts and stores custom spec."""
        custom_spec = {
            'layout_regions': {
                'header_height_percent': 10,
                'content_width_percent': 60,
                'footer_height_percent': 10,
                'sidebar_width_percent': 40
            },
            'colors': {
                'header': ['#FF0000'],
                'sidebar': ['#00FF00'],
                'content': ['#0000FF'],
                'footer': ['#FFFF00']
            }
        }
        env = DesignIterationEnvironment(initial_spec=custom_spec)
        assert env.spec == custom_spec
        assert env.iteration_count == 0
        assert env.metrics_history == []

    def test_default_spec_matches_architecture(self):
        """Verify default spec exactly matches architecture spec."""
        env = DesignIterationEnvironment()
        spec = env.spec

        # Check layout regions
        assert spec['layout_regions']['header_height_percent'] == 8
        assert spec['layout_regions']['content_width_percent'] == 70
        assert spec['layout_regions']['footer_height_percent'] == 8
        assert spec['layout_regions']['sidebar_width_percent'] == 30

        # Check colors
        assert spec['colors']['header'] == ['#AAAAAA']
        assert spec['colors']['sidebar'] == ['#888888']
        assert spec['colors']['content'] == ['#FFFFFF']
        assert spec['colors']['footer'] == ['#AAAAAA']


class TestGetState:
    """Tests for get_state method."""

    def test_get_state_structure(self):
        """Verify get_state returns dict with correct keys."""
        env = DesignIterationEnvironment()
        state = env.get_state()

        assert isinstance(state, dict)
        assert 'spec' in state
        assert 'iteration_count' in state
        assert 'metrics_history' in state
        assert len(state) == 3

    def test_get_state_initial_values(self):
        """Verify get_state returns correct initial values."""
        env = DesignIterationEnvironment()
        state = env.get_state()

        assert state['iteration_count'] == 0
        assert state['metrics_history'] == []
        assert isinstance(state['spec'], dict)

    def test_get_state_returns_copy(self):
        """Verify get_state returns deep copies, not references."""
        env = DesignIterationEnvironment()
        state1 = env.get_state()
        state2 = env.get_state()

        # Modify state1
        state1['spec']['colors']['header'] = ['#000000']
        state1['iteration_count'] = 999

        # Verify state2 and env are unchanged
        assert env.spec['colors']['header'] == ['#AAAAAA']
        assert env.iteration_count == 0
        assert state2['spec']['colors']['header'] == ['#AAAAAA']
        assert state2['iteration_count'] == 0


class TestRecordIteration:
    """Tests for record_iteration method."""

    def test_record_iteration_increments_counter(self):
        """Verify iteration_count increments from 0 to 1 to 2."""
        env = DesignIterationEnvironment()
        metrics = {'dom_depth': 6, 'accessibility_score': 45, 'layout_symmetry': 0.25,
                   'contrast_ratios': {}, 'avg_contrast_ratio': 2.0}

        assert env.iteration_count == 0
        env.record_iteration(metrics)
        assert env.iteration_count == 1
        env.record_iteration(metrics)
        assert env.iteration_count == 2

    def test_record_iteration_appends_metrics(self):
        """Verify metrics_history accumulates with correct structure."""
        env = DesignIterationEnvironment()
        metrics1 = {'dom_depth': 6, 'accessibility_score': 45, 'layout_symmetry': 0.25,
                    'contrast_ratios': {}, 'avg_contrast_ratio': 2.0}
        metrics2 = {'dom_depth': 7, 'accessibility_score': 50, 'layout_symmetry': 0.3,
                    'contrast_ratios': {}, 'avg_contrast_ratio': 2.5}

        env.record_iteration(metrics1)
        assert len(env.metrics_history) == 1
        assert env.metrics_history[0]['iteration_number'] == 0
        assert env.metrics_history[0]['metrics'] == metrics1

        env.record_iteration(metrics2)
        assert len(env.metrics_history) == 2
        assert env.metrics_history[1]['iteration_number'] == 1
        assert env.metrics_history[1]['metrics'] == metrics2

    def test_metrics_history_structure(self):
        """Verify each recorded iteration has correct structure."""
        env = DesignIterationEnvironment()
        metrics = {'dom_depth': 6, 'accessibility_score': 45, 'layout_symmetry': 0.25,
                   'contrast_ratios': {}, 'avg_contrast_ratio': 2.0}

        env.record_iteration(metrics)
        entry = env.metrics_history[0]

        assert 'iteration_number' in entry
        assert 'metrics' in entry
        assert entry['iteration_number'] == 0
        assert entry['metrics'] == metrics

    def test_record_iteration_metrics_stored_as_copy(self):
        """Verify metrics are stored as copies, not references."""
        env = DesignIterationEnvironment()
        metrics = {'dom_depth': 6, 'accessibility_score': 45, 'layout_symmetry': 0.25,
                   'contrast_ratios': {}, 'avg_contrast_ratio': 2.0}

        env.record_iteration(metrics)
        metrics['dom_depth'] = 999

        # Verify stored metrics unchanged
        assert env.metrics_history[0]['metrics']['dom_depth'] == 6


class TestApplySpecModificationsColorValidation:
    """Tests for apply_spec_modifications with color validation."""

    def test_apply_spec_modifications_valid_color_ff0000(self):
        """Valid color #FF0000 passes validation."""
        env = DesignIterationEnvironment()
        modifications = {'colors': {'header': ['#FF0000']}}
        env.apply_spec_modifications(modifications)
        assert env.spec['colors']['header'] == ['#FF0000']

    def test_apply_spec_modifications_valid_color_000000(self):
        """Valid color #000000 passes validation."""
        env = DesignIterationEnvironment()
        modifications = {'colors': {'header': ['#000000']}}
        env.apply_spec_modifications(modifications)
        assert env.spec['colors']['header'] == ['#000000']

    def test_apply_spec_modifications_valid_color_aaaaaa(self):
        """Valid color #AAAAAA passes validation."""
        env = DesignIterationEnvironment()
        modifications = {'colors': {'header': ['#AAAAAA']}}
        env.apply_spec_modifications(modifications)
        assert env.spec['colors']['header'] == ['#AAAAAA']

    def test_apply_spec_modifications_valid_color_lowercase(self):
        """Valid color in lowercase #aabbcc passes validation."""
        env = DesignIterationEnvironment()
        modifications = {'colors': {'header': ['#aabbcc']}}
        env.apply_spec_modifications(modifications)
        assert env.spec['colors']['header'] == ['#aabbcc']

    def test_apply_spec_modifications_invalid_color_gggggg(self):
        """Invalid color #GGGGGG raises ValueError."""
        env = DesignIterationEnvironment()
        modifications = {'colors': {'header': ['#GGGGGG']}}
        with pytest.raises(ValueError, match="Invalid color format"):
            env.apply_spec_modifications(modifications)

    def test_apply_spec_modifications_invalid_color_ff00(self):
        """Invalid color #FF00 (too short) raises ValueError."""
        env = DesignIterationEnvironment()
        modifications = {'colors': {'header': ['#FF00']}}
        with pytest.raises(ValueError, match="Invalid color format"):
            env.apply_spec_modifications(modifications)

    def test_apply_spec_modifications_invalid_color_ff0(self):
        """Invalid color #FF0 (too short) raises ValueError."""
        env = DesignIterationEnvironment()
        modifications = {'colors': {'header': ['#FF0']}}
        with pytest.raises(ValueError, match="Invalid color format"):
            env.apply_spec_modifications(modifications)

    def test_apply_spec_modifications_invalid_color_ff00000(self):
        """Invalid color #FF00000 (too long) raises ValueError."""
        env = DesignIterationEnvironment()
        modifications = {'colors': {'header': ['#FF00000']}}
        with pytest.raises(ValueError, match="Invalid color format"):
            env.apply_spec_modifications(modifications)

    def test_apply_spec_modifications_invalid_color_no_hash(self):
        """Invalid color FF0000 (no hash) raises ValueError."""
        env = DesignIterationEnvironment()
        modifications = {'colors': {'header': ['FF0000']}}
        with pytest.raises(ValueError, match="Invalid color format"):
            env.apply_spec_modifications(modifications)

    def test_apply_spec_modifications_empty_color_list(self):
        """Empty color list raises ValueError."""
        env = DesignIterationEnvironment()
        modifications = {'colors': {'header': []}}
        with pytest.raises(ValueError, match="Colors dict empty"):
            env.apply_spec_modifications(modifications)

    def test_apply_spec_modifications_unknown_color_region(self):
        """Unknown region name raises ValueError."""
        env = DesignIterationEnvironment()
        modifications = {'colors': {'unknown_region': ['#FF0000']}}
        with pytest.raises(ValueError, match="Unknown region"):
            env.apply_spec_modifications(modifications)

    def test_apply_spec_modifications_multiple_colors_in_list(self):
        """Multiple colors in list all validated."""
        env = DesignIterationEnvironment()
        modifications = {'colors': {'header': ['#FF0000', '#00FF00']}}
        env.apply_spec_modifications(modifications)
        assert env.spec['colors']['header'] == ['#FF0000', '#00FF00']

    def test_apply_spec_modifications_multiple_colors_with_invalid(self):
        """Invalid color in list raises ValueError."""
        env = DesignIterationEnvironment()
        modifications = {'colors': {'header': ['#FF0000', '#GGGGGG']}}
        with pytest.raises(ValueError, match="Invalid color format"):
            env.apply_spec_modifications(modifications)


class TestApplySpecModificationsPercentageValidation:
    """Tests for apply_spec_modifications with percentage validation."""

    def test_apply_spec_modifications_valid_percentage_0(self):
        """Percentage 0 passes validation."""
        env = DesignIterationEnvironment()
        modifications = {'layout_regions': {'header_height_percent': 0}}
        env.apply_spec_modifications(modifications)
        assert env.spec['layout_regions']['header_height_percent'] == 0

    def test_apply_spec_modifications_valid_percentage_100(self):
        """Percentage 100 passes validation."""
        env = DesignIterationEnvironment()
        modifications = {'layout_regions': {'header_height_percent': 100}}
        env.apply_spec_modifications(modifications)
        assert env.spec['layout_regions']['header_height_percent'] == 100

    def test_apply_spec_modifications_valid_percentage_50(self):
        """Percentage 50 passes validation."""
        env = DesignIterationEnvironment()
        modifications = {'layout_regions': {'header_height_percent': 50}}
        env.apply_spec_modifications(modifications)
        assert env.spec['layout_regions']['header_height_percent'] == 50

    def test_apply_spec_modifications_invalid_percentage_negative_1(self):
        """Percentage -1 raises ValueError."""
        env = DesignIterationEnvironment()
        modifications = {'layout_regions': {'header_height_percent': -1}}
        with pytest.raises(ValueError, match="Invalid header_height_percent"):
            env.apply_spec_modifications(modifications)

    def test_apply_spec_modifications_invalid_percentage_101(self):
        """Percentage 101 raises ValueError."""
        env = DesignIterationEnvironment()
        modifications = {'layout_regions': {'header_height_percent': 101}}
        with pytest.raises(ValueError, match="Invalid header_height_percent"):
            env.apply_spec_modifications(modifications)

    def test_apply_spec_modifications_invalid_percentage_150(self):
        """Percentage 150 raises ValueError."""
        env = DesignIterationEnvironment()
        modifications = {'layout_regions': {'header_height_percent': 150}}
        with pytest.raises(ValueError, match="Invalid header_height_percent"):
            env.apply_spec_modifications(modifications)

    def test_apply_spec_modifications_invalid_percentage_non_numeric(self):
        """Non-numeric percentage raises ValueError."""
        env = DesignIterationEnvironment()
        modifications = {'layout_regions': {'header_height_percent': 'abc'}}
        with pytest.raises(ValueError, match="Invalid header_height_percent"):
            env.apply_spec_modifications(modifications)

    def test_apply_spec_modifications_unknown_layout_region(self):
        """Unknown layout region name raises ValueError."""
        env = DesignIterationEnvironment()
        modifications = {'layout_regions': {'unknown_field': 50}}
        with pytest.raises(ValueError, match="Unknown region"):
            env.apply_spec_modifications(modifications)

    def test_apply_spec_modifications_multiple_layout_regions(self):
        """Multiple layout regions all validated and applied."""
        env = DesignIterationEnvironment()
        modifications = {
            'layout_regions': {
                'header_height_percent': 10,
                'content_width_percent': 60,
                'footer_height_percent': 15
            }
        }
        env.apply_spec_modifications(modifications)
        assert env.spec['layout_regions']['header_height_percent'] == 10
        assert env.spec['layout_regions']['content_width_percent'] == 60
        assert env.spec['layout_regions']['footer_height_percent'] == 15


class TestApplySpecModificationsWithSpecCopy:
    """Tests for apply_spec_modifications with spec_copy parameter."""

    def test_apply_spec_modifications_with_spec_copy_colors(self):
        """Modifications to spec_copy don't mutate self.spec."""
        env = DesignIterationEnvironment()
        spec_copy = {'layout_regions': env.spec['layout_regions'].copy(),
                     'colors': {k: v.copy() for k, v in env.spec['colors'].items()}}

        modifications = {'colors': {'header': ['#FF0000']}}
        env.apply_spec_modifications(modifications, spec_copy=spec_copy)

        # Verify spec_copy was modified
        assert spec_copy['colors']['header'] == ['#FF0000']

        # Verify self.spec was not modified
        assert env.spec['colors']['header'] == ['#AAAAAA']

    def test_apply_spec_modifications_with_spec_copy_layout(self):
        """Layout modifications to spec_copy don't mutate self.spec."""
        env = DesignIterationEnvironment()
        spec_copy = {'layout_regions': env.spec['layout_regions'].copy(),
                     'colors': {k: v.copy() for k, v in env.spec['colors'].items()}}

        modifications = {'layout_regions': {'header_height_percent': 50}}
        env.apply_spec_modifications(modifications, spec_copy=spec_copy)

        # Verify spec_copy was modified
        assert spec_copy['layout_regions']['header_height_percent'] == 50

        # Verify self.spec was not modified
        assert env.spec['layout_regions']['header_height_percent'] == 8


class TestApplySpecModificationsEdgeCases:
    """Tests for edge cases in apply_spec_modifications."""

    def test_apply_spec_modifications_empty_dict(self):
        """Empty modifications dict passes without error."""
        env = DesignIterationEnvironment()
        original_spec = env.spec.copy()
        env.apply_spec_modifications({})
        assert env.spec == original_spec

    def test_apply_spec_modifications_only_colors(self):
        """Modifications with only colors (no layout_regions)."""
        env = DesignIterationEnvironment()
        modifications = {'colors': {'header': ['#FF0000']}}
        env.apply_spec_modifications(modifications)
        assert env.spec['colors']['header'] == ['#FF0000']
        assert env.spec['layout_regions']['header_height_percent'] == 8  # Unchanged

    def test_apply_spec_modifications_only_layout_regions(self):
        """Modifications with only layout_regions (no colors)."""
        env = DesignIterationEnvironment()
        modifications = {'layout_regions': {'header_height_percent': 15}}
        env.apply_spec_modifications(modifications)
        assert env.spec['layout_regions']['header_height_percent'] == 15
        assert env.spec['colors']['header'] == ['#AAAAAA']  # Unchanged

    def test_apply_spec_modifications_both_colors_and_layout(self):
        """Modifications with both colors and layout_regions."""
        env = DesignIterationEnvironment()
        modifications = {
            'colors': {'header': ['#FF0000']},
            'layout_regions': {'header_height_percent': 15}
        }
        env.apply_spec_modifications(modifications)
        assert env.spec['colors']['header'] == ['#FF0000']
        assert env.spec['layout_regions']['header_height_percent'] == 15

    def test_apply_spec_modifications_multiple_iterations(self):
        """Multiple consecutive modifications work correctly."""
        env = DesignIterationEnvironment()

        mod1 = {'colors': {'header': ['#FF0000']}}
        env.apply_spec_modifications(mod1)
        assert env.spec['colors']['header'] == ['#FF0000']

        mod2 = {'layout_regions': {'header_height_percent': 20}}
        env.apply_spec_modifications(mod2)
        assert env.spec['colors']['header'] == ['#FF0000']  # Still modified
        assert env.spec['layout_regions']['header_height_percent'] == 20


class TestApplySpecModificationsValidationOrder:
    """Tests that validation errors are raised before modifications are applied."""

    def test_validation_error_prevents_modification(self):
        """Invalid modification is rejected, original spec unchanged."""
        env = DesignIterationEnvironment()
        original_header = env.spec['colors']['header'].copy()

        modifications = {'colors': {'header': ['#GGGGGG']}}
        with pytest.raises(ValueError):
            env.apply_spec_modifications(modifications)

        # Verify spec unchanged
        assert env.spec['colors']['header'] == original_header

    def test_partial_modification_with_validation_error(self):
        """If validation fails, no modifications are applied."""
        env = DesignIterationEnvironment()
        original_colors = {k: v.copy() for k, v in env.spec['colors'].items()}
        original_layout = env.spec['layout_regions'].copy()

        # Try to modify with one valid and one invalid color
        modifications = {
            'colors': {'header': ['#GGGGGG'], 'sidebar': ['#FF0000']}
        }

        with pytest.raises(ValueError):
            env.apply_spec_modifications(modifications)

        # Verify neither color was modified (validation happens before application)
        assert env.spec['colors'] == original_colors
        assert env.spec['layout_regions'] == original_layout


class TestComplexScenarios:
    """Tests for complex real-world scenarios."""

    def test_multiple_iterations_with_metrics_accumulation(self):
        """Multiple iterations accumulate metrics correctly."""
        env = DesignIterationEnvironment()

        metrics_list = [
            {'dom_depth': 6, 'accessibility_score': 45, 'layout_symmetry': 0.25,
             'contrast_ratios': {}, 'avg_contrast_ratio': 2.0},
            {'dom_depth': 5, 'accessibility_score': 55, 'layout_symmetry': 0.35,
             'contrast_ratios': {}, 'avg_contrast_ratio': 2.5},
            {'dom_depth': 5, 'accessibility_score': 65, 'layout_symmetry': 0.45,
             'contrast_ratios': {}, 'avg_contrast_ratio': 3.0},
        ]

        for metrics in metrics_list:
            env.record_iteration(metrics)

        assert env.iteration_count == 3
        assert len(env.metrics_history) == 3
        assert env.metrics_history[0]['iteration_number'] == 0
        assert env.metrics_history[1]['iteration_number'] == 1
        assert env.metrics_history[2]['iteration_number'] == 2

    def test_initialization_independence(self):
        """Different environments don't share state."""
        env1 = DesignIterationEnvironment()
        env2 = DesignIterationEnvironment()

        metrics = {'dom_depth': 6, 'accessibility_score': 45, 'layout_symmetry': 0.25,
                   'contrast_ratios': {}, 'avg_contrast_ratio': 2.0}

        env1.record_iteration(metrics)

        assert env1.iteration_count == 1
        assert env2.iteration_count == 0
        assert len(env1.metrics_history) == 1
        assert len(env2.metrics_history) == 0

    def test_spec_independence_across_instances(self):
        """Different environments don't share spec state."""
        env1 = DesignIterationEnvironment()
        env2 = DesignIterationEnvironment()

        mod1 = {'colors': {'header': ['#FF0000']}}
        env1.apply_spec_modifications(mod1)

        assert env1.spec['colors']['header'] == ['#FF0000']
        assert env2.spec['colors']['header'] == ['#AAAAAA']

    def test_custom_spec_independence(self):
        """Custom specs don't share state with default."""
        custom_spec = {
            'layout_regions': {'header_height_percent': 10, 'content_width_percent': 60,
                              'footer_height_percent': 10, 'sidebar_width_percent': 40},
            'colors': {'header': ['#FF0000'], 'sidebar': ['#00FF00'],
                      'content': ['#0000FF'], 'footer': ['#FFFF00']}
        }
        env_custom = DesignIterationEnvironment(initial_spec=custom_spec)
        env_default = DesignIterationEnvironment()

        # Modify custom
        mod = {'colors': {'header': ['#000000']}}
        env_custom.apply_spec_modifications(mod)

        assert env_custom.spec['colors']['header'] == ['#000000']
        assert env_default.spec['colors']['header'] == ['#AAAAAA']
        assert custom_spec['colors']['header'] == ['#FF0000']  # Original not modified
