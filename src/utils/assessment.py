import json
import streamlit as st
from src.llm.llama_client import call_llama
from src.helpers.pdf_report import generate_pdf_report


def generate_technical_questions(tech_stack, q_number):
    prompt = f"""
    You are an expert technical interviewer. This is question number {q_number}.
    Ask one technical short answer interview question about the given tech stack: {tech_stack} to test understanding.
    Wait for the answer before moving to the next question. Do not ask coding questions.
    Output only the question without any additional text.
    """
    return call_llama(prompt)


def grade_open_answer(question, answer):
    prompt = f"""You are an expert technical interviewer.
    Question: {question}
    Candidate Answer: {answer}

    Task:
    1. Evaluate if candidate answered correctly. Give partial credit for partially correct answers.
    2. Give no credit for incorrect or irrelevant answers.
    3. Give a score from 0–100 considering it be an interview setting.
    4. Provide 2–3 sentences of feedback about the answer, mentioning what was good and what could be improved.

    Output JSON only:
    {{
      "score": <int 0-100>,
      "feedback": "..."
    }}
    """
    return call_llama(prompt)


def run_assessment(mode, tech_stack, prefix="answer"):
    st.title(f"Technical Assessment on {'Resume' if mode=='technical1' else 'JD'}")

    if "question_number" not in st.session_state or st.session_state.question_number is None:
        st.session_state.question_number = 0
        st.session_state.questions = []
        st.session_state.answers = []
        st.session_state.grades = []
    
    total = 5

    if st.session_state.question_number < total:
        q_number = st.session_state.question_number + 1
        st.subheader(f"Question {q_number} of {total}")

        if len(st.session_state.questions) < q_number:
            question = generate_technical_questions(st.session_state.get("tech_stack", tech_stack), q_number)
            st.session_state.questions.append(question)
        question = st.session_state.questions[q_number - 1]
        st.write(question)

        answer = st.text_area(
                "Your Answer:",
                key=f"{prefix}_{q_number}",
                height=150,
                placeholder="Type your answer here..."
                )

        if st.button("Submit", key=f"submit_{prefix}_{q_number}"):
            if answer:
                st.session_state.answers.append(answer.strip())
                grade = grade_open_answer(question, answer.strip())
                st.session_state.grades.append(grade)
                st.session_state.question_number += 1
                st.rerun()
            else:
                st.warning("Please provide an answer before submitting.")

    else:
        st.success("Congratulations! You have completed all the questions.")
        st.subheader("Your Scores:")

        for i, (ques, ans, grade) in enumerate(zip(st.session_state.questions, st.session_state.answers, st.session_state.grades), 1):
            data = json.loads(grade)
            st.write(f"""
            **Q{i} Score:** {data["score"]}  
            """)
            with st.expander(f"Your Answer & Feedback"):
                st.write(f"**Answer:**\n\n{ans}")
                st.write(f"**Feedback:** {data['feedback']}")
                

        total_score = sum(json.loads(g)["score"] for g in st.session_state.grades) / len(st.session_state.grades) 
        st.subheader(f"""Total Percentage: **{round(total_score,2)}%**""")
        pdf_data = generate_pdf_report(st.session_state.questions, st.session_state.answers, st.session_state.grades)

        col1, col2, col3 = st.columns(3, gap="large")
        with col1:
            if st.button("Retake Assessment", key=f"retake_{mode}", use_container_width=True):
                st.session_state.question_number = 0
                st.session_state.answers = []
                st.session_state.grades = []
                st.rerun()

        with col2:
            st.download_button("Download Report as PDF",
                               data=pdf_data,
                               file_name="assessment_report.pdf",
                               mime="application/pdf", 
                               key=f"download_{mode}", 
                               use_container_width=True)

        with col3:
            if st.button("Exit to Menu", key=f"exit_{mode}", use_container_width=True):
                st.session_state.view_mode = mode
                st.session_state.question_number = None
                st.session_state.answers = []
                st.session_state.grades = []
                st.rerun()