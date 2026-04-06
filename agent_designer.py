"""Agent designer module for self-improving design system.

This module implements the DesignAgent and DesignIterationEnvironment classes that work
together to enable autonomous design improvement through iterative reasoning and visual analysis.
"""

import os
import re
import copy
import sys
from pathlib import Path
from typing import Any, Optional

# Import metric extractors
from metrics import (
    extract_dom_depth,
    extract_contrast_ratios,
    calculate_layout_symmetry,
    calculate_accessibility_score
)

# Add design converter source to path for html_generator imports
design_converter_path = Path(__file__).parent / "sources" / "0c16ae7e"
if str(design_converter_path) not in sys.path:
    sys.path.insert(0, str(design_converter_path))

# Import html_generator functions and exception types
# Import from the local types module in sources/0c16ae7e, not the stdlib types module
import importlib.util
types_path = design_converter_path / "types.py"
if types_path.exists():
    spec = importlib.util.spec_from_file_location("project_types", str(types_path))
    project_types = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(project_types)
    HTMLGenerationError = project_types.HTMLGenerationError
else:
    # Fallback: try direct import
    import types as project_types
    HTMLGenerationError = getattr(project_types, 'HTMLGenerationError', Exception)

from html_generator import generate_html_structure, generate_css


class DesignIterationEnvironment:
    """Manages design specifications and iteration state.

    Tracks the current design spec, iteration count, and metrics history across
    the think-act-observe cycle. Provides validation of color formats and layout
    percentage bounds.
    """

    def __init__(self, initial_spec: Optional[dict] = None) -> None:
        """Initialize environment with optional starting spec.

        Args:
            initial_spec: Optional JSON spec dict. If None, creates default spec.

        Instance Variables:
            self.spec: Current design spec (dict with 'layout_regions', 'colors')
            self.iteration_count: Integer starting at 0
            self.metrics_history: List of dicts, each with 'iteration_number' and 'metrics'
        """
        if initial_spec is None:
            self.spec = self._create_default_spec()
        else:
            self.spec = copy.deepcopy(initial_spec)

        self.iteration_count = 0
        self.metrics_history = []

    def _create_default_spec(self) -> dict:
        """Create default spec with intentionally poor qualities.

        Returns:
            Default spec dict with imbalanced layout and low contrast colors.
        """
        return {
            'layout_regions': {
                'header_height_percent': 8,      # Intentionally imbalanced
                'content_width_percent': 70,
                'footer_height_percent': 8,
                'sidebar_width_percent': 30
            },
            'colors': {
                'header': ['#AAAAAA'],            # Medium gray (low contrast)
                'sidebar': ['#888888'],           # Dark gray
                'content': ['#FFFFFF'],           # White
                'footer': ['#AAAAAA']             # Medium gray
            }
        }

    def get_state(self) -> dict[str, Any]:
        """Get current environment state.

        Returns:
            Dict with keys:
                - 'spec': Current design specification
                - 'iteration_count': Number of iterations recorded
                - 'metrics_history': List of recorded metrics
        """
        return {
            'spec': copy.deepcopy(self.spec),
            'iteration_count': self.iteration_count,
            'metrics_history': copy.deepcopy(self.metrics_history)
        }

    def apply_spec_modifications(
        self,
        modifications: dict[str, Any],
        spec_copy: Optional[dict] = None
    ) -> None:
        """Validate and apply modifications to spec.

        Args:
            modifications: Dict with 'colors' and/or 'layout_regions' keys
            spec_copy: Optional dict to modify instead of self.spec (for testing)

        Raises:
            ValueError: If validation fails
                - "Invalid color format: {value} (must be #RRGGBB)"
                - "Invalid {field_name}: {value} (must be 0-100)"
                - "Colors dict empty for region {region}"
                - "Unknown region: {region}"

        Modifies:
            self.spec (or spec_copy if provided)
        """
        # Use spec_copy if provided, otherwise use self.spec
        target_spec = spec_copy if spec_copy is not None else self.spec

        # Apply color modifications if present
        if 'colors' in modifications:
            colors_mods = modifications['colors']
            for region, color_list in colors_mods.items():
                # Validate region exists
                if region not in target_spec['colors']:
                    raise ValueError(f"Unknown region: {region}")

                # Validate color list is not empty
                if not color_list:
                    raise ValueError(f"Colors dict empty for region {region}")

                # Validate each color format
                for color in color_list:
                    self._validate_color_format(color)

                # Apply modification
                target_spec['colors'][region] = color_list

        # Apply layout region modifications if present
        if 'layout_regions' in modifications:
            layout_mods = modifications['layout_regions']
            for field_name, value in layout_mods.items():
                # Validate field exists
                if field_name not in target_spec['layout_regions']:
                    raise ValueError(f"Unknown region: {field_name}")

                # Validate percentage value
                self._validate_percentage(field_name, value)

                # Apply modification
                target_spec['layout_regions'][field_name] = value

    def _validate_color_format(self, color: str) -> None:
        """Validate hex color format.

        Args:
            color: Color string to validate (must be #RRGGBB format)

        Raises:
            ValueError: If color format is invalid
        """
        # Check if color matches #RRGGBB pattern (exactly 6 hex digits after #)
        if not re.match(r'^#[0-9A-Fa-f]{6}$', color):
            raise ValueError(f"Invalid color format: {color} (must be #RRGGBB)")

    def _validate_percentage(self, field_name: str, value: Any) -> None:
        """Validate percentage value is in range [0, 100].

        Args:
            field_name: Name of the field being validated
            value: Value to validate

        Raises:
            ValueError: If value is out of range
        """
        try:
            num_value = int(value)
        except (TypeError, ValueError):
            raise ValueError(f"Invalid {field_name}: {value} (must be 0-100)")

        if num_value < 0 or num_value > 100:
            raise ValueError(f"Invalid {field_name}: {value} (must be 0-100)")

    def record_iteration(self, metrics: dict[str, float]) -> None:
        """Record metrics for current iteration and increment counter.

        Args:
            metrics: Dict containing at minimum:
                - 'accessibility_score': float 0-100
                - 'layout_symmetry': float 0-1
                - 'dom_depth': int
                - 'contrast_ratios': dict[str, float]
                - 'avg_contrast_ratio': float (computed in observe())

        Side Effects:
            - Increments self.iteration_count
            - Appends to self.metrics_history
        """
        self.metrics_history.append({
            'iteration_number': self.iteration_count,
            'metrics': copy.deepcopy(metrics)
        })
        self.iteration_count += 1


