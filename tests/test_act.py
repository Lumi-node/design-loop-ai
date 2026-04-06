"""Unit and integration tests for DesignAgent.act() method."""

import pytest
import os
import tempfile
import shutil
import sys
import importlib.util
from pathlib import Path
from unittest.mock import patch, MagicMock

from agent_designer import DesignAgent, DesignIterationEnvironment

# Import HTMLGenerationError from the correct location
design_converter_path = Path(__file__).parent.parent / "sources" / "0c16ae7e"
types_path = design_converter_path / "types.py"
if types_path.exists():
    spec = importlib.util.spec_from_file_location("project_types", str(types_path))
    project_types = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(project_types)
    HTMLGenerationError = project_types.HTMLGenerationError
else:
    HTMLGenerationError = Exception


class TestActSuccessPath:
    """Tests for successful act() execution."""

    def test_act_returns_absolute_path_on_success(self):
        """act() returns absolute path to generated HTML file on success."""
        env = DesignIterationEnvironment()
        agent = DesignAgent()

        modifications = {'spec_modifications': {}}
        result = agent.act(modifications, env)

        assert isinstance(result, str), "act() must return string"
        assert os.path.isabs(result), "Returned path must be absolute"
        assert result.endswith('.html'), "Output must be HTML file"

    def test_act_creates_file_at_correct_path(self):
        """HTML file is created on disk at examples/iteration_N.html."""
        env = DesignIterationEnvironment()
        agent = DesignAgent()

        modifications = {'spec_modifications': {}}
        result = agent.act(modifications, env)

        # Verify file exists
        assert os.path.exists(result), f"File must exist at {result}"
        assert os.path.isfile(result), f"Path must be regular file: {result}"

        # Verify path matches expected pattern
        expected_filename = 'iteration_0.html'
        assert expected_filename in result, f"Path must contain {expected_filename}"

    def test_act_file_contains_valid_html_structure(self):
        """Generated file contains valid HTML structure (<html>, </html>, <body> tags)."""
        env = DesignIterationEnvironment()
        agent = DesignAgent()

        modifications = {'spec_modifications': {}}
        result = agent.act(modifications, env)

        with open(result, 'r', encoding='utf-8') as f:
            content = f.read()

        # Check required HTML tags
        assert '<!DOCTYPE html>' in content, "Must contain DOCTYPE"
        assert '<html>' in content or '<HTML>' in content.upper(), "Must contain <html> tag"
        assert '</html>' in content or '</HTML>' in content.upper(), "Must contain </html> closing tag"
        assert '<body' in content or '<BODY' in content.upper(), "Must contain <body> tag"
        assert '</body>' in content or '</BODY>' in content.upper(), "Must contain </body> closing tag"
        assert '<head>' in content or '<HEAD>' in content.upper(), "Must contain <head> tag"
        assert '</head>' in content or '</HEAD>' in content.upper(), "Must contain </head> closing tag"

    def test_act_file_is_readable(self):
        """Generated HTML file is readable and not empty."""
        env = DesignIterationEnvironment()
        agent = DesignAgent()

        modifications = {'spec_modifications': {}}
        result = agent.act(modifications, env)

        with open(result, 'r', encoding='utf-8') as f:
            content = f.read()

        assert len(content) > 0, "File must not be empty"
        assert isinstance(content, str), "File must be readable as text"

    def test_act_updates_env_spec_on_success(self):
        """On success, env.spec is updated with applied modifications."""
        env = DesignIterationEnvironment()
        agent = DesignAgent()
        original_spec = env.spec['colors']['header'].copy()

        modifications = {'spec_modifications': {'colors': {'header': ['#FF0000']}}}
        agent.act(modifications, env)

        # Verify env.spec was updated
        assert env.spec['colors']['header'] == ['#FF0000'], "env.spec must be updated"
        assert env.spec['colors']['header'] != original_spec, "Spec should have changed"

    def test_act_returns_path_that_exists(self):
        """Returns path that os.path.exists() confirms as True."""
        env = DesignIterationEnvironment()
        agent = DesignAgent()

        modifications = {'spec_modifications': {}}
        result = agent.act(modifications, env)

        assert os.path.exists(result), f"os.path.exists({result}) must be True"

    def test_act_iteration_naming_convention_0(self):
        """Verify iteration_0.html naming convention on first call."""
        env = DesignIterationEnvironment()
        agent = DesignAgent()

        modifications = {'spec_modifications': {}}
        result = agent.act(modifications, env)

        assert 'iteration_0.html' in result, "First call should generate iteration_0.html"

    def test_act_iteration_naming_convention_incremental(self):
        """Verify iteration_0.html, iteration_1.html, etc. naming convention."""
        env = DesignIterationEnvironment()
        agent = DesignAgent()

        modifications = {'spec_modifications': {}}

        # First call: iteration_0.html
        path_0 = agent.act(modifications, env)
        assert 'iteration_0.html' in path_0

        # Increment iteration counter for second call
        env.iteration_count = 1

        # Second call: iteration_1.html
        path_1 = agent.act(modifications, env)
        assert 'iteration_1.html' in path_1

        # Increment for third call
        env.iteration_count = 2

        # Third call: iteration_2.html
        path_2 = agent.act(modifications, env)
        assert 'iteration_2.html' in path_2

    def test_act_with_valid_color_modifications(self):
        """act() succeeds with valid color modifications."""
        env = DesignIterationEnvironment()
        agent = DesignAgent()

        modifications = {
            'spec_modifications': {
                'colors': {
                    'header': ['#FF0000'],
                    'sidebar': ['#00FF00']
                }
            }
        }
        result = agent.act(modifications, env)

        assert os.path.exists(result)
        assert env.spec['colors']['header'] == ['#FF0000']
        assert env.spec['colors']['sidebar'] == ['#00FF00']

    def test_act_with_valid_layout_modifications(self):
        """act() succeeds with valid layout modifications."""
        env = DesignIterationEnvironment()
        agent = DesignAgent()

        modifications = {
            'spec_modifications': {
                'layout_regions': {
                    'header_height_percent': 15,
                    'footer_height_percent': 10
                }
            }
        }
        result = agent.act(modifications, env)

        assert os.path.exists(result)
        assert env.spec['layout_regions']['header_height_percent'] == 15
        assert env.spec['layout_regions']['footer_height_percent'] == 10

    def test_act_with_combined_color_and_layout_modifications(self):
        """act() succeeds with combined color and layout modifications."""
        env = DesignIterationEnvironment()
        agent = DesignAgent()

        modifications = {
            'spec_modifications': {
                'colors': {'header': ['#FF0000']},
                'layout_regions': {'header_height_percent': 20}
            }
        }
        result = agent.act(modifications, env)

        assert os.path.exists(result)
        assert env.spec['colors']['header'] == ['#FF0000']
        assert env.spec['layout_regions']['header_height_percent'] == 20


