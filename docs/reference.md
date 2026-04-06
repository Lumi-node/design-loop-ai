# DesignLoop AI API Reference

This document provides a reference for the modules within the DesignLoop AI framework.

---

## 🐍 `agent_designer.py`

This module contains the core logic for defining, configuring, and managing AI agents within the DesignLoop ecosystem.

### Class: `Agent`

Represents a single, configurable AI agent.

**Signature:**
```python
class Agent:
    def __init__(self, name: str, persona: str, capabilities: list[str]): ...
    def configure_prompt(self, system_message: str, user_context: str) -> dict: ...
    def execute_task(self, input_data: dict) -> dict: ...
```

**Description:**
The `Agent` class encapsulates an AI agent's identity (name, persona) and its functional abilities. It provides methods to set up the operational context (prompting) and run tasks.

**Example Usage:**
```python
from agent_designer import Agent

# 1. Initialize the agent
design_agent = Agent(
    name="UI_Designer",
    persona="A senior UX/UI designer specializing in modern web interfaces.",
    capabilities=["generate_mockups", "critique_design", "optimize_layout"]
)

# 2. Configure the agent's operational context
config = design_agent.configure_prompt(
    system_message="You must adhere strictly to Material Design guidelines.",
    user_context="The target audience is small business owners."
)
print(f"Agent Configuration Ready: {config}")

# 3. Execute a task
task_input = {"feature": "User Dashboard", "style": "minimalist"}
result = design_agent.execute_task(task_input)
print(f"Task Result: {result}")
```

### Function: `load_agent_from_config(file_path: str) -> Agent`

**Signature:**
```python
def load_agent_from_config(file_path: str) -> Agent: ...
```

**Description:**
Loads a pre-defined `Agent` instance from a specified configuration file (e.g., JSON or YAML).

**Example Usage:**
```python
from agent_designer import load_agent_from_config

# Assuming 'agent_config.json' exists
try:
    loaded_agent = load_agent_from_config("agent_config.json")
    print(f"Successfully loaded agent: {loaded_agent.name}")
except FileNotFoundError:
    print("Configuration file not found.")
```

---

## 🚀 `main.py`

This module serves as the primary entry point for running the DesignLoop AI workflow, orchestrating agents and managing the overall design process.

### Function: `run_design_pipeline(project_brief: dict, agents: list[Agent]) -> dict`

**Signature:**
```python
def run_design_pipeline(project_brief: dict, agents: list[Agent]) -> dict: ...
```

**Description:**
Executes the complete design workflow. It iterates through the provided list of agents, passing the output of one agent as the input context for the next, based on the `project_brief` sequence.

**Example Usage:**
```python
from main import run_design_pipeline
from agent_designer import Agent

# Setup agents (assuming they are already instantiated)
designer = Agent("Designer", "...", ["generate_mockups"])
reviewer = Agent("Reviewer", "...", ["critique_design"])
agent_list = [designer, reviewer]

# Define the project scope
brief = {
    "title": "E-commerce Checkout Flow",
    "goals": ["Increase conversion rate by 15%"],
    "steps": ["design_initial", "review_and_refine"]
}

# Run the pipeline
final_output = run_design_pipeline(brief, agent_list)
print("\n--- Final Design Output ---")
print(final_output)
```

### Function: `initialize_design_loop(config_path: str) -> dict`

**Signature:**
```python
def initialize_design_loop(config_path: str) -> dict: ...
```

**Description:**
Sets up the entire DesignLoop environment, loading global settings, connecting to necessary services (e.g., LLM providers), and returning the initialized context object.

**Example Usage:**
```python
from main import initialize_design_loop

# Load global settings from a configuration file
context = initialize_design_loop("global_settings.yaml")
print(f"DesignLoop initialized successfully. LLM Provider: {context.get('llm_provider')}")
```

---

## 📊 `metrics.py`

This module provides tools for tracking, calculating, and visualizing the performance and quality of the AI agents during the design process.

### Class: `PerformanceTracker`

Manages the collection and aggregation of metrics across multiple agent runs.

**Signature:**
```python
class PerformanceTracker:
    def __init__(self, project_id: str): ...
    def record_latency(self, agent_name: str, duration_ms: float): ...
    def record_quality_score(self, agent_name: str, score: float, criteria: str): ...
    def get_summary(self) -> dict: ...
```

**Description:**
The `PerformanceTracker` allows developers to log specific events (like time taken or subjective quality scores) associated with each agent execution.

**Example Usage:**
```python
from metrics import PerformanceTracker

tracker = PerformanceTracker(project_id="P-4001")

# Record how long the UI_Designer took
tracker.record_latency("UI_Designer", 1250.5)

# Record the reviewer's assessment of the generated mockup
tracker.record_quality_score("Reviewer", 0.88, "Usability")

# Get the aggregated results
summary = tracker.get_summary()
print("\n--- Performance Summary ---")
print(summary)
```

### Function: `calculate_design_efficiency(metrics_data: list[dict]) -> float`

**Signature:**
```python
def calculate_design_efficiency(metrics_data: list[dict]) -> float: ...
```

**Description:**
Calculates a composite efficiency score based on a list of raw metric data dictionaries. Higher scores indicate faster and higher-quality design iterations.

**Example Usage:**
```python
from metrics import calculate_design_efficiency

# Sample data structure expected by the function
sample_metrics = [
    {"latency": 1000, "quality": 0.9},
    {"latency": 1500, "quality": 0.7}
]

efficiency = calculate_design_efficiency(sample_metrics)
print(f"Overall Design Efficiency Score: {efficiency:.2f}")
```

---

## 🧪 `tests/__init__.py`

This module is reserved for testing utilities and fixtures. It does not expose public API functions but is crucial for running unit and integration tests.

**Note:** This module typically contains setup hooks for `pytest` or similar testing frameworks.

**Example Usage (Internal Testing Only):**
```python
# This file is generally not imported by end-users.
# It might contain fixtures like:
# @pytest.fixture(scope="session")
# def mock_llm_service():
#     # Setup mock responses for LLM calls
#     pass
```