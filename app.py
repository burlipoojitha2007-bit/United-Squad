import re
import html
import os
import fitz
import gradio as gr
import pandas as pd
import plotly.express as px

# Beginner-friendly prototype: transparent keyword matching, not an AI hiring decision.
KNOWN_SKILLS = [
    "python", "java", "c++", "javascript", "html", "css", "react", "node.js",
    "sql", "mysql", "postgresql", "mongodb", "flask", "django", "fastapi",
    "pandas", "numpy", "scikit-learn", "machine learning", "deep learning",
    "generative ai", "genai", "rag", "llm", "tensorflow", "pytorch", "git",
    "github", "docker", "aws", "azure", "power bi", "tableau", "excel",
    "data analysis", "data visualization", "rest api", "api", "communication",
    "problem solving"
]

def extract_pdf_text(path):
    parts = []
    with fitz.open(path) as doc:
        for page in doc:
            parts.append(page.get_text())
    return "\n".join(parts).strip()

def find_skills(text):
    found = []
    text = text.lower()
    for skill in KNOWN_SKILLS:
        pattern = r"(?<![a-z0-9+#])" + re.escape(skill) + r"(?![a-z0-9+#])"
        if re.search(pattern, text):
            found.append(skill)
    return sorted(set(found))

def screen_resume(resume_text, job_description):
    required = find_skills(job_description)
    candidate = find_skills(resume_text)
    matched = [s for s in required if s in candidate]
    missing = [s for s in required if s not in candidate]
    score = round(100 * len(matched) / len(required)) if required else 0
    return score, matched, missing

def analyze_candidates(files, job_description):
    if not job_description or not job_description.strip():
        return pd.DataFrame(), None, "<p>Please enter a job description.</p>"
    if not files:
        return pd.DataFrame(), None, "<p>Please upload at least one PDF resume.</p>"

    rows = []
    for path in files:
        try:
            resume_text = extract_pdf_text(path)
            score, matched, missing = screen_resume(resume_text, job_description)
            rows.append({
                "Candidate": os.path.basename(path).removesuffix(".pdf"),
                "Match Score (%)": score,
                "Matched Skills": ", ".join(matched) or "None detected",
                "Missing Skills": ", ".join(missing) or "None detected",
                "Note": "" if resume_text else "No selectable text found; scanned PDFs may need OCR"
            })
        except Exception as exc:
            rows.append({
                "Candidate": os.path.basename(path),
                "Match Score (%)": 0,
                "Matched Skills": "Could not read PDF",
                "Missing Skills": "Check the file",
                "Note": str(exc)[:160]
            })

    df = pd.DataFrame(rows).sort_values("Match Score (%)", ascending=False).reset_index(drop=True)
    total = len(df)
    average = round(df["Match Score (%)"].mean()) if total else 0
    top = html.escape(str(df.iloc[0]["Candidate"])) if total else "None"
    top_score = int(df.iloc[0]["Match Score (%)"]) if total else 0
    summary = f"""
    <div style="display:flex;flex-wrap:wrap;gap:12px;margin:12px 0">
      <div style="flex:1;min-width:140px;background:#172554;color:white;padding:18px;border-radius:12px">
        <div>Total Resumes</div><h2>{total}</h2></div>
      <div style="flex:1;min-width:140px;background:#164e63;color:white;padding:18px;border-radius:12px">
        <div>Average Skill Match</div><h2>{average}%</h2></div>
      <div style="flex:1;min-width:160px;background:#14532d;color:white;padding:18px;border-radius:12px">
        <div>Highest Skill Match</div><h3>{top}</h3><h2>{top_score}%</h2></div>
    </div>
    <p style="color:gray">Scores reflect recognized skill keywords only, not hiring decisions.</p>
    """
    chart = px.bar(df, x="Candidate", y="Match Score (%)",
                   title="Candidate Skill Match Comparison",
                   text="Match Score (%)", range_y=[0, 110])
    chart.update_layout(xaxis_title="Resume", yaxis_title="Skill Match (%)")
    chart.update_traces(texttemplate="%{text}%", textposition="outside")
    return df, chart, summary

with gr.Blocks(theme=gr.themes.Soft(), title="AI Resume Screening System") as demo:
    gr.Markdown("""
    # 🧠 AI Resume Screening System
    ### Resume Comparison • Skills Analysis • Recruitment Prototype

    Upload PDF resumes and enter the job description to compare recognized skills.
    """)
    resume_upload = gr.File(label="Upload candidate resumes (PDF only)",
                            file_count="multiple", file_types=[".pdf"], type="filepath")
    job_input = gr.Textbox(
        label="Job Description",
        value="Python developer with SQL, Flask, Git and Pandas skills.",
        lines=4,
        placeholder="Enter the job requirements and skills..."
    )
    analyze_btn = gr.Button("🔍 Analyze Resumes", variant="primary")
    summary_output = gr.HTML(label="Overview")
    with gr.Tab("📊 Dashboard"):
        chart_output = gr.Plot(label="Candidate Comparison")
    with gr.Tab("📋 Candidate Results"):
        table_output = gr.Dataframe(label="Ranked Candidates", interactive=False, wrap=True)
    analyze_btn.click(fn=analyze_candidates, inputs=[resume_upload, job_input],
                      outputs=[table_output, chart_output, summary_output])
    gr.Markdown("""
    ---
    **Prototype notice:** This uses transparent keyword-based skill matching, not a trained AI model.
    It may miss synonyms and formatting variations. Recruiters must review resumes independently;
    never use the score as the sole basis for hiring.
    """)

if __name__ == "__main__":
    demo.launch(
    server_name="0.0.0.0",
    server_port=int(os.environ.get("PORT", 10000))
)
