# DesignLoop AI API Reference

DesignLoop AI provides a suite of modules for automating and optimizing the design-to-code generation process using AI-driven iterative refinement.

---

## 🧠 `design_agent.py`

This module contains the core `ReasoningAgent`, which orchestrates the design loop. It takes an initial design specification, generates HTML, analyzes the output against predefined design principles, and iteratively refines the specifications until performance metrics meet target thresholds.

### `ReasoningAgent` Class

The central class responsible for the entire iterative design process.

**Signature:**
```python
class ReasoningAgent:
    __init__(self, initial_spec: Dict, design_principles: List[str], max_iterations: int = 5)
    def run_design_loop(self) -> Dict:
    def think(self, current_html: str, current_metrics: Dict) -> Dict:
    def act(self, component_name: str, refinement_instructions: str) -> Dict:
    def observe(self, html_output: str) -> Dict:
```

**Description:**
*   **`__init__`**: Initializes the agent with the starting design parameters, the rules it must follow (e.g., "WCAG AA contrast"), and the maximum number of refinement steps.
*   **`run_design_loop`**: Executes the main loop: `Think` $\rightarrow$ `Act` $\rightarrow$ `Observe`. It returns the final, optimized design specification and the achieved metrics.
*   **`think`**: Analyzes the current HTML structure and metrics. It determines *what* needs improvement (e.g., "The primary CTA contrast is too low," or "Spacing around the header is inconsistent"). It outputs a set of actionable instructions.
*   **`act`**: Takes the instructions from `think()` and modifies the underlying design specification (e.g., changing a color hex code, adjusting padding values) for a specific component.
*   **`observe`**: Parses the generated HTML/CSS to extract quantifiable metrics (e.g., calculating actual contrast ratios, measuring element distances).

**Example Usage:**
```python
from design_loop.design_agent import ReasoningAgent

# 1. Define the starting point
initial_spec = {"layout": "grid", "colors": {"primary": "#007bff"}, "components": ["header", "card"]}
principles = ["contrast_ratio_min_4_5", "layout_symmetry_high", "semantic_structure_valid"]

# 2. Initialize and run the agent
agent = ReasoningAgent(initial_spec, principles, max_iterations=5)
final_result = agent.run_design_loop()

print("Design Optimization Complete.")
print(f"Final Metrics: {final_result['metrics']}")
# Expected Success: Metrics show improvement across 3+ dimensions within 5 iterations.
```

---

## 🔄 `iterative_design.py`

This module handles the state management and the actual generation/regeneration of code based on the agent's decisions. It acts as the interface between the abstract design instructions and the concrete HTML output.

### `DesignGenerator` Class

Manages the conversion pipeline from design specs to rendered code.

**Signature:**
```python
class DesignGenerator:
    __init__(self, base_template_path: str):
    def generate_html(self, design_spec: Dict) -> str:
    def regenerate_component(self, current_html: str, component_name: str, new_spec: Dict) -> str:
```

**Description:**
*   **`__init__`**: Loads the foundational HTML/CSS templates used for rendering.
*   **`generate_html`**: Takes a complete design specification dictionary and renders the full, initial HTML document.
*   **`regenerate_component`**: Performs targeted DOM/CSS manipulation on an existing HTML string. Instead of regenerating everything, it replaces or updates only the specified component based on the new, refined specification, ensuring continuity in the design loop.

**Example Usage:**
```python
from design_loop.iterative_design import DesignGenerator

generator = DesignGenerator(base_template_path="./templates/base.html")

# Initial generation
initial_spec = {"color_scheme": "light", "padding": 16}
html_output = generator.generate_html(initial_spec)

# Refinement step: Change padding on the 'card' component
refined_spec = {"padding": 24}
new_html = generator.regenerate_component(html_output, "card", refined_spec)
```

---

## 📊 `metrics.py`

This module provides the analytical tools necessary for the `ReasoningAgent` to quantify the quality of the generated design. It parses HTML/CSS and calculates objective scores.

### `DesignEvaluator` Class

A utility class for calculating various design quality scores.

**Signature:**
```python
class DesignEvaluator:
    def calculate_accessibility_score(self, html_content: str) -> float:
    def measure_layout_symmetry(self, html_content: str) -> float:
    def analyze_color_harmony(self, css_content: str) -> float:
    def extract_component_metrics(self, html_content: str, component_name: str) -> Dict:
```

**Description:**
*   **`calculate_accessibility_score`**: Scans the HTML/CSS to check for WCAG compliance (e.g., contrast ratios, alt-text presence) and returns a normalized score (0.0 to 1.0).
*   **`measure_layout_symmetry`**: Analyzes the CSS layout properties (margins, padding, grid alignment) to quantify how balanced the visual structure is.
*   **`analyze_color_harmony`**: Uses color theory algorithms to assess the relationship between colors used in the design (e.g., complementary, analogous).
*   **`extract_component_metrics`**: Provides granular data on a specific element, useful for targeted refinement in the `act()` phase.

**Example Usage:**
```python
from design_loop.metrics import DesignEvaluator

evaluator = DesignEvaluator()
html = "<div style='color: red; background-color: white;'>...</div>"

# Check accessibility
acc_score = evaluator.calculate_accessibility_score(html)
print(f"Accessibility Score: {acc_score:.2f}")

# Check color harmony (assuming CSS content is available)
css = "body { background-color: #1e3c72; }"
harmony_score = evaluator.analyze_color_harmony(css)
print(f"Color Harmony Score: {harmony_score:.2f}")
```

---

## 🧪 `tests/__init__.py`

This module serves as the entry point for unit and integration testing of the DesignLoop AI components.

### Testing Utilities

**Signature:**
```python
# No public classes, primarily imports for test runners
from .test_agent import test_reasoning_agent
from .test_generator import test_design_generator
from .test_metrics import test_design_evaluator
```

**Description:**
Contains fixtures and test cases to verify that the `ReasoningAgent` correctly drives the loop, that the `DesignGenerator` accurately transforms specs to HTML, and that the `DesignEvaluator` produces mathematically correct metrics.

**Example Usage:**
```python
# Typically run via pytest, but this shows the structure
from design_loop.tests import test_reasoning_agent

# Example test execution (conceptual)
# assert test_reasoning_agent.test_success_criteria() == True
```