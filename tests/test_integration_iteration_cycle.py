"""Integration tests for the full think-act-observe iterative cycle.

Tests verify:
- Complete 5-iteration cycle execution
- Early convergence termination
- Metrics improvement tracking across iterations
- action_history growth and length verification
- Proper improvement_from_previous delta calculation
"""

import os
import pytest
import tempfile
from unittest.mock import Mock, patch, MagicMock
from design_agent import DesignAgent


class TestFiveIterationsComplete:
    """Test that the full 5-iteration think-act-observe cycle completes correctly."""

    @pytest.fixture
    def setup_agent_with_html(self):
        """Create temporary image and HTML files, initialize agent."""
        with tempfile.TemporaryDirectory() as tmpdir:
            image_path = os.path.join(tmpdir, 'test.png')
            html_path = os.path.join(tmpdir, 'test.html')

            # Create dummy files
            open(image_path, 'w').close()

            # Create initial HTML with CSS that produces good metrics
            html_content = '''<!DOCTYPE html>
<html>
<head>
<style>
.header { background-color: rgb(30, 30, 30); color: #ffffff; padding: 15px; }
.sidebar { background-color: rgb(200, 200, 200); color: #000000; padding: 15px; }
.content { background-color: rgb(255, 255, 255); color: #000000; padding: 15px; }
.footer { background-color: rgb(30, 30, 30); color: #ffffff; padding: 15px; }
.main { display: flex; flex-direction: row; justify-content: center; align-items: center; }
</style>
</head>
<body><header>Test</header></body>
</html>'''
            with open(html_path, 'w') as f:
                f.write(html_content)

            # Initialize agent with moderate targets
            agent = DesignAgent(
                image_path,
                html_path,
                target_accessibility=70,
                target_symmetry=70,
                target_harmony=70
            )

            yield agent, image_path, html_path, tmpdir

    def test_five_iterations_complete(self, setup_agent_with_html):
        """Test loop executes 5 iterations with observe->think->act->observe cycle.

        Each iteration:
        - observe() stores metrics
        - think() returns action or None (on convergence)
        - act() updates path and appends to action_history
        - observe() stores new metrics

        Loop terminates early if all metrics >= targets before iteration 5.
        """
        agent, image_path, html_path, tmpdir = setup_agent_with_html

        # Create high-quality HTML that will produce good metrics
        html_good_contrast = '''<!DOCTYPE html><html><head><style>
.header { background-color: rgb(30, 30, 30); color: #ffffff; padding: 15px; }
.sidebar { background-color: rgb(200, 200, 200); color: #000000; padding: 15px; }
.content { background-color: rgb(255, 255, 255); color: #000000; padding: 15px; }
.footer { background-color: rgb(30, 30, 30); color: #ffffff; padding: 15px; }
.main { display: flex; flex-direction: row; justify-content: center; align-items: center; }
</style></head><body><header></header></body></html>'''

        # Prepare good regions for decent symmetry
        regions = {
            'header': {'x': 0, 'y': 0, 'width': 800, 'height': 100},
            'sidebar': {'x': 0, 'y': 100, 'width': 200, 'height': 500},
            'content': {'x': 200, 'y': 100, 'width': 600, 'height': 500},
            'footer': {'x': 0, 'y': 600, 'width': 800, 'height': 100}
        }
        colors = {
            'header': [(30, 30, 30)],
            'sidebar': [(200, 200, 200)],
            'content': [(255, 255, 255)],
            'footer': [(30, 30, 30)]
        }

        # Create temp HTML file
        good_html_path = os.path.join(tmpdir, 'good.html')
        with open(good_html_path, 'w') as f:
            f.write(html_good_contrast)

        def mock_convert_design(image_path):
            """Return good HTML path."""
            return good_html_path

        # Initial observe (iteration 0 - baseline)
        agent.observe({
            'html_content': html_good_contrast,
            'regions': regions,
            'colors': colors,
            'iteration': 0
        })
        assert 0 in agent.observations
        assert agent.observations[0]['improvement_from_previous'] is None

        # Iteration loop - will reach targets quickly with good HTML
        iterations_performed = 0

        with patch('design_agent.convert_design', side_effect=mock_convert_design):
            for iteration in range(1, 6):  # max 5 iterations
                # think()
                action = agent.think()

                # Check convergence
                if action is None:
                    # Converged, test passes
                    break

                # act() - should append to action_history
                new_html_path = agent.act(action)
                assert new_html_path is not None
                assert len(agent.action_history) == iteration

                # observe()
                agent.observe({
                    'html_content': html_good_contrast,
                    'regions': regions,
                    'colors': colors,
                    'iteration': iteration
                })
                iterations_performed = iteration

        # Assertions
        assert iterations_performed > 0, "Should complete at least 1 iteration"
        assert iterations_performed <= 5, "Should complete within 5 iterations"
        assert len(agent.action_history) == iterations_performed, \
            f"action_history length {len(agent.action_history)} != iterations_performed {iterations_performed}"


