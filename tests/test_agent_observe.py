"""Unit tests for DesignAgent.observe() method and metrics extraction."""

import os
import pytest
import tempfile
import json
from datetime import datetime
from design_agent import DesignAgent


class TestObserveExtractsMetrics:
    """Test observe() extracts accessibility, symmetry, and harmony scores."""

    @pytest.fixture
    def temp_files(self):
        """Create temporary image and HTML files for testing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            image_path = os.path.join(tmpdir, 'test.png')
            html_path = os.path.join(tmpdir, 'test.html')

            # Create dummy files
            open(image_path, 'w').close()

            # Create basic HTML with CSS for metrics calculation
            html_content = '''<!DOCTYPE html>
<html>
<head>
<style>
.header { background-color: rgb(50, 50, 50); color: #ffffff; padding: 12px; }
.sidebar { background-color: rgb(240, 240, 240); color: #000000; padding: 10px; }
.content { background-color: rgb(255, 255, 255); color: #000000; padding: 15px; }
.footer { background-color: rgb(50, 50, 50); color: #ffffff; padding: 10px; }
.main { display: flex; flex-direction: row; }
</style>
</head>
<body><header></header></body>
</html>'''
            with open(html_path, 'w') as f:
                f.write(html_content)

            yield image_path, html_path

    def test_observe_accepts_observation_dict_with_required_keys(self, temp_files):
        """Test observe() accepts dict with keys: html_content, regions, colors, iteration."""
        image_path, html_path = temp_files
        agent = DesignAgent(image_path, html_path)

        # Prepare observation dict
        observation = {
            'html_content': '<html></html>',
            'regions': {'header': None, 'sidebar': None, 'content': None, 'footer': None},
            'colors': {},
            'iteration': 0
        }

        # Should not raise
        try:
            agent.observe(observation)
        except Exception as e:
            pytest.fail(f"observe() raised unexpected exception: {e}")

    def test_observe_calculates_accessibility_score(self, temp_files):
        """Test observe() calculates and stores accessibility_score."""
        image_path, html_path = temp_files
        agent = DesignAgent(image_path, html_path)

        html_content = '''<!DOCTYPE html>
<html>
<head><style>
.header { background-color: rgb(50, 50, 50); color: #ffffff; padding: 12px; }
.content { background-color: rgb(240, 240, 240); color: #000000; padding: 15px; }
</style></head>
<body><header></header></body>
</html>'''

        observation = {
            'html_content': html_content,
            'regions': {'header': None, 'sidebar': None, 'content': None, 'footer': None},
            'colors': {},
            'iteration': 0
        }

        agent.observe(observation)

        # Verify accessibility_score was calculated and stored
        assert 0 in agent.observations
        assert 'accessibility_score' in agent.observations[0]
        assert isinstance(agent.observations[0]['accessibility_score'], int)
        assert 0 <= agent.observations[0]['accessibility_score'] <= 100

    def test_observe_calculates_symmetry_score(self, temp_files):
        """Test observe() calculates and stores symmetry_score."""
        image_path, html_path = temp_files
        agent = DesignAgent(image_path, html_path)

        html_content = '<html></html>'
        regions = {
            'header': {'x': 0, 'y': 0, 'width': 800, 'height': 100},
            'sidebar': {'x': 0, 'y': 100, 'width': 200, 'height': 500},
            'content': {'x': 200, 'y': 100, 'width': 600, 'height': 500},
            'footer': {'x': 0, 'y': 600, 'width': 800, 'height': 100}
        }

        observation = {
            'html_content': html_content,
            'regions': regions,
            'colors': {},
            'iteration': 0
        }

        agent.observe(observation)

        # Verify symmetry_score was calculated and stored
        assert 0 in agent.observations
        assert 'symmetry_score' in agent.observations[0]
        assert isinstance(agent.observations[0]['symmetry_score'], int)
        assert 0 <= agent.observations[0]['symmetry_score'] <= 100

    def test_observe_calculates_harmony_score(self, temp_files):
        """Test observe() calculates and stores harmony_score."""
        image_path, html_path = temp_files
        agent = DesignAgent(image_path, html_path)

        html_content = '<html></html>'
        colors = {
            'header': [(255, 0, 0), (0, 255, 0)],
            'sidebar': [(0, 0, 255)],
            'content': [(255, 255, 0)],
            'footer': [(255, 0, 255)]
        }

        observation = {
            'html_content': html_content,
            'regions': {},
            'colors': colors,
            'iteration': 0
        }

        agent.observe(observation)

        # Verify harmony_score was calculated and stored
        assert 0 in agent.observations
        assert 'harmony_score' in agent.observations[0]
        assert isinstance(agent.observations[0]['harmony_score'], int)
        assert 0 <= agent.observations[0]['harmony_score'] <= 100

    def test_observe_stores_all_required_metric_keys(self, temp_files):
        """Test observe() stores all required metric keys in observations."""
        image_path, html_path = temp_files
        agent = DesignAgent(image_path, html_path)

        observation = {
            'html_content': '<html></html>',
            'regions': {},
            'colors': {},
            'iteration': 0
        }

        agent.observe(observation)

        # Verify all required keys are present
        assert 0 in agent.observations
        obs = agent.observations[0]
        assert 'accessibility_score' in obs
        assert 'symmetry_score' in obs
        assert 'harmony_score' in obs
        assert 'improvement_from_previous' in obs
        assert 'timestamp' in obs

    def test_observe_with_custom_iteration_number(self, temp_files):
        """Test observe() stores metrics under correct iteration number."""
        image_path, html_path = temp_files
        agent = DesignAgent(image_path, html_path)

        observation = {
            'html_content': '<html></html>',
            'regions': {},
            'colors': {},
            'iteration': 5
        }

        agent.observe(observation)

        # Verify iteration 5 was stored, not iteration 0
        assert 5 in agent.observations
        assert 0 not in agent.observations


class TestObserveStoresInObservations:
    """Test observe() stores complete metrics data in self.observations."""

    @pytest.fixture
    def temp_files(self):
        """Create temporary image and HTML files for testing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            image_path = os.path.join(tmpdir, 'test.png')
            html_path = os.path.join(tmpdir, 'test.html')

            # Create dummy files
            open(image_path, 'w').close()
            open(html_path, 'w').close()

            yield image_path, html_path

    def test_observe_first_iteration_has_none_improvement(self, temp_files):
        """Test observe() stores improvement_from_previous as None for first iteration."""
        image_path, html_path = temp_files
        agent = DesignAgent(image_path, html_path)

        observation = {
            'html_content': '<html></html>',
            'regions': {},
            'colors': {},
            'iteration': 0
        }

        agent.observe(observation)

        # First iteration should have None improvement
        assert agent.observations[0]['improvement_from_previous'] is None

    def test_observe_second_iteration_computes_improvement_delta(self, temp_files):
        """Test observe() computes improvement_from_previous as delta for subsequent iterations."""
        image_path, html_path = temp_files
        agent = DesignAgent(image_path, html_path)

        # First observation
        observation_0 = {
            'html_content': '<html></html>',
            'regions': {},
            'colors': {},
            'iteration': 0
        }
        agent.observe(observation_0)

        # Store first metrics for comparison
        metrics_0 = agent.observations[0]
        acc_0 = metrics_0['accessibility_score']
        sym_0 = metrics_0['symmetry_score']
        har_0 = metrics_0['harmony_score']

        # Second observation with same content (will have same scores)
        observation_1 = {
            'html_content': '<html></html>',
            'regions': {},
            'colors': {},
            'iteration': 1
        }
        agent.observe(observation_1)

        # Verify improvement_from_previous is a dict with correct keys
        improvement = agent.observations[1]['improvement_from_previous']
        assert improvement is not None
        assert isinstance(improvement, dict)
        assert 'accessibility' in improvement
        assert 'symmetry' in improvement
        assert 'harmony' in improvement

        # Verify deltas are correct (should be 0 for identical content)
        assert improvement['accessibility'] == 0  # acc_1 - acc_0 = acc_0 - acc_0
        assert improvement['symmetry'] == 0
        assert improvement['harmony'] == 0

    def test_observe_improvement_delta_with_positive_change(self, temp_files):
        """Test observe() correctly computes positive improvement deltas."""
        image_path, html_path = temp_files
        agent = DesignAgent(image_path, html_path)

        # First observation with baseline accessibility score of 65
        html_0 = '''<!DOCTYPE html>
<html>
<head><style>
.header { background-color: rgb(200, 200, 200); color: #000000; padding: 5px; }
</style></head>
<body></body>
</html>'''

        agent.observe({
            'html_content': html_0,
            'regions': {},
            'colors': {},
            'iteration': 0
        })

        acc_0 = agent.observations[0]['accessibility_score']

        # Second observation with higher accessibility score (better contrast/padding)
        html_1 = '''<!DOCTYPE html>
<html>
<head><style>
.header { background-color: rgb(50, 50, 50); color: #ffffff; padding: 12px; }
.content { background-color: rgb(240, 240, 240); color: #000000; padding: 15px; }
</style></head>
<body><header></header></body>
</html>'''

        agent.observe({
            'html_content': html_1,
            'regions': {},
            'colors': {},
            'iteration': 1
        })

        acc_1 = agent.observations[1]['accessibility_score']
        improvement = agent.observations[1]['improvement_from_previous']

        # Verify delta is positive if accessibility improved
        assert improvement['accessibility'] == acc_1 - acc_0
        assert improvement['accessibility'] >= 0  # Should be positive or zero

    def test_observe_stores_timestamp_in_iso_format(self, temp_files):
        """Test observe() stores timestamp in ISO format (datetime.isoformat())."""
        image_path, html_path = temp_files
        agent = DesignAgent(image_path, html_path)

        before = datetime.now().isoformat()

        agent.observe({
            'html_content': '<html></html>',
            'regions': {},
            'colors': {},
            'iteration': 0
        })

        after = datetime.now().isoformat()

        timestamp = agent.observations[0]['timestamp']

        # Verify timestamp is a string
        assert isinstance(timestamp, str)

        # Verify timestamp is valid ISO format
        try:
            parsed = datetime.fromisoformat(timestamp)
            assert parsed is not None
        except ValueError:
            pytest.fail(f"Timestamp is not valid ISO format: {timestamp}")

        # Verify timestamp is within expected range
        assert before <= timestamp <= after

    def test_observe_stores_iteration_number(self, temp_files):
        """Test observe() stores iteration_number correctly."""
        image_path, html_path = temp_files
        agent = DesignAgent(image_path, html_path)

        for iter_num in [0, 1, 2, 3]:
            agent.observe({
                'html_content': '<html></html>',
                'regions': {},
                'colors': {},
                'iteration': iter_num
            })

            # Verify correct iteration number is stored
            assert iter_num in agent.observations

    def test_observe_multiple_iterations_builds_history(self, temp_files):
        """Test observe() can be called multiple times to build observation history."""
        image_path, html_path = temp_files
        agent = DesignAgent(image_path, html_path)

        # Perform 5 iterations of observations
        for i in range(5):
            agent.observe({
                'html_content': '<html></html>',
                'regions': {},
                'colors': {},
                'iteration': i
            })

        # Verify all 5 iterations are stored
        assert len(agent.observations) == 5
        for i in range(5):
            assert i in agent.observations
            assert 'accessibility_score' in agent.observations[i]
            assert 'symmetry_score' in agent.observations[i]
            assert 'harmony_score' in agent.observations[i]

    def test_observe_graceful_defaults_for_missing_keys(self, temp_files):
        """Test observe() uses graceful defaults if observation_dict has missing keys."""
        image_path, html_path = temp_files
        agent = DesignAgent(image_path, html_path)

        # Observation dict with missing keys
        incomplete_observation = {
            'iteration': 0
            # Missing html_content, regions, colors
        }

        # Should not raise
        try:
            agent.observe(incomplete_observation)
        except Exception as e:
            pytest.fail(f"observe() should handle missing keys gracefully: {e}")

        # Verify observations were still created with defaults
        assert 0 in agent.observations
        assert 'accessibility_score' in agent.observations[0]

    def test_observe_stores_score_metrics_with_correct_keys(self, temp_files):
        """Test observe() stores metrics with exact keys specified in AC."""
        image_path, html_path = temp_files
        agent = DesignAgent(image_path, html_path)

        agent.observe({
            'html_content': '<html></html>',
            'regions': {},
            'colors': {},
            'iteration': 0
        })

        obs = agent.observations[0]

        # Verify exact key names from AC
        assert 'accessibility_score' in obs
        assert 'symmetry_score' in obs
        assert 'harmony_score' in obs
        assert 'improvement_from_previous' in obs
        assert 'timestamp' in obs

        # Verify types
        assert isinstance(obs['accessibility_score'], int)
        assert isinstance(obs['symmetry_score'], int)
        assert isinstance(obs['harmony_score'], int)
        assert obs['improvement_from_previous'] is None or isinstance(obs['improvement_from_previous'], dict)
        assert isinstance(obs['timestamp'], str)

    def test_observe_with_valid_html_produces_valid_scores(self, temp_files):
        """Test observe() with valid HTML produces valid score values."""
        image_path, html_path = temp_files
        agent = DesignAgent(image_path, html_path)

        valid_html = '''<!DOCTYPE html>
<html>
<head><style>
.header { background-color: rgb(50, 50, 50); color: #ffffff; padding: 12px; }
.sidebar { background-color: rgb(200, 200, 200); color: #000000; padding: 10px; }
.content { background-color: rgb(255, 255, 255); color: #000000; padding: 15px; }
.footer { background-color: rgb(50, 50, 50); color: #ffffff; padding: 10px; }
</style></head>
<body></body>
</html>'''

        agent.observe({
            'html_content': valid_html,
            'regions': {
                'header': {'x': 0, 'y': 0, 'width': 800, 'height': 100},
                'sidebar': {'x': 0, 'y': 100, 'width': 200, 'height': 500},
                'content': {'x': 200, 'y': 100, 'width': 600, 'height': 500},
                'footer': {'x': 0, 'y': 600, 'width': 800, 'height': 100}
            },
            'colors': {
                'header': [(50, 50, 50)],
                'sidebar': [(200, 200, 200)],
                'content': [(255, 255, 255)],
                'footer': [(50, 50, 50)]
            },
            'iteration': 0
        })

        obs = agent.observations[0]

        # All scores should be in valid range
        assert 0 <= obs['accessibility_score'] <= 100
        assert 0 <= obs['symmetry_score'] <= 100
        assert 0 <= obs['harmony_score'] <= 100

    def test_observe_multiple_calls_update_observations(self, temp_files):
        """Test observe() multiple calls properly update observations dict."""
        image_path, html_path = temp_files
        agent = DesignAgent(image_path, html_path)

        # First call
        agent.observe({
            'html_content': '<html>1</html>',
            'regions': {},
            'colors': {},
            'iteration': 0
        })

        first_acc = agent.observations[0]['accessibility_score']

        # Second call with different content
        agent.observe({
            'html_content': '<html>2</html>',
            'regions': {},
            'colors': {},
            'iteration': 1
        })

        second_acc = agent.observations[1]['accessibility_score']

        # Both should be stored independently
        assert 0 in agent.observations
        assert 1 in agent.observations
        assert len(agent.observations) == 2