class TestActValidationErrors:
    """Tests for ValueError exceptions from validation failures."""

    def test_act_raises_valueerror_invalid_color_format_gggggg(self):
        """Raises ValueError if spec modifications have invalid color format (#GGGGGG)."""
        env = DesignIterationEnvironment()
        agent = DesignAgent()

        modifications = {'spec_modifications': {'colors': {'header': ['#GGGGGG']}}}

        with pytest.raises(ValueError) as exc_info:
            agent.act(modifications, env)

        assert 'Invalid' in str(exc_info.value)
        # Verify env.spec unchanged
        assert env.spec['colors']['header'] == ['#AAAAAA']

    def test_act_raises_valueerror_invalid_color_format_short(self):
        """Raises ValueError if color format is too short (#FF00)."""
        env = DesignIterationEnvironment()
        agent = DesignAgent()

        modifications = {'spec_modifications': {'colors': {'header': ['#FF00']}}}

        with pytest.raises(ValueError):
            agent.act(modifications, env)

        assert env.spec['colors']['header'] == ['#AAAAAA']

    def test_act_raises_valueerror_invalid_percentage_negative(self):
        """Raises ValueError if percentage is negative (-1)."""
        env = DesignIterationEnvironment()
        agent = DesignAgent()

        modifications = {'spec_modifications': {'layout_regions': {'header_height_percent': -1}}}

        with pytest.raises(ValueError) as exc_info:
            agent.act(modifications, env)

        assert 'Invalid' in str(exc_info.value)
        # Verify env.spec unchanged
        assert env.spec['layout_regions']['header_height_percent'] == 8

    def test_act_raises_valueerror_invalid_percentage_too_large(self):
        """Raises ValueError if percentage exceeds 100."""
        env = DesignIterationEnvironment()
        agent = DesignAgent()

        modifications = {'spec_modifications': {'layout_regions': {'header_height_percent': 150}}}

        with pytest.raises(ValueError):
            agent.act(modifications, env)

        assert env.spec['layout_regions']['header_height_percent'] == 8

    def test_act_raises_valueerror_unknown_region(self):
        """Raises ValueError if modifications reference unknown region."""
        env = DesignIterationEnvironment()
        agent = DesignAgent()

        modifications = {'spec_modifications': {'colors': {'unknown_region': ['#FF0000']}}}

        with pytest.raises(ValueError):
            agent.act(modifications, env)

        assert env.spec['colors']['header'] == ['#AAAAAA']

    def test_act_validation_error_does_not_modify_env(self):
        """On ValueError, env.spec is NOT modified (atomic contract)."""
        env = DesignIterationEnvironment()
        agent = DesignAgent()

        original_colors = {k: v.copy() for k, v in env.spec['colors'].items()}
        original_layout = env.spec['layout_regions'].copy()

        modifications = {'spec_modifications': {'colors': {'header': ['#INVALID']}}}

        with pytest.raises(ValueError):
            agent.act(modifications, env)

        # Verify spec unchanged
        for region, colors in original_colors.items():
            assert env.spec['colors'][region] == colors
        assert env.spec['layout_regions'] == original_layout


