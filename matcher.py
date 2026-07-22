import re
from collections import Counter


OCCUPATION_SKILLS = {
    "Data Scientist": [
        "python",
        "pandas",
        "numpy",
        "machine learning",
        "scikit-learn",
        "statistics",
        "sql",
        "data visualization",
        "tensorflow",
    ],
    "Frontend Developer": [
        "html",
        "css",
        "javascript",
        "react",
        "typescript",
        "responsive design",
        "redux",
        "ui",
        "tailwind",
    ],
    "Backend Developer": [
        "python",
        "java",
        "node",
        "rest api",
        "flask",
        "django",
        "sql",
        "microservices",
        "docker",
    ],
    "DevOps Engineer": [
        "aws",
        "azure",
        "docker",
        "kubernetes",
        "ci/cd",
        "terraform",
        "linux",
        "monitoring",
        "bash",
    ],
}


def normalize_text(text):
    lowered = text.lower()
    return re.sub(r"\s+", " ", lowered).strip()


def _skill_present(source_text, skill):
    if " " in skill or "/" in skill or "-" in skill:
        return skill in source_text
    return re.search(rf"\b{re.escape(skill)}\b", source_text) is not None


def analyze_skills(resume_text, job_desc):
    resume_clean = normalize_text(resume_text or "")
    job_clean = normalize_text(job_desc or "")

    per_occupation = []
    aggregate_skill_counts = Counter()

    for occupation, skills in OCCUPATION_SKILLS.items():
        matched_resume = [skill for skill in skills if _skill_present(resume_clean, skill)]
        matched_job = [skill for skill in skills if _skill_present(job_clean, skill)]

        skill_hits = set(matched_resume) | set(matched_job)
        total = len(skills)
        coverage = round((len(skill_hits) / total) * 100, 2) if total else 0.0

        per_occupation.append(
            {
                "occupation": occupation,
                "match_percentage": coverage,
                "matched_skills": sorted(skill_hits),
                "missing_skills": sorted(set(skills) - skill_hits),
            }
        )

        aggregate_skill_counts.update(skill_hits)

    per_occupation.sort(key=lambda row: row["match_percentage"], reverse=True)
    best_fit = per_occupation[0] if per_occupation else None

    percentages = [item["match_percentage"] for item in per_occupation]
    avg = round(sum(percentages) / len(percentages), 2) if percentages else 0.0
    strongest_skills = [name for name, _ in aggregate_skill_counts.most_common(5)]

    return {
        "best_fit": best_fit,
        "occupation_scores": per_occupation,
        "statistics": {
            "mean_match_percentage": avg,
            "top_match_percentage": max(percentages) if percentages else 0.0,
            "low_match_percentage": min(percentages) if percentages else 0.0,
            "total_occupations_compared": len(per_occupation),
            "strongest_skills_detected": strongest_skills,
        },
    }
