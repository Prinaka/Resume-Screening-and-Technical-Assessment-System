import streamlit as st
import re
import PyPDF2
import boto3
import json


bedrock = boto3.client("bedrock-runtime", region_name="us-east-1")


def call_llama(prompt):
    response = bedrock.invoke_model(
        modelId="meta.llama3-8b-instruct-v1:0",
        body=json.dumps({
            "prompt": prompt,
            "max_gen_len": 512,
            "temperature": 0.7,
            "top_p": 0.9
        })
    )
    result = json.loads(response["body"].read())
    return result["generation"]


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


def generate_technical_questions(tech_stack):
    prompt = f"""
    Based on {tech_stack}, generate only 10 technical interview questions to assess their proficiency.
    Example format:
    "question 1 : What is nltk library used for?",
    "question 2 : What is the purpose of the matplotlib.pyplot.show() function?",
    "question 3 : What is the difference between scikit-learn's LinearRegression and LogisticRegression classes?",
    "question 4 : What is the purpose of the tf.data.Dataset class in TensorFlow?",
    "question 5 : What is the difference between pandas.DataFrame and pandas.Series"
    """
    return call_llama(prompt)


def clean_ques(qna):
    qna = re.sub(r"^\s*[-*]\s*", "", qna, flags=re.MULTILINE)
    qna = re.sub(r"[^a-zA-Z0-9\s@.?+()_=':]", "", qna, flags=re.MULTILINE)
    qna = qna.splitlines()
    key = "QUESTIONS ="
    start_idx = 0
    for line in qna:
        if key in line.strip() or key.lower() in line.strip() or key.title() in line.strip():
            start_idx = qna.index(line)+1
            break
    candidate_qna = []
    for i in range(10):
        ques = re.sub(r"^\d+.", "", qna[start_idx].strip())
        candidate_qna.append(ques.strip())
        start_idx += 1
    return candidate_qna


def is_answer_relevant(question, user_answer):
    prompt = f"""
    You are a strict evaluator for a technical quiz. Your task is to check if the candidate’s answer is relevant.
    Question: "{question}"
    Candidate's answer: "{user_answer}"
    Output format (must be valid JSON only, nothing else):
    {{
    "result": "Relevant" | "Not Relevant"
    }}
    Rules:
    - If the answer is relevant → respond only with: Relevant
    - If the answer is irrelevant and nonsense → respond only with: Not Relevant
    - Do not add punctuation, emojis, or explanations
    """
    raw_response = call_llama(prompt).strip()
    try:
        parsed = json.loads(raw_response)
        result = parsed.get("result", "Not Relevant")
    except json.JSONDecodeError:
        result = "Relevant"  
    return result


def main():
    st.title("Resume Screening Chatbot")
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
            st.success("Thank you! Your details are confirmed.")
            tech_stack = candidate_info["Tech Stack"]
            if tech_stack == None:
                tech_stack = "Python"
            st.subheader("Technical Questions Based on Your Tech Stack")
            qna = generate_technical_questions(tech_stack)
            questions = clean_ques(qna)

            if "current_q" not in st.session_state:
                st.session_state.current_q = 0
            if "answers" not in st.session_state:
                st.session_state.answers = {}

            if st.session_state.current_q < len(questions):
                q = questions[st.session_state.current_q]
                st.write(q)
                
                user_input = st.text_input("Answer here:", key=f"answer_{st.session_state.current_q}")
                
                if user_input: 
                    if is_answer_relevant(q, user_input) == "Relevant":
                        st.success("Moving to next question.")
                        st.session_state.answers[st.session_state.current_q] = user_input
                        st.session_state.current_q += 1
                        st.rerun()
                    else:
                        st.error("Incorrect. Please try again.")
            else:
                st.write("Congratulations! You have completed all the questions.")
        elif confirm == "No":
            st.warning("Please update your resume or enter corrections manually.")


if __name__ == "__main__":
    main()

