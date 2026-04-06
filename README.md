<p align="center">
  <img src="assets/hero.png" alt="DesignLoop AI" width="900">
</p>

<h1 align="center">DesignLoop AI</h1>

<p align="center">
  <strong>Self-improving agent refining HTML design via visual feedback.</strong>
</p>

<p align="center">
  <a href="https://github.com/Lumi-node/design-loop-ai"><img src="https://img.shields.io/badge/License-MIT-blue.svg" alt="License Badge"></a>
  <a href="https://github.com/Lumi-node/design-loop-ai"><img src="https://img.shields.io/badge/Python-3.10%2B-blue.svg" alt="Python Badge"></a>
  <a href="https://github.com/Lumi-node/design-loop-ai"><img src="https://img.shields.io/badge/Tests-9%20Tests-green.svg" alt="Tests Badge"></a>
</p>

---

DesignLoop AI is a sophisticated proof-of-concept demonstrating an autonomous agent capable of iteratively refining raw HTML designs. It operates by taking an initial visual mockup, converting it to HTML, and then employing a reasoning agent to analyze the output against predefined design principles (e.g., contrast, symmetry).

This system closes the loop between visual intent and code quality. The agent uses extracted metrics to guide its actions, regenerating specific components in subsequent cycles until target quality thresholds are met, showcasing a path toward truly autonomous UI development.

---

## Quick Start

```bash
pip install design_loop_ai
```

```python
from iterative_design import run_design_loop
from PIL import Image

# Load the initial design mockup image
image_path = "path/to/initial_mockup.png"
target_thresholds = {"accessibility_score": 0.9, "layout_symmetry": 0.85}

# Run the iterative refinement process
final_html = run_design_loop(image_path, target_thresholds)

print("Design refinement complete. Final HTML generated.")
# Save or serve final_html
```

## What Can You Do?

### Iterative Refinement
The core functionality is the automated improvement of a design. The `iterative_design.py` entry point manages the entire process: image ingestion $\rightarrow$ HTML generation $\rightarrow$ Agent loop $\rightarrow$ Metric evaluation $\rightarrow$ Component regeneration.

### Design Analysis and Metrics
The `metrics.py` module provides quantitative feedback. The agent uses these metrics to judge the quality of the current HTML output against established design standards.

```python
from metrics import calculate_contrast_ratio

# Example usage within the agent's observation phase
ratio = calculate_contrast_ratio("#FFFFFF", "#000000")
print(f"Contrast Ratio: {ratio}")
```

### Agent Reasoning and Action
The `design_agent.py` encapsulates the decision-making logic. Its `think()` method analyzes the current state, and its `act()` method generates targeted modifications to the design specifications for the next iteration.

```python
from design_agent import ReasoningAgent

agent = ReasoningAgent()
# Agent analyzes the current HTML structure and suggests a change
suggested_change = agent.think(current_html_state)
print(f"Agent suggests: {suggested_change}")
```

## Architecture

DesignLoop AI follows a closed-loop feedback architecture. The process begins with an image input, which is converted into an initial HTML structure. This structure is fed into the `ReasoningAgent`.

1.  **Observation:** The agent calls functions in `metrics.py` to score the current HTML against quality targets.
2.  **Thinking:** The agent uses these scores to determine *why* the design failed (e.g., "low contrast in header").
3.  **Action:** The agent modifies the design specifications and instructs the HTML generator to regenerate the affected components.
4.  **Iteration:** The new HTML is observed again, and the cycle repeats until convergence or iteration limit is reached.

```mermaid
graph TD
    A[Input Image] --> B(HTML Generator);
    B --> C{Current HTML Output};
    C --> D[Metrics.py: Observation];
    D --> E[DesignAgent.py: Think()];
    E -- Decision --> F[DesignAgent.py: Act()];
    F -- New Specs --> B;
    D -- Scores --> E;
    E -- Convergence? --> G{Stop/Continue};
    G -- Continue --> C;
    G -- Stop --> H[Final HTML];
```

## API Reference

### `iterative_design.py`
*   `run_design_loop(image_path: str, thresholds: dict) -> str`: Executes the full design refinement pipeline. Returns the final, optimized HTML string.

### `design_agent.py`
*   `ReasoningAgent()`: Initializes the agent.
*   `agent.think(state: str) -> str`: Analyzes the current design state and returns a high-level reasoning or modification instruction.
*   `agent.act(instruction: str) -> dict`: Translates the reasoning into concrete, actionable design parameter changes.

### `metrics.py`
*   `calculate_contrast_ratio(color1: str, color2: str) -> float`: Computes the WCAG contrast ratio between two hex/RGB colors.
*   `calculate_layout_symmetry(html_content: str) -> float`: Assesses the visual balance and symmetry of the rendered layout.

## Research Background

This project is inspired by advancements in Reinforcement Learning applied to generative design tasks, specifically the concept of "Self-Correction" in AI agents. It builds upon principles found in visual programming and automated UI testing, aiming to bridge the gap between abstract design goals and concrete code implementation.

## Testing

The project includes 9 unit and integration tests located in the `tests/` directory, ensuring the core logic within `design_agent.py` and `metrics.py` behaves as expected across various inputs.

## Contributing

We welcome contributions! Please read our contribution guidelines (if available) or feel free to open an issue or submit a pull request with improvements, bug fixes, or new features.

## Citation

This work is an independent proof-of-concept. For inspiration on iterative refinement loops, see related literature in Active Learning and AI-driven design systems.

## License
The project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.