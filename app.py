import streamlit as st
from main import extract_text_from_pdf, extract_candidate_info, extract_jd_skills, calculate_ats_score, generate_resume_review, run_assessment
from helpers import make_donut
import os

os.environ["PYTHONWATCHDOG"] = "0"

#-------Resume Screening and Technical Assessment System-----------
st.set_page_config(page_title="TalentScout", layout="wide")

if "view_mode" not in st.session_state:
    st.session_state.view_mode = "initial"

@st.cache_data
def cached_extract_text_from_pdf(uploaded_file):
    return extract_text_from_pdf(uploaded_file)


if not st.session_state.get("confirmed", False):
    st.title("Resume Screening and Technical Assessment System")
    st.write("Hello! I am the Hiring Assistant at TalentScout. Please upload your resume below to proceed.")
    uploaded_file = st.file_uploader("Upload your Resume (PDF)", type="pdf")

    if uploaded_file:
        text = cached_extract_text_from_pdf(uploaded_file)
        resume_text = extract_candidate_info(text)

        st.subheader("Candidate Information")
        for key in resume_text:
            st.write(f"**{key}** : {resume_text[key]}")

        confirm = st.radio("Do you confirm these details are correct?", ["Yes", "No"], index=None)

        if confirm == "Yes":
            st.session_state.confirmed = True
            st.session_state.text = text
            st.session_state.resume_text = resume_text
            st.session_state.tech_stack = resume_text.get("Tech Stack", "Python")
            st.success("Thank you! Your details are confirmed.")
            st.rerun()

        elif confirm == "No":
            st.warning("Please update your resume or enter corrections manually.")
            

else:
    text = st.session_state.text
    resume_text = st.session_state.resume_text
    tech_stack = st.session_state.tech_stack

    col1, col2, col3, col4 = st.columns([0.5,2,2,2])
    with col1:
        if st.button("⬅Back"):
            st.session_state.confirmed = False
            st.session_state.view_mode = "initial"
            st.rerun()
    with col2:
        if st.button("Calculate ATS Score"):
            st.session_state.view_mode = "ats"
            st.rerun()
    with col3:
        if st.button("Assess on Your skills"):
            st.session_state.view_mode = "technical1"
            st.rerun()
    with col4:
        if st.button("Assess on JD skills"):
            st.session_state.view_mode = "technical2"
            st.rerun()

    # --------------------- ATS ---------------------
    if st.session_state.view_mode == "ats":
        st.title("ATS Score")
        jd = st.text_area("Job Description", key="jd_ats", height=200, placeholder="Paste the job description here...")
        if st.button("Submit"):
            if jd:
                jd_text = extract_jd_skills(jd)
                st.header("Results")
                ats = calculate_ats_score(resume_text, jd_text, text)
                st.subheader(f"ATS Score")
                st.altair_chart(make_donut(ats, "Percentage Match"), use_container_width=False)
                st.write(generate_resume_review(resume_text, jd))
            else:
                st.warning("Please enter a Job Description before generating the ATS score.")
    
    # --------------------- Technical Assessment on Resume ---------------------
    elif st.session_state.view_mode == "technical1":
        run_assessment("technical1", tech_stack, prefix="answer", jd_required=False)

    # --------------------- Technical Assessment on JD ---------------------
    elif st.session_state.view_mode == "technical2":
        run_assessment("technical2", "Python", prefix="answer_jd", jd_required=True)
    else:
        st.title("Select an option")
        st.write("Please choose one of the options above to proceed.")

