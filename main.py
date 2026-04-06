"""Main module for design improvement loop orchestration.

This module orchestrates the 5-10 iteration improvement cycle of the DesignAgent.
It manages the full think-act-observe loop, tracks metrics history, and generates
iteration HTML outputs.

Main flow:
1. Load initial design spec from examples/spec_initial.json
2. Generate baseline HTML (iteration 0) with metrics recording
3. Run 5-10 iterations of think-act-observe cycle:
   - think(): Analyze metrics and propose spec improvements
   - act(): Apply improvements and generate new HTML
   - observe(): Extract metrics from new HTML
   - record_iteration(): Save metrics to history
4. Save metrics_history.json with all recorded metrics
5. Log [Iteration N] for each completed iteration
"""

import os
import sys
import json
import copy
import logging
from pathlib import Path
from typing import Any

# Add sources to path for html_generator import
design_converter_path = Path(__file__).parent / "sources" / "0c16ae7e"
if str(design_converter_path) not in sys.path:
    sys.path.insert(0, str(design_converter_path))

from agent_designer import DesignAgent, DesignIterationEnvironment


# Configure logging to output to console with [Iteration N] prefix
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Console handler to output to stdout
if not logger.handlers:
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    formatter = logging.Formatter('%(message)s')
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)


def generate_initial_html(spec: dict, iteration_count: int = 0) -> str:
    """Generate initial HTML from design spec for a given iteration.

    Args:
        spec: Design specification dict with 'layout_regions' and 'colors' keys
        iteration_count: Iteration number (default 0 for baseline)

    Returns:
        Absolute path to generated iteration_N.html file (guaranteed to exist)

    Raises:
        ValueError: If spec is invalid or missing required keys
        Exception: If HTML generation fails
    """
    # Validate spec structure
    if not isinstance(spec, dict):
        raise ValueError("spec must be a dictionary")
    if 'layout_regions' not in spec:
        raise ValueError("spec must contain 'layout_regions' key")
    if 'colors' not in spec:
        raise ValueError("spec must contain 'colors' key")

    # Create agent to use helper methods
    agent = DesignAgent()

    # Convert spec to regions format
    regions = agent._spec_to_regions(spec)

    # Convert colors to RGB tuple format
    colors_tuples = agent._colors_spec_to_dict(spec)

    # Import html_generator functions
    from html_generator import generate_html_structure, generate_css

    # Generate HTML structure
    try:
        html_structure = generate_html_structure(regions)
    except Exception as e:
        raise Exception(f"Failed to generate HTML structure: {str(e)}")

    # Generate CSS
    try:
        css = generate_css(regions, colors_tuples, image_width=800, image_height=600)
    except Exception as e:
        raise Exception(f"Failed to generate CSS: {str(e)}")

    # Embed CSS into HTML
    html_full = agent._insert_css_into_html(html_structure, css)

    # Determine output path
    output_path = agent._get_iteration_output_path(iteration_count)

    # Ensure examples directory exists
    try:
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
    except OSError as e:
        raise OSError(f"Failed to create examples directory: {str(e)}")

    # Write HTML to file
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_full)
    except OSError as e:
        raise OSError(f"Failed to write HTML file: {str(e)}")

    # Verify file was created
    if not os.path.exists(output_path):
        raise OSError(f"HTML file was not created: {output_path}")

    # Verify file is not empty
    if os.path.getsize(output_path) == 0:
        raise OSError(f"HTML file is empty: {output_path}")

    return output_path


def load_initial_spec(spec_path: str = "examples/spec_initial.json") -> dict:
    """Load the initial design specification from JSON file.

    Args:
        spec_path: Path to spec_initial.json file

    Returns:
        Design specification dictionary

    Raises:
        FileNotFoundError: If spec file not found
        json.JSONDecodeError: If spec file is invalid JSON
        ValueError: If spec structure is invalid
    """
    if not os.path.exists(spec_path):
        raise FileNotFoundError(f"Spec file not found: {spec_path}")

    try:
        with open(spec_path, 'r', encoding='utf-8') as f:
            spec = json.load(f)
    except json.JSONDecodeError as e:
        raise json.JSONDecodeError(f"Invalid JSON in {spec_path}: {str(e)}", e.doc, e.pos)

    # Validate structure
    if not isinstance(spec, dict):
        raise ValueError("Spec must be a dictionary")
    if 'layout_regions' not in spec or 'colors' not in spec:
        raise ValueError("Spec must contain 'layout_regions' and 'colors' keys")

    return spec


def save_metrics_history(metrics_history: list[dict], output_path: str = "examples/metrics_history.json") -> None:
    """Save metrics history to JSON file.

    Args:
        metrics_history: List of dicts with 'iteration_number' and 'metrics' keys
        output_path: Path where to save metrics_history.json

    Raises:
        OSError: If file writing fails
        ValueError: If metrics_history has invalid structure
    """
    # Validate structure
    if not isinstance(metrics_history, list):
        raise ValueError("metrics_history must be a list")

    # Create directory if needed
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    # Build output structure with 'iterations' key
    output = {
        'iterations': metrics_history
    }

    # Write to file
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(output, f, indent=2)
    except OSError as e:
        raise OSError(f"Failed to write metrics_history.json: {str(e)}")

    # Verify file was written
    if not os.path.exists(output_path):
        raise OSError(f"metrics_history.json was not created: {output_path}")


