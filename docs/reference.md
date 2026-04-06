# DesignLoop AI API Reference

DesignLoop AI provides a suite of modules for automating and optimizing the design-to-code generation process using AI-driven iterative refinement.

---

## 🚀 `design_agent.py`

This module contains the core `ReasoningAgent`, which orchestrates the design loop. It takes an initial design specification, generates HTML, evaluates it against defined design principles, and iteratively refines the specifications until performance targets are met.

### `ReasoningAgent` Class

The central class responsible for the entire design iteration process.

**Signature:**
```python
class ReasoningAgent:
    __init__(self, initial_spec: dict, design_principles: list[str], max_iterations: int = 5):
    ...
    think(self, current_html: str, metrics: dict) -> dict:
    ...
    act(self, current_spec: dict, feedback: dict) -> dict:
    ...
    observe(self, html_output: str) -> dict:
    ...
    run_loop(self) -> dict:
    ...
```

**Description:**
*   **`__init__`**: Initializes the agent with the starting design parameters, the rules it must follow (e.g., "WCAG AA contrast"), and the maximum number of refinement steps.
*   **`think(current_html, metrics)`**: The reasoning step. Analyzes the provided HTML and current metrics. It determines *what* needs to be changed (e.g., "The primary CTA contrast is too low," or "The header spacing is inconsistent"). Returns a structured feedback dictionary.
*   **`act(current_spec, feedback)`**: The action step. Uses the feedback from `think()` to modify the design specification (e.g., adjusting color hex codes, changing padding values, altering semantic tags). Returns the updated design specification.
*   **`observe(html_output)`**: The observation step. Passes the newly generated HTML/CSS to the metric engine to extract quantifiable data (e.g., calculated contrast ratios, layout deviations). Returns a dictionary of metrics.
*   **`run_loop()`**: Executes the full cycle: `observe` $\rightarrow$ `think` $\rightarrow$ `act` $\rightarrow$ `observe`... until convergence or `max_iterations` is reached.

**Example Usage:**
```python
from design_agent import ReasoningAgent

# 1. Define initial state and goals
initial_design = {"layout": "grid", "palette": ["#000000", "#FFFFFF"], "components": {"button": {"padding": "10px"}}}
principles = ["WCAG_AA_Contrast", "Symmetry_Ratio_0.9", "Color_Harmony_Score"]

# 2. Initialize and run the agent
agent = ReasoningAgent(initial_design, principles, max_iterations=5)
final_results = agent.run_loop()

print(f"Final Design Score: {final_results['final_metrics']}")
```

---

## 🔄 `iterative_design.py`

This module handles the mechanics of the design-to-code conversion and the state management across iterations. It acts as the bridge between the abstract design specification and the concrete HTML output.

### `DesignConverter` Class

Handles the transformation from a structured design dictionary to rendered HTML/CSS.

**Signature:**
```python
class DesignConverter:
    __init__(self, template_engine: str = "Jinja2"):
    ...
    convert(self, design_spec: dict) -> tuple[str, str]:
    ...
    apply_patch(self, base_html: str, patch_spec: dict) -> str:
    ...
```

**Description:**
*   **`__init__`**: Sets up the underlying rendering engine (e.g., Jinja2, custom parser).
*   **`convert(design_spec)`**: Takes a complete design specification dictionary and renders it into a complete HTML string, including embedded CSS. Returns `(html_string, css_string)`.
*   **`apply_patch(base_html, patch_spec)`**: Efficiently updates an existing HTML structure based on a small change in the specification (e.g., changing a single `style` attribute or replacing a component's class). This avoids full re-rendering when only minor tweaks are needed.

**Example Usage:**
```python
from iterative_design import DesignConverter

converter = DesignConverter()

# Initial conversion
spec_v1 = {"layout": "flex", "color": "#FF0000"}
html_v1, _ = converter.convert(spec_v1)

# Applying a refinement (e.g., changing padding)
patch = {"component_id": "header", "style_update": "padding: 20px;"}
html_v2 = converter.apply_patch(html_v1, patch)
```

---

## 📊 `metrics.py`

This module contains the quantitative analysis tools. It parses the generated HTML/CSS and calculates objective scores against established design heuristics.

### `DesignEvaluator` Class

Responsible for running specific design checks on the rendered output.

**Signature:**
```python
class DesignEvaluator:
    __init__(self, accessibility_standards: str = "WCAG21"):
    ...
    calculate_contrast_ratio(self, color1: str, color2: str) -> float:
    ...
    analyze_layout_symmetry(self, html_content: str) -> float:
    ...
    calculate_color_harmony(self, palette: list[str]) -> float:
    ...
    evaluate_full_design(self, html_content: str, spec: dict) -> dict:
    ...
```

**Description:**
*   **`__init__`**: Configures the evaluator based on required standards (e.g., WCAG 2.1 AA).
*   **`calculate_contrast_ratio`**: Computes the luminance contrast between two provided color codes.
*   **`analyze_layout_symmetry`**: Parses the DOM structure to measure the deviation from expected symmetrical layouts (e.g., comparing left/right element widths).
*   **`calculate_color_harmony`**: Uses color theory algorithms to score how well the colors in the provided palette relate to each other.
*   **`evaluate_full_design`**: Orchestrates the other functions, running all relevant checks and aggregating them into a single, comprehensive metrics dictionary.

**Example Usage:**
```python
from metrics import DesignEvaluator

evaluator = DesignEvaluator()

# Check a specific element's contrast
contrast = evaluator.calculate_contrast_ratio("#000000", "#FFFFFF")
print(f"Contrast Ratio: {contrast:.2f}")

# Evaluate the entire output
metrics = evaluator.evaluate_full_design(html_output, current_spec)
print(f"Overall Metrics: {metrics}")
```

---

## 🧪 `tests/__init__.py`

This module serves as the entry point for unit and integration testing of the DesignLoop AI components.

### `TestRunner` Class

Provides utilities for running structured tests against the agent's behavior.

**Signature:**
```python
class TestRunner:
    __init__(self, test_suite_path: str):
    ...
    run_integration_test(self, scenario: dict) -> bool:
    ...
    assert_convergence(self, agent_output: dict, target_metrics: dict) -> bool:
    ...
```

**Description:**
*   **`__init__`**: Loads the defined test scenarios from the specified path.
*   **`run_integration_test`**: Executes a full end-to-end test scenario (e.g., "Can the agent improve a low-contrast mockup to pass WCAG AA in 5 steps?").
*   **`assert_convergence`**: Verifies that the final state of the agent meets the predefined success criteria (e.g., "Accessibility Score $\ge 0.95$").

**Example Usage:**
```python
from tests import TestRunner

runner = TestRunner("./scenarios/")

# Run a test case defined in the scenarios directory
success = runner.run_integration_test({"scenario_name": "Contrast_Improvement"})

if success:
    print("Integration Test Passed: Agent successfully optimized the design.")
```