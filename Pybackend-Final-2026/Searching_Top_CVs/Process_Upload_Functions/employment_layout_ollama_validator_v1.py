from __future__ import annotations

import argparse
import importlib.util
import sys
import json
import re
import urllib.request
from pathlib import Path

ENGINE_PATH = Path(__file__).with_name("employment_layout_engine_v1_CURRENT.py")
OLLAMA_URL = "http://localhost:11434/api/generate"
OLLAMA_MODEL = "qwen3:1.7b"
VERSION = "employment_layout_ollama_validator_v1_0"

spec = importlib.util.spec_from_file_location("layout_engine_v13", ENGINE_PATH)
engine = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = engine
spec.loader.exec_module(engine)

OPEN_RE = re.compile(r"\b(present|current|today|ongoing|now|to\s+date|till\s+date|till\s+now|until\s+date|continuing|continued)\b", re.I)
YEAR_RE = re.compile(r"\b(19|20)\d{2}\b")
MONTHS = {m.lower(): i for i, m in enumerate(
    ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"], 1
)}

def clean(v):
    return re.sub(r"\s+", " ", str(v or "")).strip()

def date_rank(value):
    s = clean(value)
    years = [int(x) for x in re.findall(r"\b(?:19|20)\d{2}\b", s)]
    low = s.lower()
    month = 0
    for name, num in MONTHS.items():
        if re.search(rf"\b{name}[a-z]*\.?\b", low):
            month = num
    if OPEN_RE.search(s):
        return (3, max(years or [0]), month)
    if years:
        return (2, years[-1], month, years[0])
    return (0, 0, 0)

def suspicious_pass(rec):
    t = clean(rec.get("title"))
    c = clean(rec.get("company"))
    if not t or not c:
        return True
    if not engine.v13_valid_title(t) or not engine.v13_valid_company(c):
        return True
    if engine.v13_is_prose(t) or engine.v13_is_prose(c):
        return True
    if engine.v13_is_skill_list(t) or engine.v13_is_skill_list(c):
        return True
    if engine.v13_is_location(c):
        return True
    bad_fragment = re.compile(r"(?i)\b(used by|responsible for|designed to|developed to|implemented to|helped to|worked on|resulting in)\b")
    if bad_fragment.search(t) or bad_fragment.search(c):
        return True
    if t.count(")") > t.count("("):
        return True
    if c.startswith((">", "<", "=", "=>", "<=")):
        return True
    return False

def candidate_lines(pdf_path):
    a = engine.analyze_pdf(pdf_path)
    lines = a.get("employment_lines") or a.get("visual_lines") or []
    out, seen = [], set()
    for i, line in enumerate(lines):
        text = clean(line.text)
        if not text or text.lower() in seen:
            continue
        seen.add(text.lower())
        out.append({
            "id": f"L{i+1}",
            "text": text,
            "page": line.page,
            "bold": bool(line.bold),
            "x0": round(line.x0, 1),
            "y0": round(line.y0, 1),
        })
    return out

