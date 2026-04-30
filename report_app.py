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

HKDSE_BIO_CURRICULUM = {} # Placeholder

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

def analyze_curriculum_coverage_with_gemini(pdf_file, curriculum_db, api_key):
    """Uses Gemini to "read" the PDF and map it to the HKDSE Curriculum."""
    if not api_key:
        return "⚠️ **Gemini API Key is missing.** Please enter your API key in the sidebar."
    if pdf_file is None:
        return "⚠️ **No Question Paper uploaded.** Upload a PDF to analyze curriculum coverage."
    
    try:
        extracted_text = extract_text(pdf_file)
        if not extracted_text.strip():
            return "Could not extract text from the PDF. Please ensure it is a text-searchable PDF."

        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        prompt = f"""
        You are an expert high school Biology teacher specializing in the HKDSE Biology curriculum.
        Below is the text from a Biology test/question paper, followed by the official HKDSE Biology curriculum framework.
        
        Your task is to analyze the test paper and determine exactly which curriculum topics and sub-topics are being assessed.
        
        Instructions:
        1. Read the test questions and map them to the provided curriculum database.
        2. Output a beautifully formatted markdown report showing the coverage. Use headings for Major Areas and bullet points for Sub-topics.
        3. Under each detected sub-topic, add a brief 1-sentence note indicating WHICH question or concept from the test paper proves this topic is being assessed.
        4. Be analytical. If a topic is completely absent from the paper, do not include it in your output report.
        
        Curriculum Framework:
        {json.dumps(curriculum_db, indent=2)}
        
        Test Paper Text:
        ---
        {extracted_text[:25000]}
        ---
        """
        
        response = model.generate_content(prompt)
        return response.text
        
    except Exception as e:
        return f"❌ **Error connecting to Gemini API:** {str(e)}"