class TestActFileIOErrors:
    """Tests for OSError exceptions from file I/O failures."""

    @patch('builtins.open', side_effect=PermissionError("Permission denied"))
    def test_act_raises_oserror_permission_denied(self, mock_open):
        """Raises OSError if file I/O fails (permissions denied)."""
        env = DesignIterationEnvironment()
        agent = DesignAgent()

        modifications = {'spec_modifications': {}}

        with pytest.raises(OSError) as exc_info:
            agent.act(modifications, env)

        assert 'Failed to write HTML' in str(exc_info.value)

    @patch('os.makedirs', side_effect=OSError("Disk full"))
    def test_act_raises_oserror_disk_full(self, mock_makedirs):
        """Raises OSError if disk is full during directory creation."""
        env = DesignIterationEnvironment()
        agent = DesignAgent()

        modifications = {'spec_modifications': {}}

        with pytest.raises(OSError) as exc_info:
            agent.act(modifications, env)

        assert 'Failed to write HTML' in str(exc_info.value)

    def test_act_file_io_error_does_not_modify_env(self):
        """On OSError, env.spec is NOT modified (atomic contract)."""
        env = DesignIterationEnvironment()
        agent = DesignAgent()

        original_colors = env.spec['colors']['header'].copy()

        modifications = {'spec_modifications': {'colors': {'header': ['#FF0000']}}}

        # Mock file write to fail after spec modification logic
        with patch('builtins.open', side_effect=PermissionError("Permission denied")):
            with pytest.raises(OSError):
                agent.act(modifications, env)

        # Verify env.spec was NOT modified due to atomicity
        assert env.spec['colors']['header'] == original_colors


class TestActHTMLGenerationErrors:
    """Tests for Exception exceptions from HTML generation failures."""

    @patch('agent_designer.generate_html_structure')
    def test_act_raises_exception_html_generation_fails(self, mock_generate_html):
        """Raises Exception if HTML generation fails."""
        mock_generate_html.side_effect = HTMLGenerationError("Invalid regions")

        env = DesignIterationEnvironment()
        agent = DesignAgent()

        modifications = {'spec_modifications': {}}

        with pytest.raises(Exception) as exc_info:
            agent.act(modifications, env)

        assert 'generation failed' in str(exc_info.value).lower()

    @patch('agent_designer.generate_css')
    def test_act_raises_exception_css_generation_fails(self, mock_generate_css):
        """Raises Exception if CSS generation fails."""
        mock_generate_css.side_effect = HTMLGenerationError("Invalid colors")

        env = DesignIterationEnvironment()
        agent = DesignAgent()

        modifications = {'spec_modifications': {}}

        with pytest.raises(Exception):
            agent.act(modifications, env)

    def test_act_html_generation_error_does_not_modify_env(self):
        """On HTML generation exception, env.spec is NOT modified (atomic contract)."""
        env = DesignIterationEnvironment()
        agent = DesignAgent()

        original_colors = env.spec['colors']['header'].copy()

        modifications = {'spec_modifications': {'colors': {'header': ['#FF0000']}}}

        # Mock HTML generation to fail
        with patch('agent_designer.generate_html_structure') as mock_gen:
            mock_gen.side_effect = HTMLGenerationError("Generation failed")

            with pytest.raises(Exception):
                agent.act(modifications, env)

        # Verify env.spec was NOT modified
        assert env.spec['colors']['header'] == original_colors

    def test_act_html_generation_error_does_not_write_file(self):
        """On HTML generation exception, no file is written to disk."""
        env = DesignIterationEnvironment()
        agent = DesignAgent()

        modifications = {'spec_modifications': {}}

        # Create temp directory and change to it
        with tempfile.TemporaryDirectory() as tmpdir:
            original_cwd = os.getcwd()
            try:
                os.chdir(tmpdir)

                # Mock HTML generation to fail
                with patch('agent_designer.generate_html_structure') as mock_gen:
                    mock_gen.side_effect = HTMLGenerationError("Generation failed")

                    # Try to act
                    with pytest.raises(Exception):
                        agent.act(modifications, env)

                    # Verify no iteration_0.html was written
                    examples_dir = os.path.join(tmpdir, 'examples')
                    iteration_file = os.path.join(examples_dir, 'iteration_0.html')
                    assert not os.path.exists(iteration_file), "No file should be written on error"
            finally:
                os.chdir(original_cwd)


