# 🚀 DesignLoop AI Quick Start Guide

Welcome to DesignLoop AI! This guide will get you up and running with our core design automation framework, focusing on the `design_agent.py` module.

DesignLoop AI enables AI agents to iteratively refine visual designs by analyzing generated code against established design principles.

## 📦 Package Structure

The core functionality resides within the `design_loop_ai` package:

*   `design_agent.py`: The central `ReasoningAgent` that orchestrates the design loop (Think $\rightarrow$ Act $\rightarrow$ Observe).
*   `iterative_design.py`: Contains the logic for managing the overall design iteration process.
*   `metrics.py`: Provides functions to analyze generated HTML/CSS against quantitative design standards.
*   `tests/__init__.py`: Unit and integration tests.

## 🧠 Core Concept: The Reasoning Agent

The `design_agent.py` module implements a `ReasoningAgent`. This agent operates in a continuous loop:

1.  **`think()`**: Analyzes the current design output (HTML/CSS) using rules defined in `metrics.py`. It identifies weaknesses (e.g., low contrast, inconsistent padding).
2.  **`act()`**: Based on the analysis, it generates *modified design specifications* (e.g., "Increase primary button padding by 10px," "Change header background to `#1a2b3c`"). These specs are fed back into the design-to-HTML converter.
3.  **`observe()`**: Executes the design-to-HTML conversion with the new specs and extracts quantifiable metrics (Accessibility Score, Symmetry Score, etc.) from the resulting code.

**Success Criteria:** The agent must improve a baseline design mockup across 3+ measurable dimensions within 5 iterations.

---

## 🛠️ Installation & Setup (Conceptual)

Assuming you have the package installed:

```bash
pip install design_loop_ai
```

## 💡 Usage Examples

Here are three practical examples demonstrating how to initialize and run the DesignLoop Agent.

### Example 1: Basic Accessibility Improvement Loop

This example focuses solely on improving the accessibility score of a simple component.

```python
from design_loop_ai.design_agent import ReasoningAgent
from design_loop_ai.iterative_design import DesignLoopRunner
from design_loop_ai.metrics import AccessibilityChecker

# 1. Define the initial state (e.g., a baseline mockup spec)
initial_spec = {"component": "button", "color_scheme": "default", "text_size": "16px"}

# 2. Initialize the agent, providing the specific metric checker
accessibility_agent = ReasoningAgent(
    metric_analyzer=AccessibilityChecker()
)

# 3. Set up the runner to manage the iteration process
runner = DesignLoopRunner(
    agent=accessibility_agent,
    initial_design_spec=initial_spec,
    max_iterations=5
)

print("--- Starting Accessibility Refinement ---")
final_design = runner.run()

print("\n✅ Design Loop Complete.")
print(f"Final Accessibility Score: {final_design.metrics['accessibility_score']}")
```

### Example 2: Multi-Dimensional Refinement (Symmetry & Harmony)

This example demonstrates the agent tackling multiple design principles simultaneously by integrating different metric checkers.

```python
from design_loop_ai.design_agent import ReasoningAgent
from design_loop_ai.iterative_design import DesignLoopRunner
from design_loop_ai.metrics import SymmetryChecker, ColorHarmonyChecker

# 1. Combine multiple metric analyzers into a composite checker
composite_checker = type('CompositeChecker', (object,), {
    'analyze': lambda html: {
        'symmetry_score': SymmetryChecker().analyze(html),
        'color_harmony_score': ColorHarmonyChecker().analyze(html)
    }
})()

# 2. Initialize the agent with the composite analyzer
multi_dim_agent = ReasoningAgent(
    metric_analyzer=composite_checker
)

# 3. Run the loop
runner = DesignLoopRunner(
    agent=multi_dim_agent,
    initial_design_spec={"layout": "grid", "palette": "vibrant"},
    max_iterations=5
)

print("\n--- Starting Multi-Dimensional Refinement ---")
final_result = runner.run()

print("\n✨ Final Design Metrics:")
print(f"  Symmetry Score: {final_result.metrics['symmetry_score']:.2f}")
print(f"  Color Harmony Score: {final_result.metrics['color_harmony_score']:.2f}")
```

### Example 3: Inspecting Agent Logic (Debugging/Testing)

If you want to see *why* the agent decided to change something, you can manually step through the `think()` and `act()` methods using the agent instance directly.

```python
from design_loop_ai.design_agent import ReasoningAgent
from design_loop_ai.metrics import ContrastRatioChecker

# Setup a minimal agent instance
contrast_agent = ReasoningAgent(
    metric_analyzer=ContrastRatioChecker()
)

# Assume 'current_html' is the output from the previous iteration
current_html = "<div style='background-color: #ccc; color: #333;'>Text</div>"

print("--- Agent Thinking Phase ---")
# The agent analyzes the current state
analysis = contrast_agent.think(current_html)
print(f"Agent Analysis: {analysis}")

# The agent decides on a change based on the analysis
new_spec = contrast_agent.act(analysis)
print(f"Agent Action (New Spec): {new_spec}")

# Simulate observation (running the design-to-HTML converter with the new spec)
# In a real scenario, this would call the converter function.
observed_metrics = contrast_agent.observe(new_spec)
print(f"Observed Metrics After Action: {observed_metrics}")
```