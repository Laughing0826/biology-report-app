import streamlit as st
import pandas as pd
import numpy as np
import io
import pdfminer.high_level
import os
import base64

# ==============================================================================
# 1. HKDSE BIOLOGY CURRICULUM KNOWLEDGE BASE
#    Extracted from the provided bio_supplement_e_2016.pdf document.
# ==============================================================================
HKDSE_BIO_CURRICULUM = {
    "Compulsory Part": {
        "I. Cells and Molecules of Life": {
            "a. Molecules of life": {
                "keywords": ["carbohydrate", "lipid", "protein", "nucleic acid", "monosaccharide", "amino acid", "fatty acid", "enzyme"],
                "objectives": ["State the elemental composition of carbohydrates, lipids and proteins.", "Describe the basic units of carbohydrates, lipids and proteins.", "Describe the occurrence and functions of sugars, lipids, proteins, vitamins and minerals."]
            },
            "b. Cellular organisation": {
                "keywords": ["cell wall", "cell membrane", "cytoplasm", "vacuole", "nucleus", "chloroplast", "mitochondrion", "organelle"],
                "objectives": ["Identify cell structures of typical animal and plant cells.", "State the functions of the organelles.", "Compare the structures of animal and plant cells."]
            },
            "c. Movement of substances across membrane": {
                "keywords": ["diffusion", "osmosis", "active transport", "cell membrane", "water potential", "surface area to volume ratio"],
                "objectives": ["Describe the fluid mosaic model of cell membrane.", "Explain the movement of substances across the cell membrane.", "Describe the effects of osmosis on animal and plant cells."]
            },
            "d. Cell cycle and cell division": {
                "keywords": ["mitosis", "meiosis", "cell cycle", "chromosome", "homologous chromosomes"],
                "objectives": ["Describe the cell cycle.", "Describe the events in different stages of mitosis.", "State the significance of mitosis.", "Describe the events in different stages of meiosis.", "State the significance of meiosis."]
            },
            "e. Cellular energetics": {
                "keywords": ["metabolism", "enzymes", "photosynthesis", "cellular respiration", "ATP"],
                "objectives": ["Explain metabolism in terms of catabolism and anabolism.", "Explain the functions of enzymes.", "State the summary equation of photosynthesis.", "State the summary equation for cellular respiration."]
            }
        },
        "II. Genetics and Evolution": {
            "a. Basic genetics": {
                "keywords": ["gene", "allele", "locus", "genotype", "phenotype", "dominant", "recessive", "homozygous", "heterozygous", "monohybrid", "dihybrid", "codominance", "sex linkage"],
                "objectives": ["Define and use the terms in basic genetics.", "Construct and interpret genetic diagrams.", "Explain codominance and multiple alleles with the ABO blood groups as an example."]
            },
            "b. Molecular genetics": {
                "keywords": ["DNA", "gene", "genetic code", "protein synthesis", "genetically modified (GM)"],
                "objectives": ["Describe the relationship between DNA, genes and chromosomes.", "Describe the basic process of protein synthesis.", "State the applications and implications of genetic engineering."]
            },
            "c. Evolution": {
                "keywords": ["fossil", "natural selection", "Darwin", "Lamarck", "speciation", "evolution"],
                "objectives": ["Interpret the evidence for evolution.", "Describe the theory of natural selection.", "Explain the role of natural selection in evolution."]
            }
        }
        # (Additional major topics like "Organisms and Environment" and "Health and Diseases" would follow this structure)
    },
    "Skills and Processes": {
        "Scientific Inquiry Skills": {
            "keywords": ["hypothesis", "variable", "control", "fair test", "reliability", "validity"],
            "objectives": ["Formulate testable hypotheses.", "Design and carry out experiments to test hypotheses.", "Identify dependent and independent variables.", "Design controlled experiments."]
        },
        "Practical Skills": {
            "keywords": ["microscope", "staining", "food test", "potometer", "quadrat", "transect"],
            "objectives": ["Use a light microscope properly.", "Prepare temporary slides.", "Perform simple food tests.", "Measure the rate of transpiration."]
        },
        "Thinking Skills": {
            "keywords": ["compare", "contrast", "classify", "analyse", "interpret", "draw conclusion"],
            "objectives": ["Compare and contrast biological structures and processes.", "Classify organisms based on observable features.", "Analyse and interpret data from tables and graphs.", "Draw valid conclusions from experimental results."]
        }
    }
}


# ==============================================================================
# 2. HELPER & ANALYSIS FUNCTIONS (Updated)
# ==============================================================================

# (load_file and display_pdf functions are unchanged)
def load_file(uploaded_file, **kwargs):
    if uploaded_file.name.endswith('.csv'): return pd.read_csv(uploaded_file, **kwargs)
    elif uploaded_file.name.endswith('.xlsx'): return pd.read_excel(uploaded_file, engine='openpyxl', **kwargs)
    else: return None

def display_pdf(pdf_file):
    base64_pdf = base64.b64encode(pdf_file.getvalue()).decode('utf-8')
    pdf_display = f'<iframe src="data:application/pdf;base64,{base64_pdf}" width="100%" height="800" type="application/pdf"></iframe>'
    st.markdown(pdf_display, unsafe_allow_html=True)