class TestActAtomicity:
    """Tests for atomic contract: spec modified only on full success."""

    def test_act_atomicity_validation_error_before_file_write(self):
        """On ValueError, file is not written and env is not modified."""
        env = DesignIterationEnvironment()
        agent = DesignAgent()

        original_spec = copy.deepcopy(env.spec)

        modifications = {'spec_modifications': {'colors': {'header': ['#INVALID']}}}

        with tempfile.TemporaryDirectory() as tmpdir:
            original_cwd = os.getcwd()
            try:
                os.chdir(tmpdir)

                with pytest.raises(ValueError):
                    agent.act(modifications, env)

                # Verify file not written
                examples_dir = os.path.join(tmpdir, 'examples')
                if os.path.exists(examples_dir):
                    html_files = [f for f in os.listdir(examples_dir) if f.endswith('.html')]
                    assert len(html_files) == 0, "No HTML files should be written on ValueError"

                # Verify env unchanged
                assert env.spec == original_spec
            finally:
                os.chdir(original_cwd)

    def test_act_atomicity_spec_copied_before_modifications(self):
        """Spec is deep copied before modifications to ensure atomicity."""
        env = DesignIterationEnvironment()
        agent = DesignAgent()

        original_header = env.spec['colors']['header'].copy()

        # Valid modifications
        modifications = {'spec_modifications': {'colors': {'header': ['#00FF00']}}}
        agent.act(modifications, env)

        # Verify spec was updated
        assert env.spec['colors']['header'] == ['#00FF00']
        assert env.spec['colors']['header'] != original_header

    def test_act_spec_updated_only_after_success(self):
        """env.spec is updated only after file successfully written."""
        env = DesignIterationEnvironment()
        agent = DesignAgent()

        modifications = {'spec_modifications': {'colors': {'header': ['#FF0000']}}}

        # This should succeed and update spec
        result = agent.act(modifications, env)

        # Verify file exists
        assert os.path.exists(result)

        # Verify spec was updated
        assert env.spec['colors']['header'] == ['#FF0000']


class TestActEmptyModifications:
    """Tests for edge cases with empty or minimal modifications."""

    def test_act_with_empty_spec_modifications(self):
        """act() succeeds with empty spec_modifications dict."""
        env = DesignIterationEnvironment()
        agent = DesignAgent()

        modifications = {'spec_modifications': {}}
        result = agent.act(modifications, env)

        assert os.path.exists(result)
        # Spec should be unchanged
        assert env.spec['colors']['header'] == ['#AAAAAA']

    def test_act_with_missing_spec_modifications_key(self):
        """act() handles missing 'spec_modifications' key gracefully."""
        env = DesignIterationEnvironment()
        agent = DesignAgent()

        # No spec_modifications key at all
        modifications = {}
        result = agent.act(modifications, env)

        assert os.path.exists(result)

    def test_act_multiple_calls_with_incremental_iteration_count(self):
        """Multiple calls with incremented iteration_count generate different files."""
        env = DesignIterationEnvironment()
        agent = DesignAgent()

        modifications = {'spec_modifications': {}}

        # First call
        path_0 = agent.act(modifications, env)
        assert 'iteration_0.html' in path_0
        assert os.path.exists(path_0)

        # Simulate iteration increment (env.record_iteration would do this)
        env.iteration_count = 1

        # Second call
        path_1 = agent.act(modifications, env)
        assert 'iteration_1.html' in path_1
        assert os.path.exists(path_1)

        # Verify both files exist and are different
        assert path_0 != path_1
        assert os.path.exists(path_0)
        assert os.path.exists(path_1)


