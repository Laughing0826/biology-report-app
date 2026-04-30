import streamlit as st
import pandas as pd
import numpy as np
import io
import pdfminer.high_level
import os
import base64

# --- Helper Functions ---

def load_file(uploaded_file, **kwargs):
    """
    Intelligently loads a file as a pandas DataFrame, whether it's CSV or Excel.
    """
    if uploaded_file.name.endswith('.csv'):
        return pd.read_csv(uploaded_file, **kwargs)
    elif uploaded_file.name.endswith('.xlsx'):
        # Add the engine for reading Excel files
        return pd.read_excel(uploaded_file, engine='openpyxl', **kwargs)
    else:
        st.error(f"Unsupported file type: {uploaded_file.name}. Please upload a CSV or XLSX file.")
        return None

def display_pdf(pdf_file):
    """Displays an uploaded PDF file in the Streamlit app."""
    base64_pdf = base64.b64encode(pdf_file.getvalue()).decode('utf-8')
    pdf_display = f'<iframe src="data:application/pdf;base64,{base64_pdf}" width="100%" height="800" type="application/pdf"></iframe>'
    st.markdown(pdf_display, unsafe_allow_html=True)

# --- Analysis Functions ---

def analyze_pdf_topics(pdf_file):
    if not pdf_file: return []
    # (This function remains the same as before)
    try:
        temp_pdf_path = f"temp_{pdf_file.name}"
        with open(temp_pdf_path, "wb") as f: f.write(pdf_file.getbuffer())
        text = pdfminer.high_level.extract_text(temp_pdf_path)
        os.remove(temp_pdf_path)
        topics = {
            "Cellular Respiration": ["respiration", "aerobic", "oxygen", "mitochondria"],
            "Photosynthesis": ["photosynthesis", "chloroplast", "carbon dioxide", "light"],
            "Gas Exchange": ["gas exchange", "stomata", "alveoli", "lungs", "leaf"],
            "Transpiration & Transport in Plants": ["transpiration", "xylem", "phloem", "water potential", "osmosis", "cohesion"],
            "Cell Division": ["mitotic", "cell division", "cell cycle", "mitosis"],
            "Scientific Investigation": ["independent variable", "dependent variable", "control", "measurement", "investigation"],
            "Nutrition & Digestion": ["nutrition", "starch", "carbohydrates"],
        }
        found_topics = [topic for topic, keywords in topics.items() if any(keyword in text.lower() for keyword in keywords)]
        return found_topics
    except Exception as e:
        st.error(f"Error processing {pdf_file.name}: {e}")
        return []


def analyze_mcq_performance(mc_analysis_file, printable_scores_file):
    """Analyzes MCQ performance from uploaded files."""
    if not mc_analysis_file or not printable_scores_file: return None
    try:
        # <-- Change: Use the new helper function
        mc_analysis_df = load_file(mc_analysis_file, header=2)
        printable_scores_df = load_file(printable_scores_file, header=1)
        
        # (Rest of the function is the same)
        avg_mcq_score = printable_scores_df['Marks (%)'].mean()
        mc_analysis_df.rename(columns={'Correct %': 'Correct_Percentage'}, inplace=True)
        mc_analysis_df['Correct_Percentage'] = pd.to_numeric(mc_analysis_df['Correct_Percentage'], errors='coerce')
        mc_analysis_df.dropna(subset=['Correct_Percentage'], inplace=True)
        difficult_mcqs = mc_analysis_df.nsmallest(3, 'Correct_Percentage').copy()
        difficult_mcqs['Correct_Percentage'] *= 100
        return {"avg_score": avg_mcq_score, "difficult_mcqs": difficult_mcqs}
    except Exception as e:
        st.error(f"Error analyzing MCQ files: {e}")
        return None

def analyze_sq_performance(sq_marks_file, target_class):
    """Analyzes SQ performance for a specific class."""
    if not sq_marks_file or not target_class: return None
    try:
        # <-- Change: Use the new helper function
        sq_marks_df = load_file(sq_marks_file, header=None)

        # (Rest of the function is the same)
        sq_marks_df.columns = [f'col_{i}' for i in range(len(sq_marks_df.columns))]
        sq_marks_df_class = sq_marks_df[sq_marks_df['col_0'].astype(str).str.startswith(target_class, na=False)].copy()
        if sq_marks_df_class.empty:
            st.warning(f"No data found for class '{target_class}'.")
            return None
        sq_columns_indices = {'SQ 1': 'col_20', 'SQ 2': 'col_21', 'SQ 3': 'col_22', 'SQ 4': 'col_23', 'SQ 5': 'col_24'}
        full_marks_sq = {'SQ 1': 3, 'SQ 2': 5, 'SQ 3': 9, 'SQ 4': 9, 'SQ 5': 9}
        avg_sq_performance = {}
        total_sq_marks_scored = 0
        for sq_name, col_index in sq_columns_indices.items():
            sq_marks_df_class.loc[:, col_index] = pd.to_numeric(sq_marks_df_class[col_index], errors='coerce')
            valid_scores = sq_marks_df_class[col_index].dropna()
            total_sq_marks_scored += valid_scores.sum()
            avg_sq_performance[sq_name] = (valid_scores.mean() / full_marks_sq[sq_name]) * 100 if not valid_scores.empty else 0.0
        total_students = len(sq_marks_df_class)
        total_sq_full_marks = sum(full_marks_sq.values())
        overall_sq_avg = ((total_sq_marks_scored / total_students) / total_sq_full_marks) * 100 if total_students > 0 else 0
        return {"avg_performance": avg_sq_performance, "overall_avg": overall_sq_avg, "weakest_sq": min(avg_sq_performance, key=avg_sq_performance.get) if avg_sq_performance else "N/A"}
    except Exception as e:
        st.error(f"Error analyzing SQ file: {e}")
        return None


def generate_teacher_comment(mcq_results, sq_results, target_class):
    # (This function remains the same)
    if not mcq_results or not sq_results: return "Analysis results are incomplete."
    return f"""Students showed a solid performance...""" # (Keeping this brief for clarity)

# --- Streamlit App UI ---
# (Page config and CSS are the same)

st.set_page_config(page_title="Biology Report Generator", page_icon="🔬", layout="wide")
st.markdown("""<style>...</style>""", unsafe_allow_html=True) # (CSS is unchanged)

st.title("🔬 S3-S6 Biology Test Analysis & Report Generator")
st.markdown("An automated tool to transform raw test scores into actionable teaching insights.")
st.markdown("---")

# --- Sidebar for File Uploads ---
with st.sidebar:
    st.header("Upload Files")
    q_pdf_file = st.file_uploader("1. Question Paper (PDF)", type="pdf")
    ms_pdf_file = st.file_uploader("2. Marking Scheme (PDF)", type="pdf")
    
    # <-- Change: Accept both .csv and .xlsx
    mc_analysis_file = st.file_uploader("3. MCQ Analysis Data", type=["csv", "xlsx"])
    printable_scores_file = st.file_uploader("4. MCQ Scores Data", type=["csv", "xlsx"])
    sq_marks_file = st.file_uploader("5. SQ Mark Sheet Data", type=["csv", "xlsx"])
    
    st.header("Settings")
    target_class = st.text_input("Enter Class to Analyze (e.g., 4R)", "4R")

# --- Main App Body ---
# (The main body logic remains the same)
if st.sidebar.button("Generate Report", use_container_width=True, type="primary"):
    # (The rest of the code for displaying tabs and content is identical)
    pass
