
import csv
import io
from flask import Flask, make_response, redirect, render_template, request, url_for
import os
from werkzeug.utils import secure_filename

from database import add_record, get_admin_stats, update_record_decision
from matcher import analyze_skills
from resume_parser import extract_text_from_path

app = Flask(__name__)

UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@app.route('/')
def home():
    return render_template('index.html')


@app.route('/admin')
def admin():
    decision_filter = request.args.get("decision", "").strip()
    search_query = request.args.get("q", "").strip().lower()
    stats = get_admin_stats()
    filtered_records = stats["records"]

    if decision_filter:
        filtered_records = [row for row in filtered_records if row.get("decision") == decision_filter]
    if search_query:
        filtered_records = [
            row
            for row in filtered_records
            if search_query in str(row.get("resume_name", "")).lower()
            or search_query in str(row.get("best_fit_role", "")).lower()
        ]

    stats["records"] = filtered_records
    stats["filtered_total"] = len(filtered_records)
    return render_template('admin/index.html', stats=stats)


@app.route('/admin/export')
def admin_export():
    stats = get_admin_stats()
    records = stats["records"]

    decision_filter = request.args.get("decision", "").strip()
    search_query = request.args.get("q", "").strip().lower()

    if decision_filter:
        records = [row for row in records if row.get("decision") == decision_filter]
    if search_query:
        records = [
            row
            for row in records
            if search_query in str(row.get("resume_name", "")).lower()
            or search_query in str(row.get("best_fit_role", "")).lower()
        ]

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["id", "resume_name", "decision", "best_fit_role", "best_fit_score", "mean_score", "timestamp"])
    for row in records:
        writer.writerow(
            [
                row.get("id", ""),
                row.get("resume_name", ""),
                row.get("decision", ""),
                row.get("best_fit_role", ""),
                row.get("best_fit_score", ""),
                row.get("mean_score", ""),
                row.get("timestamp", ""),
            ]
        )

    response = make_response(output.getvalue())
    response.headers["Content-Type"] = "text/csv"
    response.headers["Content-Disposition"] = "attachment; filename=screening_history.csv"
    return response


@app.route('/admin/update-decision', methods=['POST'])
def admin_update_decision():
    record_id = request.form.get("record_id", "").strip()
    new_decision = request.form.get("new_decision", "").strip()
    decision_filter = request.form.get("decision_filter", "").strip()
    search_query = request.form.get("q", "").strip()

    if record_id and new_decision in {"Approved", "Rejected", "Review Needed"}:
        update_record_decision(record_id, new_decision)

    return redirect(url_for("admin", decision=decision_filter, q=search_query))


@app.route('/upload', methods=['POST'])
def upload():
    if 'resume' not in request.files:
        return "No file uploaded"

    file = request.files['resume']
    job_desc = request.form.get('job_desc')

    if file.filename == '':
        return "No selected file"

    safe_name = secure_filename(file.filename)
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], safe_name)
    file.save(filepath)

    resume_text = extract_text_from_path(filepath)
    analysis = analyze_skills(resume_text=resume_text, job_desc=job_desc)

    top_score = analysis["best_fit"]["match_percentage"] if analysis["best_fit"] else 0
    if top_score >= 75:
        decision = "Approved"
    elif top_score < 50:
        decision = "Rejected"
    else:
        decision = "Review Needed"

    add_record(
        {
            "resume_name": safe_name,
            "decision": decision,
            "best_fit_role": analysis["best_fit"]["occupation"] if analysis["best_fit"] else "N/A",
            "best_fit_score": top_score,
            "mean_score": analysis["statistics"]["mean_match_percentage"],
            "top_skills": analysis["statistics"]["strongest_skills_detected"],
        }
    )

    return render_template(
        "results.html",
        filename=safe_name,
        decision=decision,
        analysis=analysis,
    )

if __name__ == '__main__':
    app.run(debug=True)