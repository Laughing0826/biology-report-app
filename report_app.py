import streamlit as st
import pandas as pd
import numpy as np
import os
import base64
import google.generativeai as genai
from pdfminer.high_level import extract_text

# ==========================================
# I. Curriculum Knowledge Base
# ==========================================
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

# ==========================================
# II. Helper & Core Analysis Functions
# ==========================================
def load_file(uploaded_file, **kwargs):
    """Loads CSV or XLSX files into a Pandas DataFrame."""
    if uploaded_file is None:
        return None
    ext = os.path.splitext(uploaded_file.name)[1].lower()
    try:
        if ext == '.csv':
            return pd.read_csv(uploaded_file, **kwargs)
        elif ext in ['.xls', '.xlsx']:
            return pd.read_excel(uploaded_file, engine='openpyxl', **kwargs)
    except Exception as e:
        st.error(f"Error loading {uploaded_file.name}: {e}")
    return None

def analyze_curriculum_coverage(pdf_file, curriculum_db):
    """Extracts text from PDF and maps it to curriculum sub-topics."""
    if pdf_file is None:
        return {}
    
    try:
        extracted_text = extract_text(pdf_file).lower()
    except Exception as e:
        st.error(f"Error extracting text from PDF: {e}")
        return {}

    detected_subtopics = {}
    for major_area, topics in curriculum_db.items():
        if isinstance(topics, dict):
            for topic, subtopics in topics.items():
                if isinstance(subtopics, dict) and 'keywords' not in subtopics:
                    for subtopic, data in subtopics.items():
                        keywords = data.get('keywords', [])
                        if any(kw.lower() in extracted_text for kw in keywords):
                            detected_subtopics[subtopic] = data.get('objectives', [])
                elif 'keywords' in subtopics:
                    keywords = subtopics.get('keywords', [])
                    if any(kw.lower() in extracted_text for kw in keywords):
                        detected_subtopics[topic] = subtopics.get('objectives', [])
    
    return detected_subtopics

def analyze_mcq_performance(mc_analysis_file, printable_scores_file):
    """Analyzes MCQ average and identifies the 3 most difficult questions."""
    avg_score = 0.0
    difficult_qs = pd.DataFrame()
    
    df_scores = load_file(printable_scores_file)
    if df_scores is not None and not df_scores.empty:
        score_cols = [c for c in df_scores.columns if 'score' in str(c).lower() or 'total' in str(c).lower() or 'mark' in str(c).lower()]
        if score_cols:
            avg_score = pd.to_numeric(df_scores[score_cols[0]], errors='coerce').mean()
        else:
            numeric_cols = df_scores.select_dtypes(include=[np.number]).columns
            if len(numeric_cols) > 0:
                avg_score = df_scores[numeric_cols[-1]].mean()

    df_mc = load_file(mc_analysis_file)
    if df_mc is not None and not df_mc.empty:
        pct_col = next((c for c in df_mc.columns if '%' in str(c) or 'correct' in str(c).lower()), None)
        q_col = next((c for c in df_mc.columns if 'question' in str(c).lower() or 'item' in str(c).lower()), None)
        
        if pct_col is None and len(df_mc.columns) >= 2: pct_col = df_mc.columns[1]
        if q_col is None and len(df_mc.columns) >= 1: q_col = df_mc.columns[0]
        
        if pct_col and q_col:
            df_mc[pct_col] = pd.to_numeric(df_mc[pct_col].astype(str).str.replace('%', ''), errors='coerce')
            difficult_qs = df_mc.sort_values(by=pct_col, ascending=True).head(3)[[q_col, pct_col]]
            
    return avg_score, difficult_qs

def analyze_sq_performance(sq_marks_file, target_class):
    """Filters SQ marks by target class and calculates averages."""
    overall_avg = 0.0
    sq_averages = pd.Series(dtype=float)
    
    df_sq = load_file(sq_marks_file)
    if df_sq is not None and not df_sq.empty:
        class_col = next((c for c in df_sq.columns if 'class' in str(c).lower()), None)
        if class_col:
            df_sq = df_sq[df_sq[class_col].astype(str).str.strip().str.upper() == target_class.strip().upper()]
        
        sq_cols = [c for c in df_sq.columns if str(c).strip().upper().startswith('SQ')]
        if not sq_cols:
             numeric_cols = df_sq.select_dtypes(include=[np.number]).columns
             sq_cols = [c for c in numeric_cols if class_col and c != class_col]
             
        if sq_cols:
            df_sq_numeric = df_sq[sq_cols].apply(pd.to_numeric, errors='coerce')
            sq_averages = df_sq_numeric.mean()
            overall_avg = sq_averages.mean()
            
    return overall_avg, sq_averages

