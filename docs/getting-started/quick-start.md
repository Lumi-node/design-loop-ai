# 🚀 DesignLoop AI Quick Start Guide

Welcome to DesignLoop AI! This guide will get you up and running quickly with our powerful design automation toolkit.

DesignLoop AI allows you to define, iterate, and evaluate design processes using intelligent agents.

## Prerequisites

Ensure you have Python installed (3.8+ recommended).

Install the package:

```bash
pip install design_loop_ai
```

## Project Structure Overview

The core components of the library are:

*   `agent_designer.py`: Contains the logic for defining and managing AI agents.
*   `main.py`: The primary entry point for running design loops.
*   `metrics.py`: Tools for evaluating the quality and performance of generated designs.
*   `tests/`: Contains unit tests.

---

## 💡 Usage Examples

Here are three practical examples demonstrating how to use the core functionalities of DesignLoop AI.

### Example 1: Simple Design Generation (Using `agent_designer.py`)

This example shows how to instantiate a basic agent and prompt it to generate a concept based on a simple requirement.

```python
# example_1_generation.py
from design_loop_ai.agent_designer import AgentDesigner

# 1. Initialize the Agent Designer
designer = AgentDesigner()

# 2. Define the prompt/goal
prompt = "Design a minimalist landing page for a sustainable coffee brand. Focus on earthy tones."

print("--- Generating Initial Design Concept ---")
# 3. Run the generation process
design_output = designer.generate_design(prompt=prompt)

print("\n✅ Design Concept Generated:")
print(design_output)
```

### Example 2: Iterative Refinement Loop (Using `main.py`)

This demonstrates the core strength of DesignLoop: iterative improvement. We start with a concept and ask the agent to refine it based on specific feedback.

```python
# example_2_iteration.py
from design_loop_ai.main import run_design_loop

# Define the initial state and the refinement steps
initial_prompt = "A dark-mode dashboard for a productivity app."
refinement_steps = [
    "Increase the contrast ratio for better accessibility.",
    "Incorporate subtle animations on hover states.",
    "Simplify the navigation bar to only three icons."
]

print("--- Starting Iterative Design Loop ---")

# Run the loop, passing the initial prompt and the sequence of feedback
final_design = run_design_loop(
    initial_prompt=initial_prompt,
    feedback_sequence=refinement_steps
)

print("\n✨ Final Refined Design:")
print(final_design)
```

### Example 3: Evaluating Design Quality (Using `metrics.py`)

Once you have a design (or a set of designs), you need to know if it's good. This example uses the `metrics` module to score the output against predefined criteria.

*(Assume `design_output_json` is the structured output from a previous step)*

```python
# example_3_evaluation.py
from design_loop_ai.metrics import DesignEvaluator

# Mock design output (in a real scenario, this comes from agent_designer)
design_output_json = {
    "layout": "Grid-based",
    "color_palette": ["#333333", "#F5F5DC"],
    "usability_score": 0.75,
    "complexity": "Low"
}

# 1. Initialize the Evaluator
evaluator = DesignEvaluator()

# 2. Define evaluation criteria (e.g., target accessibility score)
criteria = {
    "min_usability_score": 0.80,
    "max_complexity": "Medium"
}

# 3. Run the evaluation
evaluation_report = evaluator.evaluate(
    design_data=design_output_json,
    criteria=criteria
)

print("--- Design Evaluation Report ---")
print(f"Overall Score: {evaluation_report['overall_score']:.2f}")
print("Detailed Feedback:")
for metric, result in evaluation_report['details'].items():
    print(f"  - {metric}: {result}")
```

## 📚 Next Steps

1.  **Dive Deeper:** Explore `agent_designer.py` to customize agent personalities and toolsets.
2.  **Tune Metrics:** Modify the scoring functions in `metrics.py` to match your specific design quality standards.
3.  **Advanced Loops:** Experiment with complex feedback loops in `main.py` where the agent can self-correct based on metric scores.