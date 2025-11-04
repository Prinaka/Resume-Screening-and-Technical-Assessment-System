import re
import PyPDF2
import json
from .llm import call_kimi


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
    - Tech Stack (include all languages, frameworks, tools, software, libraries mentioned in the resume. Also extract skills used in internships/projects) 
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
    - Years of Experience (give numerical  result)
    - Desired Position(s) 
    - Tech Stack (include all languages, frameworks, tools, software, libraries mentioned in the job description) 
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