def generate_gemini_teacher_comment(mcq_avg, diff_qs, sq_overall, sq_avg, target_class, api_key):
    """Generates a teacher's comment using the Gemini API based on performance data."""
    if not api_key:
        return "⚠️ **Gemini API Key is missing.** Please enter your API key in the sidebar to generate the AI narrative report."
    
    try:
        genai.configure(api_key=api_key)
        # Using gemini-1.5-flash for fast, reliable text generation
        model = genai.GenerativeModel('gemini-1.5-flash') 
        
        # Format the data for the prompt
        diff_qs_str = ", ".join(diff_qs.iloc[:, 0].astype(str).tolist()) if not diff_qs.empty else "N/A"
        sq_breakdown = ", ".join([f"{idx}: {val:.1f}%" for idx, val in sq_avg.items()]) if not sq_avg.empty else "N/A"
        
        prompt = f"""
        You are an expert high school Biology teacher writing a professional, encouraging, yet analytical post-test report for a class.
        
        Here is the performance data for Class {target_class}:
        - Overall Multiple Choice (MCQ) Average: {mcq_avg:.1f}%
        - Most difficult MCQ questions (lowest correct percentage): {diff_qs_str}
        - Overall Structured Question (SQ) Average: {sq_overall:.1f}%
        - Breakdown of SQ averages: {sq_breakdown}
        
        Write a concise, 3-paragraph report summarizing this data. Highlight the strengths, clearly point out the specific weak areas based on the difficult MCQs and lowest-scoring SQs, and provide actionable advice for remediation. Do not use filler introductions like "Here is the report". Output the report directly.
        """
        
        response = model.generate_content(prompt)
        return response.text
        
    except Exception as e:
        return f"❌ **Error connecting to Gemini API:** {str(e)}"

def display_pdf(pdf_file):
    """Encodes PDF to Base64 and embeds it in an HTML iframe."""
    if pdf_file is not None:
        base64_pdf = base64.b64encode(pdf_file.getvalue()).decode('utf-8')
        pdf_display = f'<iframe src="data:application/pdf;base64,{base64_pdf}" width="100%" height="800" type="application/pdf"></iframe>'
        st.markdown(pdf_display, unsafe_allow_html=True)
    else:
        st.info("No document uploaded.")

# ==========================================
# III. User Interface (UI) and Layout
# ==========================================

st.set_page_config(page_title="Biology Report Generator", page_icon="🔬", layout="wide")
st.title("🔬 AI-Powered S3-S6 Biology Test Analysis")

if 'report_generated' not in st.session_state:
    st.session_state.report_generated = False

# 2. Sidebar
with st.sidebar:
    st.header("🔑 AI Configuration")
    gemini_api_key = st.text_input("Gemini API Key", type="password", help="Get your API key from Google AI Studio.")
    
    st.header("📂 Data Upload")
    qp_pdf = st.file_uploader("Question Paper (PDF)", type=["pdf"])
    ms_pdf = st.file_uploader("Marking Scheme (PDF)", type=["pdf"])
    
    st.divider()
    mc_analysis_file = st.file_uploader("MCQ Analysis (CSV/XLSX)", type=["csv", "xlsx"])
    printable_scores_file = st.file_uploader("Printable Scores (CSV/XLSX)", type=["csv", "xlsx"])
    sq_marks_file = st.file_uploader("SQ Marks (CSV/XLSX)", type=["csv", "xlsx"])
    
    st.divider()
    target_class = st.text_input("Target Class", value="4R")
    
    if st.button("Generate Report", type="primary", use_container_width=True):
        st.session_state.report_generated = True
        
        with st.spinner("Processing data and generating AI insights..."):
            st.session_state.detected_subtopics = analyze_curriculum_coverage(qp_pdf, HKDSE_BIO_CURRICULUM)
            st.session_state.mcq_avg, st.session_state.difficult_qs = analyze_mcq_performance(mc_analysis_file, printable_scores_file)
            st.session_state.sq_overall, st.session_state.sq_avg = analyze_sq_performance(sq_marks_file, target_class)
            
            # Use Gemini to generate the comment instead of the hardcoded logic
            st.session_state.teacher_comment = generate_gemini_teacher_comment(
                st.session_state.mcq_avg, 
                st.session_state.difficult_qs, 
                st.session_state.sq_overall, 
                st.session_state.sq_avg, 
                target_class,
                gemini_api_key
            )

