# 🚀 DesignLoop AI Quick Start Guide

Welcome to DesignLoop AI! This guide will get you up and running with our core design automation framework, focusing on the `design_agent.py` module.

DesignLoop AI allows you to automate the iterative refinement of UI designs by wrapping a design-to-HTML converter within a sophisticated Reasoning Agent loop.

## 📦 Package Structure

The core functionality resides within the `design_loop_ai` package:

*   `design_agent.py`: The main reasoning engine that drives the iterative design process.
*   `iterative_design.py`: Manages the overall loop execution and state transitions.
*   `metrics.py`: Contains functions to analyze generated HTML/CSS against predefined design principles.
*   `tests/__init__.py`: Unit tests for the components.

## ✨ Core Concept: The Reasoning Agent Loop

The `design_agent.py` implements a closed-loop system:

1.  **`think()`**: The agent analyzes the current HTML output using rules defined in `metrics.py` (e.g., "Contrast ratio for primary text is below WCAG AA").
2.  **`act()`**: Based on the analysis, the agent modifies the input design specifications (the "prompt" or "specs") to target the identified weaknesses.
3.  **`observe()`**: The new specifications are fed back into the design-to-HTML converter, and the resulting HTML is analyzed again by `metrics.py`.

**Success Criteria:** The agent must improve a baseline design mockup across 3+ measurable dimensions (Accessibility Score, Layout Symmetry, Color Harmony) within 5 iterations.

## 🛠️ Installation (Conceptual)

Assuming you have the package installed:

```bash
pip install design_loop_ai
```

## 💻 Usage Examples

Here are a few ways to utilize the `design_agent.py` module.

### Example 1: Basic Accessibility Improvement Loop

This example initializes an agent with a poor baseline design and runs the loop until the accessibility score improves significantly.

```python
from design_loop_ai.design_agent import ReasoningAgent
from design_loop_ai.iterative_design import run_design_cycle
from design_loop_ai.metrics import AccessibilityMetric

# 1. Define the initial, flawed design specification
initial_specs = {
    "layout": "two-column",
    "color_palette": ["#000000", "#FFFFFF"], # Poor contrast example
    "component_structure": "header_nav_content_footer"
}

# 2. Initialize the agent, specifying the metrics it must optimize
agent = ReasoningAgent(
    initial_specs=initial_specs,
    optimization_targets=[AccessibilityMetric()]
)

print("--- Starting Accessibility Optimization ---")

# 3. Run the full iterative cycle
final_design_html, history = run_design_cycle(agent, max_iterations=5)

print("\n✅ Optimization Complete.")
print(f"Final Accessibility Score: {history[-1]['metrics']['accessibility_score']:.2f}")
# In a real scenario, you would save final_design_html to a file
```

### Example 2: Focusing on Layout Symmetry and Harmony

This example demonstrates how to guide the agent to focus on visual aesthetics rather than just accessibility, by prioritizing different metrics.

```python
from design_loop_ai.design_agent import ReasoningAgent
from design_loop_ai.iterative_design import run_design_cycle
from design_loop_ai.metrics import LayoutSymmetryMetric, ColorHarmonyMetric

# Initial specs for a complex dashboard layout
dashboard_specs = {
    "layout": "grid_3x3",
    "spacing_unit": 10,
    "component_structure": "widget_A_widget_B_widget_C"
}

# Agent targets both symmetry and color harmony
agent = ReasoningAgent(
    initial_specs=dashboard_specs,
    optimization_targets=[LayoutSymmetryMetric(), ColorHarmonyMetric()]
)

print("\n--- Starting Aesthetic Refinement ---")

# Run the cycle, expecting the agent to adjust padding/margins (act())
final_html, history = run_design_cycle(agent, max_iterations=4)

print("\n✅ Aesthetic Refinement Complete.")
print(f"Final Symmetry Score: {history[-1]['metrics']['layout_symmetry']:.2f}")
print(f"Final Harmony Score: {history[-1]['metrics']['color_harmony']:.2f}")
```

### Example 3: Inspecting Agent State During Iteration

This example shows how to manually inspect the agent's reasoning process mid-cycle, which is crucial for debugging or understanding *why* the agent made a specific change.

```python
from design_loop_ai.design_agent import ReasoningAgent
from design_loop_ai.iterative_design import run_design_cycle
from design_loop_ai.metrics import ContrastRatioMetric

# Setup a simple agent
agent = ReasoningAgent(
    initial_specs={"layout": "single_column", "color_palette": ["#333", "#FFF"]},
    optimization_targets=[ContrastRatioMetric()]
)

print("\n--- Tracing Agent Decisions ---")

# We use a custom runner or hook to capture intermediate steps
# (Note: In a production environment, you would hook into the internal loop)
try:
    # Simulate running one step manually to see the thought process
    current_html = "<html><body><p style='color:#333; background-color:#FFF;'>Test</p></body></html>"
    
    # 1. Observe current state
    metrics = agent.observe(current_html)
    print(f"-> OBSERVE: Current Contrast Ratio: {metrics['contrast_ratio']:.2f}")
    
    # 2. Think about the failure
    reasoning = agent.think(metrics)
    print(f"-> THINK: Agent identified issue: {reasoning}")
    
    # 3. Act by modifying specs
    new_specs = agent.act(reasoning)
    print(f"-> ACT: New specs generated: {new_specs}")

except Exception as e:
    print(f"Error during manual trace: {e}")
```