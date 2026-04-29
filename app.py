"""
=============================================================================
Technical Specification & Simulation Boundary Condition Extractor
=============================================================================
Author      : [Your Name]
Description : A Streamlit application that leverages Google Gemini 2.5 Flash
              to parse engineering PDFs and extract structured simulation
              boundary conditions for use in FEA/CFD workflows.
=============================================================================
"""

import streamlit as st
import google.generativeai as genai
import pdfplumber
import json
import io
import re
from datetime import datetime

# =============================================================================
# CONFIGURATION & CONSTANTS
# =============================================================================

# --- Page Configuration (must be first Streamlit call) ---
st.set_page_config(
    page_title="SimSpec Extractor | AI Engineering Tool",
    page_icon="⚙️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# --- Gemini Model Selection ---
GEMINI_MODEL = "gemini-2.5-flash"

# --- The Engineering System Prompt (see Step 2 explanation below) ---
SYSTEM_PROMPT = """
You are a Senior Mechanical Systems Engineer and Simulation Expert with 15+ years
of experience in Finite Element Analysis (FEA), Computational Fluid Dynamics (CFD),
and Fluid-Structure Interaction (FSI) studies. You have deep expertise in interpreting
technical research papers, material datasheets, and engineering standards.

Your task is to act as an intelligent parser. When given a block of text extracted
from a technical PDF, you must identify, extract, and structure ALL engineering
parameters that are relevant to setting up a numerical simulation.

You must extract the following categories if present:
1.  **geometry_parameters**: Dimensions, thicknesses, diameters, clearances, aspect ratios.
2.  **material_properties**: Density, Young's Modulus, Poisson's ratio, thermal conductivity,
    specific heat, yield strength, tensile strength, viscosity, surface roughness.
3.  **boundary_conditions**: Applied loads, pressures, velocities, temperatures, heat fluxes,
    displacement constraints, flow rates, inlet/outlet conditions.
4.  **operating_conditions**: RPM, speed, power, torque, duty cycle, temperature ranges,
    pressure ranges, environmental conditions.
5.  **solver_hints**: Suggested mesh types, element types, time steps, convergence criteria,
    turbulence models, contact formulations — if mentioned.
6.  **key_findings**: Critical quantitative results from the paper (e.g., peak stress, max
    temperature, safety factor) that can be used for validation.
7.  **simulation_type**: The type of analysis best suited (e.g., Transient Thermal, Static
    Structural, Steady-State CFD, Harmonic Response, FSI).

Output Rules (STRICT):
- Respond ONLY with a single, valid JSON object. No markdown. No backticks. No preamble.
- Every parameter must include its "value", "unit", and "source_context" (a short quote
  or phrase from the text that confirms where you found it).
- If a category has no data in the text, include the key with an empty list [].
- For "simulation_type", provide a short string, not a list.
- Flag any values that appear ambiguous or potentially erroneous with a
  "confidence": "low" field; otherwise, omit the confidence field.

Example output format:
{
  "simulation_type": "Transient Thermal Analysis",
  "geometry_parameters": [
    {
      "parameter": "Disc Outer Diameter",
      "value": 320,
      "unit": "mm",
      "source_context": "...a ventilated disc of 320mm outer diameter was modelled..."
    }
  ],
  "material_properties": [...],
  "boundary_conditions": [...],
  "operating_conditions": [...],
  "solver_hints": [...],
  "key_findings": [...]
}
"""

# =============================================================================
# CORE FUNCTIONS
# =============================================================================

def extract_text_from_pdf(uploaded_file: io.BytesIO) -> tuple:
    """
    Extracts all text from an uploaded PDF file using pdfplumber.

    Args:
        uploaded_file: The file object from st.file_uploader.

    Returns:
        A tuple of (extracted_text: str, page_count: int).
    """
    extracted_text = ""
    page_count = 0
    try:
        with pdfplumber.open(uploaded_file) as pdf:
            page_count = len(pdf.pages)
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    extracted_text += page_text + "\n\n"
    except Exception as e:
        st.error(f"❌ PDF Extraction Error: {e}")
        return "", 0
    return extracted_text, page_count


def call_gemini_api(api_key: str, pdf_text: str, user_context: str) -> dict:
    """
    Sends the extracted PDF text to Google Gemini and returns parsed JSON.

    This function constructs the prompt, calls the API, and handles the
    response parsing. It separates the concern of "calling the model" from
    the concern of "displaying results," making it independently testable.

    Args:
        api_key    : The user-provided Google Gemini API key.
        pdf_text   : Raw text extracted from the PDF.
        user_context: Additional context notes from the user.

    Returns:
        A Python dictionary containing the extracted structured data.

    Raises:
        ValueError: If the API response cannot be parsed as JSON.
    """
    # Configure the SDK with the provided key
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel(
        model_name=GEMINI_MODEL,
        system_instruction=SYSTEM_PROMPT,
    )

    # --- Construct the user-facing prompt ---
    # We truncate the PDF text to avoid hitting token limits on very large docs.
    # 50,000 chars is safe for Gemini 2.5 Flash's large context window.
    MAX_CHARS = 50000
    truncated_text = pdf_text[:MAX_CHARS]
    was_truncated = len(pdf_text) > MAX_CHARS

    user_prompt = f"""
Analyze the following text extracted from a technical engineering PDF.
Extract all simulation-relevant parameters and return them as a structured JSON object.

{"⚠️ NOTE: The text was truncated to the first " + str(MAX_CHARS) + " characters due to length." if was_truncated else ""}

--- USER CONTEXT / SIMULATION GOAL ---
{user_context if user_context else "No additional context provided. Extract all relevant parameters."}

--- EXTRACTED PDF TEXT ---
{truncated_text}
"""

    # --- API Call ---
    response = model.generate_content(user_prompt)
    raw_response_text = response.text

    # --- Robust JSON Parsing ---
    # Gemini sometimes wraps output in ```json ... ``` despite instructions.
    # This regex strips those fences defensively.
    json_match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", raw_response_text)
    if json_match:
        json_string = json_match.group(1)
    else:
        json_string = raw_response_text.strip()

    try:
        return json.loads(json_string)
    except json.JSONDecodeError as e:
        raise ValueError(
            f"The model returned non-JSON content. Raw response:\n\n{raw_response_text}"
        ) from e


def render_extracted_data(data: dict):
    """
    Renders the structured JSON output in a clean, readable Streamlit UI.

    Args:
        data: The Python dictionary returned by call_gemini_api().
    """
    # --- Simulation Type Banner ---
    sim_type = data.get("simulation_type", "Unknown")
    st.success(f"🔬 **Recommended Simulation Type:** {sim_type}")

    # --- Define display order and icons ---
    sections = [
        ("geometry_parameters",   "📐 Geometry Parameters"),
        ("material_properties",   "🧱 Material Properties"),
        ("boundary_conditions",   "⛓️ Boundary Conditions"),
        ("operating_conditions",  "⚙️ Operating Conditions"),
        ("solver_hints",          "🖥️ Solver Hints"),
        ("key_findings",          "📊 Key Findings (for Validation)"),
    ]

    for key, label in sections:
        items = data.get(key, [])
        with st.expander(f"{label} — {len(items)} item(s) found", expanded=True):
            if not items:
                st.caption("No data found for this category in the provided document.")
            else:
                # Render each parameter as a clean table row
                for item in items:
                    col1, col2, col3 = st.columns([3, 2, 5])
                    confidence = item.get("confidence", "high")
                    param_label = item.get("parameter", "N/A")
                    if confidence == "low":
                        param_label = f"⚠️ {param_label}"

                    with col1:
                        st.markdown(f"**{param_label}**")
                    with col2:
                        value = item.get("value", "N/A")
                        unit  = item.get("unit", "")
                        st.code(f"{value} {unit}".strip(), language=None)
                    with col3:
                        context = item.get("source_context", "")
                        st.caption(f"*\"{context}\"*")
                    st.divider()


# =============================================================================
# UI LAYOUT
# =============================================================================

def render_sidebar():
    """Renders the sidebar with API key input and app info."""
    with st.sidebar:
        st.title("⚙️ SimSpec Extractor")
        st.caption("AI-powered boundary condition extraction for FEA/CFD workflows.")

        st.divider()

        st.subheader("🔑 API Configuration")
        api_key = st.text_input(
            "Google Gemini API Key",
            type="password",
            placeholder="AIza...",
            help="Get your key from Google AI Studio: https://aistudio.google.com/",
        )

        st.divider()

        st.subheader("ℹ️ About")
        st.markdown(
            """
            This tool automates the extraction of engineering simulation parameters
            from technical PDFs using **Google Gemini 2.5 Flash**.

            **Supported Inputs:**
            - Research papers (FEA, CFD, FSI)
            - Material datasheets
            - Engineering standards excerpts
            - Component test reports

            **Output:** Structured JSON with geometry, material, boundary,
            and operating parameters — ready for ANSYS, Abaqus, or OpenFOAM.
            """
        )

        st.divider()
        st.caption(f"Model: `{GEMINI_MODEL}`")
        st.caption("Built with Streamlit + Gemini API")

    return api_key


def main():
    """Main application entry point."""

    # --- Sidebar ---
    api_key = render_sidebar()

    # --- Header ---
    st.title("⚙️ Technical Specification & Simulation Boundary Condition Extractor")
    st.markdown(
        "Upload an engineering PDF and let Gemini extract every simulation-relevant "
        "parameter — geometry, materials, boundary conditions, and more — into clean, "
        "structured JSON. Designed to reduce manual pre-processing time in FEA/CFD workflows."
    )
    st.divider()

    # --- Main Input Area ---
    col_upload, col_context = st.columns([1, 1], gap="large")

    with col_upload:
        st.subheader("📄 Upload Technical PDF")
        uploaded_file = st.file_uploader(
            "Drag and drop or browse",
            type=["pdf"],
            help="Works best with text-based PDFs. Scanned/image PDFs may yield limited results.",
        )

    with col_context:
        st.subheader("🎯 Simulation Context (Optional)")
        user_context = st.text_area(
            "Describe your simulation goal to guide the extraction",
            placeholder=(
                "e.g., 'I want to run a transient thermal analysis of a disc brake rotor "
                "in ANSYS Mechanical. Focus on heat flux, material thermal properties, and "
                "rotational speed.'"
            ),
            height=133,
        )

    st.divider()

    # --- Extraction Trigger ---
    run_button = st.button(
        "🚀 Extract Parameters",
        type="primary",
        use_container_width=True,
        disabled=(not uploaded_file or not api_key),
    )

    if not api_key:
        st.warning("⚠️ Please enter your Gemini API key in the sidebar to continue.")

    if not uploaded_file and api_key:
        st.info("📂 Please upload a technical PDF to begin extraction.")

    # --- Core Workflow ---
    if run_button and uploaded_file and api_key:

        # Step 1: PDF Extraction
        with st.spinner("📖 Reading PDF..."):
            pdf_text, page_count = extract_text_from_pdf(uploaded_file)

        if not pdf_text:
            st.error("Could not extract text from this PDF. Is it a scanned/image-only document?")
            st.stop()

        st.success(f"✅ PDF parsed successfully — {page_count} pages, {len(pdf_text):,} characters extracted.")

        # Step 2: Gemini API Call
        with st.spinner(f"🧠 Analyzing with {GEMINI_MODEL}... This may take 15–30 seconds."):
            try:
                extracted_data = call_gemini_api(api_key, pdf_text, user_context)
            except ValueError as e:
                st.error(f"**Parsing Error:** {e}")
                st.stop()
            except Exception as e:
                st.error(f"**API Error:** {e}")
                st.stop()

        st.divider()
        st.header("📋 Extracted Simulation Parameters")

        # Step 3: Render structured results
        render_extracted_data(extracted_data)

        # Step 4: Raw JSON Download
        st.divider()
        col_dl1, col_dl2 = st.columns(2)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename  = f"simspec_output_{timestamp}.json"

        with col_dl1:
            st.download_button(
                label="⬇️ Download as JSON",
                data=json.dumps(extracted_data, indent=2),
                file_name=filename,
                mime="application/json",
                use_container_width=True,
            )

        with col_dl2:
            with st.expander("🔍 View Raw JSON"):
                st.json(extracted_data)


# =============================================================================
# ENTRY POINT
# =============================================================================

if __name__ == "__main__":
    main()
