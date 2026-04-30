import streamlit as st
import pandas as pd
import numpy as np
import os
import base64
import google.generativeai as genai
from pdfminer.high_level import extract_text

# ==========================================
# I. Curriculum Knowledge Base (Expanded)
# ==========================================
# This acts as the reference framework for Gemini to map the questions against.
HKDSE_BIO_CURRICULUM = {
    "Compulsory Part": {
        "I. Cells and Molecules of Life": {
            "a. Molecules of life": {
                "keywords": ["carbohydrate", "lipid", "protein", "nucleic acid", "monosaccharide", "amino acid", "fatty acid", "enzyme", "water", "inorganic ion"],
                "objectives": ["State the elemental composition of carbohydrates, lipids and proteins.", "Describe the basic units of carbohydrates, lipids and proteins.", "Describe the occurrence and functions of sugars, lipids, proteins, vitamins and minerals."]
            },
            "b. Cellular organisation": {
                "keywords": ["cell wall", "cell membrane", "cytoplasm", "vacuole", "nucleus", "chloroplast", "mitochondrion", "organelle", "prokaryotic", "eukaryotic"],
                "objectives": ["Identify cell structures of typical animal and plant cells.", "State the functions of the organelles.", "Compare the structures of animal and plant cells.", "Compare prokaryotic and eukaryotic cells."]
            },
            "c. Movement of substances across membrane": {
                "keywords": ["diffusion", "osmosis", "active transport", "cell membrane", "water potential", "plasmolysis", "haemolysis", "phagocytosis"],
                "objectives": ["Describe the fluid mosaic model of cell membrane.", "Explain the movement of substances across the cell membrane.", "Describe the effects of osmosis on animal and plant cells."]
            },
            "d. Cell cycle and division": {
                "keywords": ["mitosis", "meiosis", "cell cycle", "chromosome", "homologous chromosomes", "nuclear division", "cytoplasmic division"],
                "objectives": ["Describe the cell cycle.", "Outline and compare the processes of mitosis and meiosis.", "State the significance of mitosis and meiosis."]
            },
            "e. Cellular energetics": {
                "keywords": ["metabolism", "catabolism", "anabolism", "enzymes", "active site", "photosynthesis", "cellular respiration", "ATP", "glycolysis", "Krebs cycle", "Calvin cycle"],
                "objectives": ["Explain metabolism in terms of catabolism and anabolism.", "Explain the functions of enzymes.", "Outline the major steps of photosynthesis and cellular respiration."]
            }
        },
        "II. Genetics and Evolution": {
            "a. Basic genetics": {
                "keywords": ["gene", "allele", "locus", "genotype", "phenotype", "dominant", "recessive", "homozygous", "heterozygous", "monohybrid", "pedigree", "codominance", "sex linkage"],
                "objectives": ["Understand the law of segregation and independent assortment.", "Construct and interpret genetic diagrams and pedigrees.", "Understand the inheritance of ABO blood groups and sex-linked traits."]
            },
            "b. Molecular genetics": {
                "keywords": ["DNA", "RNA", "genetic code", "transcription", "translation", "protein synthesis", "mutation", "recombinant DNA", "DNA fingerprinting", "Human Genome Project"],
                "objectives": ["Describe the relationship between DNA, genes and chromosomes.", "Outline the process of protein synthesis.", "Recognise the applications of recombinant DNA technology and DNA fingerprinting."]
            },
            "c. Biodiversity and evolution": {
                "keywords": ["fossil", "natural selection", "Darwin", "speciation", "evolution", "classification", "binomial nomenclature", "dichotomous key", "domains", "kingdoms"],
                "objectives": ["Classify organisms and use dichotomous keys.", "Outline the mechanism of evolution.", "Interpret the evidence for evolution including fossil records."]
            }
        },
        "III. Organisms and Environment": {
            "a. Essential life processes in plants": {
                "keywords": ["autotroph", "root", "leaf", "gas exchange", "transpiration", "xylem", "phloem", "transport", "minerals", "water absorption"],
                "objectives": ["Understand plant nutrition and the need for minerals.", "Relate structures of roots and leaves to their functions.", "Explain gas exchange and transport in plants."]
            },
            "b. Essential life processes in animals": {
                "keywords": ["heterotroph", "digestion", "absorption", "assimilation", "alimentary canal", "dentition", "gas exchange", "air sacs", "circulatory system", "blood", "lymphatic system"],
                "objectives": ["Understand human nutrition and a balanced diet.", "Relate structures of the digestive, breathing, and circulatory systems to their functions."]
            },
            "c. Reproduction, growth and development": {
                "keywords": ["asexual reproduction", "sexual reproduction", "pollination", "fertilisation", "seed", "fruit", "sperm", "ovum", "menstrual cycle", "placenta", "growth curve"],
                "objectives": ["Discuss the significance of asexual and sexual reproduction.", "Outline reproduction in flowering plants and humans.", "Understand the roles of the placenta and parental care."]
            },
            "d. Coordination and response": {
                "keywords": ["stimulus", "receptor", "eye", "nervous system", "brain", "spinal cord", "neuron", "reflex action", "endocrine system", "hormone", "phototropism", "auxin"],
                "objectives": ["Understand the roles of sense organs, specifically the human eye.", "Compare nervous and hormonal coordination.", "Explain phototropism in plants."]
            },
            "e. Homeostasis": {
                "keywords": ["homeostasis", "negative feedback", "blood glucose", "insulin", "glucagon"],
                "objectives": ["Understand the concept of homeostasis.", "Explain the regulation of blood glucose level."]
            },
            "f. Ecosystems": {
                "keywords": ["abiotic", "biotic", "trophic level", "food chain", "food web", "energy flow", "carbon cycle", "nitrogen cycle", "ecological succession", "conservation"],
                "objectives": ["Understand the components of an ecosystem.", "Describe energy flow and material cycling in an ecosystem.", "Appreciate the need for conservation."]
            }
        },
        "IV. Health and Diseases": {
            "a. Personal health": {
                "keywords": ["health", "balanced diet", "exercise", "healthy lifestyle"],
                "objectives": ["Understand the meaning of health.", "Explain the relationship between health and lifestyle."]
            },
            "b. Diseases": {
                "keywords": ["infectious", "non-infectious", "pathogen", "virus", "bacteria", "transmission", "antibiotics", "vector"],
                "objectives": ["Distinguish between infectious and non-infectious diseases.", "Understand the transmission of diseases and the use of antibiotics."]
            },
            "c. Body defence mechanisms": {
                "keywords": ["physical barrier", "phagocytosis", "inflammatory response", "immune response", "antigen", "antibody", "lymphocyte", "vaccination", "immunity"],
                "objectives": ["Explain non-specific and specific defence mechanisms.", "Understand the principles of vaccination and immunity."]
            }
        }
    },
    "Elective Part": {
        "V. Human Physiology: Regulation and Control": {
            "a. Regulation of water content": {
                "keywords": ["osmoregulation", "kidney", "nephron", "ultrafiltration", "reabsorption", "ADH", "urine"],
                "objectives": ["Explain the regulation of water content in the blood.", "Relate the structure of the kidney and nephron to their functions."]
            },
            "b. Regulation of body temperature": {
                "keywords": ["temperature regulation", "skin", "hypothalamus", "vasodilation", "vasoconstriction", "sweating", "shivering"],
                "objectives": ["Explain the mechanisms of regulating body temperature in hot and cold environments."]
            },
            "c. Regulation of gas in blood": {
                "keywords": ["breathing rate", "chemoreceptor", "medulla oblongata", "carbon dioxide concentration"],
                "objectives": ["Explain the regulation of breathing rate during exercise."]
            },
            "d. Hormonal control of reproductive cycle": {
                "keywords": ["FSH", "LH", "oestrogen", "progesterone", "ovary", "uterus", "menstrual cycle"],
                "objectives": ["Explain the hormonal control of the menstrual cycle using the concept of negative feedback."]
            }
        },
        "VI. Applied Ecology": {
            "a. Human impact on the environment": {
                "keywords": ["pollution", "global warming", "greenhouse effect", "acid rain", "eutrophication", "deforestation", "algal bloom"],
                "objectives": ["Understand the causes and effects of various types of environmental pollution."]
            },
            "b. Pollution control": {
                "keywords": ["sewage treatment", "solid waste management", "landfill", "incineration", "recycling"],
                "objectives": ["Understand the principles of sewage treatment and solid waste management."]
            },
            "c. Conservation": {
                "keywords": ["biodiversity", "endangered species", "sustainable development", "ecological footprint"],
                "objectives": ["Appreciate the need for conservation and sustainable development."]
            }
        },
        "VII. Microorganisms and Humans": {
            "a. Microbiology": {
                "keywords": ["bacteria", "fungi", "virus", "culture", "aseptic technique", "growth curve", "lag phase", "log phase", "stationary phase"],
                "objectives": ["Understand the basic structure of microorganisms and their growth requirements.", "Apply aseptic techniques in culturing microorganisms."]
            },
            "b. Use of microorganisms": {
                "keywords": ["biotechnology", "brewing", "baking", "yoghurt", "biogas", "recombinant DNA"],
                "objectives": ["Understand the applications of microorganisms in the food industry and biotechnology."]
            },
            "c. Microorganisms and diseases": {
                "keywords": ["pathogen", "infection", "transmission", "food preservation", "food spoilage"],
                "objectives": ["Explain the role of microorganisms in causing diseases and food spoilage.", "Understand the principles of food preservation."]
            }
        },
        "VIII. Biotechnology": {
            "a. Recombinant DNA technology": {
                "keywords": ["restriction enzyme", "DNA ligase", "plasmid", "vector", "transgenic", "transformation"],
                "objectives": ["Describe the basic principles of recombinant DNA technology."]
            },
            "b. Applications in medicine and agriculture": {
                "keywords": ["gene therapy", "stem cell", "cloning", "GMO", "GM food", "insulin production"],
                "objectives": ["Understand the applications of biotechnology in medicine and agriculture."]
            },
            "c. Bioethics": {
                "keywords": ["ethics", "moral", "cloning", "GM crops", "safety", "patent", "human rights"],
                "objectives": ["Discuss the ethical, legal, social, economic, and environmental implications of biotechnology."]
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
HKDSE_BIO_CURRICULUM = {} 
# ==========================================
# II. Helper & Core Analysis Functions
# ==========================================
def load_file(uploaded_file, **kwargs):
    if uploaded_file is None: return None
    ext = os.path.splitext(uploaded_file.name)[1].lower()
    try:
        if ext == '.csv': return pd.read_csv(uploaded_file, **kwargs)
        elif ext in ['.xls', '.xlsx']: return pd.read_excel(uploaded_file, engine='openpyxl', **kwargs)
    except Exception as e:
        st.error(f"Error loading {uploaded_file.name}: {e}")
    return None

def clean_dataframe_header(df):
    """Smartly detects the true header row in messy school Excel sheets."""
    if df is None or df.empty: return df
    cols_str = " ".join([str(c).lower() for c in df.columns])
    
    if any(kw in cols_str for kw in ['name', 'score', 'class', 'question', 'mark', 'total']):
        return df
        
    for i, row in df.head(20).iterrows():
        row_strs = [str(x).lower() for x in row.values]
        if any(kw in x for kw in ['name', 'total', 'class', 'sq', 'mc', 'mark']) and len(set(row_strs)) > 3:
            new_cols = []
            seen = set()
            for col in df.iloc[i]:
                col_str = str(col).strip()
                if col_str in seen or col_str == 'nan':
                    col_str = f"{col_str}_{len(new_cols)}"
                seen.add(col_str)
                new_cols.append(col_str)
            df.columns = new_cols
            df = df.iloc[i+1:].reset_index(drop=True)
            return df
    return df

def extract_text_from_upload(uploaded_file):
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_file:
            temp_file.write(uploaded_file.getvalue())
            temp_path = temp_file.name
        text = extract_text(temp_path) 
        os.remove(temp_path)
        return text
    except Exception as e:
        st.error(f"Error reading PDF: {e}")
        return ""

def parse_numeric(series):
    """Robustly converts a pandas series to numeric, stripping out '%' or commas."""
    return pd.to_numeric(series.astype(str).str.replace('%', '').str.replace(',', ''), errors='coerce')

def analyze_class_ranking(df_scores, target_class):
    """Extracts the ranking leaderboard and overall class mean."""
    if df_scores is None or df_scores.empty: return 0.0, pd.DataFrame()
    
    class_col = next((c for c in df_scores.columns if 'class' in str(c).lower()), None)
    
    name_col = next((c for c in df_scores.columns if 'other name' in str(c).lower()), None)
    if not name_col:
        name_col = next((c for c in df_scores.columns if 'full name' in str(c).lower() or ('name' in str(c).lower() and 'chin' not in str(c).lower())), None)
    
    score_col = next((c for c in df_scores.columns if 'base = 100' in str(c).lower()), None)
    if not score_col:
        score_col = next((c for c in df_scores.columns if 'total mark' in str(c).lower() or 'score' in str(c).lower() or 'mark' in str(c).lower()), None)
        
    if not (name_col and score_col): return 0.0, pd.DataFrame()
         
    df_filtered = df_scores.copy()
    if class_col and target_class and str(target_class).strip():
        target = str(target_class).strip().upper()
        temp = df_filtered[df_filtered[class_col].astype(str).str.upper().str.contains(target, na=False)]
        if not temp.empty: 
            df_filtered = temp
        else:
            st.warning(f"⚠️ Could not find data matching Class '{target_class}'. Showing ALL students.")
        
    df_filtered[score_col] = parse_numeric(df_filtered[score_col])
    df_filtered = df_filtered.dropna(subset=[score_col, name_col])
    
    mean_score = df_filtered[score_col].mean()
    if pd.isna(mean_score): mean_score = 0.0
    
    cols_to_keep = []
    if class_col: cols_to_keep.append(class_col)
    cols_to_keep.extend([name_col, score_col])
    
    leaderboard = df_filtered[cols_to_keep].copy()
    leaderboard = leaderboard.sort_values(by=score_col, ascending=False).reset_index(drop=True)
    leaderboard.index = leaderboard.index + 1
    leaderboard = leaderboard.reset_index()
    leaderboard = leaderboard.rename(columns={'index': 'Rank', score_col: 'Total Score', name_col: 'Student Name'})
    if class_col: leaderboard = leaderboard.rename(columns={class_col: 'Class'})
    
    return mean_score, leaderboard

def analyze_mcq_performance(df_scores, mc_analysis_file):
    avg_score = 0.0
    difficult_qs = pd.DataFrame()
    
    if df_scores is not None and not df_scores.empty:
        score_cols = [c for c in df_scores.columns if any(kw in str(c).lower() for kw in ['score', 'total', 'mark', '%', 'avg'])]
        if score_cols:
            avg_score = parse_numeric(df_scores[score_cols[0]]).mean()
        else:
            numeric_cols = df_scores.select_dtypes(include=[np.number]).columns
            if len(numeric_cols) > 0: avg_score = df_scores[numeric_cols[-1]].mean()

    if pd.isna(avg_score): avg_score = 0.0

    df_mc = clean_dataframe_header(load_file(mc_analysis_file))
    if df_mc is not None and not df_mc.empty:
        pct_col = next((c for c in df_mc.columns if any(kw in str(c).lower() for kw in ['%', 'correct', 'rate'])), None)
        q_col = next((c for c in df_mc.columns if any(kw in str(c).lower() for kw in ['question', 'item', 'q'])), None)
        if pct_col is None and len(df_mc.columns) >= 2: pct_col = df_mc.columns[1]
        if q_col is None and len(df_mc.columns) >= 1: q_col = df_mc.columns[0]
        
        if pct_col and q_col:
            df_mc[pct_col] = parse_numeric(df_mc[pct_col])
            difficult_qs = df_mc.dropna(subset=[pct_col]).sort_values(by=pct_col, ascending=True).head(3)[[q_col, pct_col]]
            
    return avg_score, difficult_qs

def analyze_sq_performance(sq_marks_file, target_class):
    overall_avg = 0.0
    sq_averages = pd.Series(dtype=float)
    
    df_sq = clean_dataframe_header(load_file(sq_marks_file))
    if df_sq is not None and not df_sq.empty:
        class_col = next((c for c in df_sq.columns if 'class' in str(c).lower()), None)
        if class_col and target_class and str(target_class).strip():
            target = str(target_class).strip().upper()
            filtered_df = df_sq[df_sq[class_col].astype(str).str.upper().str.contains(target, na=False)]
            if not filtered_df.empty: df_sq = filtered_df
        
        sq_cols = [c for c in df_sq.columns if str(c).strip().upper().startswith('SQ') or str(c).strip().upper().startswith('Q')]
        
        if not sq_cols:
            exclude_kws = ['class', 'group', 'total', 'score', 'mark', 'name', 'id', 'rank', 'gender']
            sq_cols = [c for c in df_sq.columns if not any(kw in str(c).lower() for kw in exclude_kws)]
             
        if sq_cols:
            df_sq_numeric = df_sq[sq_cols].apply(parse_numeric)
            sq_averages = df_sq_numeric.mean().dropna()
            overall_avg = sq_averages.mean()
    
    if pd.isna(overall_avg): overall_avg = 0.0
            
    return overall_avg, sq_averages

# AI Functions
def analyze_topic_performance_with_ai(qp_pdf, sq_avg, curriculum_db, api_key, model_name):
    """Uses Gemini to map each question to a topic and analyze student performance based on their scores."""
    if not api_key: return "⚠️ **Gemini API Key is missing.**"
    if qp_pdf is None: return "⚠️ **No Question Paper uploaded.**"
    if sq_avg.empty: return "⚠️ **No SQ score data available to analyze.**"
    
    try:
        extracted_text = extract_text_from_upload(qp_pdf)
        if not extracted_text.strip(): return "Could not extract text from the PDF."
        
        sq_avg_dict = {str(k): round(v, 2) for k, v in sq_avg.items()}
        
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel(model_name)
        prompt = f"""
        You are an expert high school Biology teacher analyzing test results.
        I am giving you the test paper text, the curriculum framework, and the average score (%) the class achieved on each Structured Question (SQ).
        
        Class Averages per Question:
        {json.dumps(sq_avg_dict, indent=2)}
        
        Curriculum Framework:
        {json.dumps(curriculum_db, indent=2)}
        
        Test Paper Text:
        ---
        {extracted_text}
        ---
        
        Task:
        1. Identify which Curriculum Topic each question belongs to by reading the test paper.
        2. Create a detailed Markdown table with columns: `| Question | Curriculum Topic | Sub-topic | Class Average |`
        3. Below the table, write a brief, insightful paragraph summarizing how the students performed across the DIFFERENT TOPICS. Which concepts did they grasp well? Which topics require re-teaching based on the low averages?
        """
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"❌ **Error connecting to Gemini API ({model_name}):** {str(e)}"

def generate_gemini_teacher_comment(mcq_avg, diff_qs, sq_overall, sq_avg, target_class, api_key, model_name):
    if not api_key: return "⚠️ **Gemini API Key is missing.**"
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel(model_name) 
        diff_qs_str = ", ".join(diff_qs.iloc[:, 0].astype(str).tolist()) if not diff_qs.empty else "N/A"
        sq_breakdown = ", ".join([f"{idx}: {val:.1f}" for idx, val in sq_avg.items()]) if not sq_avg.empty else "N/A"
        prompt = f"""
        You are an expert high school Biology teacher writing a professional, encouraging, yet analytical post-test report for a class.
        Performance data for Class {target_class}:
        - Overall MCQ Average: {mcq_avg:.1f}%
        - Most difficult MCQ questions: {diff_qs_str}
        - Overall SQ Average: {sq_overall:.1f}%
        - Breakdown of SQ averages: {sq_breakdown}
        
        Write a concise, 3-paragraph report summarizing this data. Highlight strengths, weak areas, and provide actionable advice. Output directly in markdown.
        """
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"❌ **Error connecting to Gemini API:** {str(e)}"

def analyze_curriculum_coverage_with_gemini(pdf_file, curriculum_db, api_key, model_name):
    if not api_key: return "⚠️ **Gemini API Key is missing.**"
    if pdf_file is None: return "⚠️ **No Question Paper uploaded.**"
    try:
        extracted_text = extract_text_from_upload(pdf_file)
        if not extracted_text.strip(): return "Could not extract text from the PDF."
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel(model_name)
        prompt = f"Analyze the test paper and determine exactly which curriculum topics and sub-topics are being assessed.\nCurriculum Framework:\n{json.dumps(curriculum_db, indent=2)}\n\nTest Paper Text:\n---\n{extracted_text}\n---"
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"❌ **Error connecting to Gemini API:** {str(e)}"

def analyze_student_mistakes_with_gemini(student_work_pdf, api_key, model_name):
    if not api_key: return "⚠️ **Gemini API Key is missing.**"
    if student_work_pdf is None: return "No student work uploaded."
    try:
        extracted_text = extract_text_from_upload(student_work_pdf)
        if not extracted_text.strip(): return "Could not extract text from the Student Work PDF."
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel(model_name)
        prompt = f"Identify recurring factual errors, logical fallacies, or biological misconceptions from these student answers. Format with Major Misconceptions, Terminology Errors, and Actionable Advice.\n\nStudent Responses Text:\n---\n{extracted_text}\n---"
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"❌ **Error connecting to Gemini API:** {str(e)}"

def display_pdf(pdf_file):
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
st.title("🔬 AI-Powered Biology Test Analysis")

if 'report_generated' not in st.session_state:
    st.session_state.report_generated = False

with st.sidebar:
    st.header("🔑 AI Configuration")
    gemini_api_key = st.text_input("Gemini API Key", type="password")
    gemini_model_name = st.text_input("Model Version", value="gemini-1.5-pro", help="Change this to gemini-1.5-pro-latest, gemini-3.0-pro, etc.")
    
    st.header("📂 Data Upload (Max 600MB)")
    qp_pdf = st.file_uploader("Question Paper (PDF)", type=["pdf"])
    ms_pdf = st.file_uploader("Marking Scheme (PDF)", type=["pdf"])
    
    st.divider()
    mc_analysis_file = st.file_uploader("MCQ Analysis (CSV/XLSX)", type=["csv", "xlsx"])
    printable_scores_file = st.file_uploader("Printable Scores (CSV/XLSX)", type=["csv", "xlsx"])
    sq_marks_file = st.file_uploader("SQ Marks (CSV/XLSX)", type=["csv", "xlsx"])
    
    st.divider()
    st.header("📝 Student Work Analysis")
    student_work_pdf = st.file_uploader("Student Work Samples (PDF)", type=["pdf"])

    st.divider()
    target_class = st.text_input("Target Class", value="4R")
    
    if st.button("Generate AI Report", type="primary", use_container_width=True):
        st.session_state.report_generated = True
        
        with st.spinner(f"Executing Data Processing & AI Analysis..."):
            # 1. Clean Master Scoreboard first
            raw_scores = load_file(printable_scores_file)
            cleaned_scores = clean_dataframe_header(raw_scores)
            
            # 2. Extract Data
            st.session_state.class_mean, st.session_state.leaderboard = analyze_class_ranking(cleaned_scores, target_class)
            st.session_state.mcq_avg, st.session_state.difficult_qs = analyze_mcq_performance(cleaned_scores, mc_analysis_file)
            st.session_state.sq_overall, st.session_state.sq_avg = analyze_sq_performance(sq_marks_file, target_class)
            
            # 3. AI Executions
            st.session_state.topic_analysis = analyze_topic_performance_with_ai(qp_pdf, st.session_state.sq_avg, HKDSE_BIO_CURRICULUM, gemini_api_key, gemini_model_name)
            st.session_state.curriculum_report = analyze_curriculum_coverage_with_gemini(qp_pdf, HKDSE_BIO_CURRICULUM, gemini_api_key, gemini_model_name)
            st.session_state.teacher_comment = generate_gemini_teacher_comment(
                st.session_state.mcq_avg, st.session_state.difficult_qs, st.session_state.sq_overall, 
                st.session_state.sq_avg, target_class, gemini_api_key, gemini_model_name
            )
            if student_work_pdf is not None:
                st.session_state.student_mistakes_report = analyze_student_mistakes_with_gemini(student_work_pdf, gemini_api_key, gemini_model_name)
            else:
                st.session_state.student_mistakes_report = None

tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📊 Dashboard", "📜 Curriculum Mapping", "✨ Teacher's Comment", "🚨 Common Mistakes", "📚 Documents"
])

if st.session_state.report_generated:
    with tab1:
        # TOP ROW: Main Statistics
        st.header(f"Performance Overview: Class {target_class}")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("🏆 Overall Class Mean", f"{st.session_state.class_mean:.2f}%")
        with col2:
            st.metric("✅ MCQ Average", f"{st.session_state.mcq_avg:.2f}%")
        with col3:
            st.metric("📝 SQ Average", f"{st.session_state.sq_overall:.2f}%")
            
        st.divider()
        
        # MIDDLE ROW: Leaderboard & Mark Distribution Histogram
        col_rank, col_dist = st.columns(2)
        
        with col_rank:
            st.subheader("Leaderboard & Rankings")
            if not st.session_state.leaderboard.empty:
                st.dataframe(st.session_state.leaderboard, use_container_width=True, hide_index=True)
            else:
                st.info("Ranking data unavailable.")
                
        with col_dist:
            st.subheader("Mark Distribution")
            if not st.session_state.leaderboard.empty:
                scores = st.session_state.leaderboard['Total Score'].dropna()
                if not scores.empty:
                    # Create 10 bins (0-10, 10-20, etc.) for the histogram
                    counts, bins = np.histogram(scores, bins=10, range=(0, 100))
                    bin_labels = [f"{int(bins[i])}-{int(bins[i+1])}" for i in range(len(bins)-1)]
                    hist_df = pd.DataFrame({'Number of Students': counts}, index=bin_labels)
                    st.bar_chart(hist_df)
                else:
                    st.info("Insufficient score data for distribution chart.")
            else:
                st.info("Score data unavailable.")

        st.divider()
        
        # BOTTOM ROW: AI Topic Performance Table & Metrics Breakdown
        st.header("Detailed Question & Topic Analysis")
        
        st.subheader("Topic Performance Analysis (AI Evaluated)")
        st.info("Gemini AI has mapped each question to the curriculum and analyzed the class averages.")
        st.markdown(st.session_state.topic_analysis)
        
        st.divider()
        
        col_charts1, col_charts2 = st.columns(2)
        with col_charts1:
            st.subheader("Structured Questions Breakdown")
            if not st.session_state.sq_avg.empty: 
                st.bar_chart(st.session_state.sq_avg)
            else:
                st.info("SQ data unavailable.")
                
        with col_charts2:
            st.subheader("Most Difficult MCQs")
            if not st.session_state.difficult_qs.empty: 
                st.dataframe(st.session_state.difficult_qs, use_container_width=True, hide_index=True)
            else:
                st.info("MCQ difficulty data unavailable.")

    with tab2:
        st.markdown(st.session_state.curriculum_report)

    with tab3:
        st.markdown(st.session_state.teacher_comment)

    with tab4:
        if st.session_state.student_mistakes_report: st.markdown(st.session_state.student_mistakes_report)
        else: st.info("No Student Work PDF was uploaded.")
else:
    for tab in [tab1, tab2, tab3, tab4]:
        with tab: st.info("Please enter your API key, configure the model, upload files, and click Generate Report.")

with tab5:
    doc_col1, doc_col2 = st.columns(2)
    with doc_col1:
        st.subheader("Question Paper")
        if qp_pdf: display_pdf(qp_pdf)
    with doc_col2:
        st.subheader("Marking Scheme")
        if ms_pdf: display_pdf(ms_pdf)