def analyze_curriculum_coverage(pdf_file, curriculum_db):
    """
    Analyzes the uploaded question paper against the HKDSE curriculum knowledge base.
    """
    if not pdf_file:
        return {}

    try:
        temp_pdf_path = f"temp_{pdf_file.name}"
        with open(temp_pdf_path, "wb") as f:
            f.write(pdf_file.getbuffer())
        text = pdfminer.high_level.extract_text(temp_pdf_path).lower()
        os.remove(temp_pdf_path)

        coverage_report = {}
        for major_area, topics in curriculum_db.items():
            coverage_report[major_area] = {}
            for topic, subtopics in topics.items():
                coverage_report[major_area][topic] = []
                for subtopic_name, details in subtopics.items():
                    for keyword in details['keywords']:
                        if keyword.lower() in text:
                            coverage_report[major_area][topic].append(subtopic_name)
                            break # Move to the next subtopic once one keyword is found
        return coverage_report

    except Exception as e:
        st.error(f"Error processing {pdf_file.name} for curriculum analysis: {e}")
        return {}

# (analyze_mcq_performance and analyze_sq_performance are unchanged)
def analyze_mcq_performance(mc_analysis_file, printable_scores_file):
    # ... (code is identical to previous version)
    return {}
def analyze_sq_performance(sq_marks_file, target_class):
    # ... (code is identical to previous version)
    return {}
def generate_teacher_comment(mcq_results, sq_results, target_class):
    # ... (code is identical to previous version)
    return ""

# ==============================================================================
# 3. STREAMLIT APP UI (Updated)
# ==============================================================================

st.set_page_config(page_title="Biology Report Generator", page_icon="🔬", layout="wide")

# (Custom CSS is unchanged)
st.markdown("""<style>...</style>""", unsafe_allow_html=True)

st.title("🔬 S3-S6 Biology Test Analysis & Report Generator")
st.markdown("An automated tool to transform raw test scores into actionable teaching insights, aligned with the HKDSE curriculum.")
st.markdown("---")

# --- Sidebar ---
with st.sidebar:
    st.header("Upload Files")
    q_pdf_file = st.file_uploader("1. Question Paper (PDF)", type="pdf")
    ms_pdf_file = st.file_uploader("2. Marking Scheme (PDF)", type="pdf")
    mc_analysis_file = st.file_uploader("3. MCQ Analysis Data", type=["csv", "xlsx"])
    printable_scores_file = st.file_uploader("4. MCQ Scores Data", type=["csv", "xlsx"])
    sq_marks_file = st.file_uploader("5. SQ Mark Sheet Data", type=["csv", "xlsx"])
    
    st.header("Settings")
    target_class = st.text_input("Enter Class to Analyze (e.g., 4R)", "4R")

# --- Main App Body ---

if st.sidebar.button("Generate Report", use_container_width=True, type="primary"):
    if not all([q_pdf_file, mc_analysis_file, printable_scores_file, sq_marks_file]):
        st.error("Please upload all required files to generate the report.")
    else:
        # Perform all analyses
        curriculum_coverage = analyze_curriculum_coverage(q_pdf_file, HKDSE_BIO_CURRICULUM)
        mcq_results = analyze_mcq_performance(mc_analysis_file, printable_scores_file)
        sq_results = analyze_sq_performance(sq_marks_file, target_class)

        # <-- CHANGE: New Tab for Curriculum Analysis
        tab1, tab2, tab3, tab4 = st.tabs(["📊 Performance Dashboard", "📜 Curriculum Analysis", "📄 Teacher's Comment", "📚 Source Documents"])

        with tab1:
            # (This tab's content remains the same)
            st.header("📊 Student Performance Dashboard")
            # ...
        
        # <-- NEW TAB: Display the curriculum analysis
        with tab2:
            st.header("📜 HKDSE Curriculum Coverage Analysis")
            st.markdown("This section shows which parts of the HKDSE Biology curriculum were detected in the uploaded question paper.")

            if not curriculum_coverage:
                st.warning("Could not analyze curriculum coverage. Please ensure the question paper PDF is valid.")
            else:
                for major_area, topics in HKDSE_BIO_CURRICULUM.items():
                    st.subheader(major_area)
                    for topic, subtopics in topics.items():
                        with st.expander(f"{topic}", expanded=True):
                            for subtopic_name, details in subtopics.items():
                                # Check if this subtopic was detected in the analysis
                                detected = curriculum_coverage.get(major_area, {}).get(topic, []) and subtopic_name in curriculum_coverage[major_area][topic]
                                
                                # Display with a checkmark if detected
                                if detected:
                                    st.markdown(f"**<font color='green'>✔ {subtopic_name}</font>**", unsafe_allow_html=True)
                                    # Optionally show which objectives were likely covered
                                    with st.container():
                                        for objective in details['objectives']:
                                            st.write(f"<small><em>- {objective}</em></small>", unsafe_allow_html=True)
                                else:
                                    st.markdown(f"*{subtopic_name}*")
        
        with tab3:
            # (This tab's content remains the same)
            st.header("✍️ Generated Teacher's Comment")
            # ...
        
        with tab4:
            # (This tab's content remains the same)
            st.header("📚 View Source Documents")
            # ...

