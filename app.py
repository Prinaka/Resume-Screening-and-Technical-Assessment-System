import streamlit as st
import pandas as pd
import altair as alt
import plotly.express as px
from main import extract_text_from_pdf, extract_candidate_info, clean_info, generate_ats_score, generate_resume_review, generate_technical_questions
import os

os.environ["PYTHONWATCHDOG"] = "0"

#-------Resume Screening and Technical Assessment System-----------
st.set_page_config(page_title="TalentScout")

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
        info = extract_candidate_info(text)
        candidate_info = clean_info(info)

        st.subheader("Candidate Information")
        for key in candidate_info:
            st.write(f"**{key}** : {candidate_info[key]}")

        confirm = st.radio("Do you confirm these details are correct?", ["Yes", "No"], index=None)

        if confirm == "Yes":
            st.session_state.confirmed = True
            st.session_state.resume_text = text
            st.session_state.candidate_info = candidate_info
            st.session_state.tech_stack = candidate_info.get("Tech Stack", "Python")
            st.success("Thank you! Your details are confirmed.")
            st.rerun()

        elif confirm == "No":
            st.warning("Please update your resume or enter corrections manually.")
            

else:
    resume_text = st.session_state.resume_text
    candidate_info = st.session_state.candidate_info
    tech_stack = st.session_state.tech_stack

    col1, col2 = st.columns(2)
    with col1:
        if st.button("Calculate ATS Score"):
            st.session_state.view_mode = "ats"
            st.rerun()
    with col2:
        if st.button("Take Technical Assessment"):
            st.session_state.view_mode = "technical"
            st.rerun()
            
    def make_donut(value, label):
        colors = (
            ['#27AE60', '#12783D'] if value >= 80 else
            ['#F39C12', '#875A12'] if value >= 50 else
            ['#E74C3C', '#781F16']
        )
        base = pd.DataFrame({"Topic": ['', label], "%": [100 - value, value]})
        bg = pd.DataFrame({"Topic": ['', label], "%": [100, 0]})
        
        def arc(data, radius=85, corner=25):
            return alt.Chart(data).mark_arc(innerRadius=radius, cornerRadius=corner).encode(
                theta="%", color=alt.Color("Topic:N", scale=alt.Scale(domain=[label, ''], range=colors), legend=None)
            ).properties(width=250, height=250)
        
        text = alt.Chart(base).mark_text(
            align='center', color="white", font="Calibri",
            fontSize=25, fontWeight=700, fontStyle="Bold"
        ).encode(text=alt.value(f"{value} %"))
        
        return arc(bg, corner=20) + arc(base) + text

    # --------------------- ATS ---------------------
    if st.session_state.view_mode == "ats":
        st.title("ATS Score")
        jd = st.text_area("Job Description", key="jd", height=200, placeholder="Paste the job description here...")
        if st.button("Submit"):
            if jd.strip():
                st.header("Results")
                ats = generate_ats_score(resume_text, jd)
                st.subheader(f"ATS Score")
                ats_val = float(ats.strip().replace("%", ""))
                st.altair_chart(make_donut(ats_val, "Percentage Match"), use_container_width=False)
                st.write(generate_resume_review(resume_text, jd))
            else:
                st.warning("Please enter a Job Description before generating the ATS score.")
    
    # --------------------- Technical System ---------------------
    elif st.session_state.view_mode == "technical":
        st.title("Technical Assessment")
        
        if "question_number" not in st.session_state:
            st.session_state.question_number = 0
            st.session_state.answers = []
        
        if st.session_state.question_number < 15:
            q_number = st.session_state.question_number + 1
            question = generate_technical_questions(tech_stack, q_number)
            st.subheader(f"Question {q_number}")
            st.write(question)
            
            answer = st.text_area(
                "Your Answer:",
                key=f"answer_{q_number}",
                height=150,
                placeholder="Type your answer here..."
            )
            
            if st.button("Submit", key=f"submit_{q_number}"):
                if answer.strip():
                    st.session_state.answers.append(answer.strip())
                    st.session_state.question_number += 1
                    st.rerun()
                else:
                    st.warning("Please provide an answer before submitting.")
        else:
            st.success("Congratulations! You have completed all the questions.")
            st.subheader("Your Answers:")
            for i, ans in enumerate(st.session_state.answers, 1):
                st.write(f"Q{i}: {ans}")
    else:
        st.title("Select an option")

        st.write("Please choose one of the options above to proceed.")












