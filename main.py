import streamlit as st
import re
import PyPDF2
import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

def call_llama(prompt):
    client = OpenAI(
        base_url="https://router.huggingface.co/v1",
        api_key=os.environ["HF_TOKEN"],
        )
    response = client.chat.completions.create(
        model="meta-llama/Llama-3.1-8B-Instruct",
        messages=[{"role": "user","content": prompt}],
        )
    return response.choices[0].message.content

def extract_text_from_pdf(uploaded_file):
    pdf_reader = PyPDF2.PdfReader(uploaded_file)
    text = ""
    for page in pdf_reader.pages:
        page_content = page.extract_text() + "\n"
        clean_text =  re.sub(r"^\s*[-*]\s*", "", page_content)
        clean_text = re.sub(r"[^a-zA-Z0-9\s@,.+]", "", clean_text)
        text += clean_text
    return text


def extract_candidate_info(text):
    prompt = f"""
    You are an expert Resume Parser. Extract only the following details from this resume text (each in single line):
    - Full Name 
    - Email Address 
    - Phone Number 
    - Years of Experience 
    - Desired Position(s) 
    - Current Location 
    - Tech Stack (include languages, frameworks, tools, software, libraries only) 
    Resume Text:
    {text}
    Answer only the above points each in single line. Do not write additional statements.
    """
    return call_llama(prompt)


def clean_info(info):
    info = re.sub(r"^\s*[-*]\s*", "", info, flags=re.MULTILINE)
    info = re.sub(r"[^a-zA-Z0-9\s@,.+]", "", info, flags=re.MULTILINE)
    info = info.splitlines()
    candidate_info = {}
    keys = ["Full Name",
            "Email Address",
            "Phone Number",
            "Years of Experience",
            "Desired Position(s)",
            "Current Location",
            "Tech Stack"]
    for key in keys:
        for line in info:
            if key in line or key.lower() in line or key.strip() in line or key.lower().strip() in line:
                start_idx = line.find(key)+len(key)
                value = line[start_idx:len(line)]
                if value.lstrip() != '' or value.lstrip() != ' ':
                    candidate_info[key] = value.lstrip()
                    break
    return candidate_info


def generate_technical_questions(tech_stack, q_number):
    prompt = f"""
    You are an expert technical interviewer. This is question number {q_number}.
    Ask one technical, concise interview question about the given tech stack: {tech_stack}.
    Wait for the answer before moving to the next question.
    Do not repeat "first question", "second question", or similar intros — just directly ask the question.
    """
    return call_llama(prompt)


def main():
    st.title("Resume Screening and Technical Assessment System")

    if "confirmed" not in st.session_state:
        st.session_state.confirmed = False

    if not st.session_state.confirmed:
        st.write("Hello! I am the Hiring Assistant at TalentScout. Please upload your resume below to proceed.")
        uploaded_file = st.file_uploader("Upload your Resume (PDF)", type="pdf")

        if uploaded_file is not None:
            text = extract_text_from_pdf(uploaded_file)
            info = extract_candidate_info(text)
            candidate_info = clean_info(info)

            st.subheader("Candidate Information")
            for key in candidate_info:
                st.write(f"{key} : {candidate_info[key]}")

            confirm = st.radio("Do you confirm these details are correct?", ["Yes", "No"], index=None)

            if confirm == "Yes":
                st.session_state.confirmed = True
                st.session_state.candidate_info = candidate_info
                st.session_state.tech_stack = candidate_info.get("Tech Stack", "Python")
                st.success("Thank you! Your details are confirmed.")
                st.rerun()

            elif confirm == "No":
                st.warning("Please update your resume or enter corrections manually.")

    else:
        tech_stack = st.session_state.tech_stack

        st.subheader("Technical Questions Based on Your Tech Stack")

        if "question_number" not in st.session_state:
            st.session_state.question_number = 0
        if "answers" not in st.session_state:
            st.session_state.answers = []

        if st.session_state.question_number < 15:
            q_number = st.session_state.question_number + 1
            question = generate_technical_questions(tech_stack, q_number)
            st.write(f"Q{q_number}: {question}")

            answer = st.text_area(
                "Answer:",
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
            st.success("Congratulations! You have completed all the questions.")
            st.write("Your Answers:")
            for i, ans in enumerate(st.session_state.answers, 1):
                st.write(f"Q{i}: {ans}")


if __name__ == "__main__":
    main()
