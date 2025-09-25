from rapidfuzz import process
import textstat
from sentence_transformers import SentenceTransformer, util
from .llm import call_llama


sbert_model = SentenceTransformer("all-MiniLM-L6-v2")


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
                "analyzed", "managed", "created", "built", "optimized", "engineered",
                "launched", "collaborated", "initiated", "spearheaded", "deployed",
                "assembled", "calculated", "computed", "configured", "devised", "fabricated",
                "maintained", "operated", "pinpointed", "programmed", "remodeled",
                "repaired"]

IMPACT_WORDS = ["improved", "increased", "reduced", "achieved", "delivered",
                "saved", "optimised", "managed", "generated", "boosted", "enhanced",
                "accelerated", "accomplished", "attained", "completed", "conceived",
                "convinced", "discovered", "doubled", "effected", "eliminated", "expanded",
                "expedited", "founded", "initiated", "innovated", "introduced", "invented",
                "launched", "mastered", "originated", "overcame", "overhauled", "pioneered",
                "resolved", "revitalized", "spearheaded", "strengthened", "transformed", "upgraded"]

RESPONSIBLE_WORDS = ["responsible", "assisted", "helped", "supported", "spearheaded"]

SOFT_SKILLS = ["communication", "teamwork", "leadership", "collaboration",
               "adaptability", "problem solving", "creativity", "work ethic",
               "time management", "critical thinking", "interpersonal skills",
               "conflict resolution", "decision making", "empathy", "flexibility"
               "negotiation", "organization", "patience", "resilience", "self-motivation",
               "stress management", "active listening", "public speaking", "relationship building"]


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
    skill_score = (len(matched) / len(jd_skills)) * 60
    
    cand_exp = float(resume_text["Years of Experience"])
    jd_exp = float(jd_text["Years of Experience"])
    if jd_exp!=0:
        exp_score = min(1, (cand_exp / jd_exp)) * 20
    else:
        exp_score = cand_exp*20
    
    missing_penalty = (len(missing) / len(jd_skills)) * 5
    
    issues = check_formatting_issues(text)
    ease = readability_score(text)["ease"]
    if len(issues) <= 20 and ease <= 50:
        format_score = ((50-ease)/50 - (len(issues)/20)) * 5
    elif len(issues) <= 20:
        format_score = - (len(issues)/20) * 5
    elif ease <= 50:
        format_score = ((50-ease)/50) * 5
    else:
        format_score = 2

    soft_score, soft_details = calculate_soft_factors(text)
    ats_score = skill_score + exp_score + format_score - missing_penalty + soft_score*0.1
    return round(ats_score, 2)


def generate_resume_review(candidate_info, jd_text):
    prompt = f"""
    You are an experienced Technical Human Resource Manager recruiting fresh graduates. 
    Your task is to review the provided resume {candidate_info} against the job description {jd_text}. 
    Please share whether the candidate's profile aligns with the role. Keep in mind fresh graduates may have internship experiences usually.
    Output should only have 
    -strengths 
    -weaknesses 
    -recommendations in relation to the specified job requirements.
    """
    return call_llama(prompt)