# 3. Main Page Layout (Tabs)
tab1, tab2, tab3, tab4 = st.tabs([
    "📊 Performance Dashboard", 
    "📜 Curriculum Analysis", 
    "✨ AI Teacher's Comment", 
    "📚 Source Documents"
])

if st.session_state.report_generated:
    
    # --- Tab 1: Performance Dashboard ---
    with tab1:
        st.header(f"Class {target_class} Performance Dashboard")
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Multiple Choice Questions (MCQ)")
            st.metric("Overall Average Score", f"{st.session_state.mcq_avg:.2f}%")
            st.write("Most Difficult Questions (Lowest Correct %):")
            if not st.session_state.difficult_qs.empty:
                st.dataframe(st.session_state.difficult_qs, use_container_width=True, hide_index=True)
            else:
                st.info("MCQ data unavailable. Please upload files.")
                
        with col2:
            st.subheader("Structured Questions (SQ)")
            st.metric("Overall SQ Average", f"{st.session_state.sq_overall:.2f}%")
            st.write("Average Score per Question:")
            if not st.session_state.sq_avg.empty:
                st.bar_chart(st.session_state.sq_avg)
            else:
                st.info("SQ data unavailable. Please upload files.")

    # --- Tab 2: Curriculum Analysis ---
    with tab2:
        st.header("Curriculum Coverage")
        if st.session_state.detected_subtopics:
            st.success("Analysis complete. Topics detected in the question paper are highlighted below.")
            
            def render_curriculum(db_section):
                for key, value in db_section.items():
                    if isinstance(value, dict) and 'keywords' not in value:
                        st.markdown(f"### {key}")
                        for sub_topic, sub_data in value.items():
                            with st.expander(sub_topic):
                                if isinstance(sub_data, dict) and 'keywords' not in sub_data:
                                    for deepest_sub, deepest_data in sub_data.items():
                                        _render_subtopic_item(deepest_sub, deepest_data)
                                else:
                                    _render_subtopic_item(sub_topic, sub_data)
                    elif isinstance(value, dict) and 'keywords' in value:
                        with st.expander(key):
                            _render_subtopic_item(key, value)
            
            def _render_subtopic_item(name, data):
                detected = name in st.session_state.detected_subtopics
                if detected:
                    st.markdown(f"✔️ **{name}**")
                    for obj in st.session_state.detected_subtopics[name]:
                        st.markdown(f"- *{obj}*")
                else:
                    st.markdown(f"{name}")

            render_curriculum(HKDSE_BIO_CURRICULUM)
        else:
            st.info("Upload a Question Paper PDF and click 'Generate Report' to analyze curriculum coverage.")

    # --- Tab 3: AI Teacher's Comment ---
    with tab3:
        st.header("Gemini-Generated Narrative Report")
        st.markdown(st.session_state.teacher_comment)
        
        with st.expander("Copy Raw Text"):
            st.text_area("Teacher's Comment", st.session_state.teacher_comment, height=250, label_visibility="hidden")

else:
    for tab in [tab1, tab2, tab3]:
        with tab:
            st.info("👈 Please enter your Gemini API key, upload the required files in the sidebar, and click **Generate Report**.")

# --- Tab 4: Source Documents ---
with tab4:
    st.header("Document Viewer")
    doc_col1, doc_col2 = st.columns(2)
    
    with doc_col1:
        st.subheader("Question Paper")
        if qp_pdf: display_pdf(qp_pdf)
        else: st.info("Upload a Question Paper PDF in the sidebar.")
            
    with doc_col2:
        st.subheader("Marking Scheme")
        if ms_pdf: display_pdf(ms_pdf)
        else: st.info("Upload a Marking Scheme PDF in the sidebar.")