def analyze_student_mistakes_with_gemini(student_work_pdf, api_key):
    """Uses Gemini to analyze uploaded student work and identify common mistakes."""
    if not api_key:
        return "⚠️ **Gemini API Key is missing.**"
    if student_work_pdf is None:
        return "No student work uploaded."
        
    try:
        extracted_text = extract_text(student_work_pdf)
        if not extracted_text.strip():
            return "Could not extract text from the Student Work PDF. Please ensure it is text-searchable or contains readable handwriting OCR."

        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        prompt = f"""
        You are an expert high school Biology teacher marking a batch of student test papers. 
        Below is a transcript of various students' answers from a recent test.
        
        Your task is to analyze these responses and create a "Common Mistakes & Misconceptions" report for the teacher.
        
        Instructions:
        1. Identify recurring factual errors, logical fallacies, or biological misconceptions.
        2. Point out areas where students failed to use precise biological terminology (e.g., using "melt" instead of "denature" for enzymes).
        3. Format your output using clear markdown with the following sections:
           - 🔴 **Major Misconceptions**: Core misunderstandings of biological concepts.
           - 📝 **Terminology Errors**: Missing or incorrectly used keywords.
           - 💡 **Actionable Advice**: How the teacher can address these specific issues in the next lesson.
        
        Student Responses Text:
        ---
        {extracted_text[:25000]}
        ---
        """
        
        response = model.generate_content(prompt)
        return response.text
        
    except Exception as e:
        return f"❌ **Error connecting to Gemini API:** {str(e)}"

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
        return "⚠️ **Gemini API Key is missing.**"
    
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-1.5-flash') 
        
        diff_qs_str = ", ".join(diff_qs.iloc[:, 0].astype(str).tolist()) if not diff_qs.empty else "N/A"
        sq_breakdown = ", ".join([f"{idx}: {val:.1f}%" for idx, val in sq_avg.items()]) if not sq_avg.empty else "N/A"
        
        prompt = f"""
        You are an expert high school Biology teacher writing a professional, encouraging, yet analytical post-test report for a class.
        
        Here is the performance data for Class {target_class}:
        - Overall Multiple Choice (MCQ) Average: {mcq_avg:.1f}%
        - Most difficult MCQ questions (lowest correct percentage): {diff_qs_str}
        - Overall Structured Question (SQ) Average: {sq_overall:.1f}%
        - Breakdown of SQ averages: {sq_breakdown}
        
        Write a concise, 3-paragraph report summarizing this data. Highlight the strengths, clearly point out the specific weak areas based on the lowest-scoring SQs, and provide actionable advice for remediation. Output the report directly in markdown.
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

# Sidebar
with st.sidebar:
    st.header("🔑 AI Configuration")
    gemini_api_key = st.text_input("Gemini API Key", type="password", help="Get your API key from Google AI Studio.")
    
    st.header("📂 Data Upload")
    qp_pdf = st.file_uploader("Question Paper (PDF) - For AI Mapping", type=["pdf"])
    ms_pdf = st.file_uploader("Marking Scheme (PDF)", type=["pdf"])
    
    st.divider()
    mc_analysis_file = st.file_uploader("MCQ Analysis (CSV/XLSX)", type=["csv", "xlsx"])
    printable_scores_file = st.file_uploader("Printable Scores (CSV/XLSX)", type=["csv", "xlsx"])
    sq_marks_file = st.file_uploader("SQ Marks (CSV/XLSX)", type=["csv", "xlsx"])
    
    st.divider()
    st.header("📝 Student Work Analysis (Optional)")
    student_work_pdf = st.file_uploader("Student Work Samples (PDF)", type=["pdf"], help="Upload scanned student answers to have AI spot common misconceptions and terminology errors.")

    st.divider()
    target_class = st.text_input("Target Class", value="4R")
    
    if st.button("Generate AI Report", type="primary", use_container_width=True):
        st.session_state.report_generated = True
        
        with st.spinner("Executing Gemini AI Analysis... (This may take a few seconds)"):
            
            # 1. Native Gemini PDF Curriculum Analysis
            st.session_state.curriculum_report = analyze_curriculum_coverage_with_gemini(
                qp_pdf, HKDSE_BIO_CURRICULUM, gemini_api_key
            )
            
            # 2. Data Processing
            st.session_state.mcq_avg, st.session_state.difficult_qs = analyze_mcq_performance(mc_analysis_file, printable_scores_file)
            st.session_state.sq_overall, st.session_state.sq_avg = analyze_sq_performance(sq_marks_file, target_class)
            
            # 3. Gemini Teacher Comment Generation
            st.session_state.teacher_comment = generate_gemini_teacher_comment(
                st.session_state.mcq_avg, 
                st.session_state.difficult_qs, 
                st.session_state.sq_overall, 
                st.session_state.sq_avg, 
                target_class,
                gemini_api_key
            )
            
            # 4. Gemini Student Work Analysis (if provided)
            if student_work_pdf is not None:
                st.session_state.student_mistakes_report = analyze_student_mistakes_with_gemini(
                    student_work_pdf, gemini_api_key
                )
            else:
                st.session_state.student_mistakes_report = None

# Main Page Layout (Tabs)
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📊 Performance Dashboard", 
    "📜 AI Curriculum Mapping", 
    "✨ AI Teacher's Comment", 
    "🚨 Common Mistakes",
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

    # --- Tab 2: AI Curriculum Mapping ---
    with tab2:
        st.header("Gemini Curriculum Coverage Analysis")
        st.info("This breakdown is dynamically generated by Gemini reading the uploaded PDF against the HKDSE Biology curriculum.")
        st.markdown(st.session_state.curriculum_report)

    # --- Tab 3: AI Teacher's Comment ---
    with tab3:
        st.header("Gemini-Generated Narrative Report")
        st.markdown(st.session_state.teacher_comment)
        
        with st.expander("Copy Raw Text"):
            st.text_area("Teacher's Comment", st.session_state.teacher_comment, height=250, label_visibility="hidden")

    # --- Tab 4: Common Mistakes ---
    with tab4:
        st.header("Student Work Analysis: Common Mistakes & Misconceptions")
        if st.session_state.student_mistakes_report:
            st.markdown(st.session_state.student_mistakes_report)
            with st.expander("Copy Raw Text"):
                st.text_area("Mistakes Report", st.session_state.student_mistakes_report, height=250, label_visibility="hidden")
        else:
            st.info("No Student Work PDF was uploaded for analysis. Upload a file in the sidebar and re-run the report to see insights here.")

else:
    for tab in [tab1, tab2, tab3, tab4]:
        with tab:
            st.info("👈 Please enter your **Gemini API key**, upload the required files in the sidebar, and click **Generate AI Report**.")

# --- Tab 5: Source Documents ---
with tab5:
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