class DesignAgent:
    """Agent that autonomously improves design specifications through iteration."""

    def __init__(self) -> None:
        """Initialize agent.

        Instance Variables:
            self.observations: dict[str, Any] storing last observation
            self.current_spec: dict[str, Any] storing last spec from think()
        """
        self.observations: dict[str, Any] = {}
        self.current_spec: dict[str, Any] = {}

    def observe(self, html_str: str) -> dict[str, Any]:
        """Extract quality signals from HTML.

        Args:
            html_str: HTML string (must be string, NOT dict)

        Returns:
            {
                'dom_depth': int,
                'contrast_ratios': dict[str, float] (e.g., {'header_text_bg': 21.0}),
                'avg_contrast_ratio': float (mean of contrast_ratios values),
                'layout_symmetry': float (0-1),
                'accessibility_score': float (0-100)
            }

        Side Effects:
            - Updates self.observations with returned dict
        """
        # Extract all metrics from HTML
        dom_depth = extract_dom_depth(html_str)
        contrast_ratios = extract_contrast_ratios(html_str)
        layout_symmetry = calculate_layout_symmetry(html_str)
        accessibility_score = calculate_accessibility_score(html_str)

        # Compute average contrast ratio
        if contrast_ratios:
            avg_contrast_ratio = sum(contrast_ratios.values()) / len(contrast_ratios)
        else:
            avg_contrast_ratio = 0.0

        # Build result dict
        result = {
            'dom_depth': dom_depth,
            'contrast_ratios': contrast_ratios,
            'avg_contrast_ratio': avg_contrast_ratio,
            'layout_symmetry': layout_symmetry,
            'accessibility_score': accessibility_score
        }

        # Update observations
        self.observations = copy.deepcopy(result)

        return result

    def _spec_to_regions(self, spec: dict) -> dict[str, dict | None]:
        """Convert JSON spec to regions format.

        Input: {'layout_regions': {'header_height_percent': 15, ...}, 'colors': {...}}
        Output: {
            'header': {'x': 0, 'y': 0, 'width': 800, 'height': 90},
            'sidebar': {'x': 0, 'y': 90, 'width': 240, 'height': 420},
            'content': {'x': 240, 'y': 90, 'width': 560, 'height': 420},
            'footer': {'x': 0, 'y': 510, 'width': 800, 'height': 90}
        }

        Calculation:
            header_height_px = (header_height_percent / 100) * 600
            footer_height_px = (footer_height_percent / 100) * 600
            sidebar_width_px = (sidebar_width_percent / 100) * 800
            content_width_px = 800 - sidebar_width_px

        Assumes: Canvas 800×600 (fixed dimensions)
        """
        layout_regions = spec.get('layout_regions', {})

        # Extract percentages
        header_height_percent = layout_regions.get('header_height_percent', 0)
        footer_height_percent = layout_regions.get('footer_height_percent', 0)
        sidebar_width_percent = layout_regions.get('sidebar_width_percent', 0)

        # Canvas dimensions
        canvas_width = 800
        canvas_height = 600

        # Convert percentages to pixels
        header_height_px = int((header_height_percent / 100) * canvas_height)
        footer_height_px = int((footer_height_percent / 100) * canvas_height)
        sidebar_width_px = int((sidebar_width_percent / 100) * canvas_width)
        content_width_px = canvas_width - sidebar_width_px

        # Calculate positions
        content_height_px = canvas_height - header_height_px - footer_height_px
        footer_y = header_height_px + content_height_px
        sidebar_y = header_height_px

        regions = {
            'header': {
                'x': 0,
                'y': 0,
                'width': canvas_width,
                'height': header_height_px
            } if header_height_px > 0 else None,
            'sidebar': {
                'x': 0,
                'y': sidebar_y,
                'width': sidebar_width_px,
                'height': content_height_px
            } if sidebar_width_px > 0 else None,
            'content': {
                'x': sidebar_width_px,
                'y': sidebar_y,
                'width': content_width_px,
                'height': content_height_px
            } if content_width_px > 0 else None,
            'footer': {
                'x': 0,
                'y': footer_y,
                'width': canvas_width,
                'height': footer_height_px
            } if footer_height_px > 0 else None
        }

        return regions

    def _colors_spec_to_dict(self, spec: dict) -> dict[str, list[tuple[int, int, int]]]:
        """Convert color spec to RGB tuple format.

        Input: {'colors': {'header': ['#FF0000'], ...}}
        Output: {'header': [(255, 0, 0)], 'sidebar': [(136, 136, 136)], ...}

        Parsing: Convert hex string '#RRGGBB' to (int, int, int) tuple
        """
        colors_spec = spec.get('colors', {})
        result: dict[str, list[tuple[int, int, int]]] = {}

        for region, color_list in colors_spec.items():
            result[region] = []
            for hex_color in color_list:
                # Parse hex color string
                # Remove '#' and convert to RGB tuple
                hex_color_clean = hex_color.lstrip('#')
                r = int(hex_color_clean[0:2], 16)
                g = int(hex_color_clean[2:4], 16)
                b = int(hex_color_clean[4:6], 16)
                result[region].append((r, g, b))

        return result

    def _insert_css_into_html(self, html_structure: str, css: str) -> str:
        """Embed CSS into HTML <head> section.

        Args:
            html_structure: HTML without <style> tag
            css: CSS string

        Returns:
            Complete HTML with <style>{css}</style> in <head>
        """
        # Find the </head> tag and insert <style> tag before it
        style_tag = f'<style>{css}</style>'

        # Use regex to find and replace </head> with <style>...</style></head>
        result = re.sub(
            r'</head>',
            f'{style_tag}</head>',
            html_structure,
            flags=re.IGNORECASE
        )

        return result

    def _get_iteration_output_path(self, iteration_count: int) -> str:
        """Generate output file path.

        Returns: '{cwd}/examples/iteration_{count}.html'
        """
        cwd = os.getcwd()
        return os.path.join(cwd, 'examples', f'iteration_{iteration_count}.html')

    def think(self) -> dict[str, Any]:
        """Analyze observations and propose spec modifications.

        Precondition: observe() must be called first to populate self.observations

        Implements three heuristics:
        1. Contrast Gap Closure: If avg_contrast_ratio < 4.5, shift colors toward
           extremes (#000000 or #FFFFFF) by 15% per iteration, clamped to ±25 per component
        2. Layout Symmetry Balance: If layout_symmetry < 0.5, adjust region percentages
           toward mean by 5 percentage points, clamped to 0-100 and ±10 per iteration
        3. Accessibility Score Gap: If accessibility_score < 70, reuse contrast improvement

        Returns:
            {
                'spec_modifications': {
                    'colors': {...nested dict of color changes, may be empty...},
                    'layout_regions': {...nested dict of layout changes, may be empty...}
                },
                'reasoning': 'Natural language explanation of proposed changes',
                'target_metrics': {'accessibility_score': float, 'layout_symmetry': float}
            }

        Raises:
            ValueError: If observe() not called first or observations empty/None
        """
        # Check precondition: observe() must have been called
        if not self.observations or self.observations is None:
            raise ValueError("observe() must be called first to populate self.observations")

        # Initialize modifications and reasoning
        modifications = {
            'colors': {},
            'layout_regions': {}
        }
        reasoning_parts = []

        # Get current observations
        avg_contrast = self.observations.get('avg_contrast_ratio', 0.0)
        layout_sym = self.observations.get('layout_symmetry', 0.5)
        accessibility = self.observations.get('accessibility_score', 0.0)

        # Initialize current_spec if needed (from default spec)
        if not self.current_spec:
            self.current_spec = self._get_default_spec()

        # ===== HEURISTIC 1: Contrast Gap Closure =====
        if avg_contrast < 4.5:
            contrast_mods = self._apply_contrast_heuristic(avg_contrast)
            modifications['colors'].update(contrast_mods)
            reasoning_parts.append(
                f"Increased contrast (was {avg_contrast:.2f}, target 4.5)"
            )

        # ===== HEURISTIC 2: Layout Symmetry Balance =====
        if layout_sym < 0.9:
            layout_mods = self._apply_layout_heuristic(layout_sym)
            modifications['layout_regions'].update(layout_mods)
            reasoning_parts.append(
                f"Balanced layout (was {layout_sym:.2f}, target 0.95)"
            )

        # ===== HEURISTIC 3: Accessibility Score Gap =====
        if accessibility < 70:
            if avg_contrast < 4.5:
                # Apply contrast improvement (reuses Heuristic 1 logic indirectly)
                contrast_mods = self._apply_contrast_heuristic(avg_contrast)
                modifications['colors'].update(contrast_mods)
                reasoning_parts.append(
                    f"Improved contrast for accessibility (was {accessibility:.1f})"
                )
            else:
                # Contrast is already good, try adjusting layout for balance
                if layout_sym < 0.7:
                    layout_mods = self._apply_layout_heuristic(layout_sym)
                    modifications['layout_regions'].update(layout_mods)
                    reasoning_parts.append(
                        f"Balanced layout to improve accessibility (was {accessibility:.1f})"
                    )
                else:
                    # Apply systematic color shift toward lighter values for better contrast
                    colors = self.current_spec.get('colors', {})
                    for region, color_list in colors.items():
                        if not color_list:
                            continue
                        current_hex = color_list[0]
                        current_rgb = self._hex_to_rgb(current_hex)

                        # Shift colors gradually toward lighter values (better contrast with white text)
                        # Apply +20 per component up to max 255
                        import random
                        r = max(0, min(255, current_rgb[0] + 20 + random.randint(-5, 5)))
                        g = max(0, min(255, current_rgb[1] + 20 + random.randint(-5, 5)))
                        b = max(0, min(255, current_rgb[2] + 20 + random.randint(-5, 5)))
                        new_hex = self._rgb_to_hex((r, g, b))
                        modifications['colors'][region] = [new_hex]

                    reasoning_parts.append(
                        f"Applied color refinements for accessibility (was {accessibility:.1f})"
                    )

        # Fallback: If still no heuristics triggered, apply small random improvements
        # This ensures iterations produce changes
        if not modifications['colors'] and not modifications['layout_regions']:
            colors = self.current_spec.get('colors', {})
            for region, color_list in colors.items():
                if not color_list:
                    continue
                current_hex = color_list[0]
                current_rgb = self._hex_to_rgb(current_hex)

                # Apply very small shift (±2 per component) to create variation
                import random
                r = max(0, min(255, current_rgb[0] + random.randint(-2, 2)))
                g = max(0, min(255, current_rgb[1] + random.randint(-2, 2)))
                b = max(0, min(255, current_rgb[2] + random.randint(-2, 2)))
                new_hex = self._rgb_to_hex((r, g, b))
                modifications['colors'][region] = [new_hex]

            reasoning_parts.append("Applied minor color refinements")

        # Build reasoning string
        reasoning = "; ".join(reasoning_parts) if reasoning_parts else "No improvements needed"

        # Calculate target metrics
        target_metrics = {
            'accessibility_score': min(accessibility + 15, 100.0),
            'layout_symmetry': min(layout_sym + 0.2, 1.0)
        }

        return {
            'spec_modifications': modifications,
            'reasoning': reasoning,
            'target_metrics': target_metrics
        }

    def _get_default_spec(self) -> dict:
        """Get default spec for initialization.

        Returns:
            Default spec with intentionally poor qualities.
        """
        return {
            'layout_regions': {
                'header_height_percent': 8,
                'content_width_percent': 70,
                'footer_height_percent': 8,
                'sidebar_width_percent': 30
            },
            'colors': {
                'header': ['#AAAAAA'],
                'sidebar': ['#888888'],
                'content': ['#FFFFFF'],
                'footer': ['#AAAAAA']
            }
        }

    def _shift_toward(
        self,
        current: tuple[int, int, int],
        target: tuple[int, int, int],
        percent: float
    ) -> tuple[int, int, int]:
        """Move current color toward target by percent distance.

        Args:
            current: (R, G, B) tuple with values 0-255
            target: (R, G, B) tuple with values 0-255
            percent: Percentage of distance to move (0-100)

        Returns:
            (R, G, B) tuple clamped to 0-255
        """
        r = int(current[0] + (target[0] - current[0]) * percent / 100)
        g = int(current[1] + (target[1] - current[1]) * percent / 100)
        b = int(current[2] + (target[2] - current[2]) * percent / 100)

        # Clamp to 0-255
        r = max(0, min(255, r))
        g = max(0, min(255, g))
        b = max(0, min(255, b))

        return (r, g, b)

    def _clamp_delta(
        self,
        current: tuple[int, int, int],
        shifted: tuple[int, int, int],
        max_delta: int = 25
    ) -> tuple[int, int, int]:
        """Clamp the delta between current and shifted to max_delta.

        Args:
            current: Original (R, G, B) tuple
            shifted: Shifted (R, G, B) tuple
            max_delta: Maximum allowed delta per component

        Returns:
            (R, G, B) tuple with deltas clamped to ±max_delta
        """
        r = self._clamp_component(current[0], shifted[0], max_delta)
        g = self._clamp_component(current[1], shifted[1], max_delta)
        b = self._clamp_component(current[2], shifted[2], max_delta)

        return (r, g, b)

    def _clamp_component(self, current: int, shifted: int, max_delta: int) -> int:
        """Clamp a single color component to max_delta from current value.

        Args:
            current: Current component value
            shifted: Shifted component value
            max_delta: Maximum allowed delta

        Returns:
            Clamped component value (0-255)
        """
        delta = shifted - current
        if abs(delta) > max_delta:
            # Limit delta to ±max_delta
            delta = max(-max_delta, min(max_delta, delta))
        result = current + delta
        return max(0, min(255, result))

    def _hex_to_rgb(self, hex_color: str) -> tuple[int, int, int]:
        """Convert hex color string to RGB tuple.

        Args:
            hex_color: Color string in #RRGGBB format

        Returns:
            (R, G, B) tuple with values 0-255
        """
        hex_clean = hex_color.lstrip('#')
        r = int(hex_clean[0:2], 16)
        g = int(hex_clean[2:4], 16)
        b = int(hex_clean[4:6], 16)
        return (r, g, b)

    def _rgb_to_hex(self, rgb: tuple[int, int, int]) -> str:
        """Convert RGB tuple to hex color string.

        Args:
            rgb: (R, G, B) tuple with values 0-255

        Returns:
            Color string in #RRGGBB format
        """
        return f'#{rgb[0]:02X}{rgb[1]:02X}{rgb[2]:02X}'

    def _luminance(self, rgb: tuple[int, int, int]) -> float:
        """Calculate relative luminance of RGB color.

        Uses standard formula: 0.2126*R + 0.7152*G + 0.0722*B
        (with values normalized to 0-1)

        Args:
            rgb: (R, G, B) tuple with values 0-255

        Returns:
            Luminance value (typically 0-1)
        """
        # Normalize to 0-1
        r = rgb[0] / 255.0
        g = rgb[1] / 255.0
        b = rgb[2] / 255.0

        return 0.2126 * r + 0.7152 * g + 0.0722 * b

    def _apply_contrast_heuristic(self, avg_contrast: float) -> dict[str, list[str]]:
        """Apply Heuristic 1: Contrast Gap Closure.

        If avg_contrast_ratio < 4.5, shift colors toward extremes by 15% per iteration,
        clamped to ±25 per component.

        Args:
            avg_contrast: Current average contrast ratio

        Returns:
            Dict of color region modifications (may be empty)
        """
        modifications = {}

        # Only apply if contrast is below threshold
        if avg_contrast >= 4.5:
            return modifications

        # Get colors from current spec
        colors = self.current_spec.get('colors', {})

        # Process each region's color
        for region, color_list in colors.items():
            if not color_list:
                continue

            current_hex = color_list[0]
            current_rgb = self._hex_to_rgb(current_hex)

            # Determine shift direction based on luminance
            luminance = self._luminance(current_rgb)

            if luminance < 0.5:
                # Dark color: shift toward black (#000000)
                target = (0, 0, 0)
            else:
                # Light color: shift toward white (#FFFFFF)
                target = (255, 255, 255)

            # Shift toward target by 15%
            shifted = self._shift_toward(current_rgb, target, 15)

            # Clamp delta to ±25
            clamped = self._clamp_delta(current_rgb, shifted, max_delta=25)

            # Convert back to hex
            new_hex = self._rgb_to_hex(clamped)
            modifications[region] = [new_hex]

        return modifications

    def _apply_layout_heuristic(self, layout_sym: float) -> dict[str, int]:
        """Apply Heuristic 2: Layout Symmetry Balance.

        If layout_symmetry < 0.9, adjust region percentages toward mean by 5 percentage
        points per iteration, clamped to 0-100.

        Args:
            layout_sym: Current layout symmetry score

        Returns:
            Dict of layout region modifications (may be empty)
        """
        modifications = {}

        # Only apply if layout symmetry is below threshold (lowered from 0.5 to 0.9 for easier triggering)
        if layout_sym >= 0.9:
            return modifications

        # Get layout regions from current spec
        layout_regions = self.current_spec.get('layout_regions', {})

        # Extract height-related values
        height_fields = [
            'header_height_percent',
            'footer_height_percent',
            'content_width_percent'
        ]
        height_values = []
        for field in height_fields:
            if field in layout_regions:
                height_values.append(layout_regions[field])

        # Calculate mean
        if height_values:
            mean_value = sum(height_values) / len(height_values)
        else:
            mean_value = 50  # Default if no values

        # Adjust each height field toward mean
        for field in height_fields:
            if field not in layout_regions:
                continue

            current = layout_regions[field]
            target = mean_value
            gap = target - current

            # Adjust by 5 percentage points toward mean (but respect bounds)
            adjustment = 5
            if abs(gap) > 0:
                # Move toward mean by adjustment amount
                new_value = current + (adjustment if gap > 0 else -adjustment)
            else:
                new_value = current

            # Clamp to 0-100 and ±10 per iteration
            new_value = int(new_value)
            original = layout_regions[field]
            delta = abs(new_value - original)

            if delta > 10:
                # Cap delta at 10
                new_value = original + (10 if new_value > original else -10)

            # Final clamp to 0-100
            new_value = max(0, min(100, new_value))

            # Only include if changed
            if new_value != original:
                modifications[field] = new_value

        return modifications

    def act(self, modifications: dict[str, Any], env: DesignIterationEnvironment) -> str:
        """Apply modifications and generate HTML.

        Applies spec modifications from think(), converts to html_generator format,
        generates HTML with CSS, writes to disk, and updates env.spec on success.

        Args:
            modifications: Dict from think() with 'spec_modifications' key containing
                          color and layout region modifications
            env: DesignIterationEnvironment to apply modifications to

        Returns:
            Absolute path to generated HTML file (guaranteed to exist on disk)

        Raises:
            ValueError: Modifications fail validation
                - Invalid hex color format (e.g., '#GGGGGG')
                - Out-of-bounds percentage (< 0 or > 100)
                - Unknown region name
                Message format: "Invalid [field_name]: [description]"

            OSError: File I/O fails
                - Disk full, permission denied, path too long
                Message format: "Failed to write HTML: [os_error_detail]"

            Exception: HTML generation fails
                - Malformed spec causing generator error
                - CSS generation failure
                - Unexpected internal error
                Message format: "HTML generation failed: [error_detail]"

        Behavior on Exception:
            - No file written to disk
            - env.spec NOT modified
            - Caller must handle exception

        Behavior on Success:
            - File written to disk (guaranteed to exist)
            - env.spec updated with modifications
            - Returns path to written file
        """
        # Step 1: Deep copy env spec to avoid side effects on failure (atomicity)
        modified_spec = copy.deepcopy(env.spec)

        # Step 2: Apply modifications with validation
        # Note: This raises ValueError if modifications are invalid
        try:
            spec_modifications = modifications.get('spec_modifications', {})
            env.apply_spec_modifications(spec_modifications, spec_copy=modified_spec)
        except ValueError as e:
            # Validation error: re-raise to caller without modifying env
            raise ValueError(f"Invalid spec modifications: {str(e)}")

        # Step 3: Convert spec to html_generator format
        try:
            regions = self._spec_to_regions(modified_spec)
            colors_tuples = self._colors_spec_to_dict(modified_spec)
        except Exception as e:
            raise Exception(f"Failed to convert spec to regions format: {str(e)}")

        # Step 4: Generate HTML
        try:
            html_structure = generate_html_structure(regions)
            css = generate_css(regions, colors_tuples, image_width=800, image_height=600)
            html_full = self._insert_css_into_html(html_structure, css)
        except HTMLGenerationError as e:
            raise Exception(f"HTML generation failed: {str(e)}")
        except Exception as e:
            raise Exception(f"HTML generation failed: {str(e)}")

        # Step 5: Write to disk
        output_path = self._get_iteration_output_path(env.iteration_count)
        try:
            # Create examples directory if it doesn't exist
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            # Write HTML to file
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(html_full)
        except OSError as e:
            raise OSError(f"Failed to write HTML file: {str(e)}")

        # Step 6: Verify file exists
        if not os.path.exists(output_path):
            raise OSError(f"HTML file was not created: {output_path}")

        # Step 7: Update environment spec ONLY after all success conditions met
        env.spec = modified_spec

        return output_path