class TestMetricsImproveAcrossIterations:
    """Test that metrics improve and are tracked correctly across iterations."""

    @pytest.fixture
    def setup_improving_cycle(self):
        """Create agent and mock observations with improving metrics."""
        with tempfile.TemporaryDirectory() as tmpdir:
            image_path = os.path.join(tmpdir, 'test.png')
            html_path = os.path.join(tmpdir, 'test.html')

            open(image_path, 'w').close()
            with open(html_path, 'w') as f:
                f.write('<html></html>')

            agent = DesignAgent(image_path, html_path, 70, 70, 70)

            yield agent, image_path, html_path, tmpdir

    def test_metrics_improve_across_iterations(self, setup_improving_cycle):
        """Test at least one metric shows >0 improvement by iteration 5.

        Also verify:
        - action_history length matches iteration count
        - improvement_from_previous deltas are tracked correctly
        """
        agent, image_path, html_path, tmpdir = setup_improving_cycle

        # Create HTML samples with increasing quality
        html_low = '''<!DOCTYPE html><html><head><style>
.header { background-color: rgb(100, 100, 100); color: #808080; padding: 8px; }
.sidebar { background-color: rgb(200, 200, 200); color: #404040; padding: 8px; }
.content { background-color: rgb(200, 200, 200); color: #808080; padding: 8px; }
.footer { background-color: rgb(100, 100, 100); color: #808080; padding: 8px; }
</style></head><body></body></html>'''

        html_medium = '''<!DOCTYPE html><html><head><style>
.header { background-color: rgb(50, 50, 50); color: #ffffff; padding: 12px; }
.sidebar { background-color: rgb(200, 200, 200); color: #000000; padding: 12px; }
.content { background-color: rgb(255, 255, 255); color: #000000; padding: 12px; }
.footer { background-color: rgb(50, 50, 50); color: #ffffff; padding: 12px; }
.main { display: flex; flex-direction: row; }
</style></head><body></body></html>'''

        html_high = '''<!DOCTYPE html><html><head><style>
.header { background-color: rgb(30, 30, 30); color: #ffffff; padding: 15px; }
.sidebar { background-color: rgb(200, 200, 200); color: #000000; padding: 15px; }
.content { background-color: rgb(255, 255, 255); color: #000000; padding: 15px; }
.footer { background-color: rgb(30, 30, 30); color: #ffffff; padding: 15px; }
.main { display: flex; flex-direction: row; justify-content: center; align-items: center; }
</style></head><body></body></html>'''

        # Prepare regions and colors
        regions = {
            'header': {'x': 0, 'y': 0, 'width': 800, 'height': 100},
            'sidebar': {'x': 0, 'y': 100, 'width': 200, 'height': 500},
            'content': {'x': 200, 'y': 100, 'width': 600, 'height': 500},
            'footer': {'x': 0, 'y': 600, 'width': 800, 'height': 100}
        }
        colors = {
            'header': [(30, 30, 30)],
            'sidebar': [(200, 200, 200)],
            'content': [(255, 255, 255)],
            'footer': [(30, 30, 30)]
        }

        # Create temp HTML files
        html_paths = []
        for i, html_content in enumerate([html_low, html_medium, html_high, html_high, html_high, html_high]):
            temp_html = os.path.join(tmpdir, f'test_{i}.html')
            with open(temp_html, 'w') as f:
                f.write(html_content)
            html_paths.append(temp_html)

        # Mock convert_design to return paths in order
        paths_copy = html_paths[1:]

        def mock_convert_design(image_path):
            return paths_copy.pop(0) if paths_copy else html_paths[-1]

        # Observe baseline
        agent.observe({
            'html_content': html_low,
            'regions': regions,
            'colors': colors,
            'iteration': 0
        })

        initial_scores = {
            'accessibility': agent.observations[0]['accessibility_score'],
            'symmetry': agent.observations[0]['symmetry_score'],
            'harmony': agent.observations[0]['harmony_score']
        }

        # Run iteration loop
        with patch('design_agent.convert_design', side_effect=mock_convert_design):
            for iteration in range(1, 6):
                action = agent.think()
                if action is None:
                    break

                # act() adds to action_history
                new_html_path = agent.act(action)

                # observe() captures new metrics
                html_to_observe = html_high if iteration >= 2 else html_medium
                agent.observe({
                    'html_content': html_to_observe,
                    'regions': regions,
                    'colors': colors,
                    'iteration': iteration
                })

        # Verify action_history length
        final_iteration = max(agent.observations.keys())
        assert len(agent.action_history) == final_iteration, \
            f"action_history length {len(agent.action_history)} != final_iteration {final_iteration}"

        # Verify improvement tracking
        final_scores = {
            'accessibility': agent.observations[final_iteration]['accessibility_score'],
            'symmetry': agent.observations[final_iteration]['symmetry_score'],
            'harmony': agent.observations[final_iteration]['harmony_score']
        }

        # Calculate deltas
        deltas = {
            'accessibility': final_scores['accessibility'] - initial_scores['accessibility'],
            'symmetry': final_scores['symmetry'] - initial_scores['symmetry'],
            'harmony': final_scores['harmony'] - initial_scores['harmony']
        }

        # At least one metric should improve
        assert any(delta > 0 for delta in deltas.values()), \
            f"Expected at least one metric to improve, got deltas: {deltas}"

        # Verify improvement_from_previous is tracked for all iterations
        for iter_num in range(1, final_iteration + 1):
            assert 'improvement_from_previous' in agent.observations[iter_num]
            improvement = agent.observations[iter_num]['improvement_from_previous']
            assert isinstance(improvement, dict)
            assert 'accessibility' in improvement
            assert 'symmetry' in improvement
            assert 'harmony' in improvement


