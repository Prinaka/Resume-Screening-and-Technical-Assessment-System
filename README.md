# Resume Screening and Technical Assessment System

Live Demo : https://resume-screening-and-technical-assessment-system.streamlit.app

A Streamlit-based Hiring Assistant that leverages:
* Kimi K2 model to parse resumes, extract relevant details from the resume and job description.
* LLaMA 3.1 to generate technical questions based on the candidate's tech stack, and evaluate answers in real-time.
This tool is ideal for assisting candidates in the initial stages of technical recruitment.

**Key Features:**

* PDF Resume Upload: Accepts candidate resumes in PDF format.
* Resume Parsing: Extracts key candidate details using Kimi K2.
  - Full Name
  - Email Address
  - Phone Number
  - Years of Experience
  - Desired Position(s)
  - Current Location
  - Tech Stack (languages, frameworks, libraries, tools)
* Interactive Workflow: Confirms candidate information before proceeding further.
* ATS: Generates ATS score based on skills matched/missing, candidate experience, formatting issues and readability.
* Technical Question Generation: Generates 5 relevant technical questions based on the candidate's/job's tech stack
* Answer Evaluation: Evaluates candidate answers for relevance using LLaMA 3 and provides scores and feedback at end of the assessment. The responses can be downloaded as pdf by the candidate.

**Installation:**

1. Clone the repository:
```
gh repo clone Prinaka/Resume-Screening-and-Technical-Assessment-System
cd resume-screening-chatbot
```

2. Create and activate a virtual environment (optional but recommended):
```
python -m venv venv
source venv/bin/activate  # Linux/macOS
venv\Scripts\activate     # Windows
```

3. Install dependencies:
```
pip install -r requirements.txt
```

**Usage:**

Run the Streamlit app:
```
streamlit run app.py
```

**License:**

This project is licensed under the MIT License – see the [LICENSE](LICENSE) file for details.
