import re
import PyPDF2
import os
from openai import OpenAI
from huggingface_hub import login
from dotenv import load_dotenv
from transformers import AutoTokenizer, AutoModelForCausalLM
import torch

load_dotenv()

login(token=st.secrets["HF_TOKEN"])

model_id = "meta-llama/Llama-3.1-8b-instruct"
tokenizer = AutoTokenizer.from_pretrained(model_id)
model = AutoModelForCausalLM.from_pretrained(
    model_id,
    device_map="auto",       
    torch_dtype=torch.float16,
    load_in_4bit=True        
)

def call_llama(prompt):
    inputs = tokenizer.apply_chat_template(
        prompt,
        add_generation_prompt=True,
        tokenize=True,
        return_dict=True,
        return_tensors="pt",
    ).to(model.device)
    outputs = model.generate(
        **inputs,
        max_new_tokens=512,
        temperature=0.7,
        top_p=0.9
    )
    return tokenizer.decode(outputs[0][inputs["input_ids"].shape[-1]:], skip_special_tokens=True)


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
    return call_llama(prompt)