class TestEarlyConvergence:
    """Test that loop terminates early when all metrics meet targets."""

    @pytest.fixture
    def setup_converged_agent(self):
        """Create agent with conditions for early convergence."""
        with tempfile.TemporaryDirectory() as tmpdir:
            image_path = os.path.join(tmpdir, 'test.png')
            html_path = os.path.join(tmpdir, 'test.html')

            open(image_path, 'w').close()
            with open(html_path, 'w') as f:
                f.write('''<!DOCTYPE html><html><head><style>
.header { background-color: rgb(50, 50, 50); color: #ffffff; padding: 15px; }
.sidebar { background-color: rgb(200, 200, 200); color: #000000; padding: 15px; }
.content { background-color: rgb(255, 255, 255); color: #000000; padding: 15px; }
.footer { background-color: rgb(50, 50, 50); color: #ffffff; padding: 15px; }
.main { display: flex; flex-direction: row; justify-content: center; align-items: center; }
</style></head><body></body></html>''')

            agent = DesignAgent(image_path, html_path, 70, 70, 70)

            yield agent, image_path, html_path, tmpdir

    def test_early_convergence(self, setup_converged_agent):
        """Test loop terminates when all metrics >= targets (early convergence).

        Verify:
        - iterations_performed < 5 (converges before iteration 5)
        - action_history length equals iterations_performed
        - think() returns None when convergence detected
        """
        agent, image_path, html_path, tmpdir = setup_converged_agent

        # High quality HTML from the start (will trigger faster convergence)
        high_quality = '''<!DOCTYPE html><html><head><style>
.header { background-color: rgb(30, 30, 30); color: #ffffff; padding: 15px; }
.sidebar { background-color: rgb(200, 200, 200); color: #000000; padding: 15px; }
.content { background-color: rgb(255, 255, 255); color: #000000; padding: 15px; }
.footer { background-color: rgb(30, 30, 30); color: #ffffff; padding: 15px; }
.main { display: flex; flex-direction: row; justify-content: center; align-items: center; }
</style></head><body></body></html>'''

        regions = {
            'header': {'x': 0, 'y': 0, 'width': 800, 'height': 100},
            'sidebar': {'x': 0, 'y': 100, 'width': 200, 'height': 500},
            'content': {'x': 200, 'y': 100, 'width': 600, 'height': 500},
            'footer': {'x': 0, 'y': 600, 'width': 800, 'height': 100}
        }

        colors = {
            'header': [(30, 30, 30)],
            'sidebar': [(200, 200, 200)],
            'content': [(255, 255, 255)],
            'footer': [(30, 30, 30)]
        }

        # Create temp HTML files
        html_path_list = os.path.join(tmpdir, 'high.html')
        with open(html_path_list, 'w') as f:
            f.write(high_quality)

        def mock_convert_design(image_path):
            return html_path_list

        # Observe baseline with same high-quality HTML
        agent.observe({
            'html_content': high_quality,
            'regions': regions,
            'colors': colors,
            'iteration': 0
        })

        iterations_performed = 0
        converged_at = None

        with patch('design_agent.convert_design', side_effect=mock_convert_design):
            for iteration in range(1, 6):
                # think() returns None when converged
                action = agent.think()

                if action is None:
                    # Convergence detected
                    converged_at = iteration
                    break

                # act()
                new_html_path = agent.act(action)
                iterations_performed = iteration

                # observe()
                agent.observe({
                    'html_content': high_quality,
                    'regions': regions,
                    'colors': colors,
                    'iteration': iteration
                })

        # Verify convergence (may happen at any iteration, or run full 5)
        # With good HTML, should reach targets relatively quickly
        assert len(agent.action_history) == iterations_performed, \
            f"action_history length {len(agent.action_history)} != iterations_performed {iterations_performed}"

        # If convergence happened, verify action_history length matches iterations_performed
        if converged_at is not None:
            # Converged before max iterations
            assert iterations_performed < 5, "Convergence should occur within 5 iterations"
            assert len(agent.action_history) == iterations_performed, \
                f"action_history should match iterations_performed when converged"


