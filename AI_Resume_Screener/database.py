import json
import os
from datetime import datetime
from uuid import uuid4


BASE_DIR = os.path.dirname(__file__)
DATA_FILE = os.path.join(BASE_DIR, "data", "screening_history.json")


def _ensure_store():
    os.makedirs(os.path.dirname(DATA_FILE), exist_ok=True)
    if not os.path.exists(DATA_FILE):
        with open(DATA_FILE, "w", encoding="utf-8") as file:
            json.dump([], file, indent=2)


def read_records():
    _ensure_store()
    with open(DATA_FILE, "r", encoding="utf-8") as file:
        return json.load(file)


def add_record(record):
    records = read_records()
    record["id"] = record.get("id") or str(uuid4())
    record["timestamp"] = datetime.utcnow().isoformat()
    records.append(record)
    with open(DATA_FILE, "w", encoding="utf-8") as file:
        json.dump(records, file, indent=2)


def update_record_decision(record_id, decision):
    records = read_records()
    updated = False
    for row in records:
        if row.get("id") == record_id:
            row["decision"] = decision
            updated = True
            break
    if updated:
        with open(DATA_FILE, "w", encoding="utf-8") as file:
            json.dump(records, file, indent=2)
    return updated


def get_admin_stats():
    records = read_records()
    # Backfill IDs for old records created before id support.
    needs_save = False
    for row in records:
        if not row.get("id"):
            row["id"] = str(uuid4())
            needs_save = True
    if needs_save:
        with open(DATA_FILE, "w", encoding="utf-8") as file:
            json.dump(records, file, indent=2)

    approved = [row for row in records if row.get("decision") == "Approved"]
    rejected = [row for row in records if row.get("decision") == "Rejected"]
    pending = [row for row in records if row.get("decision") == "Review Needed"]

    return {
        "total": len(records),
        "approved_count": len(approved),
        "rejected_count": len(rejected),
        "review_needed_count": len(pending),
        "records": list(reversed(records)),
    }
