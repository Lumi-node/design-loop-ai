"""Unit tests for DesignAgent constructor and initialization."""

import os
import pytest
import tempfile
from design_agent import DesignAgent
from agent import ReasoningAgent


class TestDesignAgentConstructorDefaults:
    """Test DesignAgent constructor with default threshold values."""

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

    def test_agent_constructor_with_defaults(self, temp_files):
        """Test agent accepts image_path, initial_html_path; initializes with observations={}, action_history=[]."""
        image_path, html_path = temp_files

        # Create agent with defaults
        agent = DesignAgent(image_path, html_path)

        # Verify basic attributes
        assert agent.image_path == image_path
        assert agent.current_html_path == html_path
        assert agent.observations == {}
        assert agent.action_history == []

        # Verify targets default to 75
        assert agent.targets == {
            'accessibility': 75,
            'symmetry': 75,
            'harmony': 75
        }

    def test_agent_inherits_from_reasoning_agent(self, temp_files):
        """Test that DesignAgent inherits from ReasoningAgent."""
        image_path, html_path = temp_files
        agent = DesignAgent(image_path, html_path)

        # Verify inheritance
        assert isinstance(agent, ReasoningAgent)

        # Verify inherited methods exist
        assert hasattr(agent, 'think')
        assert hasattr(agent, 'act')
        assert hasattr(agent, 'observe')
        assert callable(agent.think)
        assert callable(agent.act)
        assert callable(agent.observe)

    def test_agent_constructor_does_not_raise_for_valid_paths(self, temp_files):
        """Test constructor does not raise exceptions for valid file paths."""
        image_path, html_path = temp_files

        # Should not raise
        try:
            agent = DesignAgent(image_path, html_path)
            assert agent is not None
        except Exception as e:
            pytest.fail(f"Constructor raised unexpected exception: {e}")


class TestDesignAgentConstructorThresholds:
    """Test DesignAgent constructor with custom threshold values."""

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

    def test_agent_constructor_with_custom_thresholds(self, temp_files):
        """Test agent constructor accepts custom target thresholds without raising exceptions."""
        image_path, html_path = temp_files

        # Create agent with custom thresholds
        agent = DesignAgent(
            image_path,
            html_path,
            target_accessibility=60,
            target_symmetry=80,
            target_harmony=70
        )

        # Verify targets stored correctly
        assert agent.targets == {
            'accessibility': 60,
            'symmetry': 80,
            'harmony': 70
        }

    def test_agent_validates_thresholds_in_range(self, temp_files):
        """Test constructor validates thresholds are in [0, 100] range."""
        image_path, html_path = temp_files

        # Test boundary: 0
        agent = DesignAgent(
            image_path,
            html_path,
            target_accessibility=0,
            target_symmetry=0,
            target_harmony=0
        )
        assert agent.targets['accessibility'] == 0

        # Test boundary: 100
        agent = DesignAgent(
            image_path,
            html_path,
            target_accessibility=100,
            target_symmetry=100,
            target_harmony=100
        )
        assert agent.targets['accessibility'] == 100

    def test_agent_raises_value_error_for_negative_thresholds(self, temp_files):
        """Test constructor raises ValueError if thresholds are negative."""
        image_path, html_path = temp_files

        with pytest.raises(ValueError) as excinfo:
            DesignAgent(image_path, html_path, target_accessibility=-1)
        assert "must be in [0, 100]" in str(excinfo.value)
        assert "-1" in str(excinfo.value)

    def test_agent_raises_value_error_for_thresholds_over_100(self, temp_files):
        """Test constructor raises ValueError if thresholds exceed 100."""
        image_path, html_path = temp_files

        with pytest.raises(ValueError) as excinfo:
            DesignAgent(image_path, html_path, target_symmetry=101)
        assert "must be in [0, 100]" in str(excinfo.value)
        assert "101" in str(excinfo.value)

    def test_agent_raises_value_error_for_float_thresholds(self, temp_files):
        """Test constructor raises ValueError if thresholds are float (not int)."""
        image_path, html_path = temp_files

        with pytest.raises(ValueError) as excinfo:
            DesignAgent(image_path, html_path, target_accessibility=75.5)
        assert "must be int" in str(excinfo.value)

    def test_agent_raises_value_error_for_string_thresholds(self, temp_files):
        """Test constructor raises ValueError if thresholds are string (not int)."""
        image_path, html_path = temp_files

        with pytest.raises(ValueError) as excinfo:
            DesignAgent(image_path, html_path, target_harmony="75")
        assert "must be int" in str(excinfo.value)


class TestDesignAgentPathValidation:
    """Test DesignAgent constructor path validation."""

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

    def test_agent_raises_file_not_found_for_missing_image(self, temp_files):
        """Test constructor raises FileNotFoundError if image_path doesn't exist."""
        _, html_path = temp_files
        nonexistent_image = "/tmp/nonexistent_design_agent_test_12345.png"

        with pytest.raises(FileNotFoundError) as excinfo:
            DesignAgent(nonexistent_image, html_path)
        assert "Image not found" in str(excinfo.value)

    def test_agent_raises_file_not_found_for_missing_html(self, temp_files):
        """Test constructor raises FileNotFoundError if initial_html_path doesn't exist."""
        image_path, _ = temp_files
        nonexistent_html = "/tmp/nonexistent_design_agent_test_12345.html"

        with pytest.raises(FileNotFoundError) as excinfo:
            DesignAgent(image_path, nonexistent_html)
        assert "HTML file not found" in str(excinfo.value)

    def test_agent_stores_image_path(self, temp_files):
        """Test constructor stores image_path correctly."""
        image_path, html_path = temp_files
        agent = DesignAgent(image_path, html_path)
        assert agent.image_path == image_path

    def test_agent_stores_current_html_path(self, temp_files):
        """Test constructor stores current_html_path correctly."""
        image_path, html_path = temp_files
        agent = DesignAgent(image_path, html_path)
        assert agent.current_html_path == html_path


class TestDesignAgentInitializationState:
    """Test DesignAgent initialization of internal state."""

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

    def test_agent_initializes_observations_as_empty_dict(self, temp_files):
        """Test constructor initializes observations as empty dict."""
        image_path, html_path = temp_files
        agent = DesignAgent(image_path, html_path)

        assert isinstance(agent.observations, dict)
        assert len(agent.observations) == 0
        assert agent.observations == {}

    def test_agent_initializes_action_history_as_empty_list(self, temp_files):
        """Test constructor initializes action_history as empty list."""
        image_path, html_path = temp_files
        agent = DesignAgent(image_path, html_path)

        assert isinstance(agent.action_history, list)
        assert len(agent.action_history) == 0
        assert agent.action_history == []

    def test_agent_initializes_targets_dict(self, temp_files):
        """Test constructor initializes targets dict with correct keys."""
        image_path, html_path = temp_files
        agent = DesignAgent(image_path, html_path)

        assert isinstance(agent.targets, dict)
        assert set(agent.targets.keys()) == {'accessibility', 'symmetry', 'harmony'}
        assert all(isinstance(v, int) for v in agent.targets.values())

    def test_agent_targets_dict_with_custom_values(self, temp_files):
        """Test targets dict stores exact custom values passed."""
        image_path, html_path = temp_files
        agent = DesignAgent(
            image_path,
            html_path,
            target_accessibility=40,
            target_symmetry=50,
            target_harmony=60
        )

        assert agent.targets['accessibility'] == 40
        assert agent.targets['symmetry'] == 50
        assert agent.targets['harmony'] == 60