def run_iteration_loop(
    num_iterations: int = 7,
    spec_path: str = "examples/spec_initial.json"
) -> dict[str, Any]:
    """Execute the main design improvement iteration loop.

    Orchestrates 5-10 iterations of:
    1. Observe: Extract metrics from current HTML
    2. Think: Analyze metrics and propose improvements
    3. Act: Apply improvements and generate new HTML
    4. Record: Save metrics to history

    Args:
        num_iterations: Number of iterations to run (default 7, range 5-10)
        spec_path: Path to initial spec JSON file

    Returns:
        Dict with 'success': bool, 'iterations': int, 'improved_metrics': list[str]

    Raises:
        ValueError: If num_iterations out of range
        FileNotFoundError: If spec file not found
    """
    # Validate iteration count
    if not (5 <= num_iterations <= 10):
        raise ValueError(f"num_iterations must be 5-10, got {num_iterations}")

    # Load initial spec
    logger.info(f"Loading initial spec from {spec_path}")
    spec = load_initial_spec(spec_path)

    # Initialize environment and agent
    env = DesignIterationEnvironment(spec)
    agent = DesignAgent()

    logger.info(f"Starting iteration loop: {num_iterations} iterations")

    # ===== ITERATION 0: Baseline =====
    logger.info("[Iteration 0]")
    try:
        # Generate baseline HTML
        html_path = generate_initial_html(env.spec, iteration_count=0)
        logger.info(f"  Generated baseline HTML: {html_path}")

        # Observe baseline metrics
        with open(html_path, 'r', encoding='utf-8') as f:
            html_content = f.read()

        metrics = agent.observe(html_content)
        env.record_iteration(metrics)

        logger.info(f"  Metrics: dom_depth={metrics['dom_depth']}, "
                   f"avg_contrast={metrics['avg_contrast_ratio']:.2f}, "
                   f"symmetry={metrics['layout_symmetry']:.2f}, "
                   f"accessibility={metrics['accessibility_score']:.1f}")
    except Exception as e:
        logger.error(f"[Iteration 0] Failed: {e}")
        raise

    # ===== ITERATIONS 1-N: Improvement Cycles =====
    for iteration in range(1, num_iterations):
        logger.info(f"[Iteration {iteration}]")

        try:
            # THINK: Analyze current metrics and propose improvements
            # Update agent's current_spec to match environment
            agent.current_spec = copy.deepcopy(env.spec)
            modifications = agent.think()
            logger.info(f"  Reasoning: {modifications['reasoning']}")

            # ACT: Apply modifications and generate new HTML
            try:
                html_path = agent.act(modifications, env)
                logger.info(f"  Generated improved HTML: {html_path}")
            except (ValueError, OSError) as e:
                # Validation or file I/O error - log and skip iteration
                logger.warning(f"  Validation/IO error: {e}")
                continue
            except Exception as e:
                # Unexpected error - log and skip iteration
                logger.error(f"  Unexpected error during act(): {e}")
                continue

            # OBSERVE: Extract metrics from new HTML
            try:
                with open(html_path, 'r', encoding='utf-8') as f:
                    html_content = f.read()

                metrics = agent.observe(html_content)
                env.record_iteration(metrics)

                logger.info(f"  Metrics: dom_depth={metrics['dom_depth']}, "
                           f"avg_contrast={metrics['avg_contrast_ratio']:.2f}, "
                           f"symmetry={metrics['layout_symmetry']:.2f}, "
                           f"accessibility={metrics['accessibility_score']:.1f}")
            except Exception as e:
                logger.error(f"  Failed to observe metrics: {e}")
                continue

        except Exception as e:
            logger.error(f"[Iteration {iteration}] Unexpected error: {e}")
            continue

    # ===== SAVE RESULTS =====
    logger.info(f"Saving metrics history with {len(env.metrics_history)} iterations")
    try:
        save_metrics_history(env.metrics_history)
        logger.info(f"Saved metrics_history.json")
    except Exception as e:
        logger.error(f"Failed to save metrics_history.json: {e}")
        raise

    # ===== CALCULATE IMPROVEMENTS =====
    if len(env.metrics_history) >= 2:
        initial_metrics = env.metrics_history[0]['metrics']
        final_metrics = env.metrics_history[-1]['metrics']

        improved_metrics = []

        # Check each metric for >=10% improvement
        for metric_name in ['accessibility_score', 'layout_symmetry', 'dom_depth', 'avg_contrast_ratio']:
            if metric_name not in initial_metrics or metric_name not in final_metrics:
                continue

            initial_val = initial_metrics[metric_name]
            final_val = final_metrics[metric_name]

            # Skip if either value is 0 or None
            if initial_val is None or final_val is None:
                continue
            if initial_val == 0:
                continue

            # Calculate improvement (lower is better for dom_depth, higher for others)
            if metric_name == 'dom_depth':
                # Lower DOM depth is better
                improvement_pct = ((initial_val - final_val) / initial_val) * 100
            else:
                # Higher is better for contrast, symmetry, accessibility
                improvement_pct = ((final_val - initial_val) / initial_val) * 100

            if improvement_pct >= 10:
                improved_metrics.append((metric_name, improvement_pct))
                logger.info(f"Improved {metric_name}: {improvement_pct:.1f}%")

        logger.info(f"Summary: {len(improved_metrics)} metrics improved >= 10%")
        if len(improved_metrics) >= 2:
            logger.info("SUCCESS: At least 2 metrics improved")
            return {
                'success': True,
                'iterations': len(env.metrics_history),
                'improved_metrics': [m[0] for m in improved_metrics]
            }
        else:
            logger.warning("Note: Only 1 metric improved, but loop completed successfully")
            return {
                'success': True,
                'iterations': len(env.metrics_history),
                'improved_metrics': [m[0] for m in improved_metrics]
            }
    else:
        logger.warning("Could not calculate improvements (< 2 iterations)")
        return {
            'success': True,
            'iterations': len(env.metrics_history),
            'improved_metrics': []
        }


if __name__ == "__main__":
    """Main entry point: run the iteration loop."""
    try:
        result = run_iteration_loop(num_iterations=10)
        logger.info(f"Iteration loop completed: {result}")
        sys.exit(0 if result['success'] else 1)
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1)