def ollama_json(prompt):
    payload = json.dumps({
        "model": OLLAMA_MODEL,
        "prompt": prompt,
        "stream": False,
        "format": "json",
        "options": {"temperature": 0, "num_predict": 500}
    }).encode("utf-8")
    req = urllib.request.Request(
        OLLAMA_URL, data=payload,
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    with urllib.request.urlopen(req, timeout=120) as r:
        outer = json.loads(r.read().decode("utf-8"))
    return json.loads(outer.get("response", "{}"))

def validate_choice(choice, by_id):
    if not choice or choice == "NONE":
        return ""
    item = by_id.get(choice)
    return clean(item["text"]) if item else ""

def repair_with_ollama(pdf_path, base):
    lines = candidate_lines(pdf_path)
    if not lines:
        return base, False

    # Keep the prompt bounded while preserving the employment evidence.
    date_idx = [i for i, x in enumerate(lines) if engine.has_date_range(x["text"])]
    keep_idx = sorted(set(
        j
        for i in date_idx
        for j in range(max(0, i - 1), min(len(lines), i + 1))
    ))
    lines = [lines[i] for i in keep_idx][:40]
    by_id = {x["id"]: x for x in lines}

    current = {
        "current_job_title": base.get("current_job_title", ""),
        "current_company": base.get("current_company", ""),
        "records": base.get("records", []),
    }

    prompt = f"""
/no_think
You validate employment history from resume evidence.

RULES:
1. Select ONLY candidate IDs listed below. Never invent text.
2. Job title must be an occupational role, not a skill, sentence, project heading, school heading, location, contact field, or responsibility.
3. Company must be an employer/organization, not a job title, skill list, sentence, location, contact field, project heading, or responsibility.
4. Use dates to separate employment records.
5. Do not treat Education, Projects, Activities, Awards, or Skills as employment unless the text explicitly shows an actual employer/job relationship.
6. If evidence is insufficient, return NONE.
7. Return JSON only.

CURRENT DETERMINISTIC RESULT:
{json.dumps(current, ensure_ascii=False)}

CANDIDATE LINES:
{json.dumps(lines, ensure_ascii=False)}

Return:
{{
  "records": [
    {{
      "title_id": "L# or NONE",
      "company_id": "L# or NONE",
      "date_id": "L# or NONE"
    }}
  ]
}}
"""
    try:
        ans = ollama_json(prompt)
    except Exception as e:
        base["ollama_error"] = str(e)
        return base, False

    repaired = []
    for item in ans.get("records", [])[:12]:
        title = validate_choice(item.get("title_id"), by_id)
        company = validate_choice(item.get("company_id"), by_id)
        date_text = validate_choice(item.get("date_id"), by_id)

        # Extract only a source-supported date range from the chosen line.
        date_range = engine.extract_date_range(date_text) if date_text else ""

        # Safe deterministic cleanup after ID selection.
        title = engine.v13_strip_role_label(title)
        if title:
            t, c = engine.v13_split_colon(title)
            if t and c:
                title, company = t, c

        if company:
            cp, loc = engine.v13_strip_location_from_company(company)
            company = cp
        else:
            loc = ""

        # Strong reversal check.
        if title and company:
            if (engine.v13_company_strength(title) >= 1 and
                engine.v13_role_strength(company) >= 1 and
                engine.v13_role_strength(title) == 0):
                title, company = company, title

        title_ok = bool(title and engine.v13_valid_title(title))
        company_ok = bool(company and engine.v13_valid_company(company))
        date_ok = bool(date_range)

        status = "PASS" if title_ok and company_ok and date_ok else "REVIEW_REQUIRED"

        repaired.append({
            "title": title if title_ok else "",
            "company": company if company_ok else "",
            "location": loc,
            "date_range": date_range,
            "confidence": 0.97 if status == "PASS" else 0.50,
            "status": status,
            "source": "LLM_VALIDATED",
            "title_supported": title_ok,
            "company_supported": company_ok,
            "date_supported": date_ok,
            "v13_title_valid": title_ok,
            "v13_company_valid": company_ok,
            "v13_safe_pass": status == "PASS",
        })

    if not repaired:
        return base, False

    # Current employment is selected by recency, not document order.
    ordered = sorted(repaired, key=lambda r: date_rank(r.get("date_range")), reverse=True)
    current_rec = ordered[0]

    result = dict(base)
    result["records"] = ordered
    result["current_job_title"] = current_rec.get("title", "")
    result["current_company"] = current_rec.get("company", "")
    result["previous_job_titles"] = [
        r.get("title", "") for r in ordered[1:] if r.get("title")
    ]
    result["status"] = (
        "PASS" if ordered and all(r.get("status") == "PASS" for r in ordered)
        else "REVIEW_REQUIRED"
    )
    result["validator_version"] = VERSION
    result["ollama_used"] = True
    return result, True

def build_deterministic_records(pdf_path):
    base = engine.build_layout_records(pdf_path)

    recs = list(base.get("records", []))
    if recs:
        ordered = sorted(
            recs,
            key=lambda r: date_rank(r.get("date_range")),
            reverse=True
        )
        base["records"] = ordered
        base["current_job_title"] = ordered[0].get("title", "")
        base["current_company"] = ordered[0].get("company", "")
        base["previous_job_titles"] = [
            r.get("title", "")
            for r in ordered[1:]
            if r.get("title")
            and r.get("status") == "PASS"
            and not suspicious_pass(r)
        ]

    suspicious = any(
        suspicious_pass(r)
        for r in base.get("records", [])
        if r.get("status") == "PASS"
    )

    if base.get("status") == "REVIEW_REQUIRED" or suspicious:
        base["status"] = "REVIEW_REQUIRED"

    base["validator_version"] = VERSION
    base["ollama_used"] = False
    return base


def build_validated_records(pdf_path):
    base = engine.build_layout_records(pdf_path)

    # Fix current-record ordering deterministically for every resume.
    recs = list(base.get("records", []))
    if recs:
        ordered = sorted(recs, key=lambda r: date_rank(r.get("date_range")), reverse=True)
        base["records"] = ordered
        base["current_job_title"] = ordered[0].get("title", "")
        base["current_company"] = ordered[0].get("company", "")
        base["previous_job_titles"] = [
            r.get("title", "") for r in ordered[1:] if r.get("title")
        ]

    needs_ollama = (
        base.get("status") == "REVIEW_REQUIRED"
        or any(suspicious_pass(r) for r in base.get("records", []))
    )

    if not needs_ollama:
        base["validator_version"] = VERSION
        base["ollama_used"] = False
        return base

    result, _ = repair_with_ollama(pdf_path, base)
    return result

def ascii_safe(v):
    return str(v).encode("ascii", "replace").decode("ascii")

def print_result(pdf_path):
    r = build_validated_records(pdf_path)
    print("=" * 110)
    print("LAYOUT + OLLAMA VALIDATOR")
    print("VALIDATOR:", r.get("validator_version", VERSION))
    print("FILE     :", ascii_safe(pdf_path))
    print("STATUS   :", r.get("status"))
    print("OLLAMA   :", "USED" if r.get("ollama_used") else "NONE")
    print("CHROMA   : NONE")
    print("CURRENT TITLE   :", ascii_safe(r.get("current_job_title", "")))
    print("CURRENT COMPANY :", ascii_safe(r.get("current_company", "")))
    print("PREVIOUS TITLES :", ascii_safe(" ~~ ".join(r.get("previous_job_titles", []))))
    print("=" * 110)
    for i, rec in enumerate(r.get("records", []), 1):
        print(
            f"{i:02d} | TITLE={ascii_safe(rec.get('title',''))} | "
            f"COMPANY={ascii_safe(rec.get('company',''))} | "
            f"DATE={ascii_safe(rec.get('date_range',''))} | "
            f"CONF={rec.get('confidence',0):.2f} | "
            f"{rec.get('status')} | SRC={rec.get('source','')}"
        )
    print("=" * 110)
    print("CHROMA : NONE")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("pdf")
    args = parser.parse_args()
    print_result(args.pdf)







