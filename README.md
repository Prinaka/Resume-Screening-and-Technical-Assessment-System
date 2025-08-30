# Hiring-Assistant-

A Streamlit-based Hiring Assistant Chatbot that leverages AWS Bedrock’s LLaMA 3 model to parse resumes, extract candidate information, generate technical questions based on the candidate's tech stack, and evaluate answers in real-time. This tool is ideal for automating the initial stages of technical recruitment.

Key Features:
* PDF Resume Upload: Accepts candidate resumes in PDF format.
* Resume Parsing: Extracts key candidate details:
  - Full Name
  - Email Address
  - Phone Number
  - Years of Experience
  - Desired Position(s)
  - Current Location
  - Tech Stack (languages, frameworks, libraries, tools)
* Technical Question Generation: Generates 10 relevant technical questions based on the candidate's tech stack.
* Answer Evaluation: Evaluates candidate answers for relevance using LLaMA 3 and provides immediate feedback.
* Interactive Workflow: Confirms candidate information before proceeding to the technical quiz.

Installation

1. Clone the repository:
git clone https://github.com/yourusername/resume-screening-chatbot.git
cd resume-screening-chatbot

2. Create and activate a virtual environment (optional but recommended):
python -m venv venv
source venv/bin/activate  # Linux/macOS
venv\Scripts\activate     # Windows


3. Install dependencies:
pip install -r requirements.txt


4. Configure AWS credentials (for Bedrock access):
aws configure
# Provide AWS Access Key, Secret Key, and default region (us-east-1)

Usage

Run the Streamlit app:

streamlit run app.py
