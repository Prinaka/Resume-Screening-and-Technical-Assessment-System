import streamlit as st
from streamlit_option_menu import option_menu
from src.parser import extract_text_from_pdf, extract_candidate_info, extract_jd_skills
from src.ats import calculate_ats_score, generate_resume_review
from src.assessment import run_assessment
from helpers.visuals import make_donut

#-------Resume Screening and Technical Assessment System-----------
st.set_page_config(page_title="TalentScout", layout="wide")

if "view_mode" not in st.session_state:
    st.session_state.view_mode = "home"

view_mode_map = {
    "Home": "home",
    "ATS Score": "ats",
    "Assess on Your skills": "technical1",
    "Assess on JD skills": "technical2"
}

with st.sidebar:
    view_mode_sidebar = option_menu("Navigation", list(view_mode_map.keys()), menu_icon="cast", 
                                   default_index=list(view_mode_map.keys()).index(
                                       [k for k, v in view_mode_map.items() if v == st.session_state.view_mode][0]
                                   ))

new_view_mode = view_mode_map[view_mode_sidebar]

if new_view_mode != st.session_state.view_mode:
    st.session_state.question_number = None
    st.session_state.questions = []
    st.session_state.answers = []
    st.session_state.grades = []
    
    if "resume_text" in st.session_state: del st.session_state.resume_text
    if "jd_text" in st.session_state: del st.session_state.jd_text
    if "confirmed" in st.session_state: del st.session_state.confirmed
    if "resume_text2" in st.session_state: del st.session_state.resume_text2
    if "tech_stack2" in st.session_state: del st.session_state.tech_stack2
    if "confirmed2" in st.session_state: del st.session_state.confirmed2
    if "jd_text2" in st.session_state: del st.session_state.jd_text2
    if "jd_tech_stack2" in st.session_state: del st.session_state.jd_tech_stack2
    
    st.session_state.view_mode = new_view_mode
    st.rerun() 

@st.cache_data
def cached_extract_text_from_pdf(uploaded_file):
    return extract_text_from_pdf(uploaded_file)

# ----------------- HOME PAGE -----------------

if st.session_state.view_mode == "home":

    st.title("Welcome to Resume Screening and Technical Assessment System")
    st.write("Hello! I am the Hiring Assistant at TalentScout.")
    st.write("Please choose an option from the sidebar to proceed.")

# ----------------- ATS SCORE -----------------

elif st.session_state.view_mode == "ats":

    st.title("ATS Score")
    uploaded_file = st.file_uploader("Upload your Resume (PDF only)", type="pdf", key="ats_upload")
    jd = st.text_area("Job Description", key="jd_ats", height=200, placeholder="Paste the job description here...")

    if st.button("Submit", key="ats_start"):
        if not uploaded_file or not jd:
            st.warning("Please upload a resume and paste the Job Description.")
        else:
            st.session_state.text = cached_extract_text_from_pdf(uploaded_file)
            st.session_state.resume_text = extract_candidate_info(st.session_state.text)
            st.session_state.jd_text = extract_jd_skills(jd)
            st.session_state.confirmed = False

    if "resume_text" in st.session_state and not st.session_state.confirmed:
        st.subheader("Candidate Information")
        for key, val in st.session_state.resume_text.items():
            st.write(f"**{key}** : {val}")

        confirm = st.radio("Do you confirm these details are correct?", ["Yes", "No"], index=None, key="ats_confirm_radio")

        if confirm == "Yes":
            st.session_state.confirmed = True
            st.success("Thank you! Your details are confirmed.")
        elif confirm == "No":
            st.warning("Please update your resume or enter corrections manually.")

    if st.session_state.get("confirmed", False):
        resume_text = st.session_state.resume_text
        jd = st.session_state.jd_text
        ats, info = calculate_ats_score(st.session_state.resume_text, st.session_state.jd_text, st.session_state.text)
        ats_dashboard(ats, info, resume_text, jd)

# ----------------- TECHNICAL ASSESSMENT ON RESUME -----------------

elif st.session_state.view_mode == "technical1":

    st.title("Assess on Your Skills")
    uploaded_file = st.file_uploader("Upload your Resume (PDF only)", type="pdf", key="tech1_upload")

    if st.button("Start Assessment", key="tech1_start"):
        if not uploaded_file:
            st.warning("Please paste the Job Description.")
        else:
            st.session_state.text2 = cached_extract_text_from_pdf(uploaded_file)
            st.session_state.resume_text2 = extract_candidate_info(st.session_state.text2)
            st.session_state.tech_stack2 =st.session_state.resume_text2.get("Tech Stack", "Python")
            st.session_state.confirmed2 = False

    if "resume_text2" in st.session_state and not st.session_state.confirmed2:
        st.subheader("Candidate Information")
        for key, val in st.session_state.resume_text2.items():
            st.write(f"**{key}** : {val}")

        confirm = st.radio("Do you confirm these details are correct?", ["Yes", "No"], index=None, key="confirm_radio")

        if confirm == "Yes":
            st.session_state.confirmed2 = True
            st.success("Thank you! Your details are confirmed.")
        elif confirm == "No":
            st.warning("Please update your resume or enter corrections manually.")

    if st.session_state.get("confirmed2", False):
        run_assessment("technical1", st.session_state.tech_stack2, prefix="answer")

# ----------------- TECHNICAL ASSESSMENT ON JD -----------------

elif st.session_state.view_mode == "technical2":

    st.title("Assess on JD Skills")
    jd = st.text_area("Paste Job Description here", key="jd_tech2", height=200)

    if st.button("Start Assessment", key="tech2_start"):
        if not jd:
            st.warning("Please paste the Job Description.")
        else:
            st.session_state.jd_text2 = extract_jd_skills(jd)
            st.session_state.jd_tech_stack2 =st.session_state.jd_text2.get("Tech Stack", "Python")

    if "jd_text2" in st.session_state:
        run_assessment("technical2", st.session_state.jd_tech_stack2, prefix="answer_jd")