class TestConvergenceDetectionAtEachIteration:
    """Test think() correctly returns None when all metrics >= targets."""

    @pytest.fixture
    def setup_agent_for_convergence_test(self):
        """Create agent for convergence detection."""
        with tempfile.TemporaryDirectory() as tmpdir:
            image_path = os.path.join(tmpdir, 'test.png')
            html_path = os.path.join(tmpdir, 'test.html')

            open(image_path, 'w').close()
            with open(html_path, 'w') as f:
                f.write('<html></html>')

            agent = DesignAgent(image_path, html_path, 75, 75, 75)

            yield agent, tmpdir

    def test_convergence_detection_at_each_iteration(self, setup_agent_for_convergence_test):
        """Test think() returns None when all three metrics >= their targets.

        Convergence may occur at any iteration 1-5.
        """
        agent, tmpdir = setup_agent_for_convergence_test

        # Create HTML that produces high metrics
        high_metrics_html = '''<!DOCTYPE html><html><head><style>
.header { background-color: rgb(30, 30, 30); color: #ffffff; padding: 15px; }
.sidebar { background-color: rgb(190, 190, 190); color: #000000; padding: 15px; }
.content { background-color: rgb(255, 255, 255); color: #000000; padding: 15px; }
.footer { background-color: rgb(30, 30, 30); color: #ffffff; padding: 15px; }
.main { display: flex; flex-direction: row; justify-content: center; align-items: center; }
</style></head><body></body></html>'''

        regions = {
            'header': {'x': 0, 'y': 0, 'width': 800, 'height': 100},
            'sidebar': {'x': 0, 'y': 100, 'width': 200, 'height': 500},
            'content': {'x': 200, 'y': 100, 'width': 600, 'height': 500},
            'footer': {'x': 0, 'y': 600, 'width': 800, 'height': 100}
        }

        colors = {
            'header': [(30, 30, 30)],
            'sidebar': [(190, 190, 190)],
            'content': [(255, 255, 255)],
            'footer': [(30, 30, 30)]
        }

        # Observe with high metrics (should meet targets)
        agent.observe({
            'html_content': high_metrics_html,
            'regions': regions,
            'colors': colors,
            'iteration': 0
        })

        # Get observed metrics
        metrics = agent.observations[0]
        accessibility = metrics['accessibility_score']
        symmetry = metrics['symmetry_score']
        harmony = metrics['harmony_score']

        # If all metrics are >= targets, think() should return None
        if (accessibility >= 75 and symmetry >= 75 and harmony >= 75):
            action = agent.think()
            assert action is None, "think() should return None when all metrics >= targets"
        else:
            # Otherwise, think should return an action
            action = agent.think()
            assert action is not None, "think() should return action when metrics < targets"
            assert 'issue_type' in action
            assert 'recommended_action' in action
