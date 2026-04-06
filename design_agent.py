"""DesignAgent: Iterative design refinement agent using think-act-observe cycle."""

import os
import sys
from datetime import datetime

# Add sources to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'sources', 'f98239d4'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'sources', '0c16ae7e'))

from agent import ReasoningAgent
from main import convert_design
import project_types
from metrics import (
    calculate_accessibility_score,
    calculate_symmetry_score,
    calculate_harmony_score
)


class DesignAgent(ReasoningAgent):
    """Iterative design refinement agent using think-act-observe cycle.

    Inherits from ReasoningAgent (sources/f98239d4/agent.py).
    Implements think(), act(), observe() methods for HTML/CSS analysis and refinement.
    """

    def __init__(
        self,
        image_path: str,
        initial_html_path: str,
        target_accessibility: int = 75,
        target_symmetry: int = 75,
        target_harmony: int = 75
    ):
        """Initialize design agent with image and quality targets.

        Args:
            image_path: Path to design mockup image (PNG/JPG)
            initial_html_path: Path to initial generated HTML file
            target_accessibility: Target score [0, 100], default 75
            target_symmetry: Target score [0, 100], default 75
            target_harmony: Target score [0, 100], default 75

        Raises:
            FileNotFoundError: If image_path or initial_html_path don't exist
            ValueError: If thresholds not in [0, 100] or not integers

        Initializes:
            self.observations = {}  # Dict mapping iteration -> metrics
            self.action_history = []  # List of action dicts
            self.image_path = image_path
            self.current_html_path = initial_html_path
            self.targets = {
                'accessibility': target_accessibility,
                'symmetry': target_symmetry,
                'harmony': target_harmony
            }
        """
        # Validate file paths before initializing
        if not os.path.exists(image_path):
            raise FileNotFoundError(f"Image not found: {image_path}")
        if not os.path.exists(initial_html_path):
            raise FileNotFoundError(f"HTML file not found: {initial_html_path}")

        # Validate threshold values
        for name, value in [
            ('target_accessibility', target_accessibility),
            ('target_symmetry', target_symmetry),
            ('target_harmony', target_harmony)
        ]:
            if not isinstance(value, int):
                raise ValueError(f"{name} must be int, got {type(value).__name__}")
            if not (0 <= value <= 100):
                raise ValueError(f"{name} must be in [0, 100], got {value}")

        # Call parent constructor (ReasoningAgent)
        # Note: ReasoningAgent.__init__ accepts start_position, but we don't need it
        # We'll override its observations and action_history initialization
        super().__init__()

        # Initialize design-specific state
        self.image_path = image_path
        self.current_html_path = initial_html_path
        self.targets = {
            'accessibility': target_accessibility,
            'symmetry': target_symmetry,
            'harmony': target_harmony
        }
        # observations and action_history inherited from ReasoningAgent
        # but reset to empty for consistency with architecture spec
        self.observations = {}
        self.action_history = []

    def think(self):
        """Analyze current metrics and identify improvement opportunities.

        Returns:
            None if all metrics >= targets (convergence)
            Dict with action details if issues detected:
            {
                'issue_type': 'accessibility' | 'symmetry' | 'harmony',
                'region': str (region name or 'global'),
                'severity': int (1=low, 2=medium, 3=high),
                'recommended_action': str (specific action to take)
            }

        Precondition:
            - observe() must have been called at least once
            - self.observations must not be empty

        Algorithm:
            1. Get current metrics from latest observation
            2. Check convergence: all metrics >= targets → return None
            3. Compute deficiencies for each metric
            4. Identify highest-priority deficiency
            5. Determine recommended action based on issue type
            6. Calculate severity (1-3) based on magnitude
            7. Return action dict

        Action Mapping:
            - Accessibility issues:
              * If score < 60 → "increase_contrast"
              * Else → "improve_spacing"
            - Symmetry issues:
              * "equalize_header_footer"
            - Harmony issues:
              * If score < 50 → "diversify_palette"
              * Else → "increase_saturation"
        """
        # Precondition check
        if len(self.observations) == 0:
            raise RuntimeError("observe() must be called before think()")

        # Get current metrics from latest observation
        current_iteration = max(self.observations.keys())
        current_metrics = self.observations[current_iteration]

        accessibility = current_metrics['accessibility_score']
        symmetry = current_metrics['symmetry_score']
        harmony = current_metrics['harmony_score']

        # Check convergence
        if (accessibility >= self.targets['accessibility'] and
            symmetry >= self.targets['symmetry'] and
            harmony >= self.targets['harmony']):
            return None  # Converged; no action needed

        # Compute deficiencies
        deficiencies = [
            ('accessibility', self.targets['accessibility'] - accessibility),
            ('symmetry', self.targets['symmetry'] - symmetry),
            ('harmony', self.targets['harmony'] - harmony)
        ]

        # Sort by deficiency magnitude (descending)
        deficiencies.sort(key=lambda x: x[1], reverse=True)

        # Find highest-priority issue (first with positive deficiency)
        issue_type = None
        deficiency_value = 0
        for metric_name, deficiency in deficiencies:
            if deficiency > 0:
                issue_type = metric_name
                deficiency_value = deficiency
                break

        if issue_type is None:
            return None  # No issues

        # Determine recommended action based on issue type
        if issue_type == 'accessibility':
            # Check if contrast is the main issue (heuristic)
            if accessibility < 60:
                recommended_action = 'increase_contrast'
            else:
                recommended_action = 'improve_spacing'
            region = 'global'

        elif issue_type == 'symmetry':
            # Check specific symmetry issues (heuristic)
            # Note: Would need to re-analyze regions for detailed decision
            # Simplified: use equalize_header_footer as default
            recommended_action = 'equalize_header_footer'
            region = 'global'

        elif issue_type == 'harmony':
            # Check if diversity is the issue
            if harmony < 50:
                recommended_action = 'diversify_palette'
            else:
                recommended_action = 'increase_saturation'
            region = 'global'

        # Calculate severity based on deficiency magnitude
        if deficiency_value <= 20:
            severity = 1  # Low
        elif deficiency_value <= 40:
            severity = 2  # Medium
        else:
            severity = 3  # High

        # Return action dict
        return {
            'issue_type': issue_type,
            'region': region,
            'severity': severity,
            'recommended_action': recommended_action
        }

    def act(self, action, environment=None):
        """Execute improvement action by regenerating HTML/CSS.

        Args:
            action: Dict from think() with keys:
                - 'issue_type': str
                - 'recommended_action': str
                - 'region': str
                - 'severity': int
            environment: Unused (kept for ReasoningAgent compatibility)

        Returns:
            Absolute path to newly generated index.html

        Side Effects:
            - Appends action to self.action_history
            - Updates self.current_html_path
            - Calls convert_design(self.image_path) to regenerate HTML

        Raises:
            DesignToHTMLError: If convert_design() fails (with action context in message)

        Note:
            Current implementation regenerates full HTML from image.
            Region-specific modifications are not implemented (out of scope).
        """
        # Log action to history (before convert_design in case of error)
        self.action_history.append(action)

        try:
            # Regenerate HTML from image
            new_html_path = convert_design(self.image_path)

            # Update current HTML path
            self.current_html_path = new_html_path

            return new_html_path

        except project_types.DesignToHTMLError as e:
            # Re-raise with action context
            raise project_types.DesignToHTMLError(
                f"Failed to execute action {action['recommended_action']}: {str(e)}"
            )

    def observe(self, observation_dict):
        """Extract metrics from HTML/CSS state and store in observations.

        Args:
            observation_dict: Dict with keys:
                - 'html_content': str (complete HTML with CSS)
                - 'regions': dict (from detect_layout_regions)
                - 'colors': dict (from extract_colors)
                - 'iteration': int (0-indexed iteration number)

        Returns:
            None (modifies self.observations in-place)

        Side Effects:
            - Calculates accessibility, symmetry, harmony scores
            - Computes improvement deltas from previous iteration
            - Stores metrics in self.observations[iteration_number]
            - Updates self.observations (inherited dict attribute)

        Precondition:
            - observation_dict should contain required keys
            - Call in sequence: observe(0) → think() → act() → observe(1) → ...

        Postcondition:
            - self.observations[iteration] contains metrics dict with keys:
              accessibility_score, symmetry_score, harmony_score,
              improvement_from_previous, timestamp
        """
        # Validate inputs (graceful defaults)
        html_content = observation_dict.get('html_content', '')
        regions = observation_dict.get('regions', {})
        colors = observation_dict.get('colors', {})
        iteration = observation_dict.get('iteration', 0)

        # Calculate metrics using imported functions
        accessibility_score = calculate_accessibility_score(html_content)
        symmetry_score = calculate_symmetry_score(html_content, regions)
        harmony_score = calculate_harmony_score(html_content, colors)

        # Compute improvement from previous iteration
        improvement_from_previous = None
        if len(self.observations) > 0:
            # Get previous iteration metrics
            prev_iteration = max(self.observations.keys())
            prev_metrics = self.observations[prev_iteration]
            improvement_from_previous = {
                'accessibility': accessibility_score - prev_metrics['accessibility_score'],
                'symmetry': symmetry_score - prev_metrics['symmetry_score'],
                'harmony': harmony_score - prev_metrics['harmony_score']
            }

        # Store in observations dict
        self.observations[iteration] = {
            'accessibility_score': accessibility_score,
            'symmetry_score': symmetry_score,
            'harmony_score': harmony_score,
            'improvement_from_previous': improvement_from_previous,
            'timestamp': datetime.now().isoformat()
        }
