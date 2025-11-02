import json
from fpdf import FPDF


def generate_pdf_report(questions, answers, grades):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", size=12)

    pdf.cell(200, 10, txt="Technical Assessment Report", ln=True, align='C')
    pdf.ln(10)

    for i, (ques, ans, grade) in enumerate(zip(questions, answers, grades), 1):
        data = json.loads(grade)
        score = data["score"]
        feedback = data["feedback"]

        pdf.set_font("Arial", 'B', 11)
        pdf.multi_cell(0, 10, txt=f"Question {i}:")
        pdf.set_font("Arial", '', 11)
        pdf.multi_cell(0, 10, txt=ques)
        pdf.ln(2)

        pdf.set_font("Arial", 'B', 11)
        pdf.multi_cell(0, 10, txt="Your Answer:")
        pdf.set_font("Arial", '', 11)
        pdf.multi_cell(0, 10, txt=ans)
        pdf.ln(2)

        pdf.set_font("Arial", 'B', 11)
        pdf.multi_cell(0, 10, txt=f"Score: {score}%")
        pdf.set_font("Arial", 'B', 11)
        pdf.multi_cell(0, 10, txt=f"Feedback: {feedback}")
        pdf.ln(5)

        pdf.line(10, pdf.get_y(), 200, pdf.get_y())
        pdf.ln(5)

    return pdf.output(dest='S').encode('latin-1')