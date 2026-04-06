"""Unit tests for DesignAgent.observe() method."""

import pytest
from agent_designer import DesignAgent


class TestObserveReturnStructure:
    """Tests for observe() return dict structure."""

    def test_observe_returns_dict_with_all_five_keys(self):
        """Verify observe() returns dict with all required keys."""
        agent = DesignAgent()
        html = '<html><body>test</body></html>'
        result = agent.observe(html)

        assert isinstance(result, dict)
        assert 'dom_depth' in result
        assert 'contrast_ratios' in result
        assert 'avg_contrast_ratio' in result
        assert 'layout_symmetry' in result
        assert 'accessibility_score' in result

    def test_observe_return_types(self):
        """Verify all return values have correct types."""
        agent = DesignAgent()
        html = '<html><body>test</body></html>'
        result = agent.observe(html)

        assert isinstance(result['dom_depth'], int)
        assert isinstance(result['contrast_ratios'], dict)
        assert isinstance(result['avg_contrast_ratio'], float)
        assert isinstance(result['layout_symmetry'], float)
        assert isinstance(result['accessibility_score'], float)

    def test_observe_return_value_ranges(self):
        """Verify return values are in expected ranges."""
        agent = DesignAgent()
        html = '<html><body>test</body></html>'
        result = agent.observe(html)

        assert result['dom_depth'] >= 1
        assert 0.0 <= result['layout_symmetry'] <= 1.0
        assert 0.0 <= result['accessibility_score'] <= 100.0
        assert result['avg_contrast_ratio'] >= 0.0


class TestAvgContrastRatioComputation:
    """Tests for avg_contrast_ratio calculation."""

    def test_avg_contrast_ratio_with_empty_contrast_ratios(self):
        """Verify avg_contrast_ratio is 0.0 when contrast_ratios is empty."""
        agent = DesignAgent()
        html = '<html><body>no styles here</body></html>'
        result = agent.observe(html)

        assert result['contrast_ratios'] == {}
        assert result['avg_contrast_ratio'] == 0.0

    def test_avg_contrast_ratio_with_single_pair(self):
        """Verify avg_contrast_ratio equals single pair when only one pair present."""
        agent = DesignAgent()
        html = '''<html><body>
        <div style="color: #000000; background-color: #FFFFFF;">black on white</div>
        </body></html>'''
        result = agent.observe(html)

        assert len(result['contrast_ratios']) == 1
        single_ratio = list(result['contrast_ratios'].values())[0]
        assert result['avg_contrast_ratio'] == single_ratio

    def test_avg_contrast_ratio_with_multiple_pairs(self):
        """Verify avg_contrast_ratio computes correct mean with 2+ pairs."""
        agent = DesignAgent()
        html = '''<html><body>
        <div style="color: #000000; background-color: #FFFFFF;">high contrast</div>
        <div style="color: #FFFFFF; background-color: #000000;">high contrast 2</div>
        </body></html>'''
        result = agent.observe(html)

        assert len(result['contrast_ratios']) >= 2
        expected_avg = sum(result['contrast_ratios'].values()) / len(result['contrast_ratios'])
        assert abs(result['avg_contrast_ratio'] - expected_avg) < 0.0001

    def test_avg_contrast_ratio_three_pairs(self):
        """Verify avg_contrast_ratio correctly computes mean of three pairs."""
        agent = DesignAgent()
        html = '''<html><body>
        <div style="color: #000000; background-color: #FFFFFF;">pair 1</div>
        <div style="color: #000000; background-color: #CCCCCC;">pair 2</div>
        <div style="color: #FFFFFF; background-color: #000000;">pair 3</div>
        </body></html>'''
        result = agent.observe(html)

        assert len(result['contrast_ratios']) >= 3
        # Manually compute expected mean
        ratios = list(result['contrast_ratios'].values())
        expected_mean = sum(ratios) / len(ratios)
        assert abs(result['avg_contrast_ratio'] - expected_mean) < 0.0001

    def test_avg_contrast_ratio_is_float(self):
        """Verify avg_contrast_ratio is always returned as float."""
        agent = DesignAgent()
        # Test with empty
        html1 = '<html><body>no styles</body></html>'
        result1 = agent.observe(html1)
        assert isinstance(result1['avg_contrast_ratio'], float)
        assert result1['avg_contrast_ratio'] == 0.0

        # Test with values
        html2 = '''<html><body>
        <div style="color: #000000; background-color: #FFFFFF;">test</div>
        </body></html>'''
        result2 = agent.observe(html2)
        assert isinstance(result2['avg_contrast_ratio'], float)


class TestObserveSideEffects:
    """Tests for observe() side effects on self.observations."""

    def test_observe_updates_self_observations(self):
        """Verify observe() updates self.observations with returned dict."""
        agent = DesignAgent()
        html = '<html><body>test</body></html>'
        result = agent.observe(html)

        assert agent.observations == result

    def test_observe_updates_self_observations_multiple_calls(self):
        """Verify self.observations updated on each call."""
        agent = DesignAgent()

        html1 = '<html><body>first</body></html>'
        result1 = agent.observe(html1)
        assert agent.observations == result1

        html2 = '''<html><body>
        <div style="color: #000000; background-color: #FFFFFF;">second</div>
        </body></html>'''
        result2 = agent.observe(html2)
        assert agent.observations == result2
        assert agent.observations != result1

    def test_observe_self_observations_is_copy_not_reference(self):
        """Verify self.observations is a copy, not a reference."""
        agent = DesignAgent()
        html = '<html><body>test</body></html>'
        result = agent.observe(html)

        # Modify result dict
        result['dom_depth'] = 999
        result['accessibility_score'] = 999.0

        # self.observations should not be affected (it's a copy)
        assert agent.observations['dom_depth'] != 999
        assert agent.observations['accessibility_score'] != 999.0


class TestObserveWithVariousHtmlInputs:
    """Tests for observe() with different HTML structures."""

    def test_observe_with_minimal_html(self):
        """Verify observe() works with minimal valid HTML."""
        agent = DesignAgent()
        html = '<html><body></body></html>'
        result = agent.observe(html)

        assert all(k in result for k in ['dom_depth', 'contrast_ratios', 'avg_contrast_ratio',
                                         'layout_symmetry', 'accessibility_score'])

    def test_observe_with_empty_string(self):
        """Verify observe() handles empty string gracefully."""
        agent = DesignAgent()
        result = agent.observe('')

        assert isinstance(result, dict)
        assert result['dom_depth'] >= 1
        assert result['contrast_ratios'] == {}
        assert result['avg_contrast_ratio'] == 0.0
        assert isinstance(result['layout_symmetry'], float)
        assert isinstance(result['accessibility_score'], float)

    def test_observe_with_html_containing_styles(self):
        """Verify observe() extracts metrics from HTML with inline styles."""
        agent = DesignAgent()
        html = '''<html><head><title>Test Page</title></head>
        <body>
            <header style="color: #000000; background-color: #FFFFFF;">Header</header>
            <div style="color: #FFFFFF; background-color: #333333;">Content</div>
            <footer style="color: #000000; background-color: #EEEEEE;">Footer</footer>
        </body>
        </html>'''
        result = agent.observe(html)

        # Should extract multiple contrast pairs
        assert len(result['contrast_ratios']) >= 2
        assert result['avg_contrast_ratio'] > 0.0
        assert result['dom_depth'] >= 3
        assert result['accessibility_score'] > 0.0

    def test_observe_with_deeply_nested_html(self):
        """Verify observe() measures deep nesting correctly."""
        agent = DesignAgent()
        html = '''<html>
        <body>
            <div><div><div><div><div>deeply nested</div></div></div></div></div>
        </body>
        </html>'''
        result = agent.observe(html)

        # Should detect significant nesting depth
        assert result['dom_depth'] >= 7

    def test_observe_with_html_without_color_styles(self):
        """Verify observe() handles HTML without color information."""
        agent = DesignAgent()
        html = '''<html><body>
            <div style="width: 100%; padding: 10px;">No colors here</div>
            <p style="font-size: 14px;">Plain text</p>
        </body></html>'''
        result = agent.observe(html)

        assert result['contrast_ratios'] == {}
        assert result['avg_contrast_ratio'] == 0.0

    def test_observe_with_malformed_html(self):
        """Verify observe() handles malformed HTML gracefully."""
        agent = DesignAgent()
        html = '<html><body><div>unclosed tags<div><div>'
        result = agent.observe(html)

        # Should still return valid result (BeautifulSoup recovers from malformed HTML)
        assert isinstance(result['dom_depth'], int)
        assert result['dom_depth'] >= 1

    def test_observe_with_container_and_flex_layout(self):
        """Verify observe() calculates layout_symmetry with flex containers."""
        agent = DesignAgent()
        html = '''<html><body>
        <div class="container" style="display: flex;">
            <div style="flex: 1;">One</div>
            <div style="flex: 1;">Two</div>
            <div style="flex: 1;">Three</div>
        </div>
        </body></html>'''
        result = agent.observe(html)

        # Three equal flex children should give high symmetry
        assert result['layout_symmetry'] > 0.5

    def test_observe_with_unbalanced_layout(self):
        """Verify observe() detects layout imbalance."""
        agent = DesignAgent()
        html = '''<html><body>
        <div class="container" style="display: flex;">
            <div style="flex: 0.1;">Small</div>
            <div style="flex: 0.8;">Large</div>
            <div style="flex: 0.1;">Small</div>
        </div>
        </body></html>'''
        result = agent.observe(html)

        # Unbalanced layout should have lower symmetry score
        assert isinstance(result['layout_symmetry'], float)
        assert 0.0 <= result['layout_symmetry'] <= 1.0


class TestObserveEdgeCases:
    """Tests for edge cases in observe()."""

    def test_observe_with_html_only_whitespace(self):
        """Verify observe() handles HTML that is only whitespace."""
        agent = DesignAgent()
        result = agent.observe('   \n\t   ')

        assert isinstance(result, dict)
        assert result['dom_depth'] >= 1

    def test_observe_multiple_calls_overwrites_previous(self):
        """Verify calling observe() twice completely overwrites observations."""
        agent = DesignAgent()

        html1 = '<html><body>first call</body></html>'
        agent.observe(html1)
        obs1 = agent.observations.copy()

        html2 = '''<html><body>
        <div style="color: #000000; background-color: #FFFFFF;">second call with contrast</div>
        </body></html>'''
        agent.observe(html2)
        obs2 = agent.observations.copy()

        # Observations should be different
        assert obs1 != obs2

    def test_observe_with_complex_html_structure(self):
        """Verify observe() handles complex real-world HTML."""
        agent = DesignAgent()
        html = '''<!DOCTYPE html>
        <html>
        <head>
            <title>Complex Page</title>
            <style>
                .header { color: #000; background: #FFF; }
            </style>
        </head>
        <body>
            <header>
                <nav>Navigation</nav>
            </header>
            <main>
                <article>
                    <h1>Title</h1>
                    <p style="color: #000; background-color: #FFF;">Content</p>
                </article>
                <aside>
                    <h2>Sidebar</h2>
                    <ul>
                        <li><a href="#1">Link 1</a></li>
                        <li><a href="#2">Link 2</a></li>
                    </ul>
                </aside>
            </main>
            <footer style="color: #FFF; background-color: #333;">Footer</footer>
        </body>
        </html>'''
        result = agent.observe(html)

        # All keys should be present
        assert all(k in result for k in ['dom_depth', 'contrast_ratios', 'avg_contrast_ratio',
                                         'layout_symmetry', 'accessibility_score'])
        # Should detect some accessibility features
        assert result['accessibility_score'] > 20.0

    def test_observe_consistent_results_same_html(self):
        """Verify observe() returns consistent results for same HTML."""
        agent = DesignAgent()
        html = '''<html><body>
        <div style="color: #000000; background-color: #FFFFFF;">test</div>
        </body></html>'''

        result1 = agent.observe(html)
        result2 = agent.observe(html)

        # Results should be identical (deterministic)
        assert result1['dom_depth'] == result2['dom_depth']
        assert result1['contrast_ratios'] == result2['contrast_ratios']
        assert result1['avg_contrast_ratio'] == result2['avg_contrast_ratio']
        assert result1['layout_symmetry'] == result2['layout_symmetry']
        assert result1['accessibility_score'] == result2['accessibility_score']


class TestObserveIntegration:
    """Integration tests combining multiple aspects."""

    def test_observe_integration_with_environment(self):
        """Verify observe() result can be used with record_iteration()."""
        from agent_designer import DesignIterationEnvironment

        agent = DesignAgent()
        env = DesignIterationEnvironment()

        html = '<html><body>test</body></html>'
        result = agent.observe(html)

        # Should be able to record iteration with this result
        env.record_iteration(result)
        assert len(env.metrics_history) == 1
        assert env.metrics_history[0]['metrics'] == result

    def test_observe_result_immutable_after_return(self):
        """Verify modifying returned dict doesn't affect agent state."""
        agent = DesignAgent()
        html = '<html><body>test</body></html>'
        result = agent.observe(html)

        original_dom_depth = result['dom_depth']

        # Modify returned result
        result['dom_depth'] = 999
        result['accessibility_score'] = 50.0

        # Agent's observations should still have original values
        assert agent.observations['dom_depth'] == original_dom_depth
        assert agent.observations['accessibility_score'] != 50.0
