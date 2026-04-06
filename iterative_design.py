"""Entry point for iterative design refinement loop.

This module provides the improve_design() function that orchestrates the complete
iterative improvement cycle, taking a design mockup image and running the
think-act-observe loop to achieve target quality metrics.
"""

import os
import sys

# Add sources to path for imports - order matters!
# Must insert in reverse order: insert f98239d4 first, then 0c16ae7e
# This makes 0c16ae7e appear at index 0 (highest priority)
source_0c16ae7e = os.path.join(os.path.dirname(__file__), 'sources', '0c16ae7e')
source_f98239d4 = os.path.join(os.path.dirname(__file__), 'sources', 'f98239d4')

# Insert in reverse order so 0c16ae7e's main.py is found first
sys.path.insert(0, source_f98239d4)
sys.path.insert(0, source_0c16ae7e)

# Import from source 0c16ae7e main
from main import convert_design
from image_loader import load_image
from layout_detector import detect_layout_regions
from color_extractor import extract_colors
import project_types

DesignToHTMLError = project_types.DesignToHTMLError

# Import design agent (from project root)
from design_agent import DesignAgent


def improve_design(
    image_path: str,
    target_accessibility: int = 75,
    target_symmetry: int = 75,
    target_harmony: int = 75,
    max_iterations: int = 5
) -> dict:
    """Iteratively improve design mockup HTML/CSS quality.

    Takes a design image path and runs the think-act-observe cycle up to max_iterations
    times, measuring and improving HTML/CSS quality across three dimensions:
    accessibility (WCAG compliance), symmetry (layout balance), and harmony (color cohesion).

    Args:
        image_path: Path to PNG/JPG design mockup (200-2000px)
        target_accessibility: Target WCAG score [0, 100], default 75
        target_symmetry: Target layout balance [0, 100], default 75
        target_harmony: Target color cohesion [0, 100], default 75
        max_iterations: Max iteration count [1, 10], default 5

    Returns:
        Dict with keys:
        {
            'final_html_path': str (absolute path to final index.html),
            'initial_metrics': {
                'accessibility': int,
                'symmetry': int,
                'harmony': int
            },
            'final_metrics': {
                'accessibility': int,
                'symmetry': int,
                'harmony': int
            },
            'improvement_deltas': {
                'accessibility': int (signed, can be negative),
                'symmetry': int,
                'harmony': int
            },
            'iterations_performed': int (0 to max_iterations)
        }

    Raises:
        FileNotFoundError: If image_path doesn't exist
        ValueError: If thresholds not in [0, 100] or max_iterations not in [1, 10]
        DesignToHTMLError: If initial HTML generation fails

    Algorithm:
        1. Validate inputs (raise exceptions on invalid)
        2. Generate initial HTML baseline via convert_design()
        3. Load image and extract regions/colors
        4. Initialize DesignAgent with targets
        5. Perform initial observe() to establish baseline
        6. Loop for max_iterations:
           a. think() → get action or None (convergence)
           b. If None: break early (converged)
           c. act() → regenerate HTML (handle errors gracefully)
           d. observe() → measure new metrics
        7. Compile final report dict and return

    Error Handling:
        - Initial conversion failure: raise DesignToHTMLError
        - Mid-iteration conversion failure: log, skip iteration, continue
        - Convergence before max_iterations: break early, report actual count

    Logging:
        Print progress to stdout:
        - "Iteration 0: A=65 S=72 H=80 (baseline)"
        - "Iteration 1: A=70 S=74 H=82 (Δ: +5, +2, +2)"
        - "Converged at iteration 3"
    """
    # Step 1: Validate inputs

    # Validate image_path
    if not isinstance(image_path, str) or len(image_path) == 0:
        raise ValueError("image_path must be non-empty string")
    if not os.path.exists(image_path):
        raise FileNotFoundError(f"Image file not found: {image_path}")

    # Validate thresholds
    for name, value in [
        ('target_accessibility', target_accessibility),
        ('target_symmetry', target_symmetry),
        ('target_harmony', target_harmony)
    ]:
        if not isinstance(value, int):
            raise ValueError(f"{name} must be int, got {type(value).__name__}")
        if not (0 <= value <= 100):
            raise ValueError(f"{name} must be in [0, 100], got {value}")

    # Validate iteration count
    if not isinstance(max_iterations, int):
        raise ValueError(f"max_iterations must be int, got {type(max_iterations).__name__}")
    if not (1 <= max_iterations <= 10):
        raise ValueError(f"max_iterations must be in [1, 10], got {max_iterations}")

    # Step 2: Generate initial HTML baseline
    try:
        initial_html_path = convert_design(image_path)
    except Exception as e:
        raise DesignToHTMLError(f"Failed to generate initial HTML: {str(e)}")

    # Step 3: Load image and extract regions/colors
    image = load_image(image_path)
    regions = detect_layout_regions(image)
    colors = extract_colors(image, regions)

    # Step 4: Initialize agent
    agent = DesignAgent(
        image_path,
        initial_html_path,
        target_accessibility,
        target_symmetry,
        target_harmony
    )

    # Step 5: Initial observe (iteration 0 - baseline)
    with open(initial_html_path, 'r') as f:
        initial_html_content = f.read()

    agent.observe({
        'html_content': initial_html_content,
        'regions': regions,
        'colors': colors,
        'iteration': 0
    })

    # Extract initial metrics
    initial_metrics = {
        'accessibility': agent.observations[0]['accessibility_score'],
        'symmetry': agent.observations[0]['symmetry_score'],
        'harmony': agent.observations[0]['harmony_score']
    }

    print(f"Iteration 0: A={initial_metrics['accessibility']} "
          f"S={initial_metrics['symmetry']} H={initial_metrics['harmony']} (baseline)")

    # Step 6: Iteration loop
    iterations_performed = 0
    for iteration in range(1, max_iterations + 1):
        # Think
        action = agent.think()

        # Check convergence
        if action is None:
            print(f"Converged at iteration {iteration - 1}")
            break

        # Act
        try:
            new_html_path = agent.act(action)
        except DesignToHTMLError as e:
            print(f"Iteration {iteration}: Conversion failed: {e}")
            continue  # Skip this iteration

        # Observe
        with open(new_html_path, 'r') as f:
            new_html_content = f.read()

        # Re-detect regions/colors (or reuse if unchanged)
        # For simplicity, reuse initial regions/colors
        agent.observe({
            'html_content': new_html_content,
            'regions': regions,
            'colors': colors,
            'iteration': iteration
        })

        iterations_performed = iteration

        # Log progress
        current = agent.observations[iteration]
        improvement = current['improvement_from_previous']
        print(f"Iteration {iteration}: A={current['accessibility_score']} "
              f"S={current['symmetry_score']} H={current['harmony_score']} "
              f"(Δ: {improvement['accessibility']:+d}, {improvement['symmetry']:+d}, "
              f"{improvement['harmony']:+d})")

    # Step 7: Compile final report
    final_iteration = max(agent.observations.keys())
    final_metrics = {
        'accessibility': agent.observations[final_iteration]['accessibility_score'],
        'symmetry': agent.observations[final_iteration]['symmetry_score'],
        'harmony': agent.observations[final_iteration]['harmony_score']
    }

    improvement_deltas = {
        'accessibility': final_metrics['accessibility'] - initial_metrics['accessibility'],
        'symmetry': final_metrics['symmetry'] - initial_metrics['symmetry'],
        'harmony': final_metrics['harmony'] - initial_metrics['harmony']
    }

    return {
        'final_html_path': agent.current_html_path,
        'initial_metrics': initial_metrics,
        'final_metrics': final_metrics,
        'improvement_deltas': improvement_deltas,
        'iterations_performed': iterations_performed
    }
