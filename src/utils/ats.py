from rapidfuzz import process
import textstat
from sentence_transformers import SentenceTransformer, util
from src.llm.llama_client import call_llama
from src.helpers.visuals import make_donut, bar_chart, comparison_chart
import streamlit as st
import pandas as pd
from pathlib import Path
import json

sbert_model = SentenceTransformer("all-MiniLM-L6-v2")


data_path = Path(__file__).resolve().parents[2] / "data" / "skill_normalizer.json"
with open(data_path, "r") as f:
    SKILL_NORMALIZER = json.load(f)

data_path = Path(__file__).resolve().parents[2] / "data" / "verbs.json"
with open(data_path, "r") as f:
    VERBS = json.load(f)
ACTION_VERBS = VERBS['ACTION_VERBS']
IMPACT_WORDS = VERBS['IMPACT_WORDS']
RESPONSIBLE_WORDS = VERBS['RESPONSIBLE_WORDS']
SOFT_SKILLS = VERBS['SOFT_SKILLS']


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
        key = skill.lower().strip()
        found = False

        for canonical, aliases in SKILL_NORMALIZER.items():
            if key == canonical.lower() or key in [a.lower() for a in aliases]:
                normalized.append(canonical)
                found = True
                break

        if not found:
            all_aliases = {alias.lower(): canonical for canonical, aliases in SKILL_NORMALIZER.items() for alias in aliases}
            match, score, _ = process.extractOne(key, all_aliases.keys())
            if score > 80:
                normalized.append(all_aliases[match])
            else:
                normalized.append(skill)

    normalized_unique = list(dict.fromkeys(normalized))
    return normalized_unique


def semantic_skill_match(resume_skills, jd_skills, threshold=0.6):
    resume_emb = sbert_model.encode(resume_skills, convert_to_tensor=True)
    jd_emb = sbert_model.encode(jd_skills, convert_to_tensor=True)

    similarity_matrix = util.cos_sim(resume_emb, jd_emb)
    matched, missing, extra = [], [], []
    for i, jd_skill in enumerate(jd_skills):
        max_sim = similarity_matrix[:, i].max().item()
        if max_sim >= threshold:
            matched.append(jd_skill)
        else:
            missing.append(jd_skill)
    extra = [skill for skill in resume_skills if skill not in matched]
    return matched, missing, extra


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

    total = (clarity + impact + softskills) / 2
    return round(total, 2), {
        "Clarity": clarity,
        "Impact vs Responsibility": impact,
        "Soft Skills": softskills,
    }


def calculate_ats_score(resume_text, jd_text, text):
    resume_skills = normalize_skills(resume_text["Tech Stack"].split(", "))
    jd_skills = normalize_skills(jd_text["Tech Stack"].split(", "))

    matched, missing, extra = semantic_skill_match(resume_skills, jd_skills)
    matched_ratio = (len(matched) / len(jd_skills))
    skill_score = min(1, matched_ratio) * 50
    
    cand_exp = float(resume_text["Years of Experience"])
    jd_exp = float(jd_text["Years of Experience"])
    if jd_exp==0:
        exp_score = 25
    elif cand_exp > jd_exp:
        exp_score = min(1, 0.8+(cand_exp - jd_exp)*0.05) * 25
    else:
        exp_score = (cand_exp / jd_exp) * 25
    
    missing_penalty = (len(missing) / len(jd_skills)) * 5
    
    issues = check_formatting_issues(text)
    ease = readability_score(text)["ease"]
    word_count = len(text.split())

    format_score = 5
    if ease <= 50:
        format_score += 3
    if word_count >= 200:
        format_score += 2
    if len(issues) > 5 and len(issues) <= 10:
        format_score -= 2.5
    elif len(issues) > 10:
        format_score -= 5

    soft_score, soft_details = calculate_soft_factors(text)
    ats_score = skill_score + exp_score + format_score - missing_penalty + soft_score
    return round(ats_score, 2), {
        "Skill Match": round(skill_score, 2),
        "Experience Match": round(exp_score, 2),
        "Formatting & Readability": round(format_score, 2),
        "Soft Skills & Clarity": round(soft_score, 2),
        "Soft Skill Details": soft_details,
        "Formatting Issues": issues,
        "Matched Skills": matched,
        "Missing Skills": missing,
        "Extra Skills": extra
    }


