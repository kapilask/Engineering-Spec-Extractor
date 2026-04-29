# ⚙️ SimSpec Extractor — AI-Powered Engineering Workflow Automation

> Automating the extraction of simulation boundary conditions from technical PDFs using Large Language Models.

[![Python](https://img.shields.io/badge/Python-3.10+-blue?style=flat-square&logo=python)](https://python.org)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.x-red?style=flat-square&logo=streamlit)](https://streamlit.io)
[![Gemini](https://img.shields.io/badge/Gemini-2.5%20Flash-orange?style=flat-square&logo=google)](https://ai.google.dev)
[![License](https://img.shields.io/badge/License-MIT-green?style=flat-square)](LICENSE)

---

## 🧩 The Problem

Every FEA or CFD simulation begins the same way: an engineer manually reads through
research papers, material datasheets, or test reports — sometimes 30–80 pages long —
hunting for numbers. Disc outer diameter. Thermal conductivity. Applied heat flux. Inlet
velocity. This process is slow, error-prone, and entirely unscalable.

A junior engineer can spend **2–4 hours per paper** just extracting parameters before
a single simulation is set up.

---

## 💡 The Solution

**SimSpec Extractor** uses Google Gemini 2.5 Flash as an intelligent mechanical systems
expert. You upload a PDF. It returns a fully structured JSON object containing every
simulation-relevant parameter — geometry, materials, boundary conditions, operating
conditions, solver hints, and key validation targets — with source citations for every value.

What took hours now takes **under 30 seconds**.

---

## 🏗️ Architecture

```
┌─────────────────────┐
│   User (Browser)    │
│   Streamlit UI      │
└────────┬────────────┘
         │ Upload PDF + Simulation Context
         ▼
┌─────────────────────┐
│   pdfplumber        │  ← Extracts raw text from PDF pages
│   PDF Parser        │
└────────┬────────────┘
         │ Raw text string
         ▼
┌─────────────────────────────────────────────┐
│   Google Gemini 2.5 Flash                   │
│                                             │
│   System Prompt: Senior ME / Sim Expert     │  ← Domain-specialized LLM
│   User Prompt:   PDF text + goal context    │
│                                             │
│   Output: Strict JSON schema                │
└────────┬────────────────────────────────────┘
         │ Structured JSON
         ▼
┌─────────────────────┐
│   Streamlit UI      │  ← Renders results by category
│   + JSON Download   │     with source citations
└─────────────────────┘
```

---

## 📦 Output Schema

Every extraction returns a consistent, machine-readable JSON object:

```json
{
  "simulation_type": "Transient Thermal Analysis",
  "geometry_parameters": [
    {
      "parameter": "Disc Outer Diameter",
      "value": 320,
      "unit": "mm",
      "source_context": "...a ventilated disc of 320mm outer diameter..."
    }
  ],
  "material_properties":  [...],
  "boundary_conditions":  [...],
  "operating_conditions": [...],
  "solver_hints":         [...],
  "key_findings":         [...]
}
```

This JSON can be directly consumed by downstream scripts that auto-populate
ANSYS APDL, Abaqus input decks, or OpenFOAM `0/` boundary files.

---

## 🚀 Getting Started

### 1. Clone the repository

```bash
git clone https://github.com/YOUR_USERNAME/simspec-extractor.git
cd simspec-extractor
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Get a Gemini API key

Visit [Google AI Studio](https://aistudio.google.com/) → Create API Key (free tier available).

### 4. Run the app

```bash
streamlit run app.py
```

Enter your API key in the sidebar, upload a PDF, and hit **Extract Parameters**.

---

## 📋 Requirements

```
streamlit>=1.32.0
google-generativeai>=0.5.0
pdfplumber>=0.10.0
```

> Save this as `requirements.txt` in your project root.

---

## 🔬 Use Cases & Example Inputs

| Document Type | Example | Extracted Parameters |
|---|---|---|
| Research Paper | Thermal analysis of disc brakes | Heat flux, RPM, material k & Cp, disc geometry |
| Material Datasheet | Grey Cast Iron EN-GJL-250 | E, ν, ρ, σ_y, thermal conductivity |
| CFD Study | Journal bearing water lubrication | Viscosity, clearance, eccentricity, Re number |
| Test Report | Fatigue life of notched specimens | Load amplitude, R-ratio, Kt, Nf |

---

## 🧠 Engineering Design Decisions

### Why a specialized System Prompt?
LLMs are generalists. An unguided model extracts text; a domain-prompted model
understands that "320 mm" next to "outer diameter" is a geometry parameter and
"7200 kg/m³" is a material density. The system prompt defines a 7-category schema
that mirrors the actual input panels of commercial FEA/CFD solvers.

### Why `source_context` for every value?
Auditability is non-negotiable in engineering. Every extracted number cites the
exact phrase from the source document, so an engineer can verify the extraction
before it enters a simulation. This prevents silent hallucination errors.

### Why Gemini 2.5 Flash?
Its large context window handles full research papers in a single pass without
chunking. Flash's speed-to-cost ratio is optimal for a tool used iteratively
during simulation setup.

### Why Streamlit?
Maximum development velocity. The goal is to put a functional tool in front of
engineers — not to build a perfect frontend. Streamlit allows the focus to stay
on the AI pipeline and extraction logic.

---

## 🗺️ Roadmap

- [ ] **Batch processing** — Upload multiple PDFs, get a merged parameter table
- [ ] **ANSYS script export** — Auto-generate APDL commands from extracted BCs
- [ ] **Comparison mode** — Diff two papers' parameters side-by-side
- [ ] **Vector DB integration** — Build a searchable library of past extractions
- [ ] **Confidence scoring** — Use Gemini's logprobs to quantify extraction certainty

---

## 👨‍💻 Author

**[Your Name]**
B.Tech Mechanical Engineering — MIT Manipal (6th Semester)
Minor: Machine Design | Skills: SolidWorks, CATIA, ANSYS, Python, Arduino

*Built as a demonstration of applied LLM engineering for automating
mechanical simulation workflows.*

---

## 📄 License

MIT License — see [LICENSE](LICENSE) for details.
