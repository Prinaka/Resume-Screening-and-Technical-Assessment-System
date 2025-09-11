import re
import PyPDF2
import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

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


def call_llama2(prompt):
    client = OpenAI(
        base_url="https://api.groq.com/openai/v1",
        api_key=os.environ["GROQ_API"],
        )
    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[{"role": "user","content": prompt}],
        max_tokens=128,
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
    - Years of Experience 
    - Desired Position(s) 
    - Current Location 
    - Tech Stack (include languages, frameworks, tools, software, libraries) 
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


def generate_ats_score(candidate_info, jd_text):
    prompt = f"""
    You are a skilled ATS (Applicant Tracking System) scanner with a deep understanding of data science and ATS functionality. 
    Your task is to evaluate the resume {candidate_info} against the provided job description {jd_text}. 
    Give me the percentage of match between the resume and job description. Do not make extra comments.
    """
    return call_llama(prompt)

def generate_resume_review(candidate_info, jd_text):
    prompt = f"""
    You are an experienced Technical Human Resource Manager recruiting fresh graduates. 
    Your task is to review the provided resume {candidate_info} against the job description {jd_text}. 
    Please share your professional evaluation on whether the candidate's profile aligns with the role.
    Output should only have strengths, weaknesses and recommendations in relation to the specified job requirements.
    """
    return call_llama(prompt)

def generate_technical_questions(tech_stack, q_number):
    prompt = f"""
    You are an expert technical interviewer. This is question number {q_number}.
    Ask one technical, concise interview question about the given tech stack: {tech_stack}.
    Wait for the answer before moving to the next question.
    Do not repeat "first question", "second question", or similar intros — just directly ask the question.
    """
    return call_llama2(prompt)









