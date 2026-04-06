# DesignLoop AI

<div class="hero">
  <h1 class="display-1">DesignLoop AI</h1>
  <p class="lead">Self-improving agents refining HTML design via visual feedback.</p>
</div>

---

## 🚀 Overview

DesignLoop AI is a novel system that automates the iterative refinement of web designs. Instead of relying on static prompts, our system employs a **Reasoning Agent** loop. This agent takes an initial design mockup, generates HTML, analyzes the output against established design principles (accessibility, symmetry, harmony), and then intelligently modifies the design specifications to generate a better version—all without human intervention.

Our goal is to create a robust `design_agent.py` that drives this continuous improvement cycle.

---

## ✨ Key Capabilities

<div class="row">
  <div class="col-md-4 mb-4">
    <div class="card h-100 shadow-sm">
      <div class="card-body text-center">
        <i class="fas fa-brain fa-3x text-primary mb-3"></i>
        <h5 class="card-title">Reasoning Loop</h5>
        <p class="card-text">The core agent analyzes flaws (e.g., poor contrast, inconsistent spacing) and determines the precise fix needed.</p>
      </div>
    </div>
  </div>
  <div class="col-md-4 mb-4">
    <div class="card h-100 shadow-sm">
      <div class="card-body text-center">
        <i class="fas fa-eye fa-3x text-success mb-3"></i>
        <h5 class="card-title">Visual Observation</h5>
        <p class="card-text">Automatically extracts measurable metrics (Accessibility Score, Symmetry Index) directly from the rendered HTML/CSS.</p>
      </div>
    </div>
  </div>
  <div class="col-md-4 mb-4">
    <div class="card h-100 shadow-sm">
      <div class="card-body text-center">
        <i class="fas fa-palette fa-3x text-warning mb-3"></i>
        <h5 class="card-title">Iterative Refinement</h5>
        <p class="card-text">Systematically improves designs across multiple dimensions until predefined success criteria are met.</p>
      </div>
    </div>
  </div>
</div>

---

## 🎯 Success Criteria

The agent is considered successful when it improves a baseline design mockup across **3+ measurable dimensions** (e.g., accessibility score, layout symmetry, color harmony) within **5 iterations**.

---

## 🛠️ Getting Started

Ready to see the agent in action?

<div class="d-flex justify-content-center my-4">
  <a href="getting_started.md" class="btn btn-primary btn-lg px-5">
    <i class="fas fa-arrow-right me-2"></i> Get Started Guide
  </a>
</div>

### Quick Installation

To run the core agent framework, clone the repository and install dependencies:

<div class="alert alert-info">
  <p class="mb-0">
    <code>git clone https://github.com/DesignLoopAI/designloop.git</code><br>
    <code>pip install -r requirements.txt</code>
  </p>
</div>

---

<div class="text-center mt-5 pt-4 border-top">
  <p class="text-muted">&copy; 2024 DesignLoop AI. Automating the path to perfect design.</p>
</div>