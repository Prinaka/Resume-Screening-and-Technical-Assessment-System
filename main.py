import re
import PyPDF2
import os
from openai import OpenAI
from groq import Groq
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer, util
from rapidfuzz import process
import textstat
import json
import streamlit as st

sbert_model = SentenceTransformer("all-MiniLM-L6-v2")

load_dotenv()

SKILL_NORMALIZER = {
    "js": "JavaScript",
    "py": "Python",
    "reactjs": "React",
    "tf": "TensorFlow",
    "Microsoft Azure": "Azure",
    "Amazon We Services": "AWS",
    "Google Cloud Platform": "GCP",
    "MySOL": "SQL",
    "SQL Server": "SQL"}

ACTION_VERBS = ["developed", "led", "implemented", "designed", "improved",
                "analyzed", "managed", "created", "built", "optimized", "implemented"]

IMPACT_WORDS = ["improved", "increased", "reduced", "achieved", "delivered", "saved", "optimized"]
RESPONSIBLE_WORDS = ["responsible", "assisted", "helped", "supported", "spearheaded"]

SOFT_SKILLS = ["communication", "teamwork", "leadership", "collaboration",
               "adaptability", "problem solving", "creativity"]


def call_kimi(prompt):
    client = Groq(api_key=os.environ["GROQ_API"])
    response = client.chat.completions.create(
        model="moonshotai/kimi-k2-instruct-0905",
        messages=[{"role": "user","content": prompt}],
        temperature=0.4,
        )
    return response.choices[0].message.content


def call_llama(prompt):
    client = OpenAI(
        base_url="https://api.groq.com/openai/v1",
        api_key=os.environ["GROQ_API"],
        )
    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[{"role": "user","content": prompt}],
        max_tokens=512,
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
    You are an expert Resume Parser. Extract only the following details correctly from this resume text (each in single line):
    - Full Name 
    - Email Address 
    - Phone Number 
    - Years of Experience (give numerical  result)
    - Desired Position(s) 
    - Current Location 
    - Tech Stack (include all languages, frameworks, tools, software, libraries mentioned in the resume) 
    Resume Text:
    {text}
    Answer only the above points each in single sentence. Do not write additional statements. Whole output should be JSON dictionary.
    """
    raw_output = call_kimi(prompt)

    try:
        parsed = json.loads(raw_output)
    except json.JSONDecodeError:
        cleaned = raw_output.strip("` \n").replace("json\n", "")
        parsed = json.loads(cleaned)

    return parsed

def extract_jd_skills(text):
    prompt = f"""
    Extract only the following details correctly from this job description (each in single line):
    - Years of Experience 
    - Desired Position(s) 
    - Current Location 
    - Tech Stack (include all languages, frameworks, tools, software, libraries mentioned in the resume) 
    Job description Text:
    {text}
    Answer only the above points each in single sentence. Do not write additional statements. Whole output should be JSON dictionary.
    """
    raw_output = call_kimi(prompt)

    try:
        parsed = json.loads(raw_output)
    except json.JSONDecodeError:
        cleaned = raw_output.strip("` \n").replace("json\n", "")
        parsed = json.loads(cleaned)

    return parsed

def check_formatting_issues(text):
    issues = []
    if "education" not in text.lower():
        issues.append("Missing Education section")
    ex = ["experience", "internships", "projects", "work", "research"]
    i=0
    while i<=len(ex):
        if i<len(ex) and ex[i] in text.lower():
            break
        elif i<len(ex):
            i+=1
        else:
            issues.append("Missing Experience section")
    if len(text.split()) < 200:
        issues.append("Resume too short (<200 words)")
    return issues

def readability_score(text):
    score = textstat.flesch_reading_ease(text)
    grade = textstat.flesch_kincaid_grade(text)
    return {"ease": score, "grade": grade}


def normalize_skills(extracted_skills):
    normalized = []
    for skill in extracted_skills:
        key = skill.lower()
        if key in SKILL_NORMALIZER:
            normalized.append(SKILL_NORMALIZER[key])
        else:
            # fuzzy match against known skills
            match, score, _ = process.extractOne(key, SKILL_NORMALIZER.keys())
            if score > 80:
                normalized.append(SKILL_NORMALIZER[match])
            else:
                normalized.append(skill)  
    return list(set(normalized))


def semantic_skill_match(resume_skills, jd_skills, threshold=0.6):
    resume_emb = sbert_model.encode(resume_skills, convert_to_tensor=True)
    jd_emb = sbert_model.encode(jd_skills, convert_to_tensor=True)

    similarity_matrix = util.cos_sim(resume_emb, jd_emb)
    matched, missing = [], []
    for i, jd_skill in enumerate(jd_skills):
        max_sim = similarity_matrix[:, i].max().item()
        if max_sim >= threshold:
            matched.append(jd_skill)
        else:
            missing.append(jd_skill)
    return matched, missing


def score_clarity(text):
    count_verbs = sum(text.lower().count(v) for v in ACTION_VERBS)
    count_numbers = len([w for w in text.split() if any(c.isdigit() for c in w)])
    if count_verbs > 10 and count_numbers > 5:
        return 10
    elif count_verbs > 5:
        return 7
    else:
        return 4


def score_impact(text):
    impact = sum(text.lower().count(w) for w in IMPACT_WORDS)
    weak = sum(text.lower().count(w) for w in RESPONSIBLE_WORDS)
    return min(10, (impact * 2 - weak)) if impact > 0 else 5


def score_soft_skills(text):
    count = sum(text.lower().count(s) for s in SOFT_SKILLS)
    if count >= 5:
        return 10
    elif count >= 3:
        return 7
    elif count >= 1:
        return 5
    else:
        return 3
    
def calculate_soft_factors(text):
    clarity = score_clarity(text)
    impact = score_impact(text)
    softskills = score_soft_skills(text)

    total = (clarity + impact + softskills) / 3
    return round(total, 2), {
        "Clarity": clarity,
        "Impact vs Responsibility": impact,
        "Soft Skills": softskills,
    }

def calculate_ats_score(resume_text, jd_text, text):
    resume_skills = normalize_skills(resume_text["Tech Stack"].split(", "))
    jd_skills = normalize_skills(jd_text["Tech Stack"].split(", "))

    matched, missing = semantic_skill_match(resume_skills, jd_skills)
    skill_score = (len(matched) / len(jd_skills)) * 50
    
    cand_exp = float(resume_text["Years of Experience"])
    jd_exp = float(jd_text["Years of Experience"])
    if jd_exp!=0:
        exp_score = min(1, (cand_exp / jd_exp)) * 20
    else:
        exp_score = cand_exp*20
    
    missing_penalty = (len(missing) / len(jd_skills)) * 10
    
    issues = check_formatting_issues(text)
    ease = readability_score(text)["ease"]
    if len(issues) <= 20 and ease <= 50:
        format_score = ((50-ease)/50 - (len(issues)/20)) * 10
    elif len(issues) <= 20:
        format_score = - (len(issues)/20) * 10
    elif ease <= 50:
        format_score = ((50-ease)/50) * 10
    else:
        format_score = 2

    soft_score, soft_details = calculate_soft_factors(text)
    ats_score = skill_score + exp_score + format_score - missing_penalty + soft_score*0.1
    return round(ats_score, 2)


def generate_resume_review(candidate_info, jd_text):
    prompt = f"""
    You are an experienced Technical Human Resource Manager recruiting fresh graduates. 
    Your task is to review the provided resume {candidate_info} against the job description {jd_text}. 
    Please share whether the candidate's profile aligns with the role. Fresh graduates ny have internship experiences usually.
    Output should only have 
    -strengths 
    -weaknesses 
    -recommendations in relation to the specified job requirements.
    """
    return call_llama(prompt)


def generate_technical_questions(tech_stack, q_number):
    prompt = f"""
    You are an expert technical interviewer. This is question number {q_number}.
    Ask one technical, concise interview question about the given tech stack: {tech_stack}.
    Wait for the answer before moving to the next question.
    Do not repeat "first question", "second question", or similar intros — just directly ask the question.
    """
    return call_llama(prompt)


def run_assessment(mode, tech_stack, prefix="answer", jd_required=False):
    st.title(f"Technical Assessment on {'Resume' if mode=='technical1' else 'JD'}")
    st.write("Navigation is not allowed among questions.")

    if jd_required and "jd_text" not in st.session_state:
        jd = st.text_area("Job Description", key=f"jd_{mode}", height=200, placeholder="Paste the job description here...")
        if st.button("Start Assessment", key=f"start_{mode}"):
            if jd.strip():
                jd_text = extract_jd_skills(jd)
                st.session_state.tech_stack = jd_text.get("Tech Stack", "Python")
                st.session_state.jd_text = jd
                st.session_state.question_number = 0
                st.session_state.answers = []
                st.rerun()
            else:
                st.warning("Please enter a Job Description before starting the assessment.")
        return 

    if "question_number" not in st.session_state or st.session_state.question_number is None:
        st.session_state.question_number = 0
        st.session_state.answers = []

    if st.session_state.question_number < 15:
        q_number = st.session_state.question_number + 1
        question = generate_technical_questions(st.session_state.get("tech_stack", tech_stack), q_number)

        st.subheader(f"Question {q_number} of 15")
        st.write(question)

        answer = st.text_area(
            "Your Answer:",
            key=f"{prefix}_{q_number}",
            height=150,
            placeholder="Type your answer here..."
        )

        if st.button("Submit", key=f"submit_{prefix}_{q_number}"):
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

        col1, col2 = st.columns(2)
        with col1:
            if st.button("Retake Assessment", key=f"retake_{mode}"):
                st.session_state.question_number = 0
                st.session_state.answers = []
                st.rerun()

        with col2:
            if st.button("⬅ Exit to Menu", key=f"exit_{mode}"):
                st.session_state.view_mode = "initial"
                st.session_state.question_number = None
                st.session_state.answers = []
                st.rerun()