def generate_resume_review(candidate_info, jd_text):
    prompt = f"""
    You are an experienced Technical Human Resource Manager recruiting fresh graduates. 
    Your task is to review the provided resume {candidate_info} against the job description {jd_text}. 
    Keep in mind fresh graduates may have internship experiences usually.
    Output should only have 
    -strengths 
    -weaknesses 
    -recommendations in relation to the specified job requirements.
    """
    return call_llama(prompt)


def ats_dashboard(ats, info, resume_text, jd):
    skill_match = (info["Skill Match"]/50)*100
    exp_match = (info["Experience Match"]/25)*100
    format_score = (info["Formatting & Readability"]/10)*100
    soft_score = (info["Soft Skills & Clarity"]/15)*100
    soft_details = info["Soft Skill Details"]
    issues = info["Formatting Issues"]
    matched = info["Matched Skills"]
    missing = info["Missing Skills"]
    extra = info["Extra Skills"]

    st.title("📊 Resume Analysis Dashboard")

    col1, col2 = st.columns([1, 2])
    with col1:
        st.altair_chart(make_donut(ats, "Percentage Match"), use_container_width=False)
        verdict = "✅ Strong Fit" if ats >= 70 else "⚠️ Partial Match" if ats >= 50 else "❌ Needs Improvement"
        st.subheader(verdict)

    with col2:
        scores_df = pd.DataFrame({
            "Component": ["Skill Match", "Experience Match", "Soft Skills", "Formatting"],
            "Score": [skill_match, exp_match, soft_score, format_score]
        })
        st.altair_chart(bar_chart(scores_df,"Score:Q","Component:N"), use_container_width=True)
        
        st.write(f"**Skill match score:** {skill_match:.2f} %")
        st.write(f"**Experience score:** {exp_match:.2f} %")
        st.write(f"**Format score:** {format_score:.2f} %")
        st.write(f"**Soft skills & clarity score:** {soft_score:.2f} %")

    st.divider()

    st.header("Skills Analysis")

    col1, col2 = st.columns([2,1], gap="large")
    with col1:
        st.subheader("Matched Skills")
        if matched:
            st.markdown(" ".join([f"<code style='color:green; background-color:#eaffea; padding:2px 4px; border-radius:4px;'>{skill}</code>" for skill in matched]),
                        unsafe_allow_html=True)
        else:
            st.info("No skills matched.")

        st.subheader("Missing Skills")
        if missing:
            st.markdown(" ".join([f"<code style='color:red; background-color:#ffe6e6; padding:2px 4px; border-radius:4px;'>{skill}</code>" for skill in missing]),
                        unsafe_allow_html=True)
        else:
            st.success("No missing skills.")

        if extra:
            st.subheader("Additional Skills")
            st.markdown(" ".join([f"<code style='color:blue; background-color:#e6f7ff; padding:2px 4px; border-radius:4px;'>{skill}</code>" for skill in extra]),
                        unsafe_allow_html=True)

    with col2:
        skill_data = pd.DataFrame({
        "Category": ["Matched Skills", "Missing Skills"],
        "Count": [len(matched), len(missing)]
        })
        st.altair_chart(comparison_chart(skill_data), use_container_width=True)
        st.text(f"Total required skills: {len(matched)+len(missing)}\nMatched: {len(matched)}\nMissing: {len(missing)}")


    st.divider()

    st.header("Readability & Formatting")
    st.write("Detected soft skills and how well they're conveyed:")

    for skill, detail in soft_details.items():
        st.write(f"- **{skill}**: {detail}/10")

    if issues:
        st.write("Some formatting issues were detected:")
        for issue in issues:
            st.write(f"- **{issue}**")
    else:
        st.success("No major formatting issues found ✅")

    st.divider()

    st.header("Review Summary")
    st.write(generate_resume_review(resume_text, jd))
