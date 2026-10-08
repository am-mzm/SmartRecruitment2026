"""
employment_layout_v1.py

Geometry-aware employment extraction foundation.

NO Ollama.
NO Chroma.
NO dependency on frozen Hybrid/Selector parsers.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, asdict
from typing import List, Dict, Any, Optional

import pymupdf


VERSION = "employment_layout_v1_0"


# ------------------------------------------------------------------
# DATA
# ------------------------------------------------------------------

@dataclass
class Span:
    text: str
    page: int
    x0: float
    y0: float
    x1: float
    y1: float
    size: float
    font: str
    flags: int
    bold: bool


@dataclass
class VisualLine:
    text: str
    page: int
    x0: float
    y0: float
    x1: float
    y1: float
    max_size: float
    bold: bool
    spans: List[Span]


# ------------------------------------------------------------------
# BASIC HELPERS
# ------------------------------------------------------------------

def clean(v: Any) -> str:
    return re.sub(r"\s+", " ", str(v or "")).strip()


DATE_RE = re.compile(
    r"\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Sept|Oct|Nov|Dec)[a-z]*\.?\s+(?:\d{1,2},?\s+)?\d{4}\b|\b(?:0?[1-9]|1[0-2])[/.-]\d{4}\b|\b(?:19|20)\d{2}\b",
    re.IGNORECASE,
)

RANGE_RE = re.compile(
    r"(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Sept|Oct|Nov|Dec)[a-z]*\.?\s+(?:\d{1,2},?\s+)?\d{4}\s*(?:-|\u2013|\u2014|to)\s*(?:(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Sept|Oct|Nov|Dec)[a-z]*\.?\s+(?:\d{1,2},?\s+)?\d{4}|present|current|now)|(?:0?[1-9]|1[0-2])[/.-]\d{4}\s*(?:-|\u2013|\u2014|to)\s*(?:(?:0?[1-9]|1[0-2])[/.-]\d{4}|present|current|now)",
    re.IGNORECASE,
)


def has_date(text: str) -> bool:
    return bool(DATE_RE.search(clean(text)))


def has_date_range(text: str) -> bool:
    return bool(RANGE_RE.search(clean(text)))


def is_bullet(text: str) -> bool:
    s = clean(text)
    return bool(
        s.startswith(("?", "?", "?", "?", "?", "-", "?", "?", "*", "?"))
    )


def sentence_like(text: str) -> bool:
    s = clean(text)

    if not s:
        return False

    words = s.split()

    if is_bullet(s):
        return True

    if len(words) >= 14:
        return True

    if len(words) >= 8 and s.endswith((".", ";", ":")):
        return True

    return False


def header_like(line: VisualLine) -> bool:
    if has_date_range(line.text):
        return True

    if sentence_like(line.text):
        return False

    if len(line.text.split()) <= 10:
        return True

    return False


# ------------------------------------------------------------------
# SPAN EXTRACTION
# ------------------------------------------------------------------

def extract_spans(pdf_path: str) -> List[Span]:

    doc = pymupdf.open(pdf_path)
    result: List[Span] = []

    try:
        for page_no, page in enumerate(doc):

            data = page.get_text("dict")

            for block in data.get("blocks", []):

                if block.get("type") != 0:
                    continue

                for line in block.get("lines", []):

                    for raw in line.get("spans", []):

                        text = clean(raw.get("text"))

                        if not text:
                            continue

                        bbox = raw.get("bbox", (0, 0, 0, 0))
                        flags = int(raw.get("flags", 0))
                        font = str(raw.get("font", ""))

                        bold = (
                            "bold" in font.lower()
                            or bool(flags & 16)
                        )

                        result.append(
                            Span(
                                text=text,
                                page=page_no + 1,
                                x0=float(bbox[0]),
                                y0=float(bbox[1]),
                                x1=float(bbox[2]),
                                y1=float(bbox[3]),
                                size=float(raw.get("size", 0)),
                                font=font,
                                flags=flags,
                                bold=bold,
                            )
                        )

    finally:
        doc.close()

    return result


# ------------------------------------------------------------------
# VISUAL LINE RECONSTRUCTION
# ------------------------------------------------------------------

def reconstruct_visual_lines(
    spans: List[Span],
    y_tolerance: float = 2.5,
) -> List[VisualLine]:

    pages: Dict[int, List[Span]] = {}

    for span in spans:
        pages.setdefault(span.page, []).append(span)

    output: List[VisualLine] = []

    for page_no in sorted(pages):

        page_spans = sorted(
            pages[page_no],
            key=lambda s: (s.y0, s.x0),
        )

        rows: List[List[Span]] = []

        for span in page_spans:

            best_row = None
            best_distance = None

            for row in rows[-8:]:

                baseline = sum(x.y0 for x in row) / len(row)
                distance = abs(span.y0 - baseline)

                if distance <= y_tolerance:
                    if (
                        best_distance is None
                        or distance < best_distance
                    ):
                        best_row = row
                        best_distance = distance

            if best_row is None:
                rows.append([span])
            else:
                best_row.append(span)

        for row in rows:

            row.sort(key=lambda s: s.x0)

            text = clean(" ".join(x.text for x in row))

            if not text:
                continue

            output.append(
                VisualLine(
                    text=text,
                    page=page_no,
                    x0=min(x.x0 for x in row),
                    y0=min(x.y0 for x in row),
                    x1=max(x.x1 for x in row),
                    y1=max(x.y1 for x in row),
                    max_size=max(x.size for x in row),
                    bold=any(x.bold for x in row),
                    spans=row,
                )
            )

    return sorted(
        output,
        key=lambda x: (x.page, x.y0, x.x0),
    )


# ------------------------------------------------------------------
# EMPLOYMENT SECTION SIGNALS
# ------------------------------------------------------------------

EMPLOYMENT_HEADINGS = {
    "experience",
    "work experience",
    "professional experience",
    "employment",
    "employment history",
    "work history",
    "career history",
    "professional history",
    "professional background",
}

STOP_HEADINGS = {
    "education",
    "skills",
    "technical skills",
    "projects",
    "academic projects",
    "certifications",
    "certificates",
    "awards",
    "interests",
    "activities",
    "volunteer",
    "volunteering",
    "publications",
}


def normalized_heading(text: str) -> str:
    s = clean(text).lower()
    s = re.sub(r"[^a-z ]+", "", s)
    return clean(s)


def find_employment_lines(
    lines: List[VisualLine],
) -> List[VisualLine]:

    start: Optional[int] = None
    end = len(lines)

    for i, line in enumerate(lines):

        h = normalized_heading(line.text)

        if h in EMPLOYMENT_HEADINGS:
            start = i + 1
            break

    if start is None:
        # Do not throw away document evidence.
        return lines

    for i in range(start, len(lines)):

        h = normalized_heading(lines[i].text)

        if h in STOP_HEADINGS:
            end = i
            break

    return lines[start:end]


# ------------------------------------------------------------------
# DATE-ANCHORED GEOMETRY BLOCKS
# ------------------------------------------------------------------

def build_employment_blocks(
    lines: List[VisualLine],
    header_lookback: int = 4,
    body_lookahead: int = 6,
) -> List[Dict[str, Any]]:

    anchors = [
        i for i, line in enumerate(lines)
        if has_date_range(line.text)
    ]

    blocks = []

    for block_no, idx in enumerate(anchors, 1):

        start = max(0, idx - header_lookback)
        end = min(len(lines), idx + body_lookahead + 1)

        # Stop before another date anchor.
        for j in range(idx + 1, end):
            if has_date_range(lines[j].text):
                end = j
                break

        block_lines = lines[start:end]

        candidates = {
            "date": [],
            "header": [],
            "body": [],
        }

        for line in block_lines:

            item = {
                "text": line.text,
                "page": line.page,
                "bbox": [
                    round(line.x0, 2),
                    round(line.y0, 2),
                    round(line.x1, 2),
                    round(line.y1, 2),
                ],
                "font_size": round(line.max_size, 2),
                "bold": line.bold,
            }

            if has_date_range(line.text):
                candidates["date"].append(item)

            elif header_like(line):
                candidates["header"].append(item)

            else:
                candidates["body"].append(item)

        blocks.append({
            "block_id": block_no,
            "anchor_index": idx,
            "anchor_text": lines[idx].text,
            "page": lines[idx].page,
            "lines": block_lines,
            "candidates": candidates,
        })

    return blocks


# ------------------------------------------------------------------
# PUBLIC API
# ------------------------------------------------------------------

def analyze_pdf(pdf_path: str) -> Dict[str, Any]:

    spans = extract_spans(pdf_path)
    lines = reconstruct_visual_lines(spans)
    employment_lines = find_employment_lines(lines)
    blocks = build_employment_blocks(employment_lines)

    return {
        "version": VERSION,
        "pdf_path": pdf_path,
        "span_count": len(spans),
        "visual_line_count": len(lines),
        "employment_line_count": len(employment_lines),
        "employment_block_count": len(blocks),
        "spans": spans,
        "visual_lines": lines,
        "employment_lines": employment_lines,
        "employment_blocks": blocks,
    }


# ------------------------------------------------------------------
# DIAGNOSTIC
# ------------------------------------------------------------------

def print_diagnostic(pdf_path: str) -> None:

    result = analyze_pdf(pdf_path)

    print("=" * 120)
    print("GEOMETRY EMPLOYMENT DIAGNOSTIC")
    print("=" * 120)
    print("VERSION :", result["version"])
    print("FILE    :", pdf_path)
    print("SPANS   :", result["span_count"])
    print("LINES   :", result["visual_line_count"])
    print("EMP LNS :", result["employment_line_count"])
    print("BLOCKS  :", result["employment_block_count"])
    print("OLLAMA  : NONE")
    print("CHROMA  : NONE")
    print("WRITES  : NONE")

    for block in result["employment_blocks"]:

        print("\n" + "-" * 120)
        print(
            "BLOCK",
            block["block_id"],
            "| PAGE",
            block["page"],
            "| DATE:",
            block["anchor_text"],
        )

        print("\nVISUAL LINES:")

        for line in block["lines"]:

            marker = ""

            if has_date_range(line.text):
                marker = " DATE"
            elif header_like(line):
                marker = " HEADER"
            else:
                marker = " BODY"

            print(
                f"P{line.page:02d} "
                f"X={line.x0:7.1f} "
                f"Y={line.y0:7.1f} "
                f"S={line.max_size:4.1f} "
                f"B={int(line.bold)} "
                f"[{marker.strip():6}] "
                f"{line.text}"
            )

            # Show separate spans when one visual row contains
            # horizontally separated information.
            if len(line.spans) > 1:
                for span in line.spans:
                    print(
                        f"       SPAN "
                        f"X={span.x0:7.1f} "
                        f"Y={span.y0:7.1f} "
                        f"S={span.size:4.1f} "
                        f"B={int(span.bold)} "
                        f"{span.text}"
                    )

    print("\n" + "=" * 120)
    print("OLLAMA : NONE")
    print("CHROMA : NONE")
    print("WRITES : NONE")
    print("=" * 120)



# ==================================================================
# LAYOUT-AWARE CANDIDATE / ASSIGNMENT ENGINE
# ==================================================================

from dataclasses import dataclass, asdict

ENGINE_VERSION = "layout_candidate_engine_v1_0"


@dataclass
class EmploymentRecord:
    title: str = ""
    company: str = ""
    location: str = ""
    date_range: str = ""
    confidence: float = 0.0
    status: str = "REVIEW_REQUIRED"
    source: str = "DETERMINISTIC"


LOCATION_RE = re.compile(
    r"\b(?:Remote|Hybrid|On[- ]site|"
    r"[A-Z][A-Za-z.' -]+,\s*(?:[A-Z]{2}|Canada|USA|United States|China|India|UK)|"
    r"[A-Z][A-Za-z.' -]+\s+(?:ON|BC|AB|QC|MI|NY|CA|TX|PA|OH|FL))\b",
    re.IGNORECASE,
)

TITLE_WORDS = {
    "engineer","developer","architect","analyst","manager","intern",
    "consultant","specialist","technologist","scientist","administrator",
    "director","executive","assistant","associate","coordinator",
    "lead","designer","founder","president","officer","tutor",
    "teacher","researcher","research","programmer","sales",
    "representative","advisor","technician","organizer"
}

COMPANY_WORDS = {
    "inc","llc","ltd","corp","corporation","company","group",
    "solutions","systems","technologies","technology","bank",
    "capital","markets","health","financial","services","academy",
    "university","college","center","centre","organization"
}


def ascii_safe(text):
    return str(text).encode("ascii", "replace").decode("ascii")


def split_visual_segments(line, gap_threshold=45.0):
    spans = sorted(line.spans, key=lambda s: s.x0)

    if not spans:
        return []

    groups = [[spans[0]]]

    for span in spans[1:]:
        gap = span.x0 - groups[-1][-1].x1

        if gap >= gap_threshold:
            groups.append([span])
        else:
            groups[-1].append(span)

    result = []

    for group in groups:
        text = clean(" ".join(s.text for s in group))

        if text:
            result.append({
                "text": text,
                "x0": min(s.x0 for s in group),
                "x1": max(s.x1 for s in group),
                "bold": any(s.bold for s in group),
                "font_size": max(s.size for s in group),
            })

    return result


def remove_date_text(text):
    s = clean(text)
    s = RANGE_RE.sub(" ", s)
    s = clean(s.strip(" ,|-"))
    return s


def extract_date_range(text):
    m = RANGE_RE.search(clean(text))
    return clean(m.group(0)) if m else ""


def looks_location(text):
    s = clean(text)

    if not s or has_date(s):
        return False

    if s.lower() in {"remote", "hybrid", "onsite", "on-site"}:
        return True

    return bool(LOCATION_RE.search(s))


def location_score(text):
    s = clean(text)

    if not s:
        return -100

    score = 0

    if looks_location(s):
        score += 8

    if len(s.split()) <= 4:
        score += 2

    if any(w.lower().strip(".,") in TITLE_WORDS for w in s.split()):
        score -= 5

    if sentence_like(s):
        score -= 8

    return score


def title_score(text, bold=False):
    s = clean(text)

    if not s or has_date_range(s) or looks_location(s):
        return -100

    words = s.split()

    if len(words) > 10 or sentence_like(s):
        return -100

    score = 0
    low_words = [w.lower().strip(".,()") for w in words]

    score += 4 * sum(w in TITLE_WORDS for w in low_words)

    if 1 <= len(words) <= 6:
        score += 3

    if bold:
        score += 2

    if any(w in COMPANY_WORDS for w in low_words):
        score -= 3

    if s.endswith((".", ";")):
        score -= 5

    return score


def company_score(text, bold=False):
    s = clean(text)

    if not s or has_date_range(s) or looks_location(s):
        return -100

    words = s.split()

    if len(words) > 10 or sentence_like(s):
        return -100

    score = 0
    low_words = [w.lower().strip(".,()") for w in words]

    score += 3 * sum(w in COMPANY_WORDS for w in low_words)

    if 1 <= len(words) <= 7:
        score += 2

    if bold:
        score += 2

    if any(w in TITLE_WORDS for w in low_words):
        score -= 2

    if s.endswith((".", ";")):
        score -= 5

    return score


def candidate_parts(line):
    parts = []

    for seg in split_visual_segments(line):
        text = clean(seg["text"])

        if not text:
            continue

        # Date and non-date text may occupy the same visual segment.
        non_date = remove_date_text(text)

        if non_date:
            parts.append({
                "text": non_date,
                "x0": seg["x0"],
                "x1": seg["x1"],
                "bold": seg["bold"],
                "font_size": seg["font_size"],
                "page": line.page,
                "y0": line.y0,
            })

    return parts


def choose_best(items, scorer):
    scored = []

    seen = set()

    for item in items:
        text = clean(item["text"])
        key = text.lower()

        if not text or key in seen:
            continue

        seen.add(key)

        score = scorer(text, item.get("bold", False))

        if score > -50:
            scored.append((score, item))

    scored.sort(
        key=lambda x: (
            x[0],
            bool(x[1].get("bold")),
            -len(x[1]["text"])
        ),
        reverse=True,
    )

    return scored[0] if scored else None


def build_layout_records(pdf_path):
    result = analyze_pdf(pdf_path)
    records = []

    emp_lines = result["employment_lines"]

    anchor_indexes = [
        i for i, line in enumerate(emp_lines)
        if has_date_range(line.text)
    ]

    for rec_no, idx in enumerate(anchor_indexes, 1):
        anchor = emp_lines[idx]
        date_range = extract_date_range(anchor.text)

        # Tight geometry window. Do not allow responsibility text
        # to become title/company evidence.
        indexes = []

        for offset in (-2, -1, 0, 1, 2):
            j = idx + offset

            if 0 <= j < len(emp_lines):
                line = emp_lines[j]

                if line.page == anchor.page:
                    indexes.append(j)

        candidates = []

        for j in indexes:
            line = emp_lines[j]

            if sentence_like(line.text) and not has_date_range(line.text):
                continue

            for part in candidate_parts(line):
                part["distance"] = abs(j - idx)
                candidates.append(part)

        # Location candidates are evaluated independently.
        location_candidates = []

        for item in candidates:
            score = location_score(item["text"])

            if score > 0:
                location_candidates.append((score, item))

        location_candidates.sort(
            key=lambda x: (x[0], -x[1]["distance"]),
            reverse=True
        )

        location = (
            location_candidates[0][1]["text"]
            if location_candidates else ""
        )

        usable = [
            x for x in candidates
            if clean(x["text"]).lower() != clean(location).lower()
        ]

        # Prefer candidates closest to date anchor.
        title_items = []
        company_items = []

        for item in usable:
            proximity_bonus = max(0, 3 - item["distance"])

            t = dict(item)
            t["_score_bonus"] = proximity_bonus

            c = dict(item)
            c["_score_bonus"] = proximity_bonus

            title_items.append(t)
            company_items.append(c)

        def score_title(text, bold=False):
            item = next(
                (x for x in title_items if x["text"] == text),
                {}
            )
            return title_score(text, bold) + item.get("_score_bonus", 0)

        def score_company(text, bold=False):
            item = next(
                (x for x in company_items if x["text"] == text),
                {}
            )
            return company_score(text, bold) + item.get("_score_bonus", 0)

        best_title = choose_best(title_items, score_title)
        best_company = choose_best(company_items, score_company)

        title = best_title[1]["text"] if best_title else ""
        company = best_company[1]["text"] if best_company else ""

        # Never use the same evidence as both title and company.
        if title and company and title.lower() == company.lower():
            if best_title[0] >= best_company[0]:
                company = ""
            else:
                title = ""

        confidence = 0.0

        if title:
            confidence += 0.40

        if company:
            confidence += 0.40

        if date_range:
            confidence += 0.15

        if location:
            confidence += 0.05

        confidence = round(min(confidence, 1.0), 2)

        status = (
            "PASS"
            if title and company and date_range and confidence >= 0.90
            else "REVIEW_REQUIRED"
        )

        records.append(
            EmploymentRecord(
                title=title,
                company=company,
                location=location,
                date_range=date_range,
                confidence=confidence,
                status=status,
            )
        )

    return {
        "engine_version": ENGINE_VERSION,
        "pdf_path": pdf_path,
        "records": [asdict(x) for x in records],
    }


def print_layout_records(pdf_path):
    result = build_layout_records(pdf_path)

    print("=" * 100)
    print("LAYOUT EMPLOYMENT RECORDS")
    print("ENGINE :", result["engine_version"])
    print("FILE   :", ascii_safe(pdf_path))
    print("=" * 100)

    for i, rec in enumerate(result["records"], 1):
        print(
            f"{i:02d} | "
            f"TITLE={ascii_safe(rec['title'])} | "
            f"COMPANY={ascii_safe(rec['company'])} | "
            f"LOCATION={ascii_safe(rec['location'])} | "
            f"DATE={ascii_safe(rec['date_range'])} | "
            f"CONF={rec['confidence']:.2f} | "
            f"{rec['status']}"
        )

    print("=" * 100)
    print("OLLAMA : NONE")
    print("CHROMA : NONE")





# ==================================================================
# CONSOLIDATED LAYOUT ENGINE V1.1
# Covers known structural failure classes from regression/audit.
# ==================================================================

ENGINE_VERSION = "layout_candidate_engine_v1_1"

CURRENT_WORD = r"(?:present|current|today|ongoing|now|to\s+date|till\s+date|till\s+now|until\s+date|continuing|continued)"

MONTH_WORD = (
    r"(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|"
    r"Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:t(?:ember)?)?|"
    r"Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)\.?"
)

DATE_POINT = (
    rf"(?:{MONTH_WORD}\s+(?:\d{{1,2}},?\s+)?(?:19|20)?\d{{2}}"
    rf"|(?:0?[1-9]|1[0-2])[/.-](?:19|20)?\d{{2}}"
    rf"|(?:19|20)\d{{2}})"
)

EXT_RANGE_RE = re.compile(
    rf"\b({DATE_POINT})\s*"
    rf"(?:-|\u2013|\u2014|to|through|thru|until)\s*"
    rf"({DATE_POINT}|{CURRENT_WORD})\b",
    re.IGNORECASE,
)

ROLE_LABEL_RE = re.compile(
    r"^\s*(?:job\s*title|position|role|designation|title)\s*[:\-]\s*",
    re.IGNORECASE,
)

COMPANY_LABEL_RE = re.compile(
    r"^\s*(?:company|employer|organization|organisation|client)\s*[:\-]\s*",
    re.IGNORECASE,
)

NON_EMPLOYMENT_RE = re.compile(
    r"^\s*(?:education|academic(?:s)?|academic projects?|projects?|"
    r"personal projects?|course projects?|certifications?|certificates?|"
    r"licenses?|skills|technical skills|technologies|tools|awards?|"
    r"publications?|volunteer(?:ing)?|extracurricular|interests?|"
    r"activities|references?)\s*:?\s*$",
    re.IGNORECASE,
)

BODY_START_RE = re.compile(
    r"^\s*(?:responsibilities|responsibility|duties|achievements|"
    r"accomplishments|key responsibilities|projects?)\s*:?\s*$",
    re.IGNORECASE,
)

BODY_VERB_RE = re.compile(
    r"^\s*(?:developed|designed|implemented|created|built|managed|"
    r"worked|responsible|collaborated|led|performed|supported|"
    r"maintained|analyzed|analysed|provided|assisted|conducted|"
    r"used|utilized|improved|delivered|participated|generated|"
    r"identified|reviewed|prepared|configured|deployed|tested|"
    r"monitored|coordinated|facilitated|trained|resolved)\b",
    re.IGNORECASE,
)

URL_EMAIL_RE = re.compile(
    r"(?:https?://|www\.|github\.com|linkedin\.com|[\w.+-]+@[\w.-]+\.\w+)",
    re.IGNORECASE,
)

SKILL_SEP_RE = re.compile(r"(?:\s*[|???]\s*|,\s*)")

LOCATION_TAIL_RE = re.compile(
    r"^(?P<company>.+?)\s*,?\s+"
    r"(?P<location>"
    r"Remote|Hybrid|On[- ]site|"
    r"[A-Z][A-Za-z.' -]+,\s*(?:[A-Z]{2}|Canada|USA|US|United States|China|India|UK|KE)|"
    r"[A-Z][A-Za-z.' -]+\s+(?:ON|BC|AB|QC|NS|NB|MB|SK|PE|NL|MI|NY|CA|TX|PA|OH|FL|NJ)|"
    r"[A-Z][A-Za-z.' -]+,\s*[A-Z][A-Za-z.' -]+,\s*(?:US|USA|CA|Canada)"
    r")$",
    re.IGNORECASE,
)

AT_ROLE_RE = re.compile(
    r"^(?P<title>.+?)\s+at\s+(?P<company>.+)$",
    re.IGNORECASE,
)


# Expanded headings learned from structural audit.
EMPLOYMENT_HEADINGS.update({
    "professional experiences",
    "working experience",
    "relevant experience",
    "career experience",
    "employment experience",
    "job history",
    "experience summary",
})

STOP_HEADINGS.update({
    "academics",
    "licenses",
    "references",
    "extracurricular",
    "personal projects",
    "course projects",
})


def has_date_range(text: str) -> bool:
    return bool(EXT_RANGE_RE.search(clean(text)))


def extract_date_range(text):
    m = EXT_RANGE_RE.search(clean(text))
    return clean(m.group(0)) if m else ""


def remove_date_text(text):
    return clean(EXT_RANGE_RE.sub(" ", clean(text)).strip(" ,|-"))


def normalize_candidate(text):
    s = clean(text)
    s = ROLE_LABEL_RE.sub("", s)
    s = COMPANY_LABEL_RE.sub("", s)
    return clean(s.strip(" ,;|:-"))


def hard_reject(text):
    s = clean(text)

    if not s:
        return True
    if NON_EMPLOYMENT_RE.match(s):
        return True
    if BODY_START_RE.match(s):
        return True
    if URL_EMAIL_RE.search(s):
        return True
    if sentence_like(s):
        return True
    if BODY_VERB_RE.match(s) and len(s.split()) >= 5:
        return True
    if len(s.split()) > 12:
        return True

    # Comma/pipe-heavy technology or keyword lists.
    pieces = [x for x in SKILL_SEP_RE.split(s) if clean(x)]
    if len(pieces) >= 5:
        return True

    return False


def looks_location_only(text):
    s = clean(text)

    if not s or hard_reject(s):
        return False

    if s.lower() in {
        "remote", "hybrid", "onsite", "on-site"
    }:
        return True

    # Do not call an organization a location merely because it contains
    # a geographic word.
    low = s.lower()
    if any(w in low.split() for w in COMPANY_WORDS):
        return False

    return bool(re.fullmatch(
        r"(?:[A-Z][A-Za-z.' -]+,\s*)?"
        r"(?:[A-Z]{2}|Canada|USA|US|China|India|UK|Remote|Hybrid|"
        r"[A-Z][A-Za-z.' -]+\s+(?:ON|BC|AB|QC|MI|NY|CA|TX|PA|OH|FL|NJ))",
        s,
        re.IGNORECASE
    ))


def split_company_location(text):
    s = normalize_candidate(text)

    if not s:
        return "", ""

    # Explicit trailing Remote/Hybrid.
    m = re.match(
        r"^(?P<company>.+?)\s*,\s*(?P<location>Remote|Hybrid|On[- ]site)$",
        s,
        re.IGNORECASE
    )
    if m:
        return clean(m.group("company")), clean(m.group("location"))

    m = LOCATION_TAIL_RE.match(s)
    if m:
        company = clean(m.group("company").strip(" ,-"))
        location = clean(m.group("location"))
        if company and not hard_reject(company):
            return company, location

    return s, ""


def split_visual_segments(line, gap_threshold=35.0):
    spans = sorted(line.spans, key=lambda x: x.x0)
    if not spans:
        return []

    groups = [[spans[0]]]

    for span in spans[1:]:
        previous = groups[-1][-1]
        gap = span.x0 - previous.x1

        # Geometry is primary evidence. Larger horizontal whitespace
        # means separate semantic fields.
        if gap >= gap_threshold:
            groups.append([span])
        else:
            groups[-1].append(span)

    out = []

    for group in groups:
        text = clean(" ".join(x.text for x in group))
        if not text:
            continue

        out.append({
            "text": text,
            "x0": min(x.x0 for x in group),
            "x1": max(x.x1 for x in group),
            "bold": any(x.bold for x in group),
            "font_size": max(x.size for x in group),
        })

    return out


def candidate_parts(line):
    parts = []

    for seg in split_visual_segments(line):
        raw = clean(seg["text"])
        if not raw:
            continue

        text = normalize_candidate(remove_date_text(raw))
        if not text or hard_reject(text):
            continue

        # Handle "Title at Company" as two source-supported candidates.
        m = AT_ROLE_RE.match(text)

        if m:
            values = [
                ("title_hint", clean(m.group("title"))),
                ("company_hint", clean(m.group("company"))),
            ]
        else:
            values = [("", text)]

        for hint, value in values:
            if not value or hard_reject(value):
                continue

            parts.append({
                "text": value,
                "hint": hint,
                "x0": seg["x0"],
                "x1": seg["x1"],
                "bold": seg["bold"],
                "font_size": seg["font_size"],
                "page": line.page,
                "y0": line.y0,
            })

    return parts


def title_score_v11(item):
    s = normalize_candidate(item["text"])

    if hard_reject(s) or looks_location_only(s):
        return -100

    words = [x.lower().strip(".,()") for x in s.split()]
    score = 0

    score += 5 * sum(x in TITLE_WORDS for x in words)

    if item.get("hint") == "title_hint":
        score += 10
    if item.get("hint") == "company_hint":
        score -= 10

    if 1 <= len(words) <= 7:
        score += 3

    if item.get("bold"):
        score += 2

    if any(x in COMPANY_WORDS for x in words):
        score -= 3

    score += max(0, 4 - item.get("distance", 9))

    return score


def company_score_v11(item):
    s = normalize_candidate(item["text"])

    if hard_reject(s) or looks_location_only(s):
        return -100

    company, location = split_company_location(s)

    if not company or hard_reject(company):
        return -100

    words = [x.lower().strip(".,()") for x in company.split()]
    score = 0

    score += 4 * sum(x in COMPANY_WORDS for x in words)

    if item.get("hint") == "company_hint":
        score += 10
    if item.get("hint") == "title_hint":
        score -= 10

    if 1 <= len(words) <= 8:
        score += 3

    if item.get("bold"):
        score += 2

    title_hits = sum(x in TITLE_WORDS for x in words)
    score -= 3 * title_hits

    score += max(0, 4 - item.get("distance", 9))

    return score


def collect_record_window(lines, idx):
    anchor = lines[idx]
    result = []

    # Tight window avoids crossing unrelated records.
    for j in range(max(0, idx - 2), min(len(lines), idx + 3)):
        line = lines[j]

        if line.page != anchor.page:
            continue

        if j != idx and has_date_range(line.text):
            continue

        heading = normalized_heading(line.text)

        if heading in STOP_HEADINGS or NON_EMPLOYMENT_RE.match(line.text):
            continue

        if BODY_START_RE.match(line.text):
            continue

        result.append((j, line))

    return result


def find_employment_lines(lines):
    start = None
    end = len(lines)

    for i, line in enumerate(lines):
        h = normalized_heading(line.text)
        if h in EMPLOYMENT_HEADINGS:
            start = i + 1
            break

    if start is not None:
        for i in range(start, len(lines)):
            h = normalized_heading(lines[i].text)
            if h in STOP_HEADINGS:
                end = i
                break
        return lines[start:end]

    # Conservative no-heading fallback:
    # retain document evidence only when employment-style date ranges exist.
    anchors = [i for i, x in enumerate(lines) if has_date_range(x.text)]

    if not anchors:
        return []

    first = max(0, anchors[0] - 3)
    last = min(len(lines), anchors[-1] + 5)
    return lines[first:last]


def build_layout_records(pdf_path):
    result = analyze_pdf(pdf_path)

    # Re-run section selection because analyze_pdf used whichever definition
    # existed when called, while this V1.1 function is authoritative.
    all_lines = result["visual_lines"]
    emp_lines = find_employment_lines(all_lines)

    anchors = [
        i for i, line in enumerate(emp_lines)
        if has_date_range(line.text)
    ]

    records = []

    for rec_no, idx in enumerate(anchors, 1):
        anchor = emp_lines[idx]
        date_range = extract_date_range(anchor.text)

        window = collect_record_window(emp_lines, idx)
        candidates = []

        for j, line in window:
            # Responsibility prose is never title/company evidence.
            if (
                j != idx
                and (sentence_like(line.text) or BODY_VERB_RE.match(clean(line.text)))
            ):
                continue

            for part in candidate_parts(line):
                part["distance"] = abs(j - idx)
                part["line_index"] = j
                candidates.append(part)

        # ----------------------------------------------------------
        # LOCATION
        # ----------------------------------------------------------
        location = ""
        location_source = None

        # Geometry-separated right-side location has strongest priority.
        for j, line in window:
            segments = split_visual_segments(line)

            if len(segments) >= 2:
                for seg in reversed(segments[1:]):
                    txt = normalize_candidate(remove_date_text(seg["text"]))

                    if looks_location_only(txt):
                        location = txt
                        location_source = txt
                        break

            if location:
                break

        # Company+location in one segment.
        split_candidates = []

        for item in candidates:
            company_part, location_part = split_company_location(item["text"])

            if location_part:
                split_candidates.append(
                    (company_part, location_part, item)
                )

        if not location and split_candidates:
            best_split = min(
                split_candidates,
                key=lambda x: x[2].get("distance", 99)
            )
            location = best_split[1]
            location_source = best_split[2]["text"]

        # ----------------------------------------------------------
        # TITLE / COMPANY
        # ----------------------------------------------------------
        title_ranked = sorted(
            [(title_score_v11(x), x) for x in candidates],
            key=lambda x: x[0],
            reverse=True
        )

        company_ranked = sorted(
            [(company_score_v11(x), x) for x in candidates],
            key=lambda x: x[0],
            reverse=True
        )

        title = ""
        title_item = None

        for score, item in title_ranked:
            if score < 5:
                break

            value = normalize_candidate(item["text"])

            # If candidate is company+location, do not make it title.
            cp, lp = split_company_location(value)
            if lp and cp != value:
                continue

            title = value
            title_item = item
            break

        company = ""
        company_item = None

        for score, item in company_ranked:
            if score < 4:
                break

            value = normalize_candidate(item["text"])
            cp, lp = split_company_location(value)

            if not cp:
                continue

            if title and cp.lower() == title.lower():
                continue

            # Avoid selecting another occupational title as employer.
            if title_score_v11({**item, "text": cp}) > score + 3:
                continue

            company = cp
            company_item = item

            if not location and lp:
                location = lp
                location_source = value

            break

        # Explicit Role:/Title: and Company:/Client: labels override
        # statistical scoring because they are direct document evidence.
        for j, line in window:
            raw = clean(line.text)

            if ROLE_LABEL_RE.match(raw):
                v = normalize_candidate(remove_date_text(raw))
                if v and not hard_reject(v):
                    title = v

            if COMPANY_LABEL_RE.match(raw):
                v = normalize_candidate(remove_date_text(raw))
                cp, lp = split_company_location(v)
                if cp and not hard_reject(cp):
                    company = cp
                    if lp and not location:
                        location = lp

        # ----------------------------------------------------------
        # SOURCE / COLLISION VALIDATION
        # ----------------------------------------------------------
        source_text = clean(" ".join(x.text for _, x in window)).lower()

        title_supported = bool(title and title.lower() in source_text)
        company_supported = bool(company and company.lower() in source_text)
        date_supported = bool(date_range and date_range.lower() in source_text)

        collision = bool(
            title and company and title.lower() == company.lower()
        )

        material_bad = (
            collision
            or (title and hard_reject(title))
            or (company and hard_reject(company))
            or (title and looks_location_only(title))
            or (company and looks_location_only(company))
            or (title and not title_supported)
            or (company and not company_supported)
            or not date_supported
        )

        # PASS is deliberately strict. False PASS is worse than review.
        strong_title = bool(
            title
            and title_supported
            and title_ranked
            and title_ranked[0][0] >= 7
        )

        strong_company = bool(
            company
            and company_supported
            and company_ranked
            and company_ranked[0][0] >= 5
        )

        if (
            strong_title
            and strong_company
            and date_range
            and not material_bad
        ):
            status = "PASS"
            confidence = 0.95 + (0.05 if location else 0.0)
        else:
            status = "REVIEW_REQUIRED"

            confidence = 0.15
            confidence += 0.30 if title_supported else 0
            confidence += 0.30 if company_supported else 0
            confidence += 0.15 if date_supported else 0
            confidence += 0.05 if location else 0

            confidence = min(confidence, 0.89)

        records.append({
            "title": title,
            "company": company,
            "location": location,
            "date_range": date_range,
            "confidence": round(confidence, 2),
            "status": status,
            "source": "DETERMINISTIC",
            "title_supported": title_supported,
            "company_supported": company_supported,
            "date_supported": date_supported,
        })

    # --------------------------------------------------------------
    # BUSINESS FIELDS
    # Preserve source/document order. Do not invent missing fields.
    # --------------------------------------------------------------
    current_title = records[0]["title"] if records else ""
    current_company = records[0]["company"] if records else ""

    previous_titles = [
        r["title"]
        for r in records[1:]
        if r.get("title")
    ]

    overall_status = (
        "PASS"
        if records and all(r["status"] == "PASS" for r in records)
        else "REVIEW_REQUIRED"
    )

    return {
        "engine_version": ENGINE_VERSION,
        "pdf_path": pdf_path,
        "status": overall_status,
        "current_job_title": current_title,
        "current_company": current_company,
        "previous_job_titles": previous_titles,
        "records": records,
    }


def print_layout_records(pdf_path):
    result = build_layout_records(pdf_path)

    print("=" * 110)
    print("LAYOUT EMPLOYMENT RECORDS")
    print("ENGINE :", result["engine_version"])
    print("FILE   :", ascii_safe(pdf_path))
    print("STATUS :", result["status"])
    print("CURRENT TITLE   :", ascii_safe(result["current_job_title"]))
    print("CURRENT COMPANY :", ascii_safe(result["current_company"]))
    print(
        "PREVIOUS TITLES:",
        ascii_safe(" ~~ ".join(result["previous_job_titles"]))
    )
    print("=" * 110)

    for i, rec in enumerate(result["records"], 1):
        print(
            f"{i:02d} | "
            f"TITLE={ascii_safe(rec['title'])} | "
            f"COMPANY={ascii_safe(rec['company'])} | "
            f"LOCATION={ascii_safe(rec['location'])} | "
            f"DATE={ascii_safe(rec['date_range'])} | "
            f"CONF={rec['confidence']:.2f} | "
            f"{rec['status']} | "
            f"SRC=T{int(rec['title_supported'])}"
            f"C{int(rec['company_supported'])}"
            f"D{int(rec['date_supported'])}"
        )

    print("=" * 110)
    print("OLLAMA : NONE")
    print("CHROMA : NONE")



# ==================================================================
# CONSOLIDATED STRUCTURAL VALIDATION V1.2
# Built from the blind 100-resume regression failure classes.
# No Ollama. No Chroma.
# ==================================================================

ENGINE_VERSION = "layout_candidate_engine_v1_2"

STRUCTURAL_SECTION_WORDS = {
    "education", "academics", "academic background",
    "projects", "project experience", "academic projects",
    "personal projects", "course projects", "major projects",
    "major project achievements", "major projects achievements",
    "skills", "technical skills", "core skills", "key skills",
    "technologies", "technology", "tools",
    "certifications", "certificates", "licenses",
    "awards", "honors", "publications",
    "volunteer", "volunteer work", "volunteering",
    "extracurricular", "extracurriculars",
    "extracurricular activities", "activities",
    "interests", "references",
    "security clearance",
}

EMPLOYMENT_SECTION_WORDS = {
    "experience", "work experience", "working experience",
    "professional experience", "professional experiences",
    "employment", "employment history", "employment experience",
    "work history", "job history", "career history",
    "career experience", "relevant experience",
    "professional work history", "experience summary",
}

ROLE_TERMS_V12 = {
    "engineer", "engineering", "developer", "analyst",
    "architect", "manager", "director", "consultant",
    "specialist", "administrator", "assistant",
    "associate", "intern", "internship", "technician",
    "technologist", "scientist", "researcher",
    "coordinator", "executive", "representative",
    "advisor", "adviser", "lead", "leader",
    "supervisor", "officer", "president",
    "founder", "owner", "tutor", "teacher",
    "professor", "instructor", "receptionist",
    "barista", "captain", "member", "designer",
    "programmer", "sales", "account", "qa",
    "tester", "scrum", "product", "project",
    "business", "software", "firmware", "data",
    "cloud", "machine", "marketing", "finance",
}

COMPANY_SUFFIX_RE_V12 = re.compile(
    r"\b(?:inc|incorporated|corp|corporation|company|co|llc|ltd|limited|"
    r"lp|llp|plc|group|systems?|solutions?|technologies|technology|"
    r"consulting|services?|bank|university|college|academy|institute|"
    r"health|healthcare|financial|capital|labs?|studio|media|software|"
    r"enterprises?|partners?|holdings?)\.?\b",
    re.IGNORECASE,
)

PROSE_START_RE_V12 = re.compile(
    r"^\s*(?:"
    r"achieved|administered|analyzed|analysed|assessed|assisted|"
    r"built|collaborated|conducted|configured|coordinated|created|"
    r"decreased|delivered|deployed|designed|developed|demonstrated|"
    r"ensured|established|evaluated|executed|facilitated|generated|"
    r"identified|implemented|improved|increased|installed|integrated|"
    r"led|maintained|managed|mapped|minimized|minimizing|monitored|"
    r"optimized|participated|performed|prepared|provided|reduced|"
    r"reported|research(?:ed|ing)?|resolved|reviewed|showcased|"
    r"showcasing|supported|tested|trained|utilized|used|worked|"
    r"working|responsible|responsibilities|duties|"
    r"setting|preparing|providing|creating|ensuring|developing|"
    r"designing|implementing|managing|supporting"
    r")\b",
    re.IGNORECASE,
)

PROSE_PHRASE_RE_V12 = re.compile(
    r"\b(?:responsible for|responsibilities include|"
    r"worked with|worked on|experience with|"
    r"requirements to|business growth|revenue \$|"
    r"clients demonstrating|team'?s target|"
    r"available upon request|references available|"
    r"focused on|ensuring continuous|"
    r"sales presentations|sales meetings)\b",
    re.IGNORECASE,
)

SKILL_LIST_RE_V12 = re.compile(
    r"\b(?:python|java|javascript|typescript|react|angular|"
    r"salesforce|sales loft|outreach|sql|c\+\+|c#|"
    r"aws|azure|docker|kubernetes|tableau|power bi|"
    r"excel|jira|git|github)\b",
    re.IGNORECASE,
)

COMBINED_TITLE_COMPANY_RE_V12 = re.compile(
    r"^(?P<title>.+?)\s*(?:\s[-??]\s|\s+\|\s+|,\s+)"
    r"(?P<company>.+)$"
)


def canonical_heading_v12(text):
    s = clean(text).lower()

    # Repair spaced headings such as "E XPERIENCE".
    letters_only = re.sub(r"[^a-z]", "", s)

    if letters_only == "experience":
        return "experience"
    if letters_only == "workexperience":
        return "work experience"
    if letters_only == "professionalexperience":
        return "professional experience"
    if letters_only == "employmenthistory":
        return "employment history"

    s = re.sub(r"[:|]+$", "", s).strip()
    s = re.sub(r"\s+", " ", s)
    return s


def is_structural_heading_v12(text):
    h = canonical_heading_v12(text)

    if h in STRUCTURAL_SECTION_WORDS:
        return True

    # Headings sometimes contain a little decoration.
    if len(h.split()) <= 5:
        for x in STRUCTURAL_SECTION_WORDS:
            if h == x or h.startswith(x + " "):
                return True

    return False


def is_employment_heading_v12(text):
    h = canonical_heading_v12(text)
    return h in EMPLOYMENT_SECTION_WORDS


def is_prose_v12(text):
    s = clean(text)

    if not s:
        return True

    if PROSE_START_RE_V12.search(s):
        return True

    if PROSE_PHRASE_RE_V12.search(s):
        return True

    # Normal prose punctuation is strong negative evidence.
    if s.endswith((".", ";")) and len(s.split()) >= 4:
        return True

    if len(s.split()) >= 9 and (
        "," in s or
        any(x in s.lower().split() for x in {
            "and", "the", "to", "for", "with", "of"
        })
    ):
        return True

    return False


def is_skill_list_v12(text):
    s = clean(text)

    if not s:
        return False

    hits = len(SKILL_LIST_RE_V12.findall(s))

    separators = (
        s.count(",") +
        s.count("|") +
        s.count("/") +
        s.count("?")
    )

    return hits >= 2 and separators >= 1


def is_nonemployment_context_v12(text):
    s = clean(text)
    low = s.lower()

    if is_structural_heading_v12(s):
        return True

    bad = (
        "bachelor of ",
        "master of ",
        "bachelor's ",
        "master's ",
        "degree in ",
        "coursework",
        "gpa:",
        "major projects",
        "project achievements",
        "extracurricular activities",
        "volunteer work",
        "security clearance",
        "references available",
    )

    return any(x in low for x in bad)


def hard_reject(text):
    s = clean(text)

    if not s:
        return True

    if is_structural_heading_v12(s):
        return True

    if is_nonemployment_context_v12(s):
        return True

    if BODY_START_RE.match(s):
        return True

    if URL_EMAIL_RE.search(s):
        return True

    if is_prose_v12(s):
        return True

    if is_skill_list_v12(s):
        return True

    if len(s.split()) > 12:
        return True

    return False


def valid_title_v12(text):
    s = normalize_candidate(text)

    if hard_reject(s) or looks_location_only(s):
        return False

    low = s.lower()

    # Organization/section labels cannot be job titles.
    if low in STRUCTURAL_SECTION_WORDS:
        return False

    if low in {
        "earlier employment", "professional work history",
        "experience", "work history", "employment"
    }:
        return False

    if is_skill_list_v12(s) or is_prose_v12(s):
        return False

    words = re.findall(r"[A-Za-z]+", low)

    # Single lowercase/common fragments such as "countries".
    if len(words) == 1 and s[:1].islower():
        return False

    return True


def valid_company_v12(text):
    s = normalize_candidate(text)

    if hard_reject(s) or looks_location_only(s):
        return False

    low = s.lower()

    if low in STRUCTURAL_SECTION_WORDS:
        return False

    if low in EMPLOYMENT_SECTION_WORDS:
        return False

    if low in {
        "experience", "e xperience",
        "extracurriculars", "extracurricular activities",
        "volunteer work", "major projects achievements",
        "professional work history", "earlier employment",
    }:
        return False

    if is_prose_v12(s) or is_skill_list_v12(s):
        return False

    words = re.findall(r"[A-Za-z]+", s)

    if not words:
        return False

    # Reject lowercase sentence fragments: countries, needs, surveys...
    if s[:1].islower():
        return False

    if len(words) == 1 and words[0].lower() in {
        "countries", "needs", "surveys", "requirements",
        "achievements", "responsibilities", "references",
        "projects", "activities", "skills"
    }:
        return False

    return True


def split_title_company_v12(text):
    s = normalize_candidate(text)

    if not s:
        return "", ""

    # Explicit "Role at Company".
    m = AT_ROLE_RE.match(s)
    if m:
        t = clean(m.group("title"))
        c = clean(m.group("company"))
        if valid_title_v12(t) and valid_company_v12(c):
            return t, c

    # Common student/professional format:
    # "IT INTERN- CITISCAPE LLC"
    # Require occupational evidence on left to avoid splitting normal names.
    for sep in (" - ", " ? ", " ? ", " | ", "- "):
        if sep in s:
            left, right = s.split(sep, 1)
            left = clean(left)
            right = clean(right)

            left_words = set(re.findall(r"[a-z]+", left.lower()))

            if (
                left_words & ROLE_TERMS_V12
                and valid_title_v12(left)
                and valid_company_v12(right)
            ):
                return left, right

    # "Sr. Business Analyst, Bell Canada"
    if "," in s:
        left, right = s.split(",", 1)
        left = clean(left)
        right = clean(right)

        left_words = set(re.findall(r"[a-z]+", left.lower()))

        if (
            left_words & ROLE_TERMS_V12
            and 1 <= len(left.split()) <= 7
            and valid_title_v12(left)
            and valid_company_v12(right)
        ):
            return left, right

    return "", ""


def candidate_parts(line):
    parts = []

    for seg in split_visual_segments(line):
        raw = clean(seg["text"])

        if not raw:
            continue

        text = normalize_candidate(remove_date_text(raw))

        if not text or hard_reject(text):
            continue

        title_part, company_part = split_title_company_v12(text)

        if title_part and company_part:
            values = [
                ("title_hint", title_part),
                ("company_hint", company_part),
            ]
        else:
            m = AT_ROLE_RE.match(text)

            if m:
                values = [
                    ("title_hint", clean(m.group("title"))),
                    ("company_hint", clean(m.group("company"))),
                ]
            else:
                values = [("", text)]

        for hint, value in values:
            if not value or hard_reject(value):
                continue

            parts.append({
                "text": value,
                "hint": hint,
                "x0": seg["x0"],
                "x1": seg["x1"],
                "bold": seg["bold"],
                "font_size": seg["font_size"],
                "page": line.page,
                "y0": line.y0,
            })

    return parts


def title_score_v11(item):
    s = normalize_candidate(item["text"])

    if not valid_title_v12(s):
        return -100

    words = [x.lower().strip(".,()") for x in s.split()]
    score = 0

    score += 5 * sum(x in TITLE_WORDS for x in words)
    score += 3 * sum(x in ROLE_TERMS_V12 for x in words)

    if item.get("hint") == "title_hint":
        score += 12

    if item.get("hint") == "company_hint":
        score -= 12

    if 1 <= len(words) <= 7:
        score += 3

    if item.get("bold"):
        score += 2

    if COMPANY_SUFFIX_RE_V12.search(s):
        score -= 5

    score += max(0, 4 - item.get("distance", 9))

    return score


def company_score_v11(item):
    s = normalize_candidate(item["text"])

    if not valid_company_v12(s):
        return -100

    company, location = split_company_location(s)

    if not company or not valid_company_v12(company):
        return -100

    words = [x.lower().strip(".,()") for x in company.split()]
    score = 0

    score += 4 * sum(x in COMPANY_WORDS for x in words)

    if COMPANY_SUFFIX_RE_V12.search(company):
        score += 6

    if item.get("hint") == "company_hint":
        score += 12

    if item.get("hint") == "title_hint":
        score -= 12

    if 1 <= len(words) <= 8:
        score += 3

    if item.get("bold"):
        score += 2

    title_hits = sum(x in ROLE_TERMS_V12 for x in words)

    if title_hits >= 2 and not COMPANY_SUFFIX_RE_V12.search(company):
        score -= 5

    score += max(0, 4 - item.get("distance", 9))

    return score


def find_employment_lines(lines):
    start = None
    end = len(lines)

    # Prefer explicit employment section.
    for i, line in enumerate(lines):
        if is_employment_heading_v12(line.text):
            start = i + 1
            break

    if start is not None:
        for i in range(start, len(lines)):
            if is_structural_heading_v12(lines[i].text):
                end = i
                break

        return lines[start:end]

    # No explicit heading: conservative date-anchor fallback.
    anchors = [
        i for i, line in enumerate(lines)
        if has_date_range(line.text)
    ]

    if not anchors:
        return []

    first = max(0, anchors[0] - 3)
    last = min(len(lines), anchors[-1] + 4)

    candidate_lines = lines[first:last]

    # Do not continue through a later non-employment section.
    safe = []

    for line in candidate_lines:
        if safe and is_structural_heading_v12(line.text):
            break
        safe.append(line)

    return safe


def collect_record_window(lines, idx):
    anchor = lines[idx]
    result = []

    for j in range(max(0, idx - 2), min(len(lines), idx + 3)):
        line = lines[j]

        if line.page != anchor.page:
            continue

        if j != idx and has_date_range(line.text):
            continue

        if is_structural_heading_v12(line.text):
            continue

        if BODY_START_RE.match(clean(line.text)):
            continue

        if is_prose_v12(line.text):
            continue

        result.append((j, line))

    return result


# Keep V1.1 record assembly, but enforce V1.2 semantic validation
# immediately before records are exposed to business fields.
_build_layout_records_v11 = build_layout_records


def build_layout_records(pdf_path):
    result = _build_layout_records_v11(pdf_path)

    for rec in result["records"]:
        title = clean(rec.get("title", ""))
        company = clean(rec.get("company", ""))

        # Repair combined title/company selected as title.
        if title and not company:
            t, c = split_title_company_v12(title)
            if t and c:
                title = t
                company = c

        # Repair combined title/company selected as company.
        if company:
            t, c = split_title_company_v12(company)
            if t and c and (not title or not valid_title_v12(title)):
                title = t
                company = c

        title_ok = bool(title and valid_title_v12(title))
        company_ok = bool(company and valid_company_v12(company))

        # Never expose structurally invalid values.
        if not title_ok:
            title = ""

        if not company_ok:
            company = ""

        rec["title"] = title
        rec["company"] = company

        rec["title_supported"] = bool(
            title and rec.get("title_supported", False)
        )
        rec["company_supported"] = bool(
            company and (
                rec.get("company_supported", False)
                or company.lower() in clean(
                    " ".join([
                        rec.get("company", ""),
                        rec.get("title", "")
                    ])
                ).lower()
            )
        )

        # V1.2 PASS gate:
        # both business fields must survive semantic validation.
        if not title or not company:
            rec["status"] = "REVIEW_REQUIRED"
            rec["confidence"] = min(rec.get("confidence", 0.0), 0.89)

        elif not valid_title_v12(title) or not valid_company_v12(company):
            rec["status"] = "REVIEW_REQUIRED"
            rec["confidence"] = min(rec.get("confidence", 0.0), 0.89)

        elif title.lower() == company.lower():
            rec["status"] = "REVIEW_REQUIRED"
            rec["confidence"] = min(rec.get("confidence", 0.0), 0.89)

    # Rebuild visible business fields only from validated records.
    records = result["records"]

    result["engine_version"] = ENGINE_VERSION
    result["current_job_title"] = (
        records[0]["title"] if records else ""
    )
    result["current_company"] = (
        records[0]["company"] if records else ""
    )

    result["previous_job_titles"] = [
        r["title"]
        for r in records[1:]
        if r.get("title")
    ]

    result["status"] = (
        "PASS"
        if records and all(r["status"] == "PASS" for r in records)
        else "REVIEW_REQUIRED"
    )

    return result


# ==================================================================
# FINAL DETERMINISTIC SAFETY / NORMALIZATION LAYER V1.3
# Consolidated from the complete V1.2 100-resume regression.
# No Ollama. No Chroma.
# ==================================================================

ENGINE_VERSION = "layout_candidate_engine_v1_3"

V13_NOISE_PREFIX_RE = re.compile(
    r"^[\s???????????????\-\*\?]+"
)

V13_FIELD_LABEL_RE = re.compile(
    r"^(?:"
    r"role|position|job title|title|designation|employer|company|client"
    r")\s*[:\-???]+\s*",
    re.IGNORECASE
)

V13_BAD_HEADING_RE = re.compile(
    r"^(?:"
    r"education|academics?|awards?|languages?|language|"
    r"skills?|technical skills?|coding skills?|analytics|"
    r"contact|linkedin|email|phone|personal data|personal details|"
    r"date of birth|dob|references?|achievements?/tasks?|"
    r"additional projects?|projects?|major projects?|"
    r"extracurriculars?|extracurricular activities|"
    r"volunteer(?:ing| work)?|certifications?|licenses?|"
    r"professional summary|summary|profile|objective|"
    r"job experience|work experience|experience"
    r")$",
    re.IGNORECASE
)

V13_PROSE_RE = re.compile(
    r"^(?:"
    r"achieved|administered|analyzed|analysed|assessed|assisted|"
    r"built|collaborated|conducted|configured|coordinated|created|"
    r"decreased|delivered|deployed|designed|developed|demonstrated|"
    r"ensured|established|evaluated|executed|facilitated|generated|"
    r"identified|implemented|improved|increased|installed|integrated|"
    r"led|maintained|managed|mapped|minimized|minimizing|monitored|"
    r"optimized|participated|performed|prepared|produced|producing|"
    r"provided|reduced|reported|researched|researching|resolved|"
    r"reviewed|showcased|showcasing|supported|tested|trained|"
    r"utilized|used|worked|working|exhibiting|keeping|donate|"
    r"setting|preparing|providing|creating|ensuring|developing|"
    r"designing|implementing|managing|supporting"
    r")\b",
    re.IGNORECASE
)

V13_PROSE_PHRASES_RE = re.compile(
    r"\b(?:"
    r"responsible for|responsibilities include|"
    r"through collaboration|for management|"
    r"under professor|youth empowerment|"
    r"problem solving|critical thinking|"
    r"keeping records|my services|"
    r"specialization in|team'?s target|"
    r"sales presentations|sales meetings|"
    r"requirements for|requirements to|"
    r"clients demonstrating|business growth|"
    r"activity processes|the month nominations|"
    r"additional projects which|conceptual project"
    r")\b",
    re.IGNORECASE
)

V13_SKILL_TOKEN_RE = re.compile(
    r"\b(?:"
    r"python|java|kotlin|android|ios|javascript|typescript|"
    r"react|angular|node|sql|mysql|postgres|oracle|"
    r"aws|azure|gcp|docker|kubernetes|git|github|"
    r"xgboost|lstm|lstms|arima|arimas|pytorch|tensorflow|"
    r"arduino|leds?|potentiometers?|resistors?|"
    r"salesforce|jira|tableau|power\s*bi"
    r")\b",
    re.IGNORECASE
)

V13_ROLE_RE = re.compile(
    r"\b(?:"
    r"engineer|developer|analyst|architect|manager|director|"
    r"consultant|specialist|administrator|assistant|associate|"
    r"intern|technician|technologist|scientist|researcher|"
    r"coordinator|executive|representative|advisor|adviser|"
    r"lead|leader|supervisor|officer|president|founder|owner|"
    r"tutor|teacher|professor|instructor|receptionist|barista|"
    r"captain|designer|programmer|tester|consultant|"
    r"sales|development|marketing|account|qa|support|"
    r"technologist|umpire|writer|coach|commander|"
    r"advisor|crew member|customer service|business development"
    r")\b",
    re.IGNORECASE
)

V13_COMPANY_SIGNAL_RE = re.compile(
    r"\b(?:"
    r"inc|llc|ltd|limited|corp|corporation|company|group|"
    r"systems?|solutions?|technologies|technology|services?|"
    r"bank|insurance|university|college|academy|institute|"
    r"school|hospital|health|healthcare|financial|capital|"
    r"labs?|media|software|foundation|association|centre|center|"
    r"club|team|government|ministry|department|forces?|"
    r"communications?|telecommunications?|realty|restaurant|"
    r"consulting|partners?|holdings?|organization|organisation"
    r")\b",
    re.IGNORECASE
)

V13_LOCATION_RE = re.compile(
    r"^(?:"
    r"remote|hybrid|on[- ]site|"
    r"[A-Z][A-Za-z.' -]+,\s*(?:"
    r"ON|BC|AB|QC|NS|NB|MB|SK|PE|NL|"
    r"MI|NY|CA|TX|PA|OH|FL|NJ|VA|WA|"
    r"Canada|USA|US|United States|India|China|Singapore|Nigeria|Ontario"
    r")|"
    r"[A-Z][A-Za-z.' -]+,\s*[A-Z][A-Za-z.' -]+"
    r")$",
    re.IGNORECASE
)

V13_LOCATION_WORD_RE = re.compile(
    r"\b(?:"
    r"toronto|waterloo|brampton|mississauga|montreal|calgary|"
    r"vancouver|surrey|ottawa|london|markham|richmond hill|"
    r"philadelphia|chicago|new york|california|texas|"
    r"mumbai|karachi|singapore|nigeria"
    r")\b",
    re.IGNORECASE
)


def v13_clean(value):
    s = clean(value)

    # Console/PDF extraction often converts bullets/dashes to '?'.
    s = V13_NOISE_PREFIX_RE.sub("", s).strip()

    # Remove trailing extraction separators.
    s = re.sub(r"\s*\|\s*$", "", s).strip()

    # Normalize repeated whitespace.
    s = re.sub(r"\s+", " ", s)

    return s.strip(" ,;|")


def v13_compact_heading(value):
    s = v13_clean(value).lower()
    return re.sub(r"[^a-z]", "", s)


def v13_is_heading(value):
    s = v13_clean(value)

    if not s:
        return True

    if V13_BAD_HEADING_RE.fullmatch(s):
        return True

    compact = v13_compact_heading(s)

    return compact in {
        "education",
        "awards",
        "languages",
        "skills",
        "technicalskills",
        "codingskills",
        "analytics",
        "contact",
        "linkedin",
        "email",
        "personaldata",
        "personaldetails",
        "dateofbirth",
        "achievements",
        "achievementstasks",
        "projects",
        "majorprojects",
        "extracurriculars",
        "extracurricularactivities",
        "references",
    }


def v13_is_prose(value):
    s = v13_clean(value)

    if not s:
        return False

    if V13_PROSE_RE.search(s):
        return True

    if V13_PROSE_PHRASES_RE.search(s):
        return True

    words = s.split()

    if s.endswith((".", ";")) and len(words) >= 3:
        return True

    if len(words) >= 9 and re.search(
        r"\b(?:the|and|to|for|with|through|under|of|in)\b",
        s,
        re.IGNORECASE
    ):
        return True

    return False


def v13_is_skill_list(value):
    s = v13_clean(value)

    hits = len(V13_SKILL_TOKEN_RE.findall(s))

    separators = (
        s.count(",") +
        s.count("|") +
        s.count("/") +
        s.count("?")
    )

    if hits >= 3:
        return True

    if hits >= 2 and separators >= 1:
        return True

    return False


def v13_is_fragment(value):
    s = v13_clean(value)

    if not s:
        return True

    if re.fullmatch(r"[\d\s/\\\-_.]+", s):
        return True

    if s in {"?", "-", "/", "|"}:
        return True

    if re.fullmatch(r"(?:page\s*)?\d+", s, re.IGNORECASE):
        return True

    if s.lower() in {
        "body", "countries", "contact", "linkedin", "email",
        "analytics", "participation", "personal data",
        "date of birth", "achievements/tasks",
    }:
        return True

    return False


def v13_is_location(value):
    s = v13_clean(value)

    if not s:
        return False

    if V13_LOCATION_RE.fullmatch(s):
        return True

    # Examples: Brampton, Ontario / Toronto, Ontario.
    if (
        V13_LOCATION_WORD_RE.search(s)
        and not V13_COMPANY_SIGNAL_RE.search(s)
        and not V13_ROLE_RE.search(s)
        and len(s.split()) <= 5
    ):
        return True

    if re.fullmatch(
        r"(?:FCT[- ]?)?[A-Za-z.' -]+,\s*(?:Nigeria|Canada|USA|US|India|Ontario)",
        s,
        re.IGNORECASE
    ):
        return True

    return False


def v13_valid_title(value):
    s = v13_clean(value)

    if (
        not s
        or v13_is_heading(s)
        or v13_is_prose(s)
        or v13_is_skill_list(s)
        or v13_is_fragment(s)
        or v13_is_location(s)
    ):
        return False

    low = s.lower()

    if low.startswith(("in the ", "and ", "with specialization ")):
        return False

    if "date of birth" in low:
        return False

    if len(s.split()) > 12:
        return False

    return True


def v13_valid_company(value):
    s = v13_clean(value)

    if (
        not s
        or v13_is_heading(s)
        or v13_is_prose(s)
        or v13_is_skill_list(s)
        or v13_is_fragment(s)
        or v13_is_location(s)
    ):
        return False

    low = s.lower()

    if low.startswith((
        "towards ",
        "additional projects ",
        "keeping ",
        "donate ",
        "developed ",
        "maintained ",
        "marketing team ",
    )):
        return False

    if low in {
        "job experience",
        "coding skills",
        "personal data",
        "date of birth",
        "achievements/tasks",
        "contact",
        "analytics",
    }:
        return False

    if len(s.split()) > 12:
        return False

    return True


def v13_role_strength(value):
    s = v13_clean(value)

    if not s:
        return 0

    return len(V13_ROLE_RE.findall(s))


def v13_company_strength(value):
    s = v13_clean(value)

    if not s:
        return 0

    score = len(V13_COMPANY_SIGNAL_RE.findall(s))

    # Proper-name organization evidence.
    words = [
        x for x in re.findall(r"[A-Za-z][A-Za-z&.'-]*", s)
        if x
    ]

    caps = sum(
        1 for x in words
        if x[:1].isupper() or x.isupper()
    )

    if caps >= 2:
        score += 1

    return score


def v13_split_colon(value):
    s = v13_clean(value)

    if ":" not in s:
        return "", ""

    left, right = [v13_clean(x) for x in s.split(":", 1)]

    # Company: Title
    if (
        left and right
        and v13_company_strength(left) >= 1
        and v13_role_strength(right) >= 1
        and v13_valid_company(left)
        and v13_valid_title(right)
    ):
        return right, left

    return "", ""


def v13_split_company_dash_title(value):
    s = v13_clean(value)

    # Handles "Samsung Electronics - Business Development Management"
    # and "Huawei Technologies - Territory & Marketing Manager".
    for sep in (" - ", " ? ", " ? ", " ? "):
        if sep not in s:
            continue

        left, right = [v13_clean(x) for x in s.split(sep, 1)]

        if (
            left and right
            and v13_company_strength(left) >= 1
            and v13_role_strength(right) >= 1
            and v13_valid_company(left)
            and v13_valid_title(right)
        ):
            return right, left

    return "", ""


def v13_strip_role_label(value):
    s = v13_clean(value)

    s = re.sub(
        r"^role\s*[:\-???]+\s*",
        "",
        s,
        flags=re.IGNORECASE
    )

    return v13_clean(s)


def v13_strip_location_from_company(value):
    s = v13_clean(value)

    # Preserve organization before common dash/location suffix.
    m = re.match(
        r"^(?P<company>.+?)\s+[???-]\s+"
        r"(?P<loc>[A-Z][A-Za-z.' -]+(?:,\s*[A-Za-z.' -]+)?)$",
        s
    )

    if m:
        company = v13_clean(m.group("company"))
        loc = v13_clean(m.group("loc"))

        if (
            v13_valid_company(company)
            and (
                v13_is_location(loc)
                or V13_LOCATION_WORD_RE.search(loc)
            )
        ):
            return company, loc

    return s, ""


_build_layout_records_v12 = build_layout_records


def build_layout_records(pdf_path):
    result = _build_layout_records_v12(pdf_path)

    repaired = []

    for rec in result.get("records", []):
        title = v13_clean(rec.get("title", ""))
        company = v13_clean(rec.get("company", ""))
        location = v13_clean(rec.get("location", ""))

        # ----------------------------------------------------------
        # Normalize explicit labels.
        # ----------------------------------------------------------
        title = v13_strip_role_label(title)

        # ----------------------------------------------------------
        # Company: Title
        # ----------------------------------------------------------
        t, c = v13_split_colon(title)

        if t and c:
            title, company = t, c

        # ----------------------------------------------------------
        # Company - Title stored entirely in title.
        # ----------------------------------------------------------
        t, c = v13_split_company_dash_title(title)

        if t and c:
            title, company = t, c

        # ----------------------------------------------------------
        # Company - Title stored entirely in company.
        # ----------------------------------------------------------
        t, c = v13_split_company_dash_title(company)

        if t and c:
            if not v13_valid_title(title):
                title = t
            company = c

        # ----------------------------------------------------------
        # Strong title/company reversal.
        # Example:
        # Singapore Armed Forces | Lieutenant Platoon Commander
        # Wendy's | Crew Member
        # Foundation | Social Media Manager
        # ----------------------------------------------------------
        if title and company:
            title_role = v13_role_strength(title)
            company_role = v13_role_strength(company)

            title_org = v13_company_strength(title)
            company_org = v13_company_strength(company)

            reverse = False

            if (
                company_role >= 1
                and title_org >= 1
                and title_role == 0
            ):
                reverse = True

            if (
                company_role >= 1
                and company_org == 0
                and title_org > company_org
                and title_role == 0
            ):
                reverse = True

            if reverse:
                title, company = company, title

        # ----------------------------------------------------------
        # Location mistakenly stored as company.
        # ----------------------------------------------------------
        if company and v13_is_location(company):
            if not location:
                location = company
            company = ""

        # ----------------------------------------------------------
        # Company with location suffix.
        # ----------------------------------------------------------
        if company:
            cp, loc = v13_strip_location_from_company(company)

            if cp != company:
                company = cp

                if loc and not location:
                    location = loc

        # ----------------------------------------------------------
        # Final semantic validation.
        # Invalid values are removed rather than falsely exposed.
        # ----------------------------------------------------------
        title_ok = v13_valid_title(title)
        company_ok = v13_valid_company(company)

        if not title_ok:
            title = ""

        if not company_ok:
            company = ""

        # ----------------------------------------------------------
        # Final PASS gate.
        #
        # Source support alone is NOT enough anymore.
        # Both fields must be semantically valid.
        # ----------------------------------------------------------
        safe_pass = bool(
            title
            and company
            and v13_valid_title(title)
            and v13_valid_company(company)
            and title.lower() != company.lower()
            and rec.get("date_range")
        )

        if safe_pass:
            # Do not upgrade records that were structurally uncertain
            # unless V1.3 performed an obvious safe normalization.
            if rec.get("status") == "PASS":
                rec["status"] = "PASS"
                rec["confidence"] = min(
                    max(rec.get("confidence", 0.95), 0.95),
                    1.00
                )
            else:
                rec["status"] = "REVIEW_REQUIRED"
                rec["confidence"] = min(
                    rec.get("confidence", 0.89),
                    0.89
                )
        else:
            rec["status"] = "REVIEW_REQUIRED"
            rec["confidence"] = min(
                rec.get("confidence", 0.89),
                0.89
            )

        rec["title"] = title
        rec["company"] = company
        rec["location"] = location

        # Semantic validation flags.
        rec["v13_title_valid"] = bool(title)
        rec["v13_company_valid"] = bool(company)
        rec["v13_safe_pass"] = (
            rec["status"] == "PASS"
            and bool(title)
            and bool(company)
        )

        repaired.append(rec)

    result["records"] = repaired
    result["engine_version"] = ENGINE_VERSION

    # --------------------------------------------------------------
    # BUSINESS FIELDS
    #
    # Never expose invalid responsibility/skill/location/header text.
    # Keep document order for now; recency ordering can be a separate
    # deterministic integration concern.
    # --------------------------------------------------------------
    if repaired:
        result["current_job_title"] = repaired[0].get("title", "")
        result["current_company"] = repaired[0].get("company", "")
    else:
        result["current_job_title"] = ""
        result["current_company"] = ""

    result["previous_job_titles"] = [
        r["title"]
        for r in repaired[1:]
        if r.get("title") and v13_valid_title(r["title"])
    ]

    result["status"] = (
        "PASS"
        if repaired
        and all(
            r.get("status") == "PASS"
            and r.get("v13_safe_pass")
            for r in repaired
        )
        else "REVIEW_REQUIRED"
    )

    return result

if __name__ == "__main__":
    import argparse
    import sys

    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

    parser = argparse.ArgumentParser()
    parser.add_argument("pdf")
    args = parser.parse_args()

    print_layout_records(args.pdf)