class TestActHTMLContent:
    """Tests for HTML content validation."""

    def test_act_generated_html_contains_container_div(self):
        """Generated HTML contains .container div."""
        env = DesignIterationEnvironment()
        agent = DesignAgent()

        modifications = {'spec_modifications': {}}
        result = agent.act(modifications, env)

        with open(result, 'r') as f:
            content = f.read()

        assert 'class="container"' in content or "class='container'" in content

    def test_act_generated_html_valid_with_colors(self):
        """Generated HTML is valid when colors are modified."""
        env = DesignIterationEnvironment()
        agent = DesignAgent()

        modifications = {
            'spec_modifications': {
                'colors': {
                    'header': ['#FF0000'],
                    'content': ['#00FF00'],
                    'footer': ['#0000FF'],
                    'sidebar': ['#FFFF00']
                }
            }
        }
        result = agent.act(modifications, env)

        with open(result, 'r') as f:
            content = f.read()

        # Verify HTML structure is present
        assert '<html>' in content.lower()
        assert '</html>' in content.lower()
        assert '<body' in content.lower()
        assert '</body>' in content.lower()

    def test_act_generated_html_contains_style_tag(self):
        """Generated HTML contains <style> tag with CSS."""
        env = DesignIterationEnvironment()
        agent = DesignAgent()

        modifications = {'spec_modifications': {}}
        result = agent.act(modifications, env)

        with open(result, 'r') as f:
            content = f.read()

        assert '<style>' in content or '<STYLE>' in content.upper()
        assert '</style>' in content or '</STYLE>' in content.upper()

    def test_act_generated_html_readable_utf8(self):
        """Generated HTML file is valid UTF-8."""
        env = DesignIterationEnvironment()
        agent = DesignAgent()

        modifications = {'spec_modifications': {}}
        result = agent.act(modifications, env)

        # Try to read as UTF-8
        with open(result, 'r', encoding='utf-8') as f:
            content = f.read()

        assert len(content) > 0


class TestActIntegration:
    """Integration tests combining multiple features."""

    def test_act_integration_complete_workflow(self):
        """Complete workflow: modify spec -> act -> verify output."""
        env = DesignIterationEnvironment()
        agent = DesignAgent()

        # Modify colors and layout
        modifications = {
            'spec_modifications': {
                'colors': {
                    'header': ['#FF0000'],
                    'sidebar': ['#00FF00'],
                    'content': ['#FFFFFF'],
                    'footer': ['#0000FF']
                },
                'layout_regions': {
                    'header_height_percent': 15,
                    'footer_height_percent': 10,
                    'sidebar_width_percent': 25
                }
            }
        }

        # Act
        result = agent.act(modifications, env)

        # Verify file exists and is readable
        assert os.path.exists(result)
        with open(result, 'r', encoding='utf-8') as f:
            content = f.read()

        # Verify HTML structure
        assert '<html>' in content.lower()
        assert '</html>' in content.lower()
        assert '<body' in content.lower()
        assert '</body>' in content.lower()

        # Verify env was updated
        assert env.spec['colors']['header'] == ['#FF0000']
        assert env.spec['layout_regions']['header_height_percent'] == 15

    def test_act_sequential_calls_with_different_specs(self):
        """Sequential act() calls with different modifications work correctly."""
        env = DesignIterationEnvironment()
        agent = DesignAgent()

        # First modification
        mods1 = {'spec_modifications': {'colors': {'header': ['#FF0000']}}}
        path1 = agent.act(mods1, env)
        assert os.path.exists(path1)
        assert env.spec['colors']['header'] == ['#FF0000']

        # Update iteration count
        env.iteration_count = 1

        # Second modification (building on previous)
        mods2 = {'spec_modifications': {'colors': {'sidebar': ['#00FF00']}}}
        path2 = agent.act(mods2, env)
        assert os.path.exists(path2)
        assert env.spec['colors']['header'] == ['#FF0000']  # Previous change preserved
        assert env.spec['colors']['sidebar'] == ['#00FF00']  # New change applied


# Import copy for atomicity tests
import copy
