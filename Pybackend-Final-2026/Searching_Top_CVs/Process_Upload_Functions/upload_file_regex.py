import tempfile
"""
/******************************************************************************************************************************************************************************
 *
 *                          Solution: Smart-Recruitment(Python)
 *                          Description: Handles the parsing, adding, and updating of the resumes metadata and text on to the ChromaDB collection(using regex expressions only)
 *                          Created Date: March 27, 2025
 *                          Created By: Areeb Khan
 *                          Last Updated Date: March 27, 2025
 *                          Last Updated By: Areeb Khan
 *                          Version: 1.0
 *                          Last Updated Date: August 27, 2026
 *                          Last Updated By: Ahmad sandhu
 *                          Version: 1.1 *
 ********************************************************************************************************************************************************************************/
"""
import os
import re
import docx
import PyPDF2
import sys
import spacy
import chromadb
from datetime import datetime
import logging
from dateutil.relativedelta import relativedelta
from dateutil import parser
from sentence_transformers import SentenceTransformer
from pprint import pprint
from chromadb.config import Settings
import shutil
from dotenv import load_dotenv
from sklearn.cluster import KMeans
import numpy as np
import warnings
from sklearn.exceptions import ConvergenceWarning
from flashtext import KeywordProcessor
import os
import time
from io import BytesIO
import nltk
from nltk.tokenize import word_tokenize
import employment_layout_ollama_validator_v1 as employment_validator

load_dotenv()

chromadb_host = os.getenv('CHROMADB_HOST')
chromadb_port = int(os.getenv('CHROMADB_PORT'))

# Initialize ChromaDB client
client = chromadb.HttpClient(host=chromadb_host, port=chromadb_port, settings=Settings(allow_reset=True, anonymized_telemetry=False))

# Collection names and configuration parameters

# "smart_recruitment" collection
# hnsw_space = os.getenv('COLLECTION_PARAMETER_DISTANCE')
# hnsw_construction_ef = int(os.getenv('COLLECTION_PARAMETER_CONSTRUCTION'))
# hnsw_search_ef = int(os.getenv('COLLECTION_PARAMETER_SEARCH'))
# hnsw_M = int(os.getenv('COLLECTION_PARAMETER_M'))

# "test_recruitment" collection
# collection_name = os.getenv('TEST_COLLECTION_NAME')
# hnsw_space = os.getenv('COLLECTION_PARAMETER_DISTANCE')
# hnsw_construction_ef = int(os.getenv('TEST_COLLECTION_PARAMETER_CONSTRUCTION'))
# hnsw_search_ef = int(os.getenv('TEST_COLLECTION_PARAMETER_SEARCH'))
# hnsw_M = int(os.getenv('TEST_COLLECTION_PARAMETER_M'))

# "test2_recruitment" collection
# collection_name = os.getenv('TEST2_COLLECTION_NAME')
# hnsw_space = os.getenv('COLLECTION_PARAMETER_DISTANCE')
# hnsw_construction_ef = int(os.getenv('TEST2_COLLECTION_PARAMETER_CONSTRUCTION'))
# hnsw_search_ef = int(os.getenv('TEST2_COLLECTION_PARAMETER_SEARCH'))
# hnsw_M = int(os.getenv('TEST2_COLLECTION_PARAMETER_M'))

# "test3_recruitment" collection
hnsw_space = os.getenv('COLLECTION_PARAMETER_DISTANCE')
collection_name = os.getenv('TEST3_COLLECTION_NAME')
hnsw_construction_ef = int(os.getenv('TEST3_COLLECTION_PARAMETER_CONSTRUCTION'))
hnsw_search_ef = int(os.getenv('TEST3_COLLECTION_PARAMETER_SEARCH'))
hnsw_M = int(os.getenv('TEST3_COLLECTION_PARAMETER_M'))

# "smart_recruitment_768_128_48" collection
# hnsw_space = os.getenv('COLLECTION_PARAMETER_DISTANCE')
# collection_name = os.getenv('SR_768_128_48_COLLECTION_NAME')
# hnsw_construction_ef = int(os.getenv('SR_768_128_48_COLLECTION_PARAMETER_CONSTRUCTION'))
# hnsw_search_ef = int(os.getenv('SR_768_128_48_COLLECTION_PARAMETER_SEARCH'))
# hnsw_M = int(os.getenv('SR_768_128_48_COLLECTION_PARAMETER_M'))

# Get the collection(collection_name) if it exists and if not create another one
collection = client.get_or_create_collection(
    name=collection_name,
    metadata={
        "hnsw:space": hnsw_space,  # Specify the distance function
        "hnsw:construction_ef": hnsw_construction_ef,
        "hnsw:search_ef": hnsw_search_ef,   # Search_ef for better recall and accuracy
        "hnsw:M": hnsw_M             # M for better graph connectivity
    }
)

nlp = spacy.load("en_core_web_md")

# Models to convert resume text into embedding

job_title_model = SentenceTransformer('all-MiniLM-L6-v2')
# model = SentenceTransformer("hkunlp/instructor-xl")
# model = SentenceTransformer("intfloat/e5-large-v2")
# model = SentenceTransformer("BAAI/bge-large-en-v1.5")
# model = SentenceTransformer("sentence-transformers/paraphrase-mpnet-base-v2")
model = SentenceTransformer('sentence-transformers/msmarco-distilbert-base-v4')

processed_folder = os.getenv('PROCESSED_DATA_FOLDER')
unprocessed_folder = os.getenv('UNPROCESSED_DATA_FOLDER')
skills_file_path = os.getenv('SKILLS_FILE')
job_titles_file_path = os.getenv('JOB_TITLE_FILE')

if skills_file_path and not os.path.isabs(skills_file_path):
    skills_file_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        skills_file_path
    )
    
if job_titles_file_path and not os.path.isabs(job_titles_file_path):
    job_titles_file_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        job_titles_file_path
    )

    
"""Functions for the Upload Resume Python File"""

def extract_employment_years(date_text):
    """
    Extract and normalize years from employment date text.

    Examples:
        May 2024 - Aug 2024  -> [2024, 2024]
        07/2024 - Present    -> [2024]
        9/21 to Present      -> [2021]
        8/20 to 8/21         -> [2020, 2021]
        Mar'24 - Present     -> [2024]
        Mar’24 - Present     -> [2024]
        2022 - 2023          -> [2022, 2023]
    """

    if not date_text:
        return []

    years = []

    # Four-digit years
    four_digit_years = re.findall(
        r'(?<!\d)(?:19|20)\d{2}(?!\d)',
        date_text
    )

    years.extend(
        int(year)
        for year in four_digit_years
    )

    # Numeric month / two-digit year
    #
    # 9/21
    # 08/20
    numeric_short_years = re.findall(
        r'(?<!\d)(?:0?[1-9]|1[0-2])/(\d{2})(?!\d)',
        date_text
    )

    years.extend(
        2000 + int(year)
        for year in numeric_short_years
    )

    # Month-name + apostrophe + two-digit year
    #
    # Mar'24
    # Mar’24
    apostrophe_short_years = re.findall(
        r"[A-Za-z]{3,9}\s*['\u2019](\d{2})(?!\d)",
        date_text
    )

    years.extend(
        2000 + int(year)
        for year in apostrophe_short_years
    )

    return years

def parse_single_date(date_str, current_date):
    """Parse a single date (e.g., "Sept 2018", "07/2024", or "Present")."""
    try:
        #date_str = date_str.replace('Sept', 'Sep')
        date_str = re.sub(
            r'(?i)\bSept(?=\.?\s+\d{4}\b)',
            'Sep',
            date_str
        )        
        print(f"Parsing date: {date_str}")

        # Handle "Present" or "Current"
        if re.fullmatch(
            r"(?i)(?:Present|Current|Today|Ongoing|Now|To\s+Date|Till\s+Date|Till\s+Now|Continued|Continuing|Until\s+Date|Until\s+Now)",
            date_str.strip()
        ):
            return current_date
        
        # if date_str.lower() in ["present", "current", "to date"]:
        #     return current_date

        # Handle numeric month/two-digit-year formats (e.g., "9/21", "08/20").
        short_numeric_match = re.fullmatch(r'(0?[1-9]|1[0-2])/(\d{2})', date_str.strip())
        if short_numeric_match:
            month = int(short_numeric_match.group(1))
            short_year = int(short_numeric_match.group(2))
            year = 2000 + short_year if short_year <= 50 else 1900 + short_year
            if 1900 <= year <= current_date.year:
                return datetime(year, month, 1)
            return None

        # Normalize curly apostrophe before the existing apostrophe parser.
        date_str = date_str.replace('’', "'")

        # V3: corpus-backed short month/year normalization.
        # Examples: Sept 20, Nov-19, Feb '00, July'18.
        short_month_match = re.fullmatch(
            r"(?i)(Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:t(?:ember)?)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)\.?\s*[-/' ]?\s*(\d{2})",
            date_str.strip()
        )
        if short_month_match:
            month_text = re.sub(r'(?i)^Sept$', 'Sep', short_month_match.group(1))
            short_year = int(short_month_match.group(2))
            year = 2000 + short_year if short_year <= 50 else 1900 + short_year
            try:
                month_num = datetime.strptime(month_text[:3], "%b").month
                if 1900 <= year <= current_date.year:
                    return datetime(year, month_num, 1)
                # V5: this token was conclusively recognized as month + two-digit
                # year.  If that year is outside the accepted range (for example
                # "Feb 29" -> Feb 2029 while current year is earlier), stop here.
                # Do not fall through to dateutil, which can reinterpret 29 as a
                # day-of-month and raise "day is out of range for month".
                return None
            except ValueError:
                return None

        # Handle year-only formats (e.g., "2015")
        if re.match(r'^\d{4}$', date_str):
            year = int(date_str)
            if 1900 <= year <= current_date.year:
                parsed_date = datetime(year, 1, 1)
                print(f"Parsed year-only date: {parsed_date}")
                return parsed_date
            else:
                print(f"Invalid year: {year}")
                return None

        # Handle month/year formats (e.g., "07/2024")
        if re.match(r'^\d{2}/\d{4}$', date_str):
            month, year = map(int, date_str.split('/'))
            if 1 <= month <= 12 and 1900 <= year <= current_date.year:
                parsed_date = datetime(year, month, 1)
                print(f"Parsed month/year date: {parsed_date}")
                return parsed_date
            else:
                print(f"Invalid month/year: {date_str}")
                return None
            
        # Parse month-year formats (e.g., "May'09")
        if re.match(r"^[A-Za-z]{3,9}'\d{2}$", date_str):
            month, year = date_str.split("'")
            year = int("20" + year) if int(year) <= 50 else int("19" + year)  # Handle '09 as 2009
            parsed_date = datetime(year, datetime.strptime(month, "%b").month, 1)
            print(f"Parsed month-year date with apostrophe: {parsed_date}")
            return parsed_date

        # Parse month-year formats (e.g., "Sept 2018")
        parsed_date = parser.parse(date_str.strip(), fuzzy=True, default=current_date)

        # Validate the parsed date
        if parsed_date.year > current_date.year or parsed_date.year < 1900:
            print(f"Invalid parsed date: {parsed_date}")
            return None

        print(f"Parsed month-year date: {parsed_date}")
        return datetime(parsed_date.year, parsed_date.month, 1)

    except ValueError as e:
        logging.error(f"Error parsing date: {date_str} ({e})")
        print(f"Error parsing date: {date_str} ({e})")
        return None

def calculate_experience(resume_text, exclude_volunteer=True):
    """Calculate non-overlapping employment experience from validated work sections."""
    # Use the same structural section detector as job-title extraction.  A large
    # max_lines value is intentional here: title extraction needs only recent
    # context, while total experience must retain the candidate's full career.
    experience_text = extract_experience_section(resume_text, max_lines=10000)

    if not experience_text or not experience_text.strip():
        print("No validated experience section found for experience calculation.")
        return 0.0

    month = (
        r'(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|'
        r'Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:t(?:ember)?)?|'
        r'Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)\.?'
    )
    current_terms = (
        r'(?:Present|Current|Today|Ongoing|Now|To\s+Date|'
        r'Till\s+Date|Till\s+Now|Continued|Continuing|Until\s+Date|Until\s+Now)'
    )
    date_token = (
        rf'(?:{month}\s*,?\s*\d{{4}}|'
        rf'{month}\s*[\'’]\d{{2}}|'
        rf'{month}\s*[- ]\s*\d{{2}}|'
        rf'(?:0?[1-9]|1[0-2])/\d{{4}}|'
        rf'(?:0?[1-9]|1[0-2])/\d{{2}}|'
        rf'(?:19|20)\d{{2}}|'
        rf'{current_terms})'
    )

    date_matches = list(re.finditer(date_token, experience_text, re.IGNORECASE))
    logging.info(f"Dates Found: {[match.group(0) for match in date_matches]}")
    print(f"Dates Found: {[match.group(0) for match in date_matches]}")

    intervals = []
    current_date = datetime.now()

    for i in range(len(date_matches) - 1):
        start_match = date_matches[i]
        end_match = date_matches[i + 1]
        between_dates = experience_text[start_match.end():end_match.start()]

        if not re.fullmatch(r'\s*(?:[-\u2013\u2014]|to)\s*', between_dates, re.IGNORECASE):
            continue

        start_date_str = start_match.group(0)
        end_date_str = end_match.group(0)
        start_date = parse_single_date(start_date_str, current_date)
        end_date = parse_single_date(end_date_str, current_date)

        if start_date is None or end_date is None:
            continue
        if end_date < start_date:
            print(f"Skipping reversed employment interval: {start_date_str} -> {end_date_str}")
            continue

        interval = (start_date, end_date)
        if interval not in intervals:
            intervals.append(interval)
            print(f"Added interval: {start_date} to {end_date}")

    # Supplemental conservative scan across the complete resume.  This recovers
    # older employment blocks that appear after an intervening EDUCATION/SKILLS
    # section without forcing the title extractor to treat those sections as one
    # continuous experience section.  A date range alone is never sufficient:
    # nearby occupational/explicit-role evidence is required and obvious
    # non-employment contexts are rejected.
    supplemental_range = re.compile(
        rf'(?i)\b(?P<start>{date_token})\s*(?:[-\u2013\u2014]|to)\s*'
        rf'(?P<end>{date_token})\b'
    )
    role_evidence = re.compile(
        r'(?i)\b(?:position|job\s*title|role|title)\s*[:\-]|'
        r'\b(?:architect|engineer|developer|analyst|manager|consultant|'
        r'administrator|specialist|technician|director|lead|coordinator|'
        r'officer|supervisor|scientist|programmer|associate|assistant|'
        r'intern|president|founder|owner|instructor|advisor|executive)\b'
    )
    non_employment_context = re.compile(
        r'(?i)\b(?:education|academic|degree|bachelor|master|phd|doctorate|'
        r'certification|certificate|volunteer|award|training|course)\b'
    )

    for match in supplemental_range.finditer(resume_text):
        start_date = parse_single_date(match.group('start'), current_date)
        end_date = parse_single_date(match.group('end'), current_date)
        if start_date is None or end_date is None or end_date < start_date:
            continue

        context_start = max(0, match.start() - 300)
        context_end = min(len(resume_text), match.end() + 300)
        context = resume_text[context_start:context_end]

        if not role_evidence.search(context):
            continue

        # Reject an interval only when non-employment evidence is close to the
        # date and no explicit role/title label is present.  This avoids losing
        # legitimate jobs at universities/banks while still filtering degrees,
        # certifications and project timelines.
        tight_start = max(0, match.start() - 120)
        tight_end = min(len(resume_text), match.end() + 120)
        tight_context = resume_text[tight_start:tight_end]

        # Academic/certification/volunteer evidence close to the date wins over
        # occupational words inherited from a neighboring employment record.
        # An explicit Position/Role/Job Title label in the same tight context is
        # the only override.
        if non_employment_context.search(tight_context) and not re.search(
            r'(?i)\b(?:position|job\s*title|role|title)\s*[:\-]', tight_context
        ):
            continue

        # Likewise reject a PROJECT(S) section heading immediately around the
        # date, but do not reject legitimate titles such as Project Manager.
        if re.search(r'(?im)^\s*projects?\s*$', tight_context) and not re.search(
            r'(?i)\b(?:position|job\s*title|role|title)\s*[:\-]', tight_context
        ):
            continue

        interval = (start_date, end_date)
        if interval not in intervals:
            intervals.append(interval)

    # Preserve the existing behavior that overlapping/concurrent jobs count only
    # once toward total calendar experience.
    merged_intervals = []
    for start_date, end_date in sorted(intervals, key=lambda interval: interval[0]):
        if not merged_intervals:
            merged_intervals.append([start_date, end_date])
            continue
        last_start, last_end = merged_intervals[-1]
        if start_date <= last_end:
            if end_date > last_end:
                merged_intervals[-1][1] = end_date
        else:
            merged_intervals.append([start_date, end_date])

    total_experience = relativedelta()
    for start_date, end_date in merged_intervals:
        total_experience += relativedelta(end_date, start_date)

    total_years = (
        total_experience.years
        + (total_experience.months / 12)
        + (total_experience.days / 365.25)
    )
    print(f"Total Experience: {total_experience}, Total Years: {total_years}")
    return max(round(total_years, 2), 0)

def format_experience_years_months(years_value):
    """
    Convert decimal years into a human-readable years/months value.

    Examples:
        4.66 -> "4 years 8 months"
        1.42 -> "1 year 5 months"
        1.00 -> "1 year"
        0.50 -> "6 months"
        0.00 -> "0 months"

    The decimal years value remains the canonical value used
    for metadata, ChromaDB filtering, ranking, and calculations.
    """

    try:
        years_value = float(years_value)
    except (TypeError, ValueError):
        return "N/A"

    if years_value < 0:
        years_value = 0

    total_months = round(years_value * 12)

    years = total_months // 12
    months = total_months % 12

    parts = []

    if years:
        parts.append(
            f"{years} {'year' if years == 1 else 'years'}"
        )

    if months:
        parts.append(
            f"{months} {'month' if months == 1 else 'months'}"
        )

    if not parts:
        return "0 months"

    return " ".join(parts)

# Functions reads the skills listed within the IT_Skills_List.txt file
def read_skills_from_file(file_path):
    try:
        with open(file_path, 'r') as file:
            skills_list = [line.strip() for line in file.readlines()]
        return skills_list
    except Exception as e:
        print(f"Error reading from skills list {e}")
        return[]
 
def extract_skills(resume_text):
    """Extract unique skills based on keywords from an external file."""
    try:
        # Read skills from the file
        skills_list = read_skills_from_file(skills_file_path)

        # Create a case-insensitive pattern for each skill
        skill_patterns = [re.compile(r'\b' + re.escape(skill) + r'\b', re.IGNORECASE) for skill in skills_list]

        # Find the skills mentioned in the resume text, preserving original case
        found_skills = []
        for pattern in skill_patterns:
            matches = pattern.findall(resume_text)
            if matches:
                found_skills.append(matches[0])  # Add the first match (original case)

        # Remove duplicates while preserving order
        unique_skills = list(dict.fromkeys(found_skills))
       
        # Return the skills as a comma-separated string, or 'N/A' if no skills found
        return ", ".join(unique_skills) if unique_skills else "N/A"
    
    except Exception as e:
        print(f"Error reading skills list: {e}")
        return "N/A"

# Function to extract phone number using regex
def extract_phone_number(text):
    phone_patterns = [
        r'\(\d{3}\)\s?\d{3}[-.\s]?\d{4}',        # (XXX) XXX-XXXX
        r'\d{3}[-.\s]?\d{3}[-.\s]?\d{4}',         # XXX-XXX-XXXX or XXX.XXX.XXXX
        r'\+1\s?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}',   # +1 (XXX) XXX-XXXX or +1 XXX-XXX-XXXX
        r'1[-.\s]?\d{3}[-.\s]?\d{3}[-.\s]?\d{4}',  # 1-XXX-XXX-XXXX
        r'\(\d{3}\)\s?\d{3}\s?\d{4}',  # (XXX) XXX XXXX
        r'\d{3}\s\d{3}\s\d{4}',  # XXX XXX XXXX
        r'\+1\s?\(?\d{3}\)?\s?[-.\s]?\d{3}\s?[-.\s]?\d{4}',  # +1 (XXX) XXX- XXXX with various spacings
        r'\+1\s?\(?\d{3}\)?\s?\d{3}\s?\d{4}',  # +1 (XXX) XXX XXXX
        r'\+1\(?\d{3}\)?\d{3}[-.\s]?\d{4}'  # +1(XXX)XXX-XXXX
    ]

    for pattern in phone_patterns:
        phone_match = re.search(pattern, text)
        if phone_match:
            phone = phone_match.group(0)
            phone = re.sub(r'\s+', '-', phone)  # Replace spaces with dashes
            return phone
    return "N/A"

# Function to extract location from text
def extract_location(text):
    address_patterns = [
        r'\d+\s+\w+\s+(Street|St|Avenue|Ave|Road|Rd|Lane|Ln|Boulevard|Blvd|Drive|Dr|Circle|Cir|Court|Ct)\b',
        r'\b(?:[NSEW]\s)?\w+(?:,\s?\w+){1,2}\s\d{5}(-\d{4})?',   # US ZIP Codes with optional +4
        r'\b[A-Z]\d[A-Z]\s?\d[A-Z]\d\b'                          # Canadian Postal Codes
    ]

    for pattern in address_patterns:
        location_match = re.search(pattern, text)
        if location_match:
            return location_match.group(0)

    return "N/A"

# Function to extract email address using regex
def extract_email_address(text):
    # Handle Markdown email links, including escaped colon:
    # [name@example.com](mailto:name@example.com)
    # [name@example.com](mailto\:name@example.com)
    # [RajeshGuptaji@MSN.com](mailto\:RajeshGuptaji@MSN.com)
    
    markdown_email_pattern = (
        r'\[([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})\]'
        r'\(\s*mailto\\?:.*?\)'
    )

    markdown_match = re.search(markdown_email_pattern, text, re.IGNORECASE)
    if markdown_match:
        return markdown_match.group(1).strip()

    # Handle normal plain-text email addresses
    email_pattern = r'\b[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}\b'

    email_match = re.search(email_pattern, text)
    if email_match:
        return email_match.group(0).strip()

    return "N/A"

## New added on 09/10/2026 ------
def is_plausible_filename_person_name(name):
    """
    Return True only when a cleaned filename looks reasonably
    like a person's name rather than a resume label, job title,
    document description, or other filename artifact.
    """

    if not name:
        return False

    name = name.strip()
    words = name.split()

    # Typical person-name length.
    if not 2 <= len(words) <= 4:
        return False

    # Person names should contain alphabetic components only,
    # allowing common punctuation used in names.
    for word in words:
        cleaned_word = (
            word
            .replace("-", "")
            .replace("'", "")
            .replace(".", "")
        )

        if not cleaned_word.isalpha():
            return False

    normalized_words = {
        word.lower().strip(".,:;()[]{}-_")
        for word in words
    }

    # Filename/document labels that should not be treated as names.
    document_words = {
        "resume",
        "cv",
        "curriculum",
        "vitae",
        "profile",
        "document",
        "reply",
        "email",
        "attachment",
        "candidate"
    }

    # Common job-title words.
    title_words = {
        "administrator",
        "engineer",
        "developer",
        "manager",
        "analyst",
        "architect",
        "consultant",
        "specialist",
        "technician",
        "director",
        "lead",
        "coordinator"
    }

    # Common technical / filename descriptor words.
    descriptor_words = {
        "network",
        "system",
        "systems",
        "data",
        "software",
        "cloud",
        "database",
        "technical",
        "technology",
        "gda",
        "pm"
    }

    blocked_words = (
        document_words
        | title_words
        | descriptor_words
    )

    if normalized_words.intersection(blocked_words):
        return False

    return True
    
## New added on 09/10/2026 ------
def calculate_person_name_score(
    name,
    filename_name="",
    resume_text="",
    is_spacy_person=True
):
    """
    Calculate a generic confidence score indicating how likely
    an extracted candidate is to be the resume owner's name.

    No specific person's name is used as a reference.
    """

    if not name:
        return -999

    name = name.strip()
    name_lower = name.lower()
    words = name.split()

    score = 0

    # ---------------------------------------------------------
    # 1. Basic person-name structure
    # ---------------------------------------------------------
    if 2 <= len(words) <= 4:
        score += 20
    elif len(words) == 1:
        score -= 10
    elif len(words) > 5:
        score -= 20

    # Normal alphabetic name components.
    if all(
        word.replace("-", "").replace("'", "").replace(".", "").isalpha()
        for word in words
    ):
        score += 10

    # Digits are a strong negative signal for a person's name.
    if any(char.isdigit() for char in name):
        score -= 50

    # Email / URL-like content is not a person's name.
    if "@" in name or "http://" in name_lower or "https://" in name_lower:
        score -= 50

    # ---------------------------------------------------------
    # 2. Filename evidence
    # ---------------------------------------------------------
    if filename_name:
        filename_lower = filename_name.lower().strip()

        if name_lower == filename_lower:
            score += 100
        elif (
            name_lower in filename_lower
            or filename_lower in name_lower
        ):
            score += 60

    # ---------------------------------------------------------
    # 3. spaCy PERSON evidence
    # ---------------------------------------------------------
    if is_spacy_person:
        score += 25

    # ---------------------------------------------------------
    # 4. Position in resume
    # Names near the beginning are more likely to identify
    # the resume owner than names deep in work history.
    # ---------------------------------------------------------
    position = resume_text.lower().find(name_lower)

    if position >= 0:
        if position < 500:
            score += 40
        elif position < 1500:
            score += 20
        elif position < 3000:
            score += 5

    # ---------------------------------------------------------
    # 5. Obvious organization / employment-context indicators
    # Keep this intentionally small and generic.
    # ---------------------------------------------------------
    organization_words = {
        "inc",
        "incorporated",
        "llc",
        "ltd",
        "limited",
        "corporation",
        "company",
        "group",
        "solutions",
        "services",
        "technologies",
        "network"
    }

    normalized_words = {
        word.lower().strip(".,:;()[]{}")
        for word in words
    }

    if normalized_words.intersection(organization_words):
        score -= 30

    # ---------------------------------------------------------
    # 6. Job-title indicators
    # ---------------------------------------------------------
    title_words = {
        "engineer",
        "developer",
        "administrator",
        "consultant",
        "manager",
        "analyst",
        "architect",
        "specialist",
        "technician",
        "director"
    }

    if normalized_words.intersection(title_words):
        score -= 35

    return score
    
# Function added on 09/11/2026
def extract_filename_name_candidate(filename):
    """
    Extract a plausible candidate-name string from a resume filename.

    Handles Azure filenames such as:
        10558_1618536032ResumeSathishKumar.docx
        11751_1618504982ResumeCosminaChisa.pdf
        10136_1671636160Arash_Sedigh-CV.pdf

    This function only cleans the filename.
    Final person-name validation is still performed separately.
    """

    base_name = os.path.splitext(
        os.path.basename(filename)
    )[0]

    # Remove one or more leading Azure/database numeric identifiers.
    #
    # Examples:
    #   10558_1618536032ResumeSathishKumar
    #       -> ResumeSathishKumar
    #
    #   10136_1671636160Arash_Sedigh-CV
    #       -> Arash_Sedigh-CV
    base_name = re.sub(
        r'^(?:\d+[\s_-]*)+',
        '',
        base_name
    )

    # Convert separators to spaces before tokenization.
    base_name = (
        base_name
        .replace('_', ' ')
        .replace('-', ' ')
    )

    base_name = re.sub(
        r"'s\s*",
        " ",
        base_name
    )

    # Split normal words and CamelCase filenames.
    #
    # PeterLiResume -> Peter / Li / Resume
    words = re.findall(
        r'[A-Z]?[a-z]+'
        r'|[A-Z]+(?=[A-Z][a-z]|\d|\W|$)'
        r'|\d+',
        base_name
    )

    # Remove numeric/version tokens and document labels.
    document_words = {
        "resume",
        "cv",
        "profile",
        "student"
    }

    words = [
        word
        for word in words
        if not word.isdigit()
        and word.lower() not in document_words
    ]

    words = [
        word.capitalize()
        for word in words
    ]

    if len(words) >= 3 and len(words[2]) <= 5:
        return " ".join(words[:3])

    return " ".join(words[:2])

# Function to extract the candidate name from filename
def extract_candidate_name(resume_text, filename):
    """
    Extracts candidate name by removing 'Resume', 'CV' from start or end of filename
    and includes it in the similarity check if spaCy doesn't find any names.
    """
    try:

        # ---------------------------------------------------------
        # High-confidence University of Waterloo header extraction
        #
        # Waterloo co-op resume packages normally begin:
        #
        # University of Waterloo
        # Co-operative Work Terms
        # Candidate Name
        # Student Number
        #
        # Prefer this structured source before spaCy because
        # technical terms such as "Java Swing", "Jupyter Notebook",
        # and "Adobe Photoshop" may be incorrectly tagged PERSON.
        # ---------------------------------------------------------

        lines = [
            line.strip()
            for line in resume_text.splitlines()
            if line.strip()
        ]

        if (
            len(lines) >= 4
            and lines[0].lower() == "university of waterloo"
            and lines[1].lower() == "co-operative work terms"
        ):
            waterloo_name = lines[2].strip()

            # Validate that the next line looks like a Waterloo
            # student number. This prevents blindly treating the
            # third line of an unrelated document as a name.
            next_line = lines[3].strip()

            if (
                re.fullmatch(r"\d{7,10}", next_line)
                and re.fullmatch(
                    r"[A-Za-z][A-Za-z .'\-]+",
                    waterloo_name
                )
                and 2 <= len(waterloo_name.split()) <= 5
            ):
                waterloo_name = " ".join(
                    word.capitalize()
                    if not word.isupper()
                    else word.title()
                    for word in waterloo_name.split()
                )

                print(
                    "Waterloo header name confirmed: "
                    f"{waterloo_name}"
                )

        # ---------------------------------------------------------
        # High-confidence filename + resume-text confirmation.
        #
        # A filename-derived name is trusted only when:
        #   1. the cleaned filename looks like a person's name, and
        #   2. that exact name also appears in the resume text.
        #
        # This check runs before heuristic uppercase-header recovery
        # so a job title such as "SENIOR PROJECT MANAGER" cannot
        # override a strongly confirmed candidate name such as
        # "Nazim Ali".
        # Added on 09/11/2026
        # ---------------------------------------------------------

        early_filename_name = extract_filename_name_candidate(
            filename
        )

        early_filename_name_is_person = (
            is_plausible_filename_person_name(
                early_filename_name
            )
        )

        # ---------------------------------------------------------
        # Top-of-resume "Last, First" name recovery
        #
        # Example:
        # Rehan, Mohammed
        # Senior Financial Analyst
        # location / LinkedIn / phone / email
        #
        # Recover:
        # Mohammed Rehan
        #
        # Requirements:
        #   1. first non-empty resume line is exactly "X, Y",
        #   2. both sides contain only name-like words,
        #   3. normalized name passes person-name validation,
        #   4. nearby header contains contact evidence,
        #   5. at least one name component agrees with the
        #      filename-derived candidate.
        #
        # Change #13 on 09/11/2026
        # ---------------------------------------------------------

        comma_header_lines = [
            line.strip()
            for line in resume_text[:500].splitlines()
            if line.strip()
        ]

        if comma_header_lines:
            comma_first_line = " ".join(
                comma_header_lines[0].split()
            ).strip()

            comma_name_match = re.fullmatch(
                r"([A-Za-z][A-Za-z'\-]*"
                r"(?:\s+[A-Za-z][A-Za-z'\-]*)?)"
                r"\s*,\s*"
                r"([A-Za-z][A-Za-z'\-]*"
                r"(?:\s+[A-Za-z][A-Za-z'\-]*)?)",
                comma_first_line
            )

            if comma_name_match:
                last_name_part = comma_name_match.group(1).strip()
                first_name_part = comma_name_match.group(2).strip()

                comma_suffix_credentials = {
                    "bsc",
                    "bs",
                    "msc",
                    "ms",
                    "mba",
                    "phd",
                    "ba",
                    "ma",
                    "bba",
                    "cpa",
                    "cfa",
                    "pmp",
                    "pe",
                }

                if (
                    first_name_part.lower().replace(".", "")
                    in comma_suffix_credentials
                ):
                    comma_name_match = None

            if comma_name_match:
                last_name_part = comma_name_match.group(1).strip()
                first_name_part = comma_name_match.group(2).strip()

                recovered_name = (
                    f"{first_name_part} {last_name_part}"
                )


                header_context = "\n".join(
                    comma_header_lines[1:6]
                )

                header_has_contact = bool(
                    re.search(
                        r"\b(?:phone|email|mobile|tel|telephone|"
                        r"contact|linkedin)\b|@|"
                        r"\b\d{3}[-.\s]\d{3}[-.\s]\d{4}\b",
                        header_context,
                        flags=re.IGNORECASE
                    )
                )

                filename_words = {
                    word.lower().strip(".")
                    for word in early_filename_name.split()
                    if word
                }

                recovered_words = {
                    word.lower().strip(".")
                    for word in recovered_name.split()
                    if word
                }

                filename_name_overlap = bool(
                    filename_words & recovered_words
                )

                if (
                    header_has_contact
                    and filename_name_overlap
                    and is_plausible_filename_person_name(
                        recovered_name
                    )
                ):
                    recovered_name = " ".join(
                        word.title()
                        for word in recovered_name.split()
                    )

                    print(
                        "Comma-formatted resume header name "
                        f"confirmed: {comma_first_line} -> "
                        f"{recovered_name}"
                    )

                    return recovered_name

        # ---------------------------------------------------------
        # Prefer a clean top-of-resume name header over a longer
        # filename-derived candidate.
        #
        # A filename candidate may accidentally absorb the first
        # word of the professional title on the next resume line.
        #
        # Requirements:
        #   1. filename candidate contains 3-4 words,
        #   2. first resume line contains 2-3 name-like words,
        #   3. header is an exact prefix of filename candidate,
        #   4. filename candidate is longer than the header,
        #   5. nearby lines contain contact evidence,
        #   6. recovered header passes normal name plausibility.
        #
        # Change #20
        # ---------------------------------------------------------

        if (
            early_filename_name
            and early_filename_name_is_person
        ):
            filename_words = early_filename_name.split()

            top_lines = [
                line.strip()
                for line in resume_text[:1000].splitlines()
                if line.strip()
            ]

            top_lines = top_lines[:6]

            if (
                3 <= len(filename_words) <= 4
                and top_lines
            ):
                header_line = " ".join(
                    top_lines[0].split()
                ).strip()

                header_words = header_line.split()

                if (
                    2 <= len(header_words) <= 3
                    and len(header_words) < len(filename_words)
                    and all(
                        re.fullmatch(
                            r"[A-Za-z][A-Za-z'\-]*",
                            word
                        )
                        for word in header_words
                    )
                ):
                    header_lower = [
                        word.lower()
                        for word in header_words
                    ]

                    filename_prefix_lower = [
                        word.lower()
                        for word in filename_words[
                            :len(header_words)
                        ]
                    ]

                    if (
                        header_lower
                        == filename_prefix_lower
                    ):
                        contact_context = "\n".join(
                            top_lines[1:5]
                        )

                        has_contact = bool(
                            re.search(
                                r"\b(?:phone|cell|mobile|tel|telephone|"
                                r"email|e-mail|contact|linkedin)\b|@|"
                                r"\b\d{3}[-.\s]\d{3}[-.\s]\d{4}\b",
                                contact_context,
                                flags=re.IGNORECASE
                            )
                        )

                        if has_contact:
                            recovered_name = " ".join(
                                word.title()
                                for word in header_words
                            )

                            if is_plausible_filename_person_name(
                                recovered_name
                            ):
                                print(
                                    "Top header overrides longer "
                                    "filename candidate: "
                                    f"{early_filename_name} -> "
                                    f"{recovered_name}"
                                )

                                return recovered_name

        if (
            early_filename_name
            and early_filename_name_is_person
        ):

            early_filename_pattern = re.escape(
                early_filename_name.lower()
            )

            early_filename_pattern = early_filename_pattern.replace(
                r"\ ",
                r"[\s_-]+"
            )

            early_filename_confirmed_in_text = bool(
                re.search(
                    rf"\b{early_filename_pattern}\b",
                    resume_text.lower()
                )
            )

            if early_filename_confirmed_in_text:
                print(
                    "Early filename name confirmed in resume text: "
                    f"{early_filename_name}"
                )

                return early_filename_name

        # ---------------------------------------------------------
        # Filename prefix recovery before job-title suffix
        #
        # Example:
        # Filename candidate: Anurag K Dev
        # Resume header:      Anurag K DevOps Engineer
        # Change #5
        # Recover:
        # Anurag K
        #
        # Only shorten a 3+ word filename candidate when:
        #   1. the shorter prefix looks like a person name,
        #   2. it appears near the top of the resume, and
        #   3. it is immediately followed by job-title evidence.
        # ---------------------------------------------------------

        if (
            early_filename_name
            and early_filename_name_is_person
        ):
            filename_parts = [
                part
                for part in early_filename_name.split()
                if part
            ]

            if len(filename_parts) >= 3:
                shortened_name = " ".join(
                    filename_parts[:-1]
                )

                if is_plausible_filename_person_name(
                    shortened_name
                ):
                    shortened_pattern = re.escape(
                        shortened_name.lower()
                    )

                    shortened_pattern = shortened_pattern.replace(
                        r"\ ",
                        r"[\s_-]+"
                    )

                    top_text = resume_text[:200]

                    match = re.search(
                        rf"\b{shortened_pattern}\b",
                        top_text.lower()
                    )

                    if match and match.start() <= 80:
                        following_text = top_text[
                            match.end():match.end() + 80
                        ]

                        job_title_after_name = bool(
                            re.search(
                                r"^\s*[-_:|]*\s*"
                                r"(?:devops\s+)?"
                                r"(?:engineer|developer|architect|analyst|"
                                r"manager|consultant|administrator|"
                                r"specialist|technician|director|lead|"
                                r"coordinator)\b",
                                following_text,
                                flags=re.IGNORECASE
                            )
                        )

                        if job_title_after_name:
                            print(
                                "Filename prefix before job-title "
                                "suffix confirmed: "
                                f"{early_filename_name} -> "
                                f"{shortened_name}"
                            )

                            return shortened_name
                            
        # ---------------------------------------------------------
        # Filename surname + initial recovery
        # Added on 09/11/2026
        # Example: change #2
        # Lievikov S in filename
        # Maksym Lievikov near top of resume
        # ---------------------------------------------------------

        if (
            early_filename_name
            and early_filename_name_is_person
        ):
            filename_parts = [
                part
                for part in early_filename_name.split()
                if part
            ]

            full_parts = [
                part
                for part in filename_parts
                if len(part.rstrip(".")) >= 3
            ]

            initial_parts = [
                part
                for part in filename_parts
                if len(part.rstrip(".")) == 1
            ]

            if (
                len(filename_parts) == 2
                and len(full_parts) == 1
                and len(initial_parts) == 1
            ):
                anchor = full_parts[0]

                top_text = resume_text[:500]

                recovery_patterns = [
                    rf"\b([A-Za-z][A-Za-z'\-]{{1,30}})\s+"
                    rf"({re.escape(anchor)})\b",

                    rf"\b({re.escape(anchor)})\s+"
                    rf"([A-Za-z][A-Za-z'\-]{{1,30}})\b",
                ]

                for pattern in recovery_patterns:
                    match = re.search(
                        pattern,
                        top_text,
                        flags=re.IGNORECASE
                    )

                    if not match:
                        continue

                    recovered_name = " ".join(
                        match.groups()
                    ).strip()

                    if is_plausible_filename_person_name(
                        recovered_name
                    ):
                        recovered_name = " ".join(
                            word.title()
                            for word in recovered_name.split()
                        )

                        print(
                            "Filename surname+initial recovery confirmed: "
                            f"{early_filename_name} -> "
                            f"{recovered_name}"
                        )

                        return recovered_name

        # ---------------------------------------------------------
        # Collapsed full-name recovery using one-word filename anchor
        #
        # Example: Change #3
        # Filename: Adnan
        # Resume header: adnanuddin
        #
        # Recover:
        # Adnan Uddin
        #
        # Require the collapsed token to appear very near the top
        # and to be followed by normal contact-header evidence.
        # ---------------------------------------------------------

        if early_filename_name:
            filename_parts = [
                part
                for part in early_filename_name.split()
                if part
            ]

            if len(filename_parts) == 1:
                anchor = filename_parts[0].strip(".")

                if (
                    len(anchor) >= 4
                    and re.fullmatch(
                        r"[A-Za-z][A-Za-z'\-]{3,30}",
                        anchor
                    )
                ):
                    top_text = resume_text[:300]

                    for match in re.finditer(
                        r"\b[A-Za-z][A-Za-z'\-]{6,40}\b",
                        top_text
                    ):
                        # Candidate name/header should be very near
                        # the beginning of the resume.
                        if match.start() > 80:
                            break

                        collapsed_token = match.group(0)

                        if not collapsed_token.lower().startswith(
                            anchor.lower()
                        ):
                            continue

                        suffix = collapsed_token[len(anchor):]

                        # Require a meaningful surname-sized suffix.
                        if not re.fullmatch(
                            r"[A-Za-z][A-Za-z'\-]{2,30}",
                            suffix
                        ):
                            continue

                        # Require contact-style header evidence shortly
                        # after the collapsed name token.
                        following_text = top_text[
                            match.end():match.end() + 180
                        ]

                        header_has_contact = bool(
                            re.search(
                                r"\b(?:phone|email|mobile|tel|telephone)\b|@",
                                following_text,
                                flags=re.IGNORECASE
                            )
                        )

                        if not header_has_contact:
                            continue

                        recovered_name = (
                            f"{anchor} {suffix}"
                        )

                        if is_plausible_filename_person_name(
                            recovered_name
                        ):
                            recovered_name = " ".join(
                                word.title()
                                for word in recovered_name.split()
                            )

                            print(
                                "Collapsed filename-anchor name recovery "
                                f"confirmed: {anchor} + "
                                f"{collapsed_token} -> "
                                f"{recovered_name}"
                            )

                            return recovered_name

        # ---------------------------------------------------------
        # Explicit Name: header recovery
        #
        # Change: #6 and #15 (r"(?im)^\s*name\s*[:\-]\s*")
        # Example: 
        # Name: Tejaswi
        # Email.ID: ...
        # Contact: ...
        #
        # Recover the value explicitly labeled as the candidate's
        # name near the top of the resume.
        # ---------------------------------------------------------

        top_text = resume_text[:500]

        explicit_name_match = re.search(
            r"(?im)^\s*name\s*[:\-]\s*"
            r"([A-Za-z][A-Za-z'\-]*"
            r"(?:\s+[A-Za-z][A-Za-z'\-]*){0,3})"
            r"\s*$",
            top_text
        )

        if explicit_name_match:
            explicit_name = " ".join(
                explicit_name_match.group(1).split()
            ).strip()

            explicit_name_words = explicit_name.split()

            excluded_explicit_name_words = {
                "resume",
                "cv",
                "profile",
                "summary",
                "professional",
                "experience",
                "education",
                "skills",
                "qualifications",
                "objective",
                "career",
                "employment",
                "history",
                "projects",
                "training",
                "references",
            }

            if (
                1 <= len(explicit_name_words) <= 4
                and not any(
                    word.lower()
                    in excluded_explicit_name_words
                    for word in explicit_name_words
                )
            ):
                explicit_name = " ".join(
                    word.title()
                    for word in explicit_name_words
                )

                print(
                    "Explicit Name header confirmed: "
                    f"{explicit_name}"
                )

                return explicit_name

        # ---------------------------------------------------------
        # One-word filename anchor + adjacent surname recovery
        #
        # Change: #7
        # Example structure:
        # Heli Doshi
        # phone / email ...
        #
        # The filename supplies only the first-name anchor.
        # The second name component must come from the resume
        # header itself, followed by contact evidence.
        # ---------------------------------------------------------

        if early_filename_name:
            filename_parts = [
                part
                for part in early_filename_name.split()
                if part
            ]

            if len(filename_parts) == 1:
                anchor = filename_parts[0].strip(".")

                if re.fullmatch(
                    r"[A-Za-z][A-Za-z'\-]{2,30}",
                    anchor
                ):
                    top_text = resume_text[:300]

                    match = re.search(
                        rf"\b({re.escape(anchor)})\s+"
                        r"([A-Za-z][A-Za-z'\-]{2,30})\b",
                        top_text,
                        flags=re.IGNORECASE
                    )

                    if match and match.start() <= 40:
                        recovered_name = " ".join(
                            match.groups()
                        ).strip()

                        following_text = top_text[
                            match.end():match.end() + 180
                        ]

                        header_has_contact = bool(
                            re.search(
                                r"\b(?:phone|email|mobile|tel|telephone|"
                                r"contact)\b|@|"
                                r"\b\d{3}[-.\s]\d{3}[-.\s]\d{4}\b",
                                following_text,
                                flags=re.IGNORECASE
                            )
                        )

                        if (
                            header_has_contact
                            and is_plausible_filename_person_name(
                                recovered_name
                            )
                        ):
                            recovered_name = " ".join(
                                word.title()
                                for word in recovered_name.split()
                            )

                            print(
                                "Filename anchor + adjacent surname "
                                "recovery confirmed: "
                                f"{early_filename_name} -> "
                                f"{recovered_name}"
                            )

                            return recovered_name
                
        # ---------------------------------------------------------
        # Top-of-resume first-name + initial recovery
        #
        # Change: #8
        # Example structure:
        # Shruthi.K
        # Toronto, ON
        # email / phone
        #
        # Recover a name-like first line containing a full first
        # name followed by a single-letter initial when contact
        # evidence appears immediately below the header.
        # ---------------------------------------------------------

        top_lines = [
            line.strip()
            for line in resume_text[:400].splitlines()
            if line.strip()
        ]

        if top_lines:
            first_line = top_lines[0]

            initial_name_match = re.fullmatch(
                r"([A-Za-z][A-Za-z'\-]{2,30})"
                r"\s*[.\s]\s*"
                r"([A-Za-z])\.?",
                first_line
            )

            if initial_name_match:
                header_context = "\n".join(
                    top_lines[1:5]
                )

                header_has_contact = bool(
                    re.search(
                        r"\b(?:phone|email|mobile|tel|telephone|"
                        r"contact)\b|@|"
                        r"\b\d{3}[-.\s]\d{3}[-.\s]\d{4}\b",
                        header_context,
                        flags=re.IGNORECASE
                    )
                )

                if header_has_contact:
                    recovered_name = (
                        f"{initial_name_match.group(1)} "
                        f"{initial_name_match.group(2)}"
                    )

                    if is_plausible_filename_person_name(
                        recovered_name
                    ):
                        recovered_name = " ".join(
                            word.title()
                            for word in recovered_name.split()
                        )

                        print(
                            "Top-of-resume initialed name "
                            "recovery confirmed: "
                            f"{first_line} -> "
                            f"{recovered_name}"
                        )

                        return recovered_name                
                
        # ---------------------------------------------------------
        # One-word filename confirmed as top resume header
        #
        # Change: #9
        # Example structure:
        # Ramandeep
        # email
        # phone
        #
        # A one-word filename candidate is normally too weak.
        # Accept it only when the same word appears at the very
        # beginning of the resume and contact evidence immediately
        # follows it.
        # ---------------------------------------------------------

        if early_filename_name:
            filename_parts = [
                part
                for part in early_filename_name.split()
                if part
            ]

            if len(filename_parts) == 1:
                anchor = filename_parts[0].strip(".")

                if re.fullmatch(
                    r"[A-Za-z][A-Za-z'\-]{2,30}",
                    anchor
                ):
                    top_text = resume_text[:250]

                    match = re.match(
                        rf"^\s*{re.escape(anchor)}\b",
                        top_text,
                        flags=re.IGNORECASE
                    )

                    if match:
                        following_text = top_text[
                            match.end():match.end() + 180
                        ]

                        header_has_contact = bool(
                            re.search(
                                r"\b(?:phone|email|mobile|tel|telephone|"
                                r"contact)\b|@|"
                                r"\b\d{3}[-.\s]\d{3}[-.\s]\d{4}\b",
                                following_text,
                                flags=re.IGNORECASE
                            )
                        )

                        if header_has_contact:
                            recovered_name = anchor.title()

                            print(
                                "One-word filename confirmed as "
                                "top resume header: "
                                f"{early_filename_name} -> "
                                f"{recovered_name}"
                            )

                            return recovered_name                

        print("\n========== NAME DEBUG TOP RESUME_TEXT ==========")

        for debug_i, debug_line in enumerate(
            resume_text[:1000].splitlines()[:15]
        ):
            print(
                f"NAME_DEBUG {debug_i:02d}: "
                f"{debug_line!r}"
            )

        print(
            "========== END NAME DEBUG ==========\n"
        )

        print("\n========== NAME DEBUG END RESUME_TEXT ==========")

        debug_end_lines = [
            line.strip()
            for line in resume_text[-1500:].splitlines()
            if line.strip()
        ]

        for debug_i, debug_line in enumerate(debug_end_lines[-20:]):
            print(
                f"NAME_END_DEBUG {debug_i:02d}: "
                f"{debug_line!r}"
            )

        print(
            "========== END NAME DEBUG END ==========\n"
        )

        # ---------------------------------------------------------
        # Displaced PDF header recovery
        #
        # Some PDF layouts extract the visual resume header at the
        # end of resume_text rather than at the beginning.
        #
        # Example extracted order:
        # ... template/footer text + FIRST MIDDLE LAST
        # Professional Title
        # email / website / location
        #
        # Requirements:
        #   1. candidate line is within last 5 non-empty lines,
        #   2. line ends with an uppercase 2-4 word name,
        #   3. following 1-2 lines contain contact evidence,
        #   4. recovered value passes normal name plausibility.
        #
        # Change #16
        # ---------------------------------------------------------

        end_header_lines = [
            line.strip()
            for line in resume_text[-2000:].splitlines()
            if line.strip()
        ]

        end_header_lines = end_header_lines[-5:]

        for end_i, end_line in enumerate(end_header_lines):

            following_context = "\n".join(
                end_header_lines[
                    end_i + 1:end_i + 3
                ]
            )

            end_has_contact = bool(
                re.search(
                    r"\b(?:phone|email|e-mail|mobile|tel|"
                    r"telephone|contact|linkedin)\b|@|"
                    r"\b\d{3}[-.\s]\d{3}[-.\s]\d{4}\b",
                    following_context,
                    flags=re.IGNORECASE
                )
            )

            if not end_has_contact:
                continue

            end_name_match = re.search(
                r"(?<![A-Za-z])"
                r"([A-Z][A-Z'\-]*"
                r"(?:\s+[A-Z][A-Z'\-]*){1,3})"
                r"\s*$",
                end_line
            )

            if not end_name_match:
                continue

            recovered_name = " ".join(
                word.title()
                for word in
                end_name_match.group(1).split()
            )

            if is_plausible_filename_person_name(
                recovered_name
            ):
                print(
                    "Displaced PDF header name confirmed: "
                    f"{end_line} -> {recovered_name}"
                )

                return recovered_name
                
        # ---------------------------------------------------------
        # Top-of-resume "Name | Professional Title" recovery
        #
        # Example:
        # contact information
        # First Last | Senior Business Systems Analyst
        # E-Mail: ... | Phone: ... | LinkedIn: ...
        #
        # Recover only the name before the first pipe.
        #
        # Requirements:
        #   1. candidate line is within first 3 non-empty lines,
        #   2. line contains "|",
        #   3. text before "|" is a plausible 2-4 word name,
        #   4. nearby header contains contact evidence.
        #
        # Change #14
        # ---------------------------------------------------------

        pipe_header_lines = [
            line.strip()
            for line in resume_text[:500].splitlines()
            if line.strip()
        ]

        pipe_header_context = "\n".join(
            pipe_header_lines[:5]
        )

        pipe_header_has_contact = bool(
            re.search(
                r"\b(?:phone|email|e-mail|mobile|tel|"
                r"telephone|contact|linkedin)\b|@|"
                r"\b\d{3}[-.\s]\d{3}[-.\s]\d{4}\b",
                pipe_header_context,
                flags=re.IGNORECASE
            )
        )

        if pipe_header_has_contact:
            for pipe_line in pipe_header_lines[:3]:
                pipe_line = " ".join(
                    pipe_line.split()
                ).strip()

                if "|" not in pipe_line:
                    continue

                pipe_name_part = (
                    pipe_line.split("|", 1)[0].strip()
                )

                pipe_name_words = pipe_name_part.split()

                pipe_name_is_clean = (
                    2 <= len(pipe_name_words) <= 4
                    and all(
                        re.fullmatch(
                            r"[A-Za-z][A-Za-z'\-.]*",
                            word
                        )
                        for word in pipe_name_words
                    )
                )

                if (
                    pipe_name_is_clean
                    and is_plausible_filename_person_name(
                        pipe_name_part
                    )
                ):
                    recovered_name = " ".join(
                        word.title()
                        for word in pipe_name_words
                    )

                    print(
                        "Pipe-formatted resume header name "
                        f"confirmed: {pipe_line} -> "
                        f"{recovered_name}"
                    )

                    return recovered_name

        # ---------------------------------------------------------
        # Top-of-resume name followed by professional credentials
        #
        # Handles resume headers such as:
        #   First Last, MSc, PMP
        #   First Last, MBA
        #   First Last, PhD, PMP
        #
        # Legacy Word .doc extraction may also place control
        # characters such as \x01 or \x07 before the visible text.
        #
        # Requirements:
        #   1. candidate is within first 5 non-empty lines,
        #   2. candidate portion contains 2-4 name-like words,
        #   3. text after comma consists of credential-like tokens,
        #   4. nearby lines contain contact evidence,
        #   5. candidate passes normal name plausibility.
        #
        # Change #18
        # ---------------------------------------------------------

        credential_header_lines = [
            re.sub(r"^[\x00-\x1f\x7f]+", "", line).strip()
            for line in resume_text[:1500].splitlines()
            if re.sub(
                r"^[\x00-\x1f\x7f]+", "",
                line
            ).strip()
        ]

        credential_header_lines = credential_header_lines[:5]

        for cred_i, cred_line in enumerate(
            credential_header_lines
        ):
            cred_match = re.fullmatch(
                r"([A-Za-z][A-Za-z'\-]*"
                r"(?:\s+[A-Za-z][A-Za-z'\-]*){1,3})"
                r"\s*,\s*"
                r"([A-Za-z][A-Za-z.\-]*"
                r"(?:\s*,\s*[A-Za-z][A-Za-z.\-]*){0,4})",
                cred_line
            )

            if not cred_match:
                continue

            credential_part = cred_match.group(2)

            # Credentials should be short abbreviation-like tokens,
            # not ordinary descriptive words or sentences.
            credential_tokens = [
                token.strip(".")
                for token in re.split(
                    r"\s*,\s*",
                    credential_part
                )
            ]

            if not all(
                1 <= len(token) <= 6
                and token.replace(".", "").isalpha()
                for token in credential_tokens
            ):
                continue

            contact_context = "\n".join(
                credential_header_lines[
                    cred_i + 1:cred_i + 5
                ]
            )

            has_contact = bool(
                re.search(
                    r"\b(?:phone|cell|mobile|tel|telephone|"
                    r"email|e-mail|contact|linkedin)\b|@|"
                    r"\b\d{3}[-.\s]\d{3}[-.\s]\d{4}\b",
                    contact_context,
                    flags=re.IGNORECASE
                )
            )

            if not has_contact:
                continue

            recovered_name = " ".join(
                word.title()
                for word in
                cred_match.group(1).split()
            )

            if is_plausible_filename_person_name(
                recovered_name
            ):
                print(
                    "Credential header name confirmed: "
                    f"{cred_line} -> {recovered_name}"
                )

                return recovered_name

        # ---------------------------------------------------------
        # Generic top-of-resume full-name recovery
        #
        # Some resumes begin directly with the candidate's full name:
        #
        #   First Last
        #   phone / email / LinkedIn ...
        #
        # Some extracted documents may contain a small artifact
        # before the visual resume header, for example:
        #
        #   2
        #   First Last
        #   phone / email ...
        #
        # Requirements:
        #   1. candidate is within first 3 non-empty lines,
        #   2. candidate contains 2-4 name-like words,
        #   3. candidate is not a common resume heading,
        #   4. following lines contain contact evidence,
        #   5. candidate passes normal name plausibility.
        #
        # Change #10
        # Change #19 - inspect first 3 non-empty header lines
        # ---------------------------------------------------------

        top_lines = [
            line.strip()
            for line in resume_text[:1000].splitlines()
            if line.strip()
        ]

        top_lines = top_lines[:6]

        for header_i, header_line in enumerate(
            top_lines[:3]
        ):
            candidate_line = " ".join(
                header_line.split()
            ).strip()

            candidate_words = candidate_line.split()

            if not 2 <= len(candidate_words) <= 4:
                continue

            if not all(
                re.fullmatch(
                    r"[A-Za-z][A-Za-z'\-]*",
                    word
                )
                for word in candidate_words
            ):
                continue

            excluded_header_words = {
                "resume",
                "cv",
                "profile",
                "summary",
                "professional",
                "experience",
                "education",
                "skills",
                "qualifications",
                "objective",
                "career",
                "employment",
                "history",
                "projects",
                "training",
                "references",
                "certifications",
                "technical",
                "work",
            }

            if any(
                word.lower() in excluded_header_words
                for word in candidate_words
            ):
                continue

            contact_context = "\n".join(
                top_lines[
                    header_i + 1:header_i + 5
                ]
            )

            has_contact = bool(
                re.search(
                    r"\b(?:phone|cell|mobile|tel|telephone|"
                    r"email|e-mail|contact|linkedin)\b|@|"
                    r"\b\d{3}[-.\s]\d{3}[-.\s]\d{4}\b",
                    contact_context,
                    flags=re.IGNORECASE
                )
            )

            if not has_contact:
                continue

            recovered_name = " ".join(
                word.title()
                for word in candidate_words
            )

            if is_plausible_filename_person_name(
                recovered_name
            ):
                print(
                    "Top-of-resume name confirmed: "
                    f"{candidate_line} -> {recovered_name}"
                )

                return recovered_name
                
                
        # ---------------------------------------------------------
        # Cover-letter signature name recovery
        #
        # Change: #11        
        # Example:
        # Yours sincerely,
        # Arpit Darji
        # OBJECTIVE
        #
        # Some uploaded documents contain a cover letter before
        # the actual resume. Recover a plausible candidate name
        # from a conventional cover-letter closing before falling
        # back to filename-biased scoring.
        # ---------------------------------------------------------

        cover_letter_signature_match = re.search(
            r"(?im)"
            r"^\s*(?:"
            r"yours[ \t]+sincerely|"
            r"sincerely|"
            r"best[ \t]+regards|"
            r"kind[ \t]+regards|"
            r"regards"
            r")[ \t]*[,:\-]?[ \t]*"
            r"(?:\r?\n[ \t]*)?"
            r"([A-Za-z][A-Za-z'\-]*"
            r"(?:[ \t]+[A-Za-z][A-Za-z'\-]*){1,3})"
            r"[ \t]*$",
            resume_text[:5000]
        )
        
        if cover_letter_signature_match:
            signature_name = " ".join(
                cover_letter_signature_match.group(1).split()
            ).strip()

            if is_plausible_filename_person_name(
                signature_name
            ):
                signature_name = " ".join(
                    word.title()
                    for word in signature_name.split()
                )

                print(
                    "Cover-letter signature name confirmed: "
                    f"{signature_name}"
                )

                return signature_name                
                
        # ---------------------------------------------------------
        # High-confidence uppercase name recovery near top of resume.
        #
        # Handles layouts such as:
        #
        # SHEMEN OSEMWENKHAE
        # Canada, AB | phone | email
        #
        # and collapsed PDF text such as:
        #
        # Urdu (Native/Fluent)AFAQUE AHMED
        #
        # Require agreement with the filename so arbitrary uppercase
        # headings such as CONTACT, SKILLS, AWS, etc. are not selected.
        # ---------------------------------------------------------

        top_lines = [
            line.strip()
            for line in resume_text.splitlines()
            if line.strip()
        ][:25]

        raw_filename_base = os.path.splitext(
            os.path.basename(filename)
        )[0]

        filename_for_match = re.sub(
            r'(?i)\b(?:resume|cv|profile|student)\b',
            '',
            raw_filename_base
        )

        filename_compact = re.sub(
            r'[^a-z]',
            '',
            filename_for_match.lower()
        )

        uppercase_name_pattern = re.compile(
            r'\b([A-Z][A-Z\'-]+'
            r'(?:\s+[A-Z][A-Z\'-]+){1,3})\b'
        )

        for line in top_lines:

            matches = uppercase_name_pattern.findall(line)

            for uppercase_candidate in matches:

                candidate_words = uppercase_candidate.split()

                # Avoid obvious headings / non-name phrases.
                excluded_name_words = {
                    "CONTACT",
                    "SKILLS",
                    "LANGUAGES",
                    "EDUCATION",
                    "EXPERIENCE",
                    "CERTIFICATIONS",
                    "SUMMARY",
                    "PROFILE",
                    "PROFESSIONAL",
                    "TECHNICAL",
                    "UNIVERSITY",
                    "WATERLOO",
                    # Resume-section words
                    "HIGHLIGHTS",
                    "QUALIFICATIONS",
                    "OBJECTIVE",
                    "CAREER",
                    "EMPLOYMENT",
                    "HISTORY",
                    "ACHIEVEMENTS",
                    "ACCOMPLISHMENTS",
                    "PROJECTS",
                    "TRAINING",
                    "AWARDS",
                    "REFERENCES"                    
                }

                if any(
                    word in excluded_name_words
                    for word in candidate_words
                ):
                    continue

                candidate_compact = re.sub(
                    r'[^a-z]',
                    '',
                    uppercase_candidate.lower()
                )

                # Strong confirmation:
                # whole candidate appears compacted in filename,
                # OR filename begins with candidate's first name.
                first_name = re.sub(
                    r'[^a-z]',
                    '',
                    candidate_words[0].lower()
                )

                filename_matches_candidate = (
                    candidate_compact in filename_compact
                    or filename_compact in candidate_compact
                    or (
                        len(first_name) >= 4
                        and (
                            filename_compact.startswith(first_name)
                            or first_name in filename_compact
                        )
                    )
                )

                # A plausible uppercase name at the very top of a resume
                # can also be confirmed by nearby contact information.
                # This handles resumes whose filenames are document/email
                # labels rather than the candidate's actual name.
                # Added on 09/10/2026
                candidate_position = resume_text.find(
                    uppercase_candidate
                )

                header_window = resume_text[:500].lower()

                header_has_contact_evidence = (
                    "phone" in header_window
                    or "email" in header_window
                    or re.search(
                        r'[\w.+-]+@[\w.-]+',
                        header_window
                    )
                    is not None
                )

                header_confirms_candidate = (
                    candidate_position >= 0
                    and candidate_position < 250
                    and header_has_contact_evidence
                )

                filename_matches_candidate = (
                    filename_matches_candidate
                    or header_confirms_candidate
                )

                if not filename_matches_candidate:
                    continue

                recovered_name = " ".join(
                    word.title()
                    for word in candidate_words
                )

                print(
                    "Uppercase header name confirmed: "
                    f"{recovered_name}"
                )

                return recovered_name

                return waterloo_name

        # ---------------------------------------------------------
        # High-confidence uppercase name recovery near top of resume.
        #
        # Examples:
        # SHEMEN OSEMWENKHAE
        #
        # Collapsed PDF example:
        # Urdu (Native/Fluent)AFAQUE AHMED
        #
        # Candidate must agree with the filename.
        # ---------------------------------------------------------

        top_lines = [
            line.strip()
            for line in resume_text.splitlines()
            if line.strip()
        ][:25]

        raw_filename_base = os.path.splitext(
            os.path.basename(filename)
        )[0]

        filename_for_match = re.sub(
            r'(?i)(?:resume|cv|profile|student)',
            '',
            raw_filename_base
        )

        filename_compact = re.sub(
            r'[^a-z]',
            '',
            filename_for_match.lower()
        )

        uppercase_name_pattern = re.compile(
            r'(?<![A-Z])'
            r'([A-Z][A-Z\'-]+'
            r'(?:\s+[A-Z][A-Z\'-]+){1,3})'
            r'(?![A-Z])'
        )

        excluded_name_words = {
            "CONTACT",
            "SKILLS",
            "LANGUAGES",
            "EDUCATION",
            "EXPERIENCE",
            "CERTIFICATIONS",
            "SUMMARY",
            "PROFILE",
            "PROFESSIONAL",
            "TECHNICAL",
            "UNIVERSITY",
            "WATERLOO",
            # Resume-section words
            "HIGHLIGHTS",
            "QUALIFICATIONS",
            "OBJECTIVE",
            "CAREER",
            "EMPLOYMENT",
            "HISTORY",
            "ACHIEVEMENTS",
            "ACCOMPLISHMENTS",
            "PROJECTS",
            "TRAINING",
            "AWARDS",
            "REFERENCES"            
        }

        for line in top_lines:

            matches = uppercase_name_pattern.findall(line)

            for uppercase_candidate in matches:

                candidate_words = uppercase_candidate.split()

                if any(
                    word in excluded_name_words
                    for word in candidate_words
                ):
                    continue

                candidate_compact = re.sub(
                    r'[^a-z]',
                    '',
                    uppercase_candidate.lower()
                )

                first_name = re.sub(
                    r'[^a-z]',
                    '',
                    candidate_words[0].lower()
                )

                filename_matches_candidate = (
                    candidate_compact in filename_compact
                    or filename_compact in candidate_compact
                    or (
                        len(first_name) >= 4
                        and first_name in filename_compact
                    )
                )

                if not filename_matches_candidate:
                    continue

                recovered_name = " ".join(
                    word.title()
                    for word in candidate_words
                )

                print(
                    "Uppercase header name confirmed: "
                    f"{recovered_name}"
                )

                return recovered_name

        # Use spaCy to extract names from the resume text
        doc = nlp(resume_text)

        person_names = [ent.text for ent in doc.ents if ent.label_ == "PERSON"]

        # Preprocess the names to ensure proper capitalization
        person_names = [
            " ".join(word.capitalize() for word in name.split()) for name in person_names
        ]

        person_names = [name for name in person_names if len(name.split()) > 1]

        # Filename-based extraction
        # Added on 09/11/2026
        filename_name = extract_filename_name_candidate(filename)
        
        #--------Removed on 09/11/2026
        # Filename-based extraction
        #base_name = os.path.splitext(os.path.basename(filename))[0]

        # Remove 'Resume', 'CV', 'Profile' from start and end (case-insensitive)
        #base_name = re.sub(r'^(resume|cv|profile|student)', '', base_name, flags=re.IGNORECASE)
        #base_name = re.sub(r'(resume|cv|profile|student)$', '', base_name, flags=re.IGNORECASE)

        # Remove leading numbers
        #base_name = re.sub(r'^\d+\s*', '', base_name)

        # Replace underscores and hyphens with spaces
        #base_name = base_name.replace('_', ' ').replace('-', ' ')
        #base_name = re.sub(r"'s\s*", ' ', base_name)

        # Split the name into words
        #words = re.findall(r'[A-Z]?[a-z]+|[A-Z]+(?=[A-Z][a-z]|\d|\W|$)|\d+', base_name)

        # Remove words that are entirely numbers
        #words = [word for word in words if not word.isdigit()]

        # Capitalize each word
        #words = [word.capitalize() for word in words]

        # Construct the candidate name
        #if len(words) >= 3 and len(words[2]) <= 5:
        #    filename_name = ' '.join(words[:3])
        #else:
        #    filename_name = ' '.join(words[:2])
        #----------

        print(f"Filename: {filename_name}")

        # Add the name extracted from the filename to the list of person names
        #if filename_name and filename_name not in person_names:
        #    person_names.append(filename_name)

        # Add filename-derived name only when the cleaned filename
        # itself looks like a plausible person's name.
        # removed above 2 lines and Added this on 09/10/2026
        filename_name_is_person = is_plausible_filename_person_name(
            filename_name
        )

        print(
            f"Filename person-name validation: "
            f"{filename_name} -> {filename_name_is_person}"
        )

        if (
            filename_name
            and filename_name_is_person
            and filename_name not in person_names
        ):
            person_names.append(filename_name)
    
        # ---------------------------------------------------------
        # Prefer filename name when it is also found in resume text.
        #
        # The filename is a strong source for candidate identity.
        # This prevents false spaCy PERSON entities such as
        # "Tensorflow Andkeras" from winning semantic similarity.
        # ---------------------------------------------------------

        #if filename_name: 
        if filename_name and filename_name_is_person:
            filename_name_lower = filename_name.lower()

            filename_confirmed_in_text = bool(
                re.search(
                    rf'\b{re.escape(filename_name_lower)}\b',
                    resume_text.lower()
                )
            )

            if filename_confirmed_in_text:
                print(
                    f"Filename name confirmed in resume text: "
                    f"{filename_name}"
                )
                return filename_name

        person_names = [
            name for name in person_names
            if not any(char.isdigit() for char in name)  # Exclude names with numbers
            and len(name) > 2  # Exclude names with 2 or fewer characters
            ##and not any(len(part) <= 2 for part in name.split())  # Exclude names with short parts like "Bk"
            and not any(len(part) == 1 for part in name.split())  # Allow valid 2-letter name parts such as Li, Wu, Lu
        ]

        # If spaCy or filename-based logic finds names, process them
        if person_names:
            print(f"Names found: {person_names}")

            # Score each extracted name using generic person-name confidence rules.
            name_scores = []

            for name in person_names:
                score = calculate_person_name_score(
                    name=name,
                    filename_name=filename_name,
                    resume_text=resume_text,
                    is_spacy_person=True
                )

                name_scores.append((name, score))

            print("Name candidate scores:")
            for name, score in name_scores:
                print(f"  {name}: {score}")

            best_name, best_score = max(
                name_scores,
                key=lambda item: item[1]
            )

            print(
                f"Best name selected based on confidence score: "
                f"{best_name} ({best_score})"
            )

            return best_name

        # If no names are found, return "Unknown"
        return "Unknown"

    except Exception as e:
        print(f"Error extracting candidate name: {e}")
        return "Unknown"
    
def read_job_titles_from_file(file_path):
    """Read job titles from a file and return them as a list."""
    try:
        with open(file_path, 'r') as file:
            job_titles = [line.strip() for line in file.readlines()]
        return job_titles
    except Exception as e:
        print(f"Error reading job titles from file: {e}")
        return []
    
def post_process_job_titles(job_titles):
    """Filter out incorrect job titles."""
    filtered_job_titles = []
    for title in job_titles:
        if not any(char.isdigit() for char in title) and len(title.split()) <= 5:
            filtered_job_titles.append(title)
    return filtered_job_titles

def extract_previous_job_titles_docx(resume_text):
    """
    High-confidence DOCX structural extraction.

    Uses explicit Position: lines when available.
    First Position is the current title and is excluded.
    Existing extract_previous_job_titles() remains the fallback.
    """
    try:
        positions = []

        for line in resume_text.splitlines():
            match = re.match(r'(?i)^\s*position\s*:\s*(.+?)\s*$', line)
            if not match:
                continue

            title = match.group(1).strip()

            # Remove employer/contract suffix.
            title = re.sub(
                r'(?i)\s*[–—-]\s*Contractor\s+at\s+.+$',
                '',
                title
            )

            # Remove remote-work annotation.
            title = re.sub(
                r'(?i)\s*\(\s*100%\s*Remote\s*Work\s*\)\s*$',
                '',
                title
            )

            title = title.strip()

            if title:
                positions.append(title)

        # Need current + at least one previous position.
        if len(positions) >= 2:
            previous_titles = positions[1:]
            result = "~~".join(previous_titles)

            print(
                f"DOCX structural previous job titles: {result}"
            )
            return result

        # Preserve existing behavior for other DOCX formats.
        return extract_previous_job_titles(resume_text)

    except Exception as e:
        print(
            f"DOCX structural previous-title extraction error: {e}"
        )
        return extract_previous_job_titles(resume_text)


def extract_previous_job_titles(resume_text):
    """
    Extracts job titles from the resume text, processes them, and returns them
    as a single string with "~~" separators.
    """
    job_titles_keywords = read_job_titles_from_file(job_titles_file_path)  # Reads job titles from the file
    job_titles_keywords.sort(key=len, reverse=True)

    combined_text = extract_experience_section(resume_text)  # Extracts the experience section from the resume
    print(f"Relevant Combined Text: {combined_text}")

    keyword_processor = KeywordProcessor()
    for job_title in job_titles_keywords:
        keyword_processor.add_keyword(job_title)

    found_job_titles = keyword_processor.extract_keywords(combined_text)
    combined_job_titles = post_process_job_titles(found_job_titles)

    if not combined_job_titles:
        return "N/A"

    # Combine job titles into a single string with "~~" as the separator
    previous_job_titles = "~~".join(combined_job_titles)
    print(f"Stored Job Titles: {previous_job_titles}")
    return previous_job_titles

# ---------------------------------------------------------
# Project / non-employment indicators
# ---------------------------------------------------------

project_indicators = {
    "project",
    "personal project",
    "academic project",
    "course project",
    "school project",
    "capstone",
    "final project",
    "side project",
    "research project",
    "class project",
    "university project",
    "college project"
}

def is_project_context(lines, date_index):
    """
    Determine whether a dated entry is clearly a project
    rather than actual employment.

    Important:
    Do NOT reject legitimate titles such as:
        Project Manager
        Project Engineer
        Project Coordinator

    Reject explicit project-work structures such as:
        Project Team Member
        Personal Project
        Academic Project
        Course Project
        Joint Project
    """

    # ---------------------------------------------------------
    # 1. Check the dated line itself
    # ---------------------------------------------------------

    current_line = lines[date_index].strip()

    direct_project_patterns = [
        r'(?i)^\s*project\s+team\s+member\b',
        r'(?i)^\s*project\s+member\b',
        r'(?i)^\s*personal\s+project\b',
        r'(?i)^\s*academic\s+project\b',
        r'(?i)^\s*course\s+project\b',
        r'(?i)^\s*school\s+project\b',
        r'(?i)^\s*class\s+project\b',
        r'(?i)^\s*university\s+project\b',
        r'(?i)^\s*college\s+project\b',
        r'(?i)^\s*research\s+project\b',
        r'(?i)^\s*capstone\b',
        r'(?i)^\s*final\s+project\b',
        # Handles collapsed PDF text such as:
        # (remote,project-basedexperience)        
        r'(?i)\bproject\s*[-–—]?\s*based\s*experience\b',
        # Project/artifact name followed by a technology stack.
        #
        # Examples:
        # Porch Package Security System — STM32, C++, Altium
        # Inventory Application — React, Python, SQL
        # Weather Dashboard — JavaScript, HTML, CSS
        #
        # Require BOTH:
        #   1. artifact/project-style noun
        #   2. separator followed by multiple technologies
        r'(?i)\b(?:'
        r'system|application|app|bot|game|'
        r'dashboard|platform|tool|website|'
        r'prototype|model|regulator'
        r')\b'
        r'.*?[—–]'
        r'\s*'
        r'[A-Za-z0-9+#./-]+'
        r'(?:\s*,\s*[A-Za-z0-9+#./-]+){1,}',       
        # Named project/artifact followed by separator.
        #
        # Examples:
        # Big Idea Project | TechGenius Summer Camp
        # Course Timeline Project | GitHub
        # Inventory Project - Python, SQL
        #
        # Does NOT reject:
        # Project Manager
        # Senior Project Manager
        # Project Engineer
        # Project Coordinator
        r'(?i)^.{1,80}\bproject\b\s*(?:\||[-–—])',
    ]

    for pattern in direct_project_patterns:
        if re.search(pattern, current_line):
            return True


    # ---------------------------------------------------------
    # 2. Check the next two nearby lines for explicit project
    #    descriptions.
    #
    # Do NOT use a generic search for the word "project".
    # Otherwise phrases such as "Project Engineers" or
    # "Project Controllers" create false positives.
    # ---------------------------------------------------------

    nearby_project_patterns = [
        r'(?i)^\s*personal\s+project\b',
        r'(?i)^\s*academic\s+project\b',
        r'(?i)^\s*course\s+project\b',
        r'(?i)^\s*school\s+project\b',
        r'(?i)^\s*class\s+project\b',
        r'(?i)^\s*university\s+project\b',
        r'(?i)^\s*college\s+project\b',
        r'(?i)^\s*research\s+project\b',
        r'(?i)^\s*capstone\b',
        r'(?i)^\s*final\s+project\b',

        # Examples:
        # Microsoft & Avanade (Joint Project)
        # Microsoft Joint Project
        r'(?i)\(\s*joint\s+project\s*\)',
        r'(?i)\bjoint\s+project\b',
    ]

    # ---------------------------------------------------------
    # 2. Check nearby lines for explicit project descriptions.
    # ---------------------------------------------------------

    for offset in range(1, 3):

        idx = date_index + offset

        if idx >= len(lines):
            break

        nearby_line = lines[idx].strip()

        for pattern in nearby_project_patterns:
            if re.search(pattern, nearby_line):
                return True

    # ---------------------------------------------------------
    # 3. Detect portfolio/project entries formatted as:
    #
    # Project Name | React, Node.js, PostgreSQL, GitHub | DATE
    #
    # Do not require the literal word "Project".
    #
    # Structural requirements:
    #   - pipe-delimited entry
    #   - technology-heavy segment
    #   - left side does NOT contain an occupational title
    #
    # This avoids treating portfolio artifacts as employment.
    # ---------------------------------------------------------

    occupational_title_pattern = re.compile(
        r'(?i)\b(?:'
        r'developer|engineer|analyst|manager|intern|'
        r'associate|assistant|specialist|coordinator|'
        r'technician|designer|architect|administrator|'
        r'lead|consultant|scientist|director|officer|'
        r'representative|programmer|instructor|teacher|'
        r'supervisor|recruiter|fellow|advisor|'
        r'executive|sales|tutor'
        r')\b'
    )

    technology_token_pattern = re.compile(
        r'(?i)^(?:'
        r'[A-Za-z][A-Za-z0-9.+#/-]*'
        r')$'
    )

    if "|" in current_line:

        pipe_parts = [
            part.strip()
            for part in current_line.split("|")
            if part.strip()
        ]

        if len(pipe_parts) >= 2:

            left_part = pipe_parts[0]

            # Ignore the date portion when determining whether
            # the second segment looks like a technology stack.
            possible_stack = pipe_parts[1]

            tech_tokens = [
                token.strip()
                for token in possible_stack.split(",")
                if token.strip()
            ]

            tech_like_count = sum(
                1
                for token in tech_tokens
                if technology_token_pattern.fullmatch(token)
            )

            # A company/date line may contain a technology stack while the
            # actual occupational title appears on the following physical line.
            #
            # Example:
            # Dandelion Networks Inc. | React Native, TypeScript, AWS, Firebase
            # Mobile Developer (Android & iOS)
            #
            # Do not classify this employment layout as a portfolio project.
            next_line_has_occupational_title = False

            if date_index + 1 < len(lines):
                next_line = lines[date_index + 1].strip()

                next_line_has_occupational_title = bool(
                    occupational_title_pattern.search(next_line)
                )

            if (
                not occupational_title_pattern.search(left_part)
                and not next_line_has_occupational_title
                and len(tech_tokens) >= 3
                and tech_like_count >= 3
            ):
                return True

    # ---------------------------------------------------------
    # 4. Detect clearly extracurricular/team activity.
    #
    # Examples of structure:
    #
    # Robotics Team
    # Team Captain
    #
    # Student Club
    # President
    #
    # Competition Team
    # Team Member
    #
    # Important:
    # Do NOT classify normal employment phrases such as:
    #   Team Lead
    #   Engineering Team Manager
    #
    # The activity must contain an extracurricular organization
    # signal such as club/society/robotics/competition together
    # with a team/leadership signal.
    # ---------------------------------------------------------

    # Fragmented PDF layouts may place the extracurricular
    # role several physical lines after the date range:
    #
    # Robotics
    # Team
    # 3161
    # September
    # 2022
    # -
    # June
    # 2024
    # Team
    # Captain
    #
    # Use a slightly wider structural window around the date.

    local_start = max(0, date_index - 10)
    local_end = min(len(lines), date_index + 9)

    local_context = " ".join(
        line.strip()
        for line in lines[local_start:local_end]
        if line.strip()
    )

    extracurricular_org_pattern = re.compile(
        r'(?i)\b(?:'
        r'robotics\s+team|'
        r'student\s+club|'
        r'school\s+club|'
        r'university\s+club|'
        r'college\s+club|'
        r'campus\s+club|'
        r'student\s+society|'
        r'student\s+association|'
        r'competition\s+team|'
        r'varsity\s+team'
        r')\b'
    )

    extracurricular_role_pattern = re.compile(
        r'(?i)\b(?:'
        r'captain|'
        r'club\s+president|'
        r'vice\s+president|'
        r'team\s+member|'
        r'volunteer\s+member|'
        r'student\s+leader'
        r')\b'
    )

    if (
        extracurricular_org_pattern.search(local_context)
        and extracurricular_role_pattern.search(local_context)
    ):
        return True

    return False

def extract_most_recent_job_title(resume_text, return_details=False):
    """
    Extract the most recent employment job title from a resume.

    Strategy:
    1. Extract the experience section.
    2. Find employment date ranges.
    3. Select the most recent employment period.
    4. Inspect the lines surrounding that date.
    5. Remove dates, employers, locations, and separators.
    6. Prefer a meaningful job title over generic words such as
       'Developer', 'Engineer', or 'Analyst'.
    """

    import re

    def _format_job_title_result(
        title,
        confidence="LOW",
        score=0,
        source="none",
        reason="",
        margin=0
    ):
        details = {
            "title": title,
            "confidence": confidence,
            "score": score,
            "source": source,
            "reason": reason,
            "margin": margin,
            "requires_review": confidence == "LOW"
        }
        return details if return_details else title

    combined_text = extract_experience_section(resume_text)

    print("\n========== JOB TITLE EXTRACTION ==========")
    print("Relevant Combined Text:")
    print(combined_text)

    if not combined_text or not combined_text.strip():
        print("No experience section found.")
        return _format_job_title_result("N/A", reason="no_experience_section")

    # ---------------------------------------------------------
    # 1. Normalize the text
    # ---------------------------------------------------------

    lines = []

    for line in combined_text.splitlines():

        if not line.strip():
            continue

        normalized_line = re.sub(
            r'\s+',
            ' ',
            line
        ).strip()

        # -----------------------------------------------------
        # Repair PDF-split 4-digit years.
        #
        # Examples:
        #
        # 2 023 -> 2023
        # 20 24 -> 2024
        # 202 3 -> 2023
        #
        # Restrict this to pieces that together form a valid
        # 19xx/20xx year so ordinary numbers are untouched.
        # -----------------------------------------------------

        normalized_line = re.sub(
            r'(?<!\d)'
            r'((?:19|20))\s+(\d{2})'
            r'(?!\d)',
            r'\1\2',
            normalized_line
        )

        normalized_line = re.sub(
            r'(?<!\d)'
            r'([12])\s+(\d{3})'
            r'(?!\d)',
            lambda m: (
                m.group(1) + m.group(2)
                if re.fullmatch(
                    r'(?:19|20)\d{2}',
                    m.group(1) + m.group(2)
                )
                else m.group(0)
            ),
            normalized_line
        )

        normalized_line = re.sub(
            r'(?<!\d)'
            r'((?:19|20)\d)\s+(\d)'
            r'(?!\d)',
            r'\1\2',
            normalized_line
        )

        # Repair malformed current-employment date:
        # Jan - 2019 To Till date -> Jan 2019 - Till date
        normalized_line = re.sub(
            r'(?i)\b'
            r'(Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|'
            r'May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|'
            r'Sep(?:t(?:ember)?)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)'
            r'\s*[-–—]\s*'
            r'((?:19|20)\d{2})'
            r'\s+(?:to\s+)?'
            r'(Present|Current|Now|Today|Ongoing|To\s+Date|Till\s+Date|Till\s+Now|Continued|Continuing|Until\s+Date|Until\s+Now)\b',
            r'\1 \2 - \3',
            normalized_line
        )
        
        lines.append(normalized_line)

    if not lines:
        return _format_job_title_result(
            "N/A",
            reason="no_normalized_experience_lines"
        )

    # ---------------------------------------------------------
    # Repair dates glued directly to titles/employers by PDF
    # extraction.
    #
    # Examples:
    #
    # SoftwareDeveloperJul2024–PresentCornellTech
    # -> SoftwareDeveloper Jul2024–Present CornellTech
    #
    # ResearchAssistantJun2023–Dec2023University...
    # -> ResearchAssistant Jun2023–Dec2023 University...
    #
    # Keep this targeted to month/date boundaries rather than
    # splitting all CamelCase text globally.
    # ---------------------------------------------------------

    glued_month_pattern = (
        r'(?:'
        r'Jan(?:uary)?|'
        r'Feb(?:ruary)?|'
        r'Mar(?:ch)?|'
        r'Apr(?:il)?|'
        r'May|'
        r'Jun(?:e)?|'
        r'Jul(?:y)?|'
        r'Aug(?:ust)?|'
        r'Sep(?:t(?:ember)?)?|'
        r'Oct(?:ober)?|'
        r'Nov(?:ember)?|'
        r'Dec(?:ember)?'
        r')'
    )

    repaired_lines = []

    for line in lines:

        # DeveloperJul2024
        # AssistantMay2023
        #
        # Only split when the month begins with its normal
        # uppercase spelling and is followed by a year.
        line = re.sub(
            rf'(?<=[a-z])'
            rf'(?={glued_month_pattern}\s*\d{{4}})',
            ' ',
            line
        )

        # PresentCornellTech
        # CurrentCompanyName
        line = re.sub(
            r'('
            r'Present|Current|Now|Today|Ongoing|'
            r'To\s+Date|Till\s+Date|Till\s+Now|'
            r'Continued|Continuing'
            r')'
            r'(?=(?-i:[A-Z]))',
            r'\1 ',
            line,
            flags=re.IGNORECASE
        )

        # Dec2023University
        # Jun2024Yale
        line = re.sub(
            r'((?:19|20)\d{2})(?=(?-i:[A-Z]))',
            r'\1 ',
            line
        )

        repaired_lines.append(line)

    lines = repaired_lines
    
    # ---------------------------------------------------------
    # 2. Employment date patterns
    #
    # Supports examples such as:
    # May 2024 – August 2024
    # September 2024 - December 2024
    # May 2024 – Present
    # 07/2024 – Present
    # Jan 2024 - Apr 2024
    # ---------------------------------------------------------

    month_pattern = (
        r'(?:'
        r'Jan(?:uary)?\.?|'
        r'Feb(?:ruary)?\.?|'
        r'Mar(?:ch)?\.?|'
        r'Apr(?:il)?\.?|'
        r'May\.?|'
        r'Jun(?:e)?\.?|'
        r'Jul(?:y)?\.?|'
        r'Aug(?:ust)?\.?|'
        r'Sep(?:t(?:ember)?)?\.?|'
        r'Oct(?:ober)?\.?|'
        r'Nov(?:ember)?\.?|'
        r'Dec(?:ember)?\.?'
        r')'
    )

    # ---------------------------------------------------------
    # Flexible employment date-range pattern
    #
    # Supports:
    # May 2024 - Aug 2024
    # May 13 2024 - August 9, 2024
    # May 13, 2024 - August 9, 2024
    # 07/2024 - Present
    # Jan 2024 - Till Date
    # 2022 - 2023
    # ---------------------------------------------------------

    current_date_terms = (
        r'(?:'
        r'Present|'
        r'Current|'
        r'Now|'
        r'Today|'
        r'Ongoing|'
        r'To\s+Date|'
        r'Till\s+Date|'
        r'Till\s+Now|'
        r'Continued|'
        r'Continuing'
        r')'
    )

    # Month with optional day:
    #
    # May 2024
    # May 13 2024
    # May 13, 2024
    # December 2023
    # December2023
    #
    month_date_pattern = (
        rf'{month_pattern}'
        rf'\s*'
        rf'(?:\d{{1,2}}\s*,?\s*)?'
        rf'(?:19|20)\d{{2}}'
    )

    # ---------------------------------------------------------
    # Month + 2-digit apostrophe year
    #
    # Examples:
    # Mar'24
    # Mar’24
    # Aug'22
    # ---------------------------------------------------------

    short_year_date_pattern = (
        rf'{month_pattern}'
        rf'\s*[\'\u2019]\s*'
        rf'\d{{2}}'
    )

    # ---------------------------------------------------------
    # Numeric month + 2-digit year
    #
    # Examples:
    # 9/21
    # 08/20
    # 12/24
    # ---------------------------------------------------------

    numeric_short_year_date_pattern = (
        r'(?:0?[1-9]|1[0-2])'
        r'/'
        r'\d{2}'
    )
    
    # ---------------------------------------------------------
    # Compact same-year date range where the year appears only
    # once at the end.
    #
    # Examples:
    # May27-Aug12,2024
    # May 27-Aug 12, 2024
    # May27-August12,2024
    # ---------------------------------------------------------

    compact_same_year_range_pattern = (
        rf'{month_pattern}'
        rf'\s*\d{{1,2}}'
        rf'\s*[-\u2013\u2014]\s*'
        rf'{month_pattern}'
        rf'\s*\d{{1,2}}'
        rf'\s*,?\s*'
        rf'(?:19|20)\d{{2}}'
    )

    # ---------------------------------------------------------    
    # Employment date-range separator.
    #
    # Supports:
    # May 2024 - Aug 2024
    # May 2024 – Aug 2024
    # Oct 2022 to Present
    # ---------------------------------------------------------    

    date_range_separator = (
        r'\s*(?:[-\u2013\u2014]|\bto\b)\s*'
    )
    
    # ---------------------------------------------------------
    # Month-to-month range where the year appears only once.
    #
    # Examples:
    # May – August 2024
    # July – September 2023
    # May - Aug 2022
    # ---------------------------------------------------------

    month_to_month_same_year_pattern = (
        rf'{month_pattern}'
        rf'{date_range_separator}'
        rf'{month_pattern}'
        rf'\s*'
        rf'(?:19|20)\d{{2}}'
    )
    
    date_range_pattern = re.compile(
        rf'(?i)(?:'

        # May27-Aug12,2024
        # May 27-Aug 12, 2024
        rf'{compact_same_year_range_pattern}'

        rf'|'

        # May – August 2024
        # July – September 2023
        rf'{month_to_month_same_year_pattern}'

        rf'|'
        
        # May 2024 - August 2024
        # May 13 2024 - August 9, 2024
        rf'{month_date_pattern}'
        rf'{date_range_separator}'
        rf'{month_date_pattern}'

        rf'|'

        # May 2024 - Present
        # Oct 2022 to Present
        rf'{month_date_pattern}'
        rf'{date_range_separator}'
        rf'{current_date_terms}\.?'

        rf'|'

        # 9/21 to Present
        # 09/21 - Present
        rf'{numeric_short_year_date_pattern}'
        rf'{date_range_separator}'
        rf'{current_date_terms}\.?'

        rf'|'

        # 8/20 to 8/21
        # 08/20 - 08/21
        rf'{numeric_short_year_date_pattern}'
        rf'{date_range_separator}'
        rf'{numeric_short_year_date_pattern}'

        rf'|'

        # 07/2024 - Present
        rf'\d{{1,2}}/\d{{4}}'
        rf'{date_range_separator}'
        rf'{current_date_terms}\.?'

        rf'|'

        # 07/2024 - 08/2024
        rf'\d{{1,2}}/\d{{4}}'
        rf'{date_range_separator}'
        rf'\d{{1,2}}/\d{{4}}'

        rf'|'

        # 2022 - 2023
        rf'(?:19|20)\d{{2}}'
        rf'{date_range_separator}'
        rf'(?:19|20)\d{{2}}'

        rf'|'

        # 2022 - Present
        # 2021 to Current
        # 2020 – Till Date
        rf'(?:19|20)\d{{2}}'
        rf'{date_range_separator}'
        rf'{current_date_terms}\.?'

        rf'|'

        # Mar'24 - Present
        # Mar’24 – Present
        rf'{short_year_date_pattern}'
        rf'{date_range_separator}'
        rf'{current_date_terms}\.?'

        rf'|'

        # Aug'22 - Mar'24
        # Aug’22 – Mar’24
        rf'{short_year_date_pattern}'
        rf'{date_range_separator}'
        rf'{short_year_date_pattern}'
        
        rf')\b'
    )

    # ---------------------------------------------------------
    # 3. Find every dated EXPERIENCE line
    # ---------------------------------------------------------

    date_candidates = []

    # Month number is needed so that:
    # Sep 2024 ranks above May 2024 when both end in 2024.
    month_numbers = {
        "jan": 1,
        "january": 1,
        "feb": 2,
        "february": 2,
        "mar": 3,
        "march": 3,
        "apr": 4,
        "april": 4,
        "may": 5,
        "jun": 6,
        "june": 6,
        "jul": 7,
        "july": 7,
        "aug": 8,
        "august": 8,
        "sep": 9,
        "sept": 9,
        "september": 9,
        "oct": 10,
        "october": 10,
        "nov": 11,
        "november": 11,
        "dec": 12,
        "december": 12,
    }

    def get_month_number(date_part):
        """
        Return the first month found in a date string.
        Supports Jan, January, Sep., September, and MM/YYYY.
        """

        numeric_match = re.search(
            r'\b(\d{1,2})/\d{4}\b',
            date_part
        )

        if numeric_match:
            month = int(numeric_match.group(1))

            if 1 <= month <= 12:
                return month

        word_match = re.search(
            r'(?i)\b('
            r'Jan(?:uary)?|'
            r'Feb(?:ruary)?|'
            r'Mar(?:ch)?|'
            r'Apr(?:il)?|'
            r'May|'
            r'Jun(?:e)?|'
            r'Jul(?:y)?|'
            r'Aug(?:ust)?|'
            r'Sep(?:t(?:ember)?)?|'
            r'Oct(?:ober)?|'
            r'Nov(?:ember)?|'
            r'Dec(?:ember)?'
            r')\.?\b',
            date_part
        )

        if word_match:
            key = word_match.group(1).lower().rstrip(".")
            return month_numbers.get(key, 0)

        return 0

    # -----------------------------------------------------
    # Extract years
    #
    # Supports:
    # 2024
    # '24
    # ’24
    #
    # Two-digit years:
    # 00-50 -> 2000-2050
    # 51-99 -> 1951-1999
    # -----------------------------------------------------

    def extract_years_from_date(date_value):

        year_values = []

        year_matches = re.findall(
            r'(?:(?:19|20)\d{2}|[\'\u2019]\d{2})',
            date_value
        )

        for year_text in year_matches:

            if year_text.startswith(
                ("'", "\u2019")
            ):
                short_year = int(
                    year_text[1:]
                )

                if short_year <= 50:
                    full_year = 2000 + short_year
                else:
                    full_year = 1900 + short_year

                year_values.append(
                    full_year
                )

            else:
                year_values.append(
                    int(year_text)
                )

        return year_values


    # Once a real Education section begins, dates below it must
    # not compete with employment dates.
    in_education_section = False

    for index, line in enumerate(lines):

        normalized_line = re.sub(
            r'[^a-z ]',
            '',
            line.lower()
        ).strip()

        # PDF extraction may split section headings:
        #
        # Educa tion -> Education
        # E D U C A T I O N -> Education
        #
        # Use this only for heading comparison.
        compact_heading = re.sub(
            r'\s+',
            '',
            normalized_line
        )

        # -----------------------------------------------------
        # Detect a REAL education section heading.
        # Exact/near-exact headings only.
        #
        # Do NOT trigger on sentences such as:
        # "Co-operative Education model..."
        # -----------------------------------------------------

        if (
            normalized_line in {
                "education",
                "educational background",
                "academic background",
                "academic history",
                "education and certifications",
            }
            or compact_heading in {
                "education",
                "educationalbackground",
                "academicbackground",
                "academichistory",
                "educationandcertifications",
            }
        ):
            in_education_section = True
            continue

        if in_education_section:
            continue

        match = date_range_pattern.search(line)

        if not match:
            continue

        date_text = match.group(0)

        # -----------------------------------------------------
        # Reject planned/future work-term schedule dates.
        #
        # But if a real EXPERIENCE section starts AFTER the
        # planned-work-term heading, dates inside that new
        # experience section must be allowed.
        # -----------------------------------------------------

        future_context_start = max(
            0,
            index - 10
        )

        future_context_lines = lines[
            future_context_start:index + 1
        ]

        future_context = "\n".join(
            future_context_lines
        )

        normalized_future_context = re.sub(
            r'[^a-z0-9\n]+',
            ' ',
            future_context.lower()
        )

        future_work_pattern = re.compile(
            r'(?i)\b(?:'
            r'planned\s+future\s+work\s+terms?|'
            r'future\s+work\s+terms?|'
            r'planned\s+work\s+terms?'
            r')\b'
        )

        experience_heading_pattern = re.compile(
            r'(?im)^\s*(?:'
            r'experience|'
            r'experiences|'
            r'work\s+experience|'
            r'professional\s+experience|'
            r'employment\s+history|'
            r'work\s+history'
            r')\s*$'
        )

        future_matches = list(
            future_work_pattern.finditer(
                normalized_future_context
            )
        )

        if future_matches:

            last_future_pos = (
                future_matches[-1].start()
            )

            experience_matches = list(
                experience_heading_pattern.finditer(
                    normalized_future_context
                )
            )

            last_experience_pos = (
                experience_matches[-1].start()
                if experience_matches
                else -1
            )

            # Skip only when the planned/future-work marker
            # is the most recent relevant section marker.
            #
            # Cindy:
            #
            # Planned Future Work Term(s)
            # ...
            # EXPERIENCE
            # Assistant Project Manager Jan 2024 - Present
            #
            # EXPERIENCE is newer, so KEEP the real job.
            #
            # Neeraija planned dates:
            #
            # Planned Future Work Term(s)
            # Jan-Apr 2025
            # ...
            #
            # no newer EXPERIENCE heading yet, so SKIP.
            if last_future_pos > last_experience_pos:

                print(
                    "Skipping planned future work-term date: "
                    f"{date_text}"
                )

                continue

        # -----------------------------------------------------
        # Extra defense against degree dates accidentally being
        # interpreted as employment.
        # -----------------------------------------------------

        lower_line = line.lower()

        education_terms = (
            "bachelor of ",
            "bachelor's ",
            "bachelors ",
            "master of ",
            "master's ",
            "masters ",
            "phd ",
            "doctor of ",
            "diploma ",
            "degree ",
            "expected graduation",
            "candidate for bachelor",
            "candidate for master",
        )

        if any(term in lower_line for term in education_terms):
            print(f"Skipping education entry: {line}")
            continue

        years = extract_employment_years(
            date_text
        )

        if not years:
            continue

        start_year = years[0]
        
        # -----------------------------------------------------
        # Current jobs:
        # Present / Current / Now / To Date
        # -----------------------------------------------------

        is_current = bool(
            re.search(
                r'(?i)\b(?:'
                r'Present|'
                r'Current|'
                r'Today|'
                r'Ongoing|'
                r'Now|'
                r'To\s+Date|'
                r'Till\s+Date|'
                r'Till\s+Now|'
                r'Continued|'
                r'Continuing'
                r')\b',
                date_text
            )
        )

        if is_current:
            # Artificial high value used only for sorting.
            end_year = 9999
            end_month = 12

        else:
            end_year = (
                years[-1]
                if len(years) > 1
                else start_year
            )
            
            # Get the month appearing after the dash.
            date_parts = re.split(
                r'\s*[-\u2013\u2014]\s*',
                date_text,
                maxsplit=1
            )

            if len(date_parts) == 2:
                end_month = get_month_number(date_parts[1])
            else:
                end_month = 0

        # Start month helps break additional ties.
        date_parts = re.split(
            r'\s*[-\u2013\u2014]\s*',
            date_text,
            maxsplit=1
        )

        start_month = get_month_number(date_parts[0])

        date_candidates.append({
            "line_index": index,
            "line": line,
            "date_text": date_text,
            "start_year": start_year,
            "start_month": start_month,
            "end_year": end_year,
            "end_month": end_month,
            "is_current": is_current
        })

    # ---------------------------------------------------------
    # Reconstruct a job title when PDF extraction has split
    # the employment row across many physical lines.
    #
    # Examples:
    #
    # AI
    # Trainee
    # Scale
    # AI
    # (Remote)
    # |
    # June
    # 2023
    # -
    # Jan
    # 2024
    #
    # -> AI Trainee
    #
    # Umpir e
    # |
    # Baseball
    # Ontario
    # April
    # 2020
    # -
    # August
    # 2024
    #
    # -> Umpire
    # ---------------------------------------------------------

    def reconstruct_fragmented_title(
        source_lines,
        start_index,
        window_end,
        date_text
    ):

        # -----------------------------------------------------
        # Find where the date physically starts.
        # -----------------------------------------------------

        first_date_part = re.split(
            r'\s*[-\u2013\u2014]\s*',
            date_text,
            maxsplit=1
        )[0]

        first_month_match = re.search(
            r'(?i)\b('
            r'Jan(?:uary)?|'
            r'Feb(?:ruary)?|'
            r'Mar(?:ch)?|'
            r'Apr(?:il)?|'
            r'May|'
            r'Jun(?:e)?|'
            r'Jul(?:y)?|'
            r'Aug(?:ust)?|'
            r'Sep(?:t(?:ember)?)?|'
            r'Oct(?:ober)?|'
            r'Nov(?:ember)?|'
            r'Dec(?:ember)?'
            r')\.?\b',
            first_date_part
        )

        first_year_match = re.search(
            r'(?:(?:19|20)\d{2}|[\'\u2019]\d{2})',
            first_date_part
        )

        first_month = (
            first_month_match.group(1)
            if first_month_match
            else ""
        )

        first_year = (
            first_year_match.group(0)
            if first_year_match
            else ""
        )

        date_start_index = None

        for idx in range(
            start_index,
            window_end
        ):

            physical_line = source_lines[idx].strip()

            if not physical_line:
                continue

            if (
                first_month
                and re.search(
                    rf'(?i)\b{re.escape(first_month)}\.?\b',
                    physical_line
                )
            ):
                date_start_index = idx
                break

            if (
                first_year
                and first_year in physical_line
            ):
                date_start_index = idx
                break

        if date_start_index is None:
            return None, None


        # -----------------------------------------------------
        # Look backward from the date for title-like lines.
        # Limit the search so we do not wander into unrelated
        # sections of the resume.
        # -----------------------------------------------------

        search_start = max(
            start_index,
            date_start_index - 10
        )

        possible_lines = []

        for idx in range(
            search_start,
            date_start_index
        ):

            value = source_lines[idx].strip()

            if not value:
                continue

            # Remove separator-only lines.
            if re.fullmatch(
                r'[_|:\-–—\s]+',
                value
            ):
                continue

            value = re.sub(
                r'\s+',
                ' ',
                value
            ).strip()

            # ---------------------------------------------
            # Repair fully character-spaced alphabetic words.
            #
            # Examples:
            # A u d i o       -> Audio
            # V i d e o       -> Video
            # S p e c i a l i s t -> Specialist
            # P r o f e s s i o n a l -> Professional
            # ---------------------------------------------

            if re.fullmatch(
                r'(?:[A-Za-z]\s+){1,}[A-Za-z]',
                value
            ):
                value = re.sub(
                    r'\s+',
                    '',
                    value
                )
                
            # ---------------------------------------------
            # Repair common PDF word splits.
            # ---------------------------------------------

            value = re.sub(
                r'(?i)\bumpir\s+e\b',
                'Umpire',
                value
            )

            value = re.sub(
                r'(?i)\b('
                r'specialis|'
                r'analys|'
                r'assistan|'
                r'consultan|'
                r'recruitmen'
                r')\s+t\b',
                r'\1t',
                value
            )

            possible_lines.append(
                (idx, value)
            )


        # -----------------------------------------------------
        # Strong occupational indicators.
        # -----------------------------------------------------

        fragmented_title_terms = {
            "developer",
            "engineer",
            "analyst",
            "manager",
            "intern",
            "trainee",
            "associate",
            "assistant",
            "specialist",
            "coordinator",
            "technician",
            "designer",
            "architect",
            "administrator",
            "admin",
            "lead",
            "consultant",
            "scientist",
            "director",
            "officer",
            "representative",
            "programmer",
            "tutor",
            "instructor",
            "executive",
            "recruiter",
            "teacher",
            "coach",
            "president",
            "counsellor",
            "counselor",
            "attendant",
            "commander",
            "umpire"
        }


        # -----------------------------------------------------
        # Scan backward. The title is usually the closest
        # title-looking text before employer/location/date.
        # -----------------------------------------------------

        for pos in range(
            len(possible_lines) - 1,
            -1,
            -1
        ):

            line_index, value = possible_lines[pos]

            lower_value = value.lower()

            has_title_term = any(
                re.search(
                    rf'\b{re.escape(term)}\b',
                    lower_value
                )
                for term in fragmented_title_terms
            )

            if not has_title_term:
                continue

                # -------------------------------------------------
                # A hyphen-prefixed line can be either:
                #
                # - General Executive at Bayview Computer Club
                #       -> legitimate role
                #
                # or:
                #
                # - Managed daily operations and led employees
                #       -> responsibility sentence
                #
                # For hyphen-prefixed lines, require concise role
                # structure or an explicit "at/for" relationship.
                # -------------------------------------------------

                if re.match(
                    r'^\s*-\s+',
                    following_line
                ):

                    hyphen_words = re.findall(
                        r"[A-Za-z][A-Za-z'&./-]*",
                        following_clean
                    )

                    has_role_relationship = bool(
                        re.search(
                            r'(?i)\s+(?:at|for)\s+',
                            following_clean
                        )
                    )

                    if (
                        not has_role_relationship
                        and len(hyphen_words) > 8
                    ):
                        continue

            title = value


            # -------------------------------------------------
            # Include a short preceding modifier when useful:
            #
            # AI
            # Trainee
            #
            # -> AI Trainee
            #
            # IT
            # Intern
            #
            # -> IT Intern
            # -------------------------------------------------

            if pos > 0:

                previous_value = possible_lines[
                    pos - 1
                ][1].strip()

                previous_lower = (
                    previous_value.lower()
                )

                title_modifiers = {
                    "ai",
                    "it",
                    "qa",
                    "ui",
                    "ux",
                    "sr",
                    "sr.",
                    "jr",
                    "jr.",
                    "senior",
                    "junior"
                }

                if (
                    previous_lower
                    in title_modifiers
                ):
                    title = (
                        previous_value
                        + " "
                        + title
                    )

                    line_index = possible_lines[
                        pos - 1
                    ][0]

            # -------------------------------------------------
            # Recover fragmented multi-word occupational titles.
            #
            # Examples:
            #
            # Audio
            # Video
            # Specialist
            #
            # -> Audio Video Specialist
            #
            # Machine
            # Learning
            # Engineer
            #
            # -> Machine Learning Engineer
            #
            # Only allow known role-descriptor words so employer
            # names are not accidentally attached.
            # -------------------------------------------------

            fragmented_role_prefixes = {
                "audio",
                "video",
                "software",
                "data",
                "machine",
                "learning",
                "project",
                "product",
                "technical",
                "business",
                "research",
                "firmware",
                "hardware",
                "quality",
                "customer",
                "marketing",
                "sales",
                "design",
                "web",
                "cloud",
                "systems",
                "system",
                "security",
                "network",
                "financial",
                "accounting"
            }

            prefix_parts = []

            prefix_pos = pos - 1

            # If the previous value was already consumed by the
            # normal modifier logic above, do not duplicate it.
            if (
                pos > 0
                and possible_lines[pos - 1][1].strip().lower()
                in title_modifiers
            ):
                prefix_pos = pos - 2

            while (
                prefix_pos >= 0
                and len(prefix_parts) < 3
            ):

                prefix_value = (
                    possible_lines[prefix_pos][1]
                    .strip()
                )

                prefix_lower = prefix_value.lower()

                if prefix_lower not in fragmented_role_prefixes:
                    break

                prefix_parts.insert(
                    0,
                    prefix_value
                )

                line_index = possible_lines[
                    prefix_pos
                ][0]

                prefix_pos -= 1

            if prefix_parts:
                title = (
                    " ".join(prefix_parts)
                    + " "
                    + title
                )

            title = re.sub(
                r'\s+',
                ' ',
                title
            ).strip()

            print(
                "Reconstructed fragmented title: "
                f"'{title}'"
            )

            return title, line_index


        return None, None

    # ---------------------------------------------------------
    # Fallback: PDF may split a date across multiple lines.
    #
    # Example:
    #
    # April
    # 2020
    # -
    # August
    # 2024
    #
    # Only use this fallback when the normal line-by-line
    # scanner found ZERO employment dates. This protects
    # resumes whose PDF layout already extracts correctly.
    # ---------------------------------------------------------

    if not date_candidates:

        print(
            "No normal employment dates found. "
            "Trying fragmented-date reconstruction."
        )

        seen_fragmented_dates = set()

        for start_index in range(len(lines)):

            # Join a limited window only.
            # 12 lines is enough for heavily fragmented PDFs
            # without combining an entire resume section.
            window_end = min(
                len(lines),
                start_index + 18
            )

            # -------------------------------------------------
            # Normalize each physical PDF line BEFORE joining.
            #
            # This avoids accidentally collapsing:
            #
            # M a y 2 0 2 4 t o A u g u s t 2 0 2 4
            #
            # into:
            #
            # May2024toAugust2024
            #
            # Instead:
            #
            # M a y       -> May
            # 2 0 2 4     -> 2024
            # t o         -> to
            # A u g u s t -> August
            # 2 0 2 4     -> 2024
            #
            # producing:
            #
            # May 2024 to August 2024
            # -------------------------------------------------

            def normalize_fragmented_line(line):

                text = line.strip()

                if not text:
                    return ""

                # Remove excessive internal whitespace first.
                text = re.sub(
                    r'\s+',
                    ' ',
                    text
                ).strip()

                # ---------------------------------------------
                # Character-spaced alphabetic token:
                #
                # M a y -> May
                # A u g u s t -> August
                # G r e w a l -> Grewal
                #
                # Require the entire line to have this shape.
                # ---------------------------------------------

                if re.fullmatch(
                    r'(?:[A-Za-z]\s+){1,}[A-Za-z]',
                    text
                ):
                    return re.sub(
                        r'\s+',
                        '',
                        text
                    )

                # ---------------------------------------------
                # Character-spaced numeric token:
                #
                # 2 0 2 4 -> 2024
                # ---------------------------------------------

                if re.fullmatch(
                    r'(?:\d\s+){1,}\d',
                    text
                ):
                    return re.sub(
                        r'\s+',
                        '',
                        text
                    )

                return text


            normalized_window_lines = [
                normalize_fragmented_line(line)
                for line in lines[
                    start_index:window_end
                ]
                if line.strip()
            ]


            reconstructed_for_match = " ".join(
                line
                for line in normalized_window_lines
                if line
            )


            reconstructed_for_match = re.sub(
                r'\s+',
                ' ',
                reconstructed_for_match
            ).strip()


            # Preserve this variable because later fallback
            # logic may still reference reconstructed.
            reconstructed = reconstructed_for_match
            
            # ---------------------------------------------------------
            # Normalize word-based date separator:
            #
            # May 2024 to August 2024
            # ->
            # May 2024 - August 2024
            #
            # Do this only when "to" occurs between date components.
            # ---------------------------------------------------------

            reconstructed_for_match = re.sub(
                rf'(?i)'
                rf'(?<=(?:19|20)\d{{2}})'
                rf'\s+to\s+'
                rf'(?={month_pattern})',
                ' - ',
                reconstructed_for_match
            )

            match = date_range_pattern.search(
                reconstructed_for_match
            )

            if not match:
                continue

            date_text = match.group(0)
#------------
            # -------------------------------------------------
            # Reject Planned Future Work Term dates in the
            # fragmented-date fallback.
            #
            # We must check BOTH:
            #
            # 1. physical lines before this reconstruction window
            # 2. text inside the current reconstructed window
            #    before the matched date
            #
            # This matters when start_index == 0 and the
            # Planned Future Work Term marker appears inside
            # the same reconstructed window as the date.
            #
            # A later real EXPERIENCE heading resets the context.
            # -------------------------------------------------

            nearest_future_index = -1
            nearest_experience_index = -1

            # ---------------------------------------------
            # First check physical lines before/start of
            # the current window.
            # ---------------------------------------------

            for idx in range(start_index, -1, -1):

                check_line = lines[idx].strip()

                if (
                    nearest_future_index < 0
                    and re.search(
                        r'(?i)planned\s+future\s+work\s+term',
                        check_line
                    )
                ):
                    nearest_future_index = idx

                if (
                    nearest_experience_index < 0
                    and re.fullmatch(
                        r'(?i)(?:'
                        r'EXPERIENCE|'
                        r'EXPERIENCES|'
                        r'WORK\s*EXPERIENCE|'
                        r'PROFESSIONAL\s*EXPERIENCE|'
                        r'WORK\s*HISTORY|'
                        r'EMPLOYMENT\s*HISTORY'
                        r')',
                        check_line
                    )
                ):
                    nearest_experience_index = idx

                if (
                    nearest_future_index >= 0
                    and nearest_experience_index >= 0
                ):
                    break

            # ---------------------------------------------
            # Also check text INSIDE this reconstructed
            # window before the matched date.
            #
            # Example:
            #
            # Experience
            # ...
            # Planned Future Work Term(s)
            # Jan - Apr 2025
            #
            # When start_index == 0, the backward physical
            # scan alone cannot detect that planned marker.
            # ---------------------------------------------

            text_before_fragmented_date = (
                reconstructed_for_match[
                    :match.start()
                ]
            )

            future_inside = list(
                re.finditer(
                    r'(?i)planned\s+future\s+work\s+term'
                    r'(?:\(s\))?',
                    text_before_fragmented_date
                )
            )

            experience_inside = list(
                re.finditer(
                    r'(?i)\b(?:'
                    r'WORK\s*EXPERIENCE|'
                    r'PROFESSIONAL\s*EXPERIENCE|'
                    r'EMPLOYMENT\s*HISTORY|'
                    r'WORK\s*HISTORY|'
                    r'EXPERIENCES?|'
                    r'EXPERIENCE'
                    r')\b',
                    text_before_fragmented_date
                )
            )

            # If Planned Future Work Term appears inside the
            # current reconstruction window, determine whether
            # a newer Experience heading occurs AFTER it.
            if future_inside:

                last_future_inside = (
                    future_inside[-1].start()
                )

                last_experience_inside = -1

                for exp_match in experience_inside:

                    if (
                        exp_match.start()
                        > last_future_inside
                    ):
                        last_experience_inside = (
                            exp_match.start()
                        )

                # Planned Future Work Term is the active context
                # unless a later real EXPERIENCE heading resets it.
                if last_experience_inside < 0:

                    print(
                        "Skipping planned future work-term date "
                        "during fragmented reconstruction: "
                        f"{date_text}"
                    )

                    continue

            # If the marker was not inside this window, use the
            # physical-line context found above.
            elif (
                nearest_future_index >= 0
                and nearest_future_index
                > nearest_experience_index
            ):

                print(
                    "Skipping planned future work-term date "
                    "during fragmented reconstruction: "
                    f"{date_text}"
                )

                continue
#------------
            normalized_date_key = re.sub(
                r'\s+',
                ' ',
                date_text.lower()
            ).strip()

            if normalized_date_key in seen_fragmented_dates:
                continue

            seen_fragmented_dates.add(
                normalized_date_key
            )

            # -------------------------------------------------
            # Do not accept reconstructed education periods.
            # -------------------------------------------------

            before_date_text = reconstructed_for_match[
                :match.start()
            ].lower()

            education_terms = (
                "bachelor of ",
                "bachelor's ",
                "bachelors ",
                "master of ",
                "master's ",
                "masters ",
                "phd ",
                "doctor of ",
                "diploma ",
                "degree ",
                "expected graduation",
                "candidate for bachelor",
                "candidate for master",
            )

            if any(
                term in before_date_text
                for term in education_terms
            ):
                continue

            years = extract_employment_years(
                date_text
            )

            if not years:
                continue

            start_year = years[0]
            
            is_current = bool(
                re.search(
                    r'(?i)\b(?:'
                    r'Present|'
                    r'Current|'
                    r'Today|'
                    r'Ongoing|'
                    r'Now|'
                    r'To\s+Date|'
                    r'Till\s+Date|'
                    r'Till\s+Now|'
                    r'Continued|'
                    r'Continuing'
                    r')\b',
                    date_text
                )
            )

            date_parts = re.split(
                r'\s*[-\u2013\u2014]\s*',
                date_text,
                maxsplit=1
            )

            start_month = get_month_number(
                date_parts[0]
            )

            if is_current:

                end_year = 9999
                end_month = 12

            else:

                end_year = (
                    years[-1]
                    if len(years) > 1
                    else start_year
                )
                
                end_month = (
                    get_month_number(date_parts[1])
                    if len(date_parts) == 2
                    else 0
                )

            # -------------------------------------------------
            # Determine which physical line actually contains
            # the beginning of the date.
            #
            # Prefer the first line in this window containing
            # the start month or start year.
            # -------------------------------------------------

            actual_index = start_index

            first_date_part = date_parts[0]

            first_year_match = re.search(
                r'(?:19|20)\d{2}',
                first_date_part
            )

            first_year_text = (
                first_year_match.group(0)
                if first_year_match
                else ""
            )

            for offset in range(
                window_end - start_index
            ):

                physical_line = lines[
                    start_index + offset
                ]

                if (
                    first_year_text
                    and first_year_text
                    in physical_line
                ):
                    actual_index = (
                        start_index + offset
                    )
                    break

            # -------------------------------------------------
            # Try to recover the actual title from fragmented
            # physical lines.
            # -------------------------------------------------

            fragmented_title, fragmented_title_index = (
                reconstruct_fragmented_title(
                    lines,
                    start_index,
                    window_end,
                    date_text
                )
            )

            # -------------------------------------------------
            # Fragmented layout where the JOB TITLE appears
            # AFTER the employment date.
            #
            # Example:
            #
            # Keen
            # Computer
            # Solutions
            # May
            # 2024
            # -
            # Aug
            # 2024
            # Engineering
            # &
            # Data
            # Insights
            # Inter n
            # ▪ Reduced search latency...
            #
            # -> Engineering & Data Insights Intern
            #
            # Only use this when the normal fragmented-title
            # recovery did not already find a title.
            # -------------------------------------------------

            if not fragmented_title:

                after_fragmented_date = (
                    reconstructed_for_match[
                        match.end():
                    ].strip()
                )

                # Stop before the first responsibility bullet.
                after_fragmented_date = re.split(
                    r'[•▪●○◦]',
                    after_fragmented_date,
                    maxsplit=1
                )[0].strip()

                # Repair common split title words.
                #
                # Inter n -> Intern
                # Assistan t -> Assistant
                # Specialis t -> Specialist
                after_fragmented_date = re.sub(
                    r'(?i)\b('
                    r'inter|'
                    r'assistan|'
                    r'specialis|'
                    r'consultan|'
                    r'analys'
                    r')\s+'
                    r'(n|t)\b',
                    lambda m: (
                        m.group(1) + m.group(2)
                    ),
                    after_fragmented_date
                )

                # Normalize whitespace.
                after_fragmented_date = re.sub(
                    r'\s+',
                    ' ',
                    after_fragmented_date
                ).strip()

                fragmented_after_title_terms = {
                    "developer",
                    "engineer",
                    "engineering",
                    "analyst",
                    "manager",
                    "intern",
                    "associate",
                    "assistant",
                    "specialist",
                    "coordinator",
                    "technician",
                    "designer",
                    "architect",
                    "administrator",
                    "lead",
                    "consultant",
                    "scientist",
                    "director",
                    "officer",
                    "representative",
                    "programmer",
                    "tutor",
                    "instructor",
                    "executive",
                    "trainee",
                    "supervisor",
                    "commander",
                    "president",
                    "recruiter",
                }

                after_title_lower = (
                    after_fragmented_date.lower()
                )

                after_has_title_term = any(
                    re.search(
                        rf'\b{re.escape(term)}\b',
                        after_title_lower
                    )
                    for term
                    in fragmented_after_title_terms
                )

                after_title_words = re.findall(
                    r"[A-Za-z][A-Za-z'&./-]*",
                    after_fragmented_date
                )

                # Keep this deliberately conservative.
                # A real title should be short and contain an
                # occupational term.
                if (
                    after_has_title_term
                    and 1 <= len(after_title_words) <= 8
                ):

                    fragmented_title = (
                        after_fragmented_date
                    )

                    print(
                        "Recovered fragmented title after date: "
                        f"'{fragmented_title}'"
                    )

            # -------------------------------------------------
            # Recover title from fragmented:
            #
            # TITLE | EMPLOYER DATE
            #
            # Examples:
            #
            # Audio Video Specialist |
            # Sri Sathya Sai Baba Centre ...
            # May 2022 - Present
            #
            # -> Audio Video Specialist
            #
            # This is useful when the physical PDF lines are
            # heavily character-spaced but the reconstructed
            # window preserves the pipe separator.
            # -------------------------------------------------

            if not fragmented_title and "|" in reconstructed_for_match:

                before_date = reconstructed_for_match[
                    :match.start()
                ].strip()
                
                # Use the LAST pipe before this date.
                #
                # The reconstructed window may contain an older
                # employment record with another pipe.
                # The last pipe is closest to the current date.
                pipe_parts = before_date.rsplit("|", 1)

                if len(pipe_parts) == 2:

                    title_side = pipe_parts[0].strip()

                    # -------------------------------------------------
                    # The text before the last pipe may still contain
                    # an older employment record.
                    #
                    # Example:
                    #
                    # Lighting Design Professional | Employer ...
                    # Experience Audio Video Specialist
                    #
                    # Keep only the text after the most recent
                    # Experience marker.
                    # -------------------------------------------------

                    experience_parts = re.split(
                        r'(?i)\b(?:'
                        r'work\s+experience|'
                        r'professional\s+experience|'
                        r'experience'
                        r')\b',
                        title_side
                    )

                    if len(experience_parts) > 1:
                        title_side = experience_parts[-1].strip()

                    # Remove common section headers if still present.
                    title_side = re.sub(
                        r'(?i)^(?:'
                        r'work\s+experience|'
                        r'professional\s+experience|'
                        r'experience'
                        r')\s+',
                        '',
                        title_side
                    ).strip()

                    # Keep only a short probable job-title phrase.
                    title_words = title_side.split()

                    if len(title_words) > 6:
                        title_words = title_words[-6:]

                    title_side = " ".join(title_words).strip()

                    fragmented_title_terms_pipe = {
                        "developer",
                        "engineer",
                        "analyst",
                        "manager",
                        "intern",
                        "trainee",
                        "associate",
                        "assistant",
                        "specialist",
                        "coordinator",
                        "technician",
                        "designer",
                        "architect",
                        "administrator",
                        "lead",
                        "consultant",
                        "scientist",
                        "director",
                        "officer",
                        "representative",
                        "programmer",
                        "tutor",
                        "instructor",
                        "executive",
                        "recruiter",
                        "teacher",
                        "coach",
                        "president",
                        "counsellor",
                        "counselor",
                        "attendant",
                        "umpire",
                        "professional",
                        "supervisor",
                        "commander",
                        "president",
                        "member"
                    }

                    title_side_lower = title_side.lower()

                    if any(
                        re.search(
                            rf'\b{re.escape(term)}\b',
                            title_side_lower
                        )
                        for term in fragmented_title_terms_pipe
                    ):
                        fragmented_title = title_side

                        print(
                            "Recovered fragmented pipe-layout title: "
                            f"'{fragmented_title}'"
                        )

            if fragmented_title:

                synthetic_line = (
                    f"{fragmented_title} {date_text}"
                )

                actual_index = (
                    fragmented_title_index
                    if fragmented_title_index is not None
                    else actual_index
                )

            else:

                # Fall back to the original reconstructed text
                # if no reliable title was found.
                synthetic_line = reconstructed_for_match

            # -------------------------------------------------
            # Apply the same structural project validation to
            # fragmented-date candidates before accepting them.
            #
            # This prevents reconstructed dates from bypassing
            # project/non-employment filtering.
            # -------------------------------------------------

            if is_project_context(lines, actual_index):
                print(
                    "Skipping fragmented date in project context: "
                    f"{date_text}"
                )
                continue

            date_candidates.append({
                "line_index": actual_index,
                "line": synthetic_line,
                "date_text": date_text,
                "start_year": start_year,
                "start_month": start_month,
                "end_year": end_year,
                "end_month": end_month,
                "is_current": is_current,
                "reconstructed": True
            })

            print(
                "Detected fragmented employment date: "
                f"{date_text}"
            )

            # One match per starting window is sufficient.
            # Ranking below will choose the latest.

    # ---------------------------------------------------------
    # Final fallback: year-only employment entries.
    #
    # Example:
    #
    # Cyberisk
    # Intern, Computer Networking & Security |
    # Karachi, Pakistan | 2023
    #
    # A standalone year is too dangerous to treat as a normal
    # date globally because resumes contain education years,
    # awards, projects, certifications, etc.
    #
    # Therefore only accept a year-only entry when:
    #   1. the year is at the END of the line
    #   2. the same line contains a recognizable job-title term
    #   3. the line is not a bullet/responsibility
    # ---------------------------------------------------------

    if not date_candidates:

        print(
            "No interval dates found. "
            "Trying year-only employment fallback."
        )

        year_only_title_terms = {
            "developer",
            "engineer",
            "engineering",
            "analyst",
            "manager",
            "intern",
            "associate",
            "assistant",
            "specialist",
            "coordinator",
            "technician",
            "designer",
            "architect",
            "administrator",
            "lead",
            "consultant",
            "scientist",
            "director",
            "officer",
            "representative",
            "programmer",
            "tutor",
            "head",
            "instructor",
            "executive",
            "trainee",
            "supervisor",
            "recruiter",
            "commander",
            "president",
            "master",
            "internship",
        }

        for idx, line in enumerate(lines):

            stripped_line = line.strip()

            # Never use a bullet/responsibility sentence.
            if re.match(
                r'^\s*[•▪●○◦➢➤►\-]',
                stripped_line
            ):
                continue

            year_match = re.search(
                r'(?:\||,|\s)\s*((?:19|20)\d{2})\s*$',
                stripped_line
            )

            if not year_match:
                continue

            year_text = year_match.group(1)
            year_value = int(year_text)

            # Remove the year and the separator immediately
            # before it.
            before_year = stripped_line[
                :year_match.start()
            ].strip()

            before_year = re.sub(
                r'\s*[|,;:\-–—]+\s*$',
                '',
                before_year
            ).strip()

            before_year_lower = before_year.lower()

            has_title_term = any(
                re.search(
                    rf'\b{re.escape(term)}\b',
                    before_year_lower
                )
                for term in year_only_title_terms
            )

            if not has_title_term:
                continue

            # If the row contains pipe-separated location text,
            # keep only the first segment containing the title.
            #
            # Intern, Computer Networking & Security |
            # Karachi, Pakistan
            #
            # -> Intern, Computer Networking & Security
            role_text = before_year.split(
                "|",
                1
            )[0].strip()

            if not role_text:
                continue

            print(
                "Detected year-only employment entry: "
                f"title='{role_text}', year={year_text}"
            )

            date_candidates.append({
                "line_index": idx,
                "line": f"{role_text} {year_text}",
                "date_text": year_text,
                "start_year": year_value,
                "start_month": 0,
                "end_year": year_value,
                "end_month": 12,
                "is_current": False,
                "reconstructed": True,
                "year_only": True,
            })

    # ---------------------------------------------------------
    # Fallback: employer + single month/year, followed by role.
    #
    # Structural layout:
    #
    # Employer Name          June 2023
    # Scrum MasterProject 1: ...
    #
    # or:
    #
    # Employer Name          Jun 2023
    # Software Engineer
    #
    # Only use this when no interval-style employment date has
    # already been found.
    # ---------------------------------------------------------

    if not date_candidates:

        print(
            "No year-only employment entry found. "
            "Trying single month-year employment fallback."
        )

        single_month_year_pattern = re.compile(
            r'(?i)\b('
            r'Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|'
            r'May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|'
            r'Sep(?:t(?:ember)?)?\.?|Oct(?:ober)?|'
            r'Nov(?:ember)?|Dec(?:ember)?'
            r')'
            r'\s+'
            r'((?:19|20)\d{2})'
            r'\s*$'
        )

        for idx, line in enumerate(lines):

            stripped_line = line.strip()

            if re.match(
                r'^\s*[â€¢â–ªâ—â—‹â—¦ï‚·âž¢âž¤â–º\-]',
                stripped_line
            ):
                continue

            month_year_match = single_month_year_pattern.search(
                stripped_line
            )

            if not month_year_match:
                continue

            # Require non-date text before the month/year.
            employer_text = stripped_line[
                :month_year_match.start()
            ].strip(" |,:;-–—")

            if not employer_text:
                continue

            # Do not treat obvious education/project lines as
            # employment.
            if is_project_context(lines, idx):
                continue

            # Look immediately below the employer/date line for
            # a concise occupational role.
            if idx + 1 >= len(lines):
                continue

            role_candidate = lines[idx + 1].strip()

            if not role_candidate:
                continue

            # Never treat a bullet/responsibility as a title.
            if re.match(
                r'^\s*[â€¢â–ªâ—â—‹â—¦ï‚·âž¢âž¤â–º\-]',
                role_candidate
            ):
                continue

            # -------------------------------------------------
            # Recover a title that is immediately followed by a
            # project-description marker on the same extracted
            # line.
            #
            # Examples:
            #
            # Scrum MasterProject 1:
            # -> Scrum Master
            #
            # Product ManagerProject A:
            # -> Product Manager
            # -------------------------------------------------

            role_candidate = re.split(
                r'(?i)(?='
                r'Project\s*(?:\d+|[A-Z])?\s*:'
                r')',
                role_candidate,
                maxsplit=1
            )[0].strip()

            if not role_candidate:
                continue

            role_lower = role_candidate.lower()

            has_role_term = any(
                re.search(
                    rf'\b{re.escape(term)}\b',
                    role_lower
                )
                for term in year_only_title_terms
            )

            if not has_role_term:
                continue

            role_words = re.findall(
                r"[A-Za-z][A-Za-z0-9&+.'/-]*",
                role_candidate
            )

            if not (
                1 <= len(role_words) <= 8
            ):
                continue

            month_text = month_year_match.group(1)
            year_value = int(
                month_year_match.group(2)
            )

            month_lookup = {
                "jan": 1,
                "january": 1,
                "feb": 2,
                "february": 2,
                "mar": 3,
                "march": 3,
                "apr": 4,
                "april": 4,
                "may": 5,
                "jun": 6,
                "june": 6,
                "jul": 7,
                "july": 7,
                "aug": 8,
                "august": 8,
                "sep": 9,
                "sept": 9,
                "september": 9,
                "oct": 10,
                "october": 10,
                "nov": 11,
                "november": 11,
                "dec": 12,
                "december": 12
            }

            normalized_month = (
                month_text.lower().rstrip(".")
            )

            month_value = month_lookup.get(
                normalized_month
            )

            if not month_value:
                continue

            print(
                "Detected single month-year employment entry: "
                f"employer='{employer_text}', "
                f"date='{month_text} {year_value}', "
                f"role='{role_candidate}'"
            )

            date_candidates.append({
                "line_index": idx,
                "line": (
                    f"{role_candidate} "
                    f"{month_text} {year_value}"
                ),
                "date_text": (
                    f"{month_text} {year_value}"
                ),
                "start_year": year_value,
                "start_month": month_value,
                "end_year": year_value,
                "end_month": month_value,
                "is_current": False,
                "reconstructed": True
            })

            break

    if not date_candidates:
        print("No employment dates found.")
        return _format_job_title_result(
            "N/A", 
            reason="no_employment_dates"
        )

    # ---------------------------------------------------------
    # 4. Rank employment periods accurately
    #
    # Current jobs first.
    # Then latest end year/month.
    # Then latest start year/month.
    # ---------------------------------------------------------

    date_candidates.sort(
        key=lambda x: (
            x["is_current"],
            x["end_year"],
            x["end_month"],
            x["start_year"],
            x["start_month"],
            x["line_index"]       # Tie-breaker: prefer later occurrence
        ),
        reverse=True
    )

    latest = None

    for candidate in date_candidates:

        candidate_index = candidate["line_index"]

        if is_project_context(lines, candidate_index):
            print(
                f"Skipping project entry: "
                f"{candidate['line']}"
            )
            continue

        # -----------------------------------------------------
        # Reject clearly non-employment volunteer/event entries.
        #
        # Some resumes place volunteer activities under a generic
        # EXPERIENCE heading instead of VOLUNTEER EXPERIENCE.
        #
        # Examples:
        #
        # Food Drive | City             September 2023
        # Volunteered at the annual...
        #
        # Library Christmas Event       Nov - Dec 2023
        # Arranged materials...
        #
        # Do not reject legitimate employment just because a
        # resume contains the word "volunteer" elsewhere.
        # -----------------------------------------------------

        candidate_line = candidate["line"].strip()

        # -----------------------------------------------------
        # Reject dates whose nearest structural section is
        # clearly non-employment.
        #
        # Examples:
        #
        # Planned Future Work Term(s)
        # Jan - Apr 2025
        #
        # Relevant Courses
        # Object-Oriented Software Development
        # Sept. 2024 - Present
        #
        # The nearest recognized section heading wins.
        # This avoids rejecting legitimate EXPERIENCE dates
        # merely because an Education/Projects section occurs
        # somewhere else in the resume.
        # -----------------------------------------------------

        nonemployment_section_patterns = [
            r'^\s*planned\s+future\s+work\s+term(?:s)?\s*:?\s*$',
            r'^\s*relevant\s+courses?\s*:?\s*$',
            r'^\s*coursework\s*:?\s*$',
            r'^\s*academic\s+projects?\s*:?\s*$',
            r'^\s*projects?\s*:?\s*$',
            r'^\s*education\s*:?\s*$',
            r'^\s*awards?\s*:?\s*$',
            r'^\s*certifications?\s*:?\s*$',
            r'^\s*academic\s+experience\s*:?\s*$'
        ]

        employment_section_patterns = [
            r'^\s*experience\s*:?\s*$',
            r'^\s*professional\s+experience\s*:?\s*$',
            r'^\s*work\s+experience\s*:?\s*$',
            r'^\s*employment\s*:?\s*$',
            r'^\s*employment\s+history\s*:?\s*$',
            r'^\s*professional\s+history\s*:?\s*$',
            r'^\s*experience\s+highlights\s*:?\s*$'
        ]

        nearest_structural_section = None

        # Look backward only a limited distance. We want the
        # section governing this date, not an unrelated heading
        # many paragraphs earlier.
        for section_index in range(
            candidate_index - 1,
            max(-1, candidate_index - 10),
            -1
        ):
            section_line = lines[section_index].strip()

            if not section_line:
                continue

            if any(
                re.search(
                    pattern,
                    section_line,
                    re.IGNORECASE
                )
                for pattern in employment_section_patterns
            ):
                nearest_structural_section = "employment"
                break

            if any(
                re.search(
                    pattern,
                    section_line,
                    re.IGNORECASE
                )
                for pattern in nonemployment_section_patterns
            ):
                nearest_structural_section = "nonemployment"
                break

        if nearest_structural_section == "nonemployment":
            print(
                "Skipping date under non-employment section: "
                f"{candidate['line']}"
            )
            continue

        nearby_nonemployment_text = " ".join(
            lines[
                max(0, candidate_index - 1):
                min(len(lines), candidate_index + 3)
            ]
        ).lower()

        volunteer_activity = bool(
            re.search(
                r'\b(?:'
                r'volunteer|volunteered|volunteering|'
                r'community\s+service|charity|fundraiser'
                r')\b',
                nearby_nonemployment_text,
                re.IGNORECASE
            )
        )

        event_activity = bool(
            re.search(
                r'(?i)\b(?:'
                r'food\s+drive|'
                r'charity\s+event|'
                r'fundraising\s+event|'
                r'community\s+event|'
                r'christmas\s+event'
                r')\b',
                candidate_line
            )
        )

        # -----------------------------------------------------
        # Determine whether the dated entry has an explicit
        # occupational title.
        #
        # The title may be on the date line itself or on the
        # immediately preceding line, which is common in resumes:
        #
        #     COMPANY | SOFTWARE DEVELOPER
        #     Oct 2021 - June 2023
        #
        # Do not classify legitimate titled work as non-employment
        # merely because a nearby responsibility mentions volunteer
        # work or community service.
        # -----------------------------------------------------

        previous_line = (
            lines[candidate_index - 1].strip()
            if candidate_index > 0
            else ""
        )

        candidate_title_context = " ".join(
            part
            for part in (
                previous_line,
                candidate_line
            )
            if part
        )

        # -----------------------------------------------------
        # Build an additional compact form so occupational
        # titles can still be recognized when PDF extraction
        # removes spaces:
        #
        #     SOFTWAREDEVELOPER
        #     DATAANALYST
        #     PROJECTMANAGER
        #
        # Keep the normal word-boundary check first so ordinary
        # readable text remains the primary signal.
        # -----------------------------------------------------

        compact_candidate_title_context = re.sub(
            r'[^a-z0-9]+',
            '',
            candidate_title_context.lower()
        )

        job_title_terms = [
            "developer",
            "engineer",
            "analyst",
            "manager",
            "intern",
            "associate",
            "assistant",
            "specialist",
            "coordinator",
            "technician",
            "designer",
            "architect",
            "administrator",
            "lead",
            "consultant",
            "scientist",
            "director",
            "officer",
            "representative",
            "programmer",
            "instructor",
            "teacher",
            "supervisor",
            "member",
            "trainee",
            "recruiter",
        ]

        candidate_has_job_title = bool(
            re.search(
                r'(?i)\b(?:'
                + "|".join(
                    re.escape(term)
                    for term in job_title_terms
                )
                + r')\b',
                candidate_title_context
            )
            or any(
                term in compact_candidate_title_context
                for term in job_title_terms
            )
        )

        if (
            (
                volunteer_activity
                and not candidate_has_job_title
            )
            or (
                event_activity
                and not candidate_has_job_title
            )
        ):

            print(
                "Skipping volunteer/non-employment entry: "
                f"{candidate['line']}"
            )
            continue

        latest = candidate
        break

    if latest is None:
        print("No actual employment entry found.")
        return _format_job_title_result("N/A", reason="only_project_or_nonemployment_dates")

    latest_index = latest["line_index"]
    latest_date = latest["date_text"]

    print(f"Selected latest employment date: {latest_date}")
    print(f"Selected employment line: {latest['line']}")

    # ---------------------------------------------------------
    # 5. Get the lines around the selected date
    # ---------------------------------------------------------

    start_context = max(0, latest_index - 3)
    end_context = min(len(lines), latest_index + 4)

    context_lines = lines[start_context:end_context]

    # ---------------------------------------------------------
    # 5a. Detect whether the selected date belongs to a project
    # ---------------------------------------------------------

    # Use the same strict structural project detector.
    # Do not simply search nearby text for the word "project".
    project_context = is_project_context(
        lines,
        latest_index
    )

    if project_context:
        print("Project-related context detected.")

    print("\nContext around latest employment:")
    for i, context_line in enumerate(context_lines):
        print(f"{start_context + i}: {context_line}")

    # ---------------------------------------------------------
    # 6. Build possible title candidates
    # ---------------------------------------------------------

    candidates = []

    # ---------------------------------------------------------
    # Candidate A:
    # Text before the date on the SAME line
    #
    # Example:
    # Quantitative Strategies Software Developer Co-Op
    # May 2024 – August 2024
    #
    # or:
    # FIRMWARE DESIGN TEAM MEMBER- ELECTRIUM MOBILITY
    # September 2024 - December 2024
    # ---------------------------------------------------------

    date_line = latest["line"]

    before_date = date_line[:date_line.lower().find(
        latest_date.lower()
    )].strip()

    if before_date:
        candidates.append({
            "text": before_date,
            "source": "same-line-before-date",
            "score": 140
        })

    # ---------------------------------------------------------
    # Candidate A2:
    # Job title appearing AFTER the date on the SAME line.
    #
    # Example:
    #
    # Kumon Institute of Education Co. Ltd.
    # March 2023 - August 2024 TEACHING ASSISTANT
    #
    # PDF extraction may collapse employer + date + title
    # onto one physical line.
    # ---------------------------------------------------------

    date_start = date_line.lower().find(
        latest_date.lower()
    )

    if date_start >= 0:

        date_end = date_start + len(latest_date)

        after_date = date_line[
            date_end:
        ].strip()

        # Remove separators immediately after the date.
        after_date = re.sub(
            r'^[|,:;\-–—]+\s*',
            '',
            after_date
        ).strip()

        # -----------------------------------------------------
        # Repair heavily fragmented job titles appearing after
        # the date on the same physical PDF line.
        #
        # Example:
        #
        # Q AA u t o m a t i o nE n g i n e e r
        #
        # -> QAAutomationEngineer
        # -> QA Automation Engineer
        #
        # Only apply when several isolated single-letter tokens
        # indicate character-spaced PDF extraction.
        # -----------------------------------------------------

        single_letter_fragments = re.findall(
            r'(?<![A-Za-z])[A-Za-z](?![A-Za-z])',
            after_date
        )

        if (
            len(single_letter_fragments) >= 3
            and re.fullmatch(
                r'[A-Za-z\s]+',
                after_date
            )
        ):

            compact_after_date = re.sub(
                r'\s+',
                '',
                after_date
            )

            # Split acronym followed by normal CamelCase word.
            #
            # QAAutomation -> QA Automation
            compact_after_date = re.sub(
                r'(?<=[A-Z])(?=[A-Z][a-z])',
                ' ',
                compact_after_date
            )

            # Split normal CamelCase boundaries.
            #
            # AutomationEngineer -> Automation Engineer
            compact_after_date = re.sub(
                r'(?<=[a-z])(?=[A-Z])',
                ' ',
                compact_after_date
            )

            after_date = compact_after_date.strip()

        if after_date:

            after_words = re.findall(
                r"[A-Za-z][A-Za-z'&./-]*",
                after_date
            )

            after_lower = after_date.lower()

            after_title_terms = {
                "developer",
                "engineer",
                "analyst",
                "manager",
                "intern",
                "associate",
                "assistant",
                "specialist",
                "coordinator",
                "technician",
                "designer",
                "architect",
                "administrator",
                "lead",
                "consultant",
                "scientist",
                "director",
                "officer",
                "representative",
                "programmer",
                "tutor",
                "instructor",
                "executive",
                "trainee",
                "architect",
                "head",
                "commander",
                "president",
                "sysadmin"
            }

            after_has_title_word = any(
                re.search(
                    rf'\b{re.escape(term)}\b',
                    after_lower
                )
                for term in after_title_terms
            )

            # Avoid accepting a long responsibility sentence
            # after the date as the title.
            if (
                after_has_title_word
                and 1 <= len(after_words) <= 10
            ):
                candidates.append({
                    "text": after_date,
                    "source": "same-line-after-date",
                    "score": 180
                })

    # ---------------------------------------------------------
    # Candidate B:
    # Previous lines
    # ---------------------------------------------------------

    for offset in range(1, 4):
        idx = latest_index - offset

        if idx < 0:
            continue

        candidate_line = lines[idx].strip()

        if candidate_line:
            candidates.append({
                "text": candidate_line,
                "source": f"previous-line-{offset}",
                "score": 60 - (offset * 5)      
            })

    # ---------------------------------------------------------
    # Candidate B2:
    # Recover a title from earlier in the employment block when
    # the selected date has been attached by PDF extraction to a
    # responsibility sentence instead of the title.
    #
    # Example:
    #
    # Software Development Engineer (Intern)
    # ThirstyBrain.Inc, Canada
    # ...
    # •Handled system failures ... Merkle TreesJune 2024 - Sep 2024
    #
    # -> Software Development Engineer (Intern)
    #
    # This fallback runs only when the text before the selected
    # date clearly looks like responsibility/prose text.
    # ---------------------------------------------------------

    selected_before_date = before_date.strip()

    selected_for_check = re.sub(
        r'^[•●▪◦*-]+\s*',
        '',
        selected_before_date
    ).strip()

    selected_words = re.findall(
        r"[A-Za-z][A-Za-z'&./()-]*",
        selected_for_check
    )

    responsibility_starters = (
        "developed",
        "implemented",
        "handled",
        "managed",
        "created",
        "designed",
        "built",
        "maintained",
        "supported",
        "optimized",
        "improved",
        "configured",
        "administered",
        "collaborated",
        "utilized",
        "worked",
        "performed",
        "provided",
        "led",
        "assisted",
        "responsible"
    )

    selected_looks_like_prose = (
        len(selected_words) > 10
        or selected_for_check.lower().startswith(
            responsibility_starters
        )
    )

    if selected_looks_like_prose:

        backward_title_terms = {
            "developer",
            "engineer",
            "analyst",
            "manager",
            "intern",
            "associate",
            "assistant",
            "specialist",
            "coordinator",
            "technician",
            "designer",
            "architect",
            "administrator",
            "lead",
            "consultant",
            "scientist",
            "director",
            "officer",
            "representative",
            "programmer",
            "instructor",
            "teacher",
            "supervisor",
            "executive",
            "trainee",
            "recruiter",
            "sysadmin"
        }

        # Search backward only within a reasonable portion of
        # the current employment block.
        search_start = max(
            0,
            latest_index - 30
        )

        for back_index in range(
            latest_index - 1,
            search_start - 1,
            -1
        ):

            back_line = lines[back_index].strip()

            if not back_line:
                continue

            # Skip bullets / responsibility lines.
            if re.match(
                r'^[•●▪◦*-]+\s*',
                back_line
            ):
                continue

            back_clean = re.sub(
                r'\s+',
                ' ',
                back_line
            ).strip()

            back_words = re.findall(
                r"[A-Za-z][A-Za-z'&./()-]*",
                back_clean
            )

            # A title should be reasonably concise.
            if not (
                1 <= len(back_words) <= 10
            ):
                continue

            back_lower = back_clean.lower()

            # Skip headings.
            if back_lower in {
                "experience",
                "professional experience",
                "work experience",
                "work history",
                "employment history",
                "relevant experience"
            }:
                continue

            has_title_signal = any(
                re.search(
                    rf'(?i)\b{re.escape(term)}\b',
                    back_clean
                )
                for term in backward_title_terms
            )

            if not has_title_signal:
                continue

            print(
                "Recovered earlier title from "
                "responsibility-date layout: "
                f"'{back_clean}'"
            )

            candidates.append({
                "text": back_clean,
                "source":
                    "backward-employment-block-title",
                "score": 210
            })

            break

    # ---------------------------------------------------------
    # 7. Clean candidate text
    # ---------------------------------------------------------

    def clean_candidate(candidate):
        text = candidate.strip()

        # Remove date text
        text = re.sub(
            date_range_pattern,
            '',
            text
        ).strip()

        # Remove bullet characters
        text = re.sub(r'^[•●▪◦*-]+\s*', '', text)

        # Normalize whitespace
        text = re.sub(r'\s+', ' ', text).strip()

        # -----------------------------------------------------
        # Repair compact CamelCase job titles created by PDF
        # extraction.
        #
        # Examples:
        #
        # SoftwareDeveloper -> Software Developer
        # SoftwareEngineer  -> Software Engineer
        # ResearchAssistant -> Research Assistant
        # TeachingAssistant -> Teaching Assistant
        # ProjectManager    -> Project Manager
        #
        # Only apply to a single compact alphabetic token that
        # contains a recognizable occupational suffix. This
        # avoids globally splitting company names or arbitrary
        # CamelCase text.
        # -----------------------------------------------------

        compact_title_terms = (
            r'Developer|'
            r'Engineer|'
            r'Analyst|'
            r'Manager|'
            r'Intern|'
            r'Associate|'
            r'Assistant|'
            r'Specialist|'
            r'Coordinator|'
            r'Technician|'
            r'Designer|'
            r'Architect|'
            r'Administrator|'
            r'Consultant|'
            r'Scientist|'
            r'Director|'
            r'Officer|'
            r'Representative|'
            r'Programmer|'
            r'Instructor|'
            r'Supervisor|'
            r'commander|'
            r'president|'
            r'Recruiter'
        )

        if (
            re.fullmatch(r'[A-Za-z]{4,60}', text)
            and re.search(
                rf'(?:{compact_title_terms})$',
                text,
                re.IGNORECASE
            )
            and re.search(r'[a-z][A-Z]', text)
        ):
            text = re.sub(
                r'(?<=[a-z])(?=[A-Z])',
                ' ',
                text
            )
            
        # -----------------------------------------------------
        # PDF extraction may concatenate the end of a
        # responsibility sentence with an employer.
        #
        # Example:
        #
        # provide effective customer service.Montana's BBQ & Bar
        #
        # -> Montana's BBQ & Bar
        #
        # Only apply when text exists on both sides of a
        # sentence-ending period.
        # -----------------------------------------------------

        if "." in text:

            sentence_parts = [
                part.strip()
                for part in text.split(".")
                if part.strip()
            ]

            if len(sentence_parts) >= 2:

                last_part = sentence_parts[-1]

                # The text before the final period looks like
                # sentence/responsibility language.
                before_last = " ".join(
                    sentence_parts[:-1]
                ).lower()

                responsibility_words = {
                    "provide",
                    "provided",
                    "maintain",
                    "maintained",
                    "manage",
                    "managed",
                    "develop",
                    "developed",
                    "support",
                    "supported",
                    "complete",
                    "completed",
                    "serve",
                    "served",
                    "work",
                    "worked",
                    "responsible",
                    "customer",
                    "commander",
                    "president",
                    "service",
                }

                if any(
                    re.search(
                        rf'\b{re.escape(word)}\b',
                        before_last
                    )
                    for word in responsibility_words
                ):
                    text = last_part

        # -----------------------------------------------------
        # Repair common PDF extraction splits inside job-title
        # words.
        #
        # Examples:
        # Specialis t -> Specialist
        # Analys t    -> Analyst
        # Assistan t  -> Assistant
        # -----------------------------------------------------

        text = re.sub(
            r'(?i)\b('
            r'specialis|'
            r'analys|'
            r'assistan|'
            r'consultan|'
            r'recruitmen'
            r')\s+t\b',
            r'\1t',
            text
        )

        # -----------------------------------------------------
        # Remove employer / engagement text after a strong
        # title when both appear before the date.
        #
        # Examples:
        # Talent Management Specialist, One Key Technology
        # Software Engineering Intern at Ciena Corporation
        # Data Analyst, ABC Company
        # -----------------------------------------------------

        title_employer_split = re.match(
            r'(?i)^(.+?\b(?:'
            r'Engineer|Engineering|'
            r'Developer|Analyst|Manager|Intern|'
            r'Associate|Assistant|Specialist|'
            r'Coordinator|Technician|Designer|'
            r'Architect|Administrator|Lead|'
            r'Consultant|Scientist|Director|'
            r'Officer|Representative|Programmer|'
            r'Tutor|Instructor|Executive|Recruiter'
            r'))'
            r'\s*(?:,|\bat\b|[-–—])\s+'
            r'.+$',
            text
        )

        if title_employer_split:
            text = title_employer_split.group(1).strip()

        # -----------------------------------------------------
        # Employer/location — job title layout
        #
        # Examples:
        #
        # Grewal Guyatt LLP, Richmond Hill, ON — Accounting Associate
        # ABC Corp, Toronto, ON — Data Analyst
        # XYZ Inc., New York, NY — Senior Developer
        #
        # Keep the right side when it looks like a concise
        # occupational title.
        # -----------------------------------------------------

        if re.search(r'\s[-—–]\s', text):

            left_part, right_part = re.split(
                r'\s[-—–]\s',
                text,
                maxsplit=1
            )

            right_part = right_part.strip()

            right_words = re.findall(
                r"[A-Za-z][A-Za-z'&./-]*",
                right_part
            )

            common_title_terms = {
                "associate",
                "analyst",
                "developer",
                "engineer",
                "manager",
                "director",
                "intern",
                "assistant",
                "specialist",
                "technician",
                "consultant",
                "coordinator",
                "administrator",
                "architect",
                "lead",
                "supervisor",
                "officer",
                "representative",
                "researcher",
                "scientist",
                "accountant",
                "executive",
                "trainee",
                "instructor",
                "commander",
                "president",
                "head",
            }

            right_has_title_term = any(
                re.search(
                    rf'\b{re.escape(term)}\b',
                    right_part.lower()
                )
                for term in common_title_terms
            )

            right_is_concise = (
                1 <= len(right_words) <= 8
            )

            if (
                right_has_title_term
                and right_is_concise
            ):
                text = right_part

        # Remove trailing separators
        text = re.sub(r'\s*[|,:;/-]+\s*$', '', text).strip()

        # -----------------------------------------------------
        # Remove a trailing location from a possible job title
        #
        # Examples:
        # Software Developer Waterloo, Ontario
        # Data Analyst Toronto, ON
        # Software Engineer Detroit, MI
        #
        # Keep the title portion.
        # -----------------------------------------------------

        trailing_location_pattern = re.compile(
            r'(?i)\s+'
            r'(?:'
            # Canadian cities
            r'Toronto|Waterloo|Ottawa|Montreal|Vancouver|Calgary|'
            r'Edmonton|Winnipeg|Mississauga|Brampton|Hamilton|'
            r'Kitchener|Oakville|Markham|'
            # Common US cities
            r'Detroit|Chicago|Boston|Seattle|New\s+York|'
            r'San\s+Francisco'
            r')'
            r'\s*,?\s*'
            r'(?:'
            # Canadian provinces.
            # Allow PDF extraction to insert spaces inside words:
            # Ontario -> O ntario
            r'O\s*ntario|ON|'
            r'Q\s*uebec|QC|'
            r'B\s*ritish\s+C\s*olumbia|BC|'
            r'A\s*lberta|AB|'
            r'M\s*anitoba|MB|'
            # US state abbreviations
            r'[A-Z]{2}'
            r')'
            r'\s*$'
        )

        text = trailing_location_pattern.sub('', text).strip()

        # -----------------------------------------------------
        # Remove common location-only values
        # -----------------------------------------------------

        location_pattern = re.compile(
            r'(?i)^('
            r'toronto|waterloo|ottawa|montreal|vancouver|calgary|'
            r'edmonton|winnipeg|ontario|canada|usa|united states|'
            r'new york|boston|chicago|seattle|san francisco'
            r')(?:\s*,.*)?$'
        )

        if location_pattern.match(text):
            return ""

        bad_headers = {
            "experience",
            "work experience",
            "technical experience",
            "professional experience"
        }

        if text.lower() in bad_headers:
            return ""
    
        # -----------------------------------------------------
        # Remove obvious email / URL
        # -----------------------------------------------------

        if '@' in text or 'http://' in text.lower() or 'https://' in text.lower():
            return ""

        return text.strip()

    cleaned_candidates = []

    # ---------------------------------------------------------
    # Detect split-line employment layouts
    #
    # Example:
    #
    # Software Developer          Waterloo, Ontario
    # Islamic Information Centre May 2024 - Aug 2024
    #
    # In this layout, text before the date is the EMPLOYER,
    # while the previous line contains the actual job title.
    # ---------------------------------------------------------

    split_layout_title_terms = {
        "developer",
        "engineer",
        "analyst",
        "manager",
        "intern",
        "associate",
        "assistant",
        "specialist",
        "coordinator",
        "technician",
        "designer",
        "architect",
        "administrator",
        "lead",
        "consultant",
        "scientist",
        "director",
        "officer",
        "representative",
        "programmer",
        "tutor",
        "executive",
        "sysadmin",
        "trainee",
        "head",
        "commander",
        "president",
        "advisor",
        "assessor",        
        "fellow",
        "internship",
        "instructor"
    }

    split_layout_employer_terms = {
        "inc",
        "llc",
        "ltd",
        "corp",
        "corporation",
        "company",
        "university",
        "college",
        "school",
        "bank",
        "capital",
        "group",
        "hospital",
        "clinic",
        "institute",
        "centre",
        "center",
        "technologies",
        "department",
        "organization",
        "organisation",        
        "technology",
        "commander",
        "president",
        "school",
        "solutions"
    }

    # ---------------------------------------------------------
    # Strong three-line employment layout:
    #
    # TITLE
    # EMPLOYER
    # DATE
    #
    # Example:
    #
    # Data Analyst
    # Aviva Insurance, Toronto, Canada
    # June 2022 - Present
    #
    # Boost previous-line-2 only when:
    #   - current line is essentially date-only
    #   - previous-line-1 looks employer/location-like
    #   - previous-line-2 looks like a concise job title
    # ---------------------------------------------------------

    if latest_index >= 2:

        date_only_text = clean_candidate(
            date_line
        )

        employer_line = clean_candidate(
            lines[latest_index - 1]
        )

        title_line = clean_candidate(
            lines[latest_index - 2]
        )

        title_lower = title_line.lower()

        title_words = re.findall(
            r"[A-Za-z][A-Za-z'&./-]*",
            title_line
        )

        title_has_role_term = any(
            re.search(
                rf'\b{re.escape(term)}\b',
                title_lower
            )
            for term in split_layout_title_terms
        )

        title_is_concise = (
            1 <= len(title_words) <= 10
        )

        employer_looks_plausible = bool(
            employer_line
        ) and not any(
            re.search(
                rf'\b{re.escape(term)}\b',
                employer_line.lower()
            )
            for term in split_layout_title_terms
        )

        # clean_candidate(date_line) should be empty when the
        # physical line contains only the date range.
        date_is_standalone = (
            not date_only_text
        )

        if (
            date_is_standalone
            and employer_looks_plausible
            and title_has_role_term
            and title_is_concise
        ):

            print(
                "Detected title/employer/date three-line layout: "
                f"title='{title_line}', "
                f"employer='{employer_line}'"
            )

            for candidate in candidates:

                if (
                    candidate["source"] == "previous-line-2"
                    and clean_candidate(
                        candidate["text"]
                    ) == title_line
                ):
                    candidate["score"] += 100
                    break
                    
    # ---------------------------------------------------------
    # Recover an explicit role stated in nearby prose when the
    # selected date line itself does not contain a job title.
    #
    # Examples:
    #
    # Served as a Trainer and Supervisor.
    # Worked as a Software Engineer.
    # Role as an Operations Analyst.
    #
    # This is a FALLBACK only. It must not compete with a
    # normal title already found on the selected date line.
    # ---------------------------------------------------------

    selected_before_date = (
    clean_candidate(before_date) or ""
    )

    selected_lower = selected_before_date.lower()

    selected_has_title_term = any(
        re.search(
            rf'\b{re.escape(term)}\b',
            selected_lower
        )
        for term in split_layout_title_terms
    )

    if not selected_has_title_term:

        role_phrase_patterns = [
            re.compile(
                r'(?i)\bserved\s+as\s+(?:an?\s+)?'
                r'([A-Za-z][A-Za-z &/\-]{2,60})'
            ),
            re.compile(
                r'(?i)\bworked\s+as\s+(?:an?\s+)?'
                r'([A-Za-z][A-Za-z &/\-]{2,60})'
            ),
            re.compile(
                r'(?i)\brole\s+as\s+(?:an?\s+)?'
                r'([A-Za-z][A-Za-z &/\-]{2,60})'
            ),
            re.compile(
                r'(?i)\bacting\s+as\s+(?:an?\s+)?'
                r'([A-Za-z][A-Za-z &/\-]{2,60})'
            ),
        ]

        # Search backward near the selected employment date.
        # Ashwin's explicit title appears earlier in the same
        # employment block.
        role_search_start = max(
            0,
            latest_index - 25
        )

        for idx in range(
            latest_index - 1,
            role_search_start - 1,
            -1
        ):

            role_line = lines[idx].strip()

            if not role_line:
                continue

            for role_pattern in role_phrase_patterns:

                role_match = role_pattern.search(
                    role_line
                )

                if not role_match:
                    continue

                recovered_role = (
                    role_match.group(1).strip()
                )

                # Stop at sentence boundaries.
                recovered_role = re.split(
                    r'[.;|]',
                    recovered_role,
                    maxsplit=1
                )[0].strip()

                # Do not accept long prose as a title.
                role_words = recovered_role.split()

                if not (
                    1 <= len(role_words) <= 8
                ):
                    continue

                candidates.append({
                    "text": recovered_role,
                    "source": "explicit-role-phrase",
                    "score": 190
                })

                print(
                    "Recovered explicit nearby role: "
                    f"'{recovered_role}'"
                )

                break

            else:
                continue

            break

    same_line_candidate = next(
        (
            candidate
            for candidate in candidates
            if candidate["source"] == "same-line-before-date"
        ),
        None
    )

    previous_line_candidate = next(
        (
            candidate
            for candidate in candidates
            if candidate["source"] == "previous-line-1"
        ),
        None
    )

    if same_line_candidate and previous_line_candidate:

        same_text = (
            clean_candidate(
                same_line_candidate["text"]
            ) or ""
        )

        previous_text = (
            clean_candidate(
                previous_line_candidate["text"]
            ) or ""
        )

        same_lower = same_text.lower()
        previous_lower = previous_text.lower()

        same_has_title_word = any(
            re.search(
                rf'\b{re.escape(term)}\b',
                same_lower
            )
            for term in split_layout_title_terms
        )

        same_has_employer_word = any(
            re.search(
                rf'\b{re.escape(term)}\b',
                same_lower
            )
            for term in split_layout_employer_terms
        )

        previous_has_title_word = any(
            re.search(
                rf'\b{re.escape(term)}\b',
                previous_lower
            )
            for term in split_layout_title_terms
        )

        # -----------------------------------------------------
        # Structural checks for:
        #
        # TITLE
        # EMPLOYER + DATE
        #
        # We do NOT require the employer to contain words such
        # as Inc, LLC, Bank, Centre, etc.
        #
        # Examples:
        #
        # Data Analyst
        # TD Insurance, Toronto       Feb 2022 - Present
        #
        # Software Developer
        # Islamic Information Centre May 2024 - Aug 2024
        # -----------------------------------------------------

        same_words = re.findall(
            r"[A-Za-z][A-Za-z'&.-]*",
            same_text
        )

        previous_words = re.findall(
            r"[A-Za-z][A-Za-z'&./-]*",
            previous_text
        )

        # Job-title lines are normally concise.
        previous_is_concise = (
            1 <= len(previous_words) <= 10
        )

        # Employer names are normally also fairly concise.
        same_is_concise = (
            1 <= len(same_words) <= 10
        )

        # Reject obvious sentence/bullet text.
        previous_looks_like_sentence = bool(
            re.search(
                r'(?i)\b(?:'
                r'developed|implemented|created|managed|worked|'
                r'provided|designed|built|conducted|collaborated|'
                r'utilized|used|led|assisted|responsible|'
                r'performed|maintained|supported'
                r')\b',
                previous_text
            )
        )

        previous_starts_like_bullet = bool(
            re.match(
                r'^[•●▪◦*→\-–—]',
                lines[latest_index - 1].strip()
            )
        ) if latest_index > 0 else False

        # Section headings should never become titles.
        previous_is_header = (
            previous_lower.strip()
            in {
                "experience",
                "experiences",
                "work experience",
                "professional experience",
                "technical experience",
                "employment",
                "employment history"
            }
        )

        # Same-line text is probably an employer if it does NOT
        # itself contain a recognizable title word.
        structurally_looks_like_employer = (
            same_is_concise
            and not same_has_title_word
        )

        structurally_looks_like_title = (
            previous_has_title_word
            and previous_is_concise
            and not previous_looks_like_sentence
            and not previous_starts_like_bullet
            and not previous_is_header
        )

        # Strong evidence of:
        #
        # TITLE
        # EMPLOYER + DATE
        #
        # Only boost the previous line when:
        #   1. same-line text looks employer-like
        #   2. same-line text does NOT look like a title
        #   3. previous line DOES look like a title
        #
        # This avoids globally boosting previous lines.

        if (
            structurally_looks_like_employer
            and structurally_looks_like_title
        ):

            # -------------------------------------------------
            # Remove trailing location from a title appearing
            # above an employer/date line.
            #
            # Examples:
            #
            # DECA Chapter President Georgetown, ON
            # -> DECA Chapter President
            #
            # Software Developer Toronto, ON
            # -> Software Developer
            #
            # Only strip text AFTER the last recognized title
            # term, so titles such as "Manager, IT" are safe.
            # -------------------------------------------------

            previous_title_matches = []

            for term in split_layout_title_terms:

                previous_title_matches.extend(
                    re.finditer(
                        rf'\b{re.escape(term)}\b',
                        previous_text,
                        re.IGNORECASE
                    )
                )

            if previous_title_matches:

                last_title_match = max(
                    previous_title_matches,
                    key=lambda m: m.end()
                )

                trailing_after_title = (
                    previous_text[
                        last_title_match.end():
                    ].strip()
                )

                if re.fullmatch(
                    r"[A-Za-z][A-Za-z .'-]{1,50}"
                    r",\s*[A-Z]{2,3}",
                    trailing_after_title
                ):
                    previous_text = previous_text[
                        :last_title_match.end()
                    ].strip()

                    # Update the actual candidate too,
                    # not just the local display variable.
                    previous_line_candidate["text"] = (
                        previous_text
                    )

            print(
                "Detected split-line title/employer layout: "
                f"title='{previous_text}', "
                f"employer='{same_text}'"
            )

            same_line_candidate["score"] -= 120
            previous_line_candidate["score"] += 120

    # ---------------------------------------------------------
    # Handle employer + date followed by role lines
    #
    # Example:
    #
    # Bayview Secondary School (2022 - 2023)
    # - General Executive at Bayview Computer Club
    # - Sysadmin for Bayview's Engineering Club
    #
    # Policy:
    # Use the FIRST valid role listed below the employer.
    # ---------------------------------------------------------

    if same_line_candidate:

        employer_text = (
            clean_candidate(
                same_line_candidate["text"]
            ) or ""
        )

        employer_lower = employer_text.lower()

        same_line_looks_like_employer = any(
            re.search(
                rf'\b{re.escape(term)}\b',
                employer_lower
            )
            for term in split_layout_employer_terms
        )

        same_line_looks_like_title = any(
            re.search(
                rf'\b{re.escape(term)}\b',
                employer_lower
            )
            for term in split_layout_title_terms
        )

        employer_words = re.findall(
            r"[A-Za-z][A-Za-z'&./()-]*",
            employer_text
        )

        employer_is_concise = (
            1 <= len(employer_words) <= 12
        )

        # Structural employer detection:
        # A concise date-bearing line with no title keyword is
        # probably the employer even when it lacks Inc/LLC/Bank/etc.
        structurally_looks_like_employer_below = (
            employer_is_concise
            and not same_line_looks_like_title
        )

        if (
            same_line_looks_like_employer
            or structurally_looks_like_employer_below
        ) and not same_line_looks_like_title:

            # Look immediately BELOW the employer/date line.
            # First valid title wins.
            for offset in range(1, 4):

                idx = latest_index + offset

                if idx >= len(lines):
                    break

                following_line = lines[idx].strip()

                if not following_line:
                    continue

                # -------------------------------------------------
                # Reject true responsibility bullets.
                #
                # Do NOT reject "-" automatically because some
                # resumes use hyphens for legitimate role entries:
                #
                # - General Executive at Bayview Computer Club
                #
                # Symbol bullets are still rejected immediately.
                # Hyphen-prefixed lines are evaluated below using
                # title structure.
                # -------------------------------------------------

                if re.match(
                    r'^\s*[•▪●○◦➢➤►]\s*',
                    following_line
                ):
                    continue
                    
                # -------------------------------------------------
                # A following line with its OWN employment date is
                # a separate employment record, not the title of
                # the current employer/date row.
                #
                # Example:
                #
                # Talent Management Specialist ... Mar'24-Present
                # IT Recruitment Specialist ... Aug'22-Mar'24
                #
                # Do not attach the second job to the first one.
                # -------------------------------------------------

                if date_range_pattern.search(following_line):
                    continue

                following_clean = clean_candidate(
                    following_line
                )

                if not following_clean:
                    continue

                # Normalize explicit role/title labels before
                # evaluating the following line as a job title.
                #
                # Examples:
                #
                # Key Role: Sr. Security Advisor and Assessor ...
                # Role: Business Development Manager
                # Position: Software Developer
                # Job Title: Data Engineer
                # Title: Systems Analyst
                # -------------------------------------------------

                following_clean = re.sub(
                    r'(?i)^(?:key\s+role|job\s+title|role|position|title)'
                    r'\s*[:\-–—]\s*',
                    '',
                    following_clean
                ).strip()

                if not following_clean:
                    continue

                following_lower = following_clean.lower()

                # -------------------------------------------------
                # Following role line may also contain a location.
                #
                # Examples:
                #
                # Field Hand St. Catharines, ON
                # Data Analyst Toronto, ON
                # Technician Waterloo, ON
                #
                # First try to remove a trailing city + state/province
                # when a comma + 2-letter region code is present.
                # -------------------------------------------------

                role_candidate = following_clean

                location_match = re.search(
                    r',\s*[A-Z]{2}\s*$',
                    role_candidate
                )

                has_location_suffix = bool(location_match)

                if has_location_suffix:

                    # Known Canadian / US province-state abbreviations.
                    region_codes = {
                        "AB", "BC", "MB", "NB", "NL", "NS", "NT",
                        "NU", "ON", "PE", "QC", "SK", "YT",
                        "AL", "AK", "AZ", "AR", "CA", "CO", "CT",
                        "DE", "FL", "GA", "HI", "ID", "IL", "IN",
                        "IA", "KS", "KY", "LA", "ME", "MD", "MA",
                        "MI", "MN", "MS", "MO", "MT", "NE", "NV",
                        "NH", "NJ", "NM", "NY", "NC", "ND", "OH",
                        "OK", "OR", "PA", "RI", "SC", "SD", "TN",
                        "TX", "UT", "VT", "VA", "WA", "WV", "WI",
                        "WY", "DC"
                    }

                    region_match = re.search(
                        r',\s*([A-Z]{2})\s*$',
                        role_candidate
                    )

                    region_code = (
                        region_match.group(1)
                        if region_match
                        else ""
                    )

                    if region_code in region_codes:

                        # Remove location from known pattern:
                        #
                        # Field Hand St. Catharines, ON
                        #
                        # We use known job-title keywords from the beginning
                        # of the line where possible.
                        location_role_match = re.match(
                            r'(?i)^(.+?\b(?:'
                            r'Hand|'
                            r'Analyst|Developer|Engineer|Manager|Intern|'
                            r'Associate|Assistant|Specialist|Coordinator|'
                            r'Technician|Designer|Architect|Administrator|'
                            r'Lead|Member|Supervisor|Director|Officer|'
                            r'Consultant|Scientist|Programmer|Instructor|'
                            r'Recruiter'
                            r'))\b'
                            r'.*,\s*[A-Z]{2}\s*$',
                            role_candidate
                        )

                        if location_role_match:
                            role_candidate = (
                                location_role_match.group(1).strip()
                            )


                following_lower = role_candidate.lower()

                has_title_word = any(
                    re.search(
                        rf'\b{re.escape(term)}\b',
                        following_lower
                    )
                    for term in split_layout_title_terms
                )

                # Field Hand is a legitimate occupational title, but "Hand"
                # is intentionally not added globally because it is too broad.
                has_field_hand_title = bool(
                    re.search(
                        r'(?i)^Field\s+Hand$',
                        role_candidate
                    )
                )

                if not (
                    has_title_word
                    or has_field_hand_title
                ):
                    continue


                role_only = re.split(
                    r'(?i)\s+(?:at|for)\s+',
                    role_candidate,
                    maxsplit=1
                )[0].strip()
                
                # Remove explicit role/title labels.
                #
                # Role – Business Development Manager
                # -> Business Development Manager

                role_only = re.sub(
                    r'(?i)^(?:key\s+role|job\s+title|role|position|title)'
                    r'\s*[:\-–—]\s*',
                    '',
                    role_only
                ).strip()

                role_only = re.sub(
                    r'^[•●▪◦*:\-–—]+\s*',
                    '',
                    role_only
                ).strip()

                # ---------------------------------------------
                # Remove a trailing city/location from a role
                # recovered below an employer/date line.
                #
                # Examples:
                #
                # Lieutenant Platoon Commander Singapore, SG
                # -> Lieutenant Platoon Commander
                #
                # Software Engineering Intern Montreal, QC
                # -> Software Engineering Intern
                #
                # Only strip text AFTER a recognized title term.
                # This avoids damaging titles such as:
                #
                # Manager, IT
                # ---------------------------------------------

                title_term_matches = []

                for term in split_layout_title_terms:

                    title_term_matches.extend(
                        re.finditer(
                            rf'\b{re.escape(term)}\b',
                            role_only,
                            re.IGNORECASE
                        )
                    )

                if title_term_matches:

                    last_title_match = max(
                        title_term_matches,
                        key=lambda m: m.end()
                    )

                    trailing_after_title = (
                        role_only[
                            last_title_match.end():
                        ].strip()
                    )

                    # City/region + comma + 2/3-letter
                    # province/state/country abbreviation.
                    #
                    # Singapore, SG
                    # Montreal, QC
                    # Toronto, ON
                    # New York, NY
                    location_suffix_match = re.fullmatch(
                        r"[A-Za-z][A-Za-z .'-]{1,50}"
                        r",\s*[A-Z]{2,3}",
                        trailing_after_title
                    )

                    if location_suffix_match:

                        role_only = role_only[
                            :last_title_match.end()
                        ].strip()

                if role_only:

                    print(
                        "Detected employer/date followed by role: "
                        f"employer='{employer_text}', "
                        f"role='{role_only}'"
                    )

                    candidates.append({
                        "text": role_only,
                        "source": "following-role-line",
                        "score": 180
                    })

                    break

    # ---------------------------------------------------------
    # Handle three-line employment layout:
    #
    # EMPLOYER
    # DATE
    # JOB TITLE
    #
    # Example:
    #
    # Laurentian Bank of Canada
    # Jan 2019 - Till date
    # DevOps Engineer
    #
    # The existing following-role logic handles:
    #
    # EMPLOYER + DATE
    # JOB TITLE
    #
    # This handles the date-only middle line.
    # ---------------------------------------------------------

    if latest_index + 1 < len(lines):

        current_date_line_clean = clean_candidate(
            lines[latest_index]
        ) or ""

        # A standalone date line should contain essentially
        # nothing after removing the recognized date.
        date_removed = date_range_pattern.sub(
            '',
            lines[latest_index]
        ).strip()

        date_removed = re.sub(
            r'^[\s|,:;\-–—()]+|[\s|,:;\-–—()]+$',
            '',
            date_removed
        ).strip()

        if not date_removed:

            following_line = lines[
                latest_index + 1
            ].strip()

            if following_line:

                # Never accept a responsibility/bullet.
                if not re.match(
                    r'^\s*[•▪●○◦➢➤►]',
                    following_line
                ):

                    following_clean = (
                        clean_candidate(
                            following_line
                        ) or ""
                    )

                    following_lower = (
                        following_clean.lower()
                    )

                    has_title_word = any(
                        re.search(
                            rf'\b{re.escape(term)}\b',
                            following_lower
                        )
                        for term
                        in split_layout_title_terms
                    )

                    # Keep this conservative. A title directly
                    # below a standalone employment date should
                    # still look like a concise occupational
                    # title.
                    following_words = re.findall(
                        r"[A-Za-z][A-Za-z'&./-]*",
                        following_clean
                    )

                    if (
                        has_title_word
                        and
                        1 <= len(following_words) <= 8
                    ):

                        print(
                            "Detected standalone-date followed "
                            "by role: "
                            f"date='{lines[latest_index]}', "
                            f"role='{following_clean}'"
                        )

                        candidates.append({
                            "text": following_clean,
                            "source":
                                "standalone-date-following-role",
                            "score": 190
                        })

    for candidate in candidates:
        cleaned = clean_candidate(candidate["text"])

        if cleaned:
            cleaned_candidates.append({
                "text": cleaned,
                "source": candidate["source"],
                "score": candidate["score"]
            })

    # ---------------------------------------------------------
    # 8. Read job titles from job_titles.txt
    #
    # These are supporting keywords only.
    # They are NOT required for a title to be valid.
    # ---------------------------------------------------------

    try:
        job_titles_keywords = read_job_titles_from_file(
            job_titles_file_path
        )

        job_titles_keywords = [
            title.strip()
            for title in job_titles_keywords
            if title.strip()
        ]

    except Exception:
        job_titles_keywords = []

    # Sort longest titles first
    job_titles_keywords.sort(
        key=len,
        reverse=True
    )

    # ---------------------------------------------------------
    # 9. Score title candidates
    # ---------------------------------------------------------

    generic_terms = {
        "developer",
        "engineer",
        "analyst",
        "manager",
        "intern",
        "co-op",
        "associate",
        "student",
        "assistant",
        "specialist",
        "coordinator",
        "technician",
        "designer",
        "architect",
        "administrator",
        "lead",
        "commander",
        "president",
        "founder",
        "internship",
        "member"
    }

    employer_indicators = {
        "inc",
        "llc",
        "ltd",
        "corp",
        "corporation",
        "company",
        "university",
        "bank",
        "capital",
        "group",
        "hospital",
        "clinic",
        "institute",
        "centre",
        "school",
        "center"
    }

    # ---------------------------------------------------------
    # Recover a known job title from severely collapsed PDF
    # text.
    #
    # Example:
    #
    # ...MicrosoftWindows,LinuxNationalJudgeToronto...
    #
    # -> National Judge
    #
    # This uses job_titles.txt as the anchor rather than
    # hardcoding individual resume titles.
    # ---------------------------------------------------------

    def recover_collapsed_known_title(text):

        if not text:
            return None

        # -----------------------------------------------------
        # Preserve a readable title segment inside a long
        # employer + title + client/details line.
        #
        # Example:
        #
        # InTunnel Monitor, Canada.
        # Enterprise / Security Architect, DevSecOps Lead.
        # The end clients were ...
        #
        # -> Enterprise / Security Architect, DevSecOps Lead
        #
        # This must happen BEFORE collapsed-text recovery.
        # Otherwise CamelCase elsewhere in the line can cause
        # a valid multi-part title to be reduced to something
        # generic such as "Architect".
        # -----------------------------------------------------

        sentence_segments = re.split(
            r'(?<=[.!?])\s+',
            text
        )

        for segment in sentence_segments:

            segment = segment.strip(
                " \t\r\n.,;:"
            )

            if not segment:
                continue

            segment_words = re.findall(
                r"[A-Za-z][A-Za-z0-9/&+-]*",
                segment
            )

            # A real title segment should remain concise.
            if not (
                2 <= len(segment_words) <= 10
            ):
                continue

            title_term_hits = sum(
                1
                for term in split_layout_title_terms
                if re.search(
                    rf'(?i)\b{re.escape(term)}\b',
                    segment
                )
            )

            # At least one occupational title term is enough
            # when the segment is concise and contains a clear
            # structured separator such as "/" or ",".
            if title_term_hits < 1:
                continue

            # Extra evidence that this is a structured
            # multi-part title rather than prose.
            has_title_separator = bool(
                re.search(
                    r'[/,]',
                    segment
                )
            )

            if not has_title_separator:
                continue

            print(
                "Detected readable title segment before "
                "collapsed-text recovery: "
                f"'{segment}'"
            )

            return segment

        # -----------------------------------------------------
        # Preserve clear readable multi-word job titles.
        #
        # Collapsed-title recovery is only for genuinely damaged
        # text where the title itself cannot be read normally.
        # -----------------------------------------------------

        readable_title_patterns = [
            r'\bAssistant\s+Project\s+Manager\b',
            r'\bProject\s+Manager\b',
            r'\bFull[- ]?stack\s+Developer\b',
            r'\bSoftware\s+Developer\b',
            r'\bSoftware\s+Engineer\b',
            r'\bData\s+Analyst\b',
            r'\bData\s+Scientist\b',
            r'\bResearch\s+Assistant\b',
            r'\bAccounting\s+Associate\b',
            r'\bTechnical\s+Product\s+Intern\b',
            r'\bComputer\s+Programming\s+Intern\b',
            r'\bProject\s+Developer\b',
            r'\bApp\s+Developer\b',
            r'\bMachine\s+Learning\s*/\s*Software\s+Engineer\b',
            r'\bQuantitative\s+Strategies\s+Software\s+Developer\s+Co-Op\b',
        ]

        if any(
            re.search(
                pattern,
                text,
                re.IGNORECASE
            )
            for pattern in readable_title_patterns
        ):
            return None
            
        # Only use this rescue for suspiciously long/collapsed
        # candidates. Normal titles should use normal logic.
        # old code..
        ##if len(text) < 45:
        ##    return None

        # -----------------------------------------------------
        # Only use collapsed-title recovery when the text
        # actually shows evidence of PDF word concatenation.
        #
        # Good rescue example:
        #
        # LinuxNationalJudgeToronto
        #
        # Normal titles such as these must NOT be rewritten:
        #
        # Quantitative Strategies Software Developer Co-Op
        # Assistant Project Manager: StarterHacks
        # Machine Learning / Software Engineer
        # App Developer - Knit Wiz
        # -----------------------------------------------------

        if len(text) < 45:
            return None

        # CamelCase words glued together by PDF extraction:
        #
        # LinuxNationalJudgeToronto
        # StudentInternWaterloo
        #
        has_glued_camelcase = bool(
            re.search(
                r'[a-z][A-Z]',
                text
            )
        )

        # Extremely long alphabetic token with no spaces.
        #
        # Useful for badly collapsed PDFs even when the
        # capitalization pattern is inconsistent.
        glued_alpha_tokens = re.findall(
            r'[A-Za-z]+',
            text
        )

        has_very_long_glued_token = any(
            len(token) >= 30
            for token in glued_alpha_tokens
        )

        if not (
            has_glued_camelcase
            or has_very_long_glued_token
        ):
            return None

        # Restore likely CamelCase boundaries:
        #
        # LinuxNationalJudgeToronto
        # ->
        # Linux National Judge Toronto
        expanded = re.sub(
            r'(?<=[a-z])(?=[A-Z])',
            ' ',
            text
        )

        expanded = re.sub(
            r'(?<=[A-Z])(?=[A-Z][a-z])',
            ' ',
            expanded
        )

        expanded = re.sub(
            r'\s+',
            ' ',
            expanded
        ).strip()

        matches = []

        # Prefer longer known titles first.
        sorted_known_titles = sorted(
            job_titles_keywords,
            key=lambda x: len(x),
            reverse=True
        )

        for known_title in sorted_known_titles:

            known_title = known_title.strip()

            if not known_title:
                continue

            pattern = (
                r'(?i)(?<![A-Za-z])'
                + re.escape(known_title)
                + r'(?![A-Za-z])'
            )

            for match in re.finditer(
                pattern,
                expanded
            ):

                recovered_title = known_title

                # ---------------------------------------------
                # Preserve common title modifiers appearing
                # immediately before a known title.
                #
                # Examples:
                # National Judge
                # Senior Analyst
                # Lead Developer
                # Regional Manager
                # ---------------------------------------------

                prefix_text = expanded[
                    :match.start()
                ].rstrip()

                # -------------------------------------------------
                # Recover a multi-word uppercase title phrase that
                # immediately precedes a known occupational title.
                #
                # This handles collapsed PDF text such as:
                #
                # communicationINDEPENDENT ENGLISH AND COMMUNICATION TUTOR
                #
                # After CamelCase boundary repair:
                #
                # communication INDEPENDENT ENGLISH AND COMMUNICATION TUTOR
                #
                # known_title = "Tutor"
                #
                # Recover:
                # Independent English and Communication Tutor
                #
                # The phrase must begin with an uppercase word and
                # remain immediately adjacent to the known title.
                # Lowercase connector words such as "and", "of",
                # "for", "to", "&" are allowed inside the phrase.
                # -------------------------------------------------

                uppercase_title_prefix = re.search(
                    r'('

                    # The recovered title MUST begin with an
                    # uppercase/title-like word. A lowercase connector
                    # cannot start the recovered phrase.
                    r'[A-Z][A-Z0-9&./+\-]*'

                    # Additional title words may be uppercase words
                    # or lowercase connector words.
                    r'(?:\s+'
                    r'(?:'
                    r'[A-Z][A-Z0-9&./+\-]*'
                    r'|and|of|for|to|the|in|on|with|&'
                    r')'
                    r')*'

                    r')\s*$',
                    prefix_text
                )

                if uppercase_title_prefix:

                    title_prefix = uppercase_title_prefix.group(1).strip()

                    recovered_title = (
                        title_prefix
                        + " "
                        + known_title
                    )

                    # Convert all-uppercase recovered PDF titles into
                    # normal display capitalization while preserving
                    # common lowercase connector words.
                    words = recovered_title.split()

                    connector_words = {
                        "and", "of", "for", "to",
                        "the", "in", "on", "with"
                    }

                    normalized_words = []

                    for word in words:

                        if word.lower() in connector_words:
                            normalized_words.append(word.lower())

                        elif word.isupper():
                            normalized_words.append(word.title())

                        else:
                            normalized_words.append(word)

                    recovered_title = " ".join(normalized_words)

                else:

                    # Existing single-modifier fallback.
                    prefix_match = re.search(
                        r'(?i)\b('
                        r'senior|sr\.?|'
                        r'junior|jr\.?|'
                        r'lead|principal|chief|'
                        r'assistant|associate|'
                        r'national|regional|'
                        r'global|corporate'
                        r')\s*$',
                        prefix_text
                    )

                    if prefix_match:

                        modifier = prefix_match.group(1)

                        recovered_title = (
                            modifier
                            + " "
                            + known_title
                        )

                matches.append({
                    "title": recovered_title,
                    "position": match.start(),
                    "known_length": len(known_title)
                })


        if not matches:
            return None


        # Prefer:
        #   1. title closest to the employment date
        #   2. longer known title when tied
        #
        # Since this function receives text BEFORE the date,
        # the largest position is closest to that date.
        matches.sort(
            key=lambda x: (
                x["position"],
                x["known_length"]
            ),
            reverse=True
        )

        best = matches[0]["title"]

        print(
            "Recovered title from collapsed PDF text: "
            f"'{best}'"
        )

        return best

    scored_candidates = []

    for candidate in cleaned_candidates:

        text = candidate["text"]
        lower_text = text.lower()

        score = candidate["score"]

        # ---------------------------------------------
        # Resolve pipe-delimited title layouts BEFORE
        # candidate scoring.
        #
        # Supports:
        #
        #   TITLE | TECHNOLOGY STACK
        #   TITLE | EMPLOYER
        #   EMPLOYER | TITLE
        #   EMPLOYER | COLLAPSEDTITLE
        #
        # Examples:
        #
        #   Software Developer | React, AWS
        #       -> Software Developer
        #
        #   LEXINGTONYOUTHSTEAMTEAM | SOFTWAREDEVELOPER
        #       -> Software Developer
        #
        # Change/Added 8/29/2026
        # Use the existing known-title vocabulary rather than
        # assuming that the left side of "|" is always the title.
        # ---------------------------------------------

        if "|" in text:

            pipe_parts = [
                part.strip()
                for part in text.split("|")
                if part.strip()
            ]

            if len(pipe_parts) >= 2:

                left_part = pipe_parts[0]
                right_part = pipe_parts[1]

                def get_pipe_known_title(part):

                    compact_part = re.sub(
                        r'[^a-z0-9]+',
                        '',
                        part.lower()
                    )

                    if not compact_part:
                        return None

                    matches = []

                    for known_title in job_titles_keywords:

                        known_title = known_title.strip()

                        if not known_title:
                            continue

                        compact_known_title = re.sub(
                            r'[^a-z0-9]+',
                            '',
                            known_title.lower()
                        )

                        # Exact compact equivalence allows recovery of
                        # collapsed PDF titles such as SOFTWAREDEVELOPER.
                        if compact_part == compact_known_title:
                            matches.append(known_title)
                            continue

                        # Normal readable known-title match.
                        pattern = (
                            r'(?i)(?<!\w)'
                            + re.escape(known_title)
                            + r'(?!\w)'
                        )

                        if re.search(pattern, part):
                            matches.append(known_title)

                    if not matches:
                        return None

                    return max(
                        matches,
                        key=len
                    )

                left_known_title = get_pipe_known_title(
                    left_part
                )

                right_known_title = get_pipe_known_title(
                    right_part
                )

                if right_known_title and not left_known_title:

                    print(
                        "Scoring employer | title layout: "
                        f"'{text}' -> '{right_known_title}'"
                    )

                    text = right_known_title
                    lower_text = text.lower()

                    # Strong structural evidence:
                    # pipe layout + exact known-title vocabulary match.
                    score += 80

                elif left_known_title:

                    print(
                        "Scoring title | details layout: "
                        f"'{text}' -> '{left_known_title}'"
                    )

                    text = left_known_title
                    lower_text = text.lower()

        # ---------------------------------------------
        # Rescue severely collapsed PDF candidates.
        # ---------------------------------------------

        collapsed_recovered_title = (
            recover_collapsed_known_title(text)
        )

        if collapsed_recovered_title:

            text = collapsed_recovered_title
            lower_text = text.lower()

            # Strong structural recovery from a known title.
            score += 80

        # ---------------------------------------------
        # "Project" can be part of a legitimate job
        # title and must not automatically imply that
        # the entry is a personal/academic project.
        #
        # Examples:
        # Assistant Project Manager
        # Project Manager
        # Project Lead
        # Project Coordinator
        # Project Engineer
        #
        # Do NOT include generic "Project Team Member"
        # here because that can still represent a
        # school/personal project rather than employment.
        # ---------------------------------------------

        project_is_job_title = bool(
            re.search(
                r'(?i)\b'
                r'(?:assistant\s+)?'
                r'project\s+'
                r'(?:manager|lead|coordinator|engineer|'
                r'analyst|director|specialist|officer)'
                r'\b',
                text
            )
        )
        
        # ---------------------------------------------
        # Detect project / non-employment titles
        # ---------------------------------------------

        project_hits = sum(
            1
            for indicator in project_indicators
            if indicator in lower_text
            and not (
                project_is_job_title
                and indicator.lower().strip() == "project"
            )
        )

        if project_hits:
            score -= 50
        
        words = re.findall(r"[A-Za-z]+(?:[-/][A-Za-z]+)*", text
        )

        if not words:
            continue

        # ---------------------------------------------
        # Known job-title match
        # ---------------------------------------------

        matched_titles = []

        for known_title in job_titles_keywords:
            pattern = r'(?i)(?<!\w)' + re.escape(
                known_title
            ) + r'(?!\w)'

            if re.search(pattern, text):
                matched_titles.append(known_title)

        if matched_titles:
            longest_match = max(
                matched_titles,
                key=len
            )

            # Stronger score for complete title phrases
            score += min(len(longest_match.split()) * 20, 80)

        # ---------------------------------------------
        # Job-title semantic words
        # ---------------------------------------------

        title_words_found = sum(
            1 for word in generic_terms
            if re.search(
                rf'(?i)\b{re.escape(word)}\b',
                text
            )
        )

        score += title_words_found * 12

        # ---------------------------------------------
        # Penalize employer/entity candidates that have
        # no occupational title signal.
        #
        # Structural examples:
        #
        # ABC Technologies Ltd.
        # Example Corporation
        # XYZ Bank
        #
        # These should lose to a nearby explicit role such as:
        #
        # Project Management Internship
        # Software Engineer
        # Data Analyst
        #
        # Important:
        # Do NOT penalize organization words when the candidate
        # also contains a real occupational title:
        #
        # Bank Operations Analyst
        # Technology Manager
        # University Research Assistant
        # ---------------------------------------------

        employer_hits = sum(
            1
            for indicator in employer_indicators
            if re.search(
                rf'(?i)\b{re.escape(indicator)}\b',
                text
            )
        )

        if (
            employer_hits > 0
            and title_words_found == 0
            and not matched_titles
        ):
            score -= 60

        # ---------------------------------------------
        # Penalize employer-like text
        # ---------------------------------------------

        employer_hits = sum(
            1
            for word in employer_indicators
            if re.search(
                rf'(?i)\b{re.escape(word)}\b',
                text
            )
        )

        score -= employer_hits * 20

        project_words = {
            "project",
            "prototype",
            "robot",
            "controller",
            "capstone",
            "course",
            "academic",
            "research"
        }

        project_hits = sum(
            1
            for word in project_words
            if re.search(
                rf'(?i)\b{re.escape(word)}\b',
                text
            )
            and not (
                project_is_job_title
                and word == "project"
            )
        )

        score -= project_hits * 40

        # ---------------------------------------------
        # Penalize location-heavy lines
        # ---------------------------------------------

        location_words = {
            "toronto",
            "waterloo",
            "ontario",
            "canada",
            "new york",
            "boston",
            "chicago",
            "vancouver",
            "calgary",
            "ottawa"
        }

        location_hits = sum(
            1
            for location in location_words
            if location in lower_text
        )

        score -= location_hits * 15

        # ---------------------------------------------
        # Penalize very long lines
        # ---------------------------------------------

        if len(words) > 10:
            score -= 20

        if len(words) > 15:
            score -= 30

        # ---------------------------------------------
        # Reward concise title-like text
        # ---------------------------------------------

        if 2 <= len(words) <= 8:
            score += 15

        # ---------------------------------------------
        # Reward known title phrases
        # ---------------------------------------------

        if matched_titles:
            score += 25

        scored_candidates.append({
            "text": text,
            "score": score,
            "source": candidate["source"],
            "matched_titles": matched_titles
        })

    if not scored_candidates:
        print("No viable job title candidates found.")
        return _format_job_title_result("N/A", reason="no_viable_title_candidates")

    # ---------------------------------------------------------
    # 10. Select the highest-scoring candidate
    # ---------------------------------------------------------

    scored_candidates.sort(
        key=lambda x: x["score"],
        reverse=True
    )

    print("\nScored title candidates:")

    for candidate in scored_candidates:
        print(
            f"  Score={candidate['score']:>4} | "
            f"Source={candidate['source']} | "
            f"Title={candidate['text']}"
        )

    best_candidate = scored_candidates[0]

    best_title = best_candidate["text"]

    # ---------------------------------------------------------
    # Handle collapsed employer + location + title layouts
    #
    # Example PDF extraction:
    #
    # High School Tutoring Center Shanghai, China
    # Teaching Assistant and Organizer
    #
    # may become:
    #
    # High School Tutoring Center Shanghai, China
    # Teaching Assistant and Organizer
    #
    # all on one physical line.
    #
    # Only remove the prefix when:
    #   1. the candidate contains an employer-like word
    #   2. a recognizable job-title phrase occurs AFTER it
    #
    # This avoids shortening normal titles such as:
    # Quantitative Strategies Software Developer Co-Op
    # ---------------------------------------------------------

    collapsed_employer_prefix_terms = {
        "company",
        "corporation",
        "corp",
        "inc",
        "llc",
        "ltd",
        "university",
        "college",
        "school",
        "bank",
        "group",
        "hospital",
        "clinic",
        "institute",
        "centre",
        "center",
        "organization",
        "organisation"
    }

    # ---------------------------------------------------------
    # Structurally recover a job-title suffix when PDF/DOCX
    # extraction collapses:
    #
    # EMPLOYER / LOCATION + JOB TITLE
    #
    # Examples of structure:
    #
    # Company Name Senior Technical Program Manager
    # Company, Ontario CA Sr Solution Manager
    #
    # Do NOT maintain a list of complete job-title phrases here.
    # Instead:
    #   1. require employer/location evidence before the title
    #   2. locate an occupational head word
    #   3. recover a concise title suffix ending at that head word
    # ---------------------------------------------------------

    collapsed_role_head_pattern = re.compile(
        r'(?i)\b(?:'
        + "|".join(
            re.escape(term)
            for term in sorted(
                split_layout_title_terms,
                key=len,
                reverse=True
            )
        )
        + r')\b'
    )

    # Structural evidence that text BEFORE the role is probably
    # employer/location information rather than part of the title.
    collapsed_prefix_signal_pattern = re.compile(
        r'(?i)\b(?:'
        r'inc|llc|ltd|corp|corporation|company|'
        r'university|college|school|bank|capital|group|'
        r'hospital|clinic|institute|centre|center|'
        r'technologies|technology|solutions|department|'
        r'toronto|waterloo|ontario|canada|'
        r'vancouver|calgary|ottawa'
        r')\b'
        r'|,\s*[A-Z]{2,3}\b'
    )

    role_matches = list(
        collapsed_role_head_pattern.finditer(best_title)
    )

    if role_matches:

        # Use the LAST occupational head word. In a collapsed
        # employer/title string this is normally the actual role
        # head, e.g. Manager in "Senior Technical Program Manager".
        role_head_match = role_matches[-1]

        words_with_spans = list(
            re.finditer(
                r"[A-Za-z][A-Za-z0-9&+./'-]*",
                best_title
            )
        )

        role_word_index = None

        for word_index, word_match in enumerate(words_with_spans):
            if (
                word_match.start() <= role_head_match.start()
                < word_match.end()
            ):
                role_word_index = word_index
                break

        if role_word_index is not None:

            # Job titles are normally compact. Recover up to
            # four descriptor words before the occupational head:
            #
            # Senior Technical Program Manager
            # Sr Solution Manager
            # Cloud Data Architect
            #
            # Then choose the earliest suffix that has structural
            # employer/location evidence before it.
            max_prefix_words = 4
            recovered_collapsed_title = None

            for prefix_count in range(
                max_prefix_words,
                -1,
                -1
            ):

                start_word_index = max(
                    0,
                    role_word_index - prefix_count
                )

                candidate_start = words_with_spans[
                    start_word_index
                ].start()

                prefix_text = best_title[
                    :candidate_start
                ].strip(" ,|:-–—")

                candidate_title = best_title[
                    candidate_start:
                    role_head_match.end()
                ].strip(" ,|:-–—")

                candidate_words = re.findall(
                    r"[A-Za-z][A-Za-z0-9&+./'-]*",
                    candidate_title
                )

                prefix_has_structural_signal = bool(
                    collapsed_prefix_signal_pattern.search(
                        prefix_text
                    )
                )

                if (
                    prefix_has_structural_signal
                    and 1 <= len(candidate_words) <= 5
                ):
                    recovered_collapsed_title = candidate_title
                    break

            if recovered_collapsed_title:

                print(
                    "Detected structural collapsed "
                    "employer/location/title layout: "
                    f"'{best_title}' -> "
                    f"'{recovered_collapsed_title}'"
                )

                best_title = recovered_collapsed_title
                
    # ---------------------------------------------------------
    # Handle known title + employer/location separated by comma
    #
    # Examples:
    #
    # Firmware Team Member, University of Waterloo Formula Electric,
    # Waterloo, ON
    # -> Firmware Team Member
    #
    # Data Analyst, ABC Corporation, Toronto, ON
    # -> Data Analyst
    #
    # Only apply this when:
    #   1. job_titles.txt matched a known title
    #   2. that known title appears at the START
    #   3. it is immediately followed by a comma
    #
    # This avoids blindly truncating ordinary comma-containing
    # job titles.
    # ---------------------------------------------------------

    matched_known_titles = best_candidate.get(
        "matched_titles",
        []
    )

    if matched_known_titles:

        longest_known_title = max(
            matched_known_titles,
            key=len
        ).strip()

        known_title_prefix_match = re.match(
            rf'(?i)^\s*'
            rf'({re.escape(longest_known_title)})'
            rf'\s*,\s+',
            best_title
        )

        if known_title_prefix_match:

            cleaned_known_title = (
                known_title_prefix_match
                .group(1)
                .strip()
            )

            print(
                "Detected known-title + employer/location layout: "
                f"'{best_title}' -> "
                f"'{cleaned_known_title}'"
            )

            best_title = cleaned_known_title

    # ---------------------------------------------------------
    # Handle organization prefix + known title
    #
    # Examples:
    #
    # UWaterloo Rocketry Design Team Member
    # -> Design Team Member
    #
    # ABC Corporation Software Developer
    # -> Software Developer
    #
    # Only apply when a known job title from job_titles.txt
    # occurs at the END of the candidate and there is text
    # before it.
    # ---------------------------------------------------------

    matched_known_titles = best_candidate.get(
        "matched_titles",
        []
    )

    if matched_known_titles:

        # -----------------------------------------------------
        # If the entire candidate already equals a known title,
        # do NOT try to interpret a shorter matched title at the
        # end as an employer-prefix layout.
        #
        # Example:
        #
        # Test Automation Developer
        #
        # matched titles may include:
        #
        # Test Automation Developer
        # Developer
        #
        # The full title must win. We must not reduce it to:
        #
        # Developer
        # -----------------------------------------------------

        exact_known_title_match = any(
            best_title.strip().lower()
            ==
            known_title.strip().lower()
            for known_title in matched_known_titles
        )

        if not exact_known_title_match:

            # Longest titles first so a complete title wins over
            # shorter partial matches.
            sorted_known_titles = sorted(
                matched_known_titles,
                key=len,
                reverse=True
            )

            for known_title in sorted_known_titles:

                suffix_match = re.search(
                    rf'(?i)(?<!\w)'
                    rf'({re.escape(known_title.strip())})'
                    rf'\s*$',
                    best_title
                )

                if not suffix_match:
                    continue

                prefix_text = best_title[
                    :suffix_match.start()
                ].strip()

                if not prefix_text:
                    continue

                # -------------------------------------------------
                # Only remove a prefix when there is positive
                # evidence that the prefix represents an employer,
                # organization, institution, or named team.
                #
                # Do NOT maintain a list of possible title
                # modifiers. New titles can contain arbitrary
                # descriptive words:
                #
                # Strategic Business Executive
                # Enterprise Security Architect
                # Digital Transformation Manager
                # Customer Experience Director
                #
                # Those should remain intact unless the prefix
                # actually looks organizational.
                # -------------------------------------------------

                prefix_lower = prefix_text.lower()

                prefix_words = re.findall(
                    r"[A-Za-z]+",
                    prefix_text
                )

                # ---------------------------------------------
                # Strong employer / institution evidence
                # ---------------------------------------------

                prefix_has_employer_indicator = any(
                    re.search(
                        rf'(?i)\b{re.escape(word)}\b',
                        prefix_text
                    )
                    for word in employer_indicators
                )

                # ---------------------------------------------
                # Organization/team vocabulary
                # ---------------------------------------------

                organization_signal_words = {
                    "team",
                    "club",
                    "society",
                    "association",
                    "foundation",
                    "laboratory",
                    "lab",
                    "rocket",
                    "rocketry",
                    "motorsport",
                    "racing"
                }

                prefix_has_org_signal = any(
                    re.search(
                        rf'(?i)\b{re.escape(word)}\b',
                        prefix_text
                    )
                    for word in organization_signal_words
                )

                # ---------------------------------------------
                # Preserve the complete candidate unless there
                # is actual organizational evidence.
                # ---------------------------------------------

                if not (
                    prefix_has_employer_indicator
                    or prefix_has_org_signal
                ):
                    continue

                cleaned_known_title = (
                    suffix_match.group(1).strip()
                )

                print(
                    "Detected organization-prefix + known-title layout: "
                    f"'{best_title}' -> "
                    f"'{cleaned_known_title}'"
                )

                best_title = cleaned_known_title
                break


    # ---------------------------------------------------------
    # Handle title : employer / organization / engagement
    #
    # Examples:
    #
    # Assistant Project Manager: StarterHacks
    # -> Assistant Project Manager
    #
    # Data Analyst: ABC Corporation
    # -> Data Analyst
    #
    # Software Developer: Internal Platform Team
    # -> Software Developer
    #
    # Only keep the left side when it is short and contains
    # a recognized job-title term.
    # ---------------------------------------------------------

    if ":" in best_title:

        left_part, right_part = best_title.split(
            ":",
            1
        )

        left_part = left_part.strip()
        right_part = right_part.strip()

        left_words = re.findall(
            r"[A-Za-z]+(?:[-/][A-Za-z]+)*",
            left_part
        )

        left_has_title_term = any(
            re.search(
                rf'(?i)\b{re.escape(word)}\b',
                left_part
            )
            for word in generic_terms
        )

        if (
            right_part
            and left_has_title_term
            and 1 <= len(left_words) <= 8
        ):
            best_title = left_part
            
    # ---------------------------------------------------------
    # 11. Remove employer information after separators
    #
    # Examples:
    #
    # DATA ANALYST | WALMART, CANADA
    # ->
    # DATA ANALYST
    #
    # FIRMWARE DESIGN TEAM MEMBER- ELECTRIUM MOBILITY
    # ->
    # FIRMWARE DESIGN TEAM MEMBER
    # ---------------------------------------------------------

    # ---------------------------------------------------------
    # Handle pipe-delimited title layouts.
    #
    # Common structures:
    #
    #   TITLE | TECHNOLOGY STACK
    #   TITLE | EMPLOYER
    #   EMPLOYER | TITLE
    #
    # Do not blindly keep the left side. Determine which side
    # contains an occupational title signal.
    #
    # Also support PDF-collapsed titles such as:
    #
    #   SOFTWAREDEVELOPER
    #   DATAANALYST
    #   PROJECTMANAGER
    #   Add on 8/29/2026
    # ---------------------------------------------------------

    if "|" in best_title:

        pipe_parts = [
            part.strip()
            for part in best_title.split("|")
            if part.strip()
        ]

        if len(pipe_parts) >= 2:

            left_part = pipe_parts[0]
            right_part = pipe_parts[1]

            def pipe_part_has_title_signal(part):

                part_lower = part.lower()

                # Normal readable title:
                # "Software Developer"
                normal_match = any(
                    re.search(
                        rf'\b{re.escape(term)}\b',
                        part_lower
                    )
                    for term in split_layout_title_terms
                )

                if normal_match:
                    return True

                # Collapsed PDF title:
                # "SOFTWAREDEVELOPER"
                # "DATAANALYST"
                compact_part = re.sub(
                    r'[^a-z0-9]+',
                    '',
                    part_lower
                )

                return any(
                    re.sub(
                        r'[^a-z0-9]+',
                        '',
                        term.lower()
                    ) in compact_part
                    for term in split_layout_title_terms
                )

            left_has_title = pipe_part_has_title_signal(
                left_part
            )

            right_has_title = pipe_part_has_title_signal(
                right_part
            )
            
            if right_has_title and not left_has_title:

                print(
                    "Detected employer | title layout: "
                    f"'{best_title}' -> '{right_part}'"
                )

                best_title = right_part

            elif left_has_title and not right_has_title:

                print(
                    "Detected title | details layout: "
                    f"'{best_title}' -> '{left_part}'"
                )

                best_title = left_part

            else:

                # Preserve existing behavior when the structure
                # remains ambiguous.
                best_title = left_part


            # -----------------------------------------------------
            # Restore canonical spacing for a collapsed known title.
            #
            # PDF extraction may remove spaces:
            #
            #     SOFTWAREDEVELOPER -> Software Developer
            #     DATAANALYST       -> Data Analyst
            #     PROJECTMANAGER    -> Project Manager
            #
            # Added/Changed on 8/29/2026            
            # Match the compact selected text against the existing
            # job-title vocabulary already loaded for this function.
            # -----------------------------------------------------

            compact_selected_title = re.sub(
                r'[^a-z0-9]+',
                '',
                best_title.lower()
            )

            collapsed_known_title_matches = [
                known_title.strip()
                for known_title in job_titles_keywords
                if known_title.strip()
                and re.sub(
                    r'[^a-z0-9]+',
                    '',
                    known_title.lower()
                ) == compact_selected_title
            ]

            if collapsed_known_title_matches:

                restored_title = max(
                    collapsed_known_title_matches,
                    key=len
                )

                print(
                    "Restored collapsed known title: "
                    f"'{best_title}' -> '{restored_title}'"
                )

                best_title = restored_title

    # Handle title - employer
    if " - " in best_title:
        parts = [
            part.strip()
            for part in best_title.split(" - ")
            if part.strip()
        ]

        if len(parts) >= 2:
            first_part = parts[0]

            # Keep the first part if it looks title-like
            if any(
                re.search(
                    rf'(?i)\b{re.escape(word)}\b',
                    first_part
                )
                for word in generic_terms
            ):
                best_title = first_part

    # Handle title - employer patterns.
    #
    # Remove employer text when a recognized job-title term appears
    # before the separator.
    #
    # Examples:
    #   Developer - Company
    #   Developer- Company
    #   Team Member- Company
    #   Technician - Company
    #   Engineering Team Member - Company

    title_employer_pattern = re.compile(
        r'(?i)^(.*?\b(?:'
        r'Engineer|Engineering|Developer|Analyst|Manager|Intern|'
        r'Co-Op|Team Member|Team Lead|Member|Lead|Assistant|Coordinator|'
        r'Specialist|Consultant|Designer|Architect|Administrator|Technician'
        r'))\s*-\s*.*$'
    )

    best_title = title_employer_pattern.sub(
        r'\1',
        best_title
    ).strip()

    # Remove trailing separators
    best_title = re.sub(
        r'\s*[|,:;/-]+\s*$',
        '',
        best_title
    ).strip()

    # ---------------------------------------------------------
    # 11A. Final structural title cleanup
    #
    # Remove resume-layout text that can become attached to an
    # otherwise valid occupational title during PDF/DOCX
    # extraction.
    #
    # This is intentionally structural, not resume-specific.
    # ---------------------------------------------------------

    # ---------------------------------------------------------
    # A. Remove leading section/header labels.
    #
    # Examples:
    #   Experience Web Development And Design
    #       -> Web Development And Design
    #
    #   Work Experience Software Engineer
    #       -> Software Engineer
    # ---------------------------------------------------------

    best_title = re.sub(
        r'(?i)^\s*(?:'
        r'work\s+experience|'
        r'professional\s+experience|'
        r'employment\s+experience|'
        r'employment\s+history|'
        r'career\s+history|'
        r'experience'
        r')\s*[:|/-]?\s+',
        '',
        best_title
    ).strip()

    # ---------------------------------------------------------
    # B. Remove trailing work-arrangement qualifiers.
    #
    # Examples:
    #   Web Developer — Remote (Freelancing)
    #       -> Web Developer
    #
    #   Software Engineer - Remote
    #       -> Software Engineer
    #
    # Important:
    # Only remove these when they occur after a separator.
    # This avoids changing legitimate occupational wording.
    # ---------------------------------------------------------

    best_title = re.sub(
        r'(?i)\s*(?:[-–—|])\s*'
        r'(?:'
        r'remote|'
        r'hybrid|'
        r'on[-\s]?site|'
        r'onsite'
        r')'
        r'(?:\s*\([^)]*\))?'
        r'\s*$',
        '',
        best_title
    ).strip()

    # ---------------------------------------------------------
    # C. Remove trailing parenthetical employment-mode labels.
    #
    # Examples:
    #   Web Developer (Freelancing)
    #       -> Web Developer
    #
    #   Software Engineer (Contract)
    #       -> Software Engineer
    #
    # Do not remove arbitrary parentheses.
    # ---------------------------------------------------------

    best_title = re.sub(
        r'(?i)\s*\(\s*(?:'
        r'freelance|freelancing|'
        r'contract|contractor|'
        r'part[-\s]?time|'
        r'full[-\s]?time|'
        r'remote|hybrid'
        r')\s*\)\s*$',
        '',
        best_title
    ).strip()

    # ---------------------------------------------------------
    # D. Remove trailing city/province/state location.
    #
    # This handles a title followed directly by a location when
    # PDF extraction has collapsed columns together.
    #
    # Examples:
    #   Beauty Advisor / Sales In Cosmetics Cambridge, Ontario
    #       -> Beauty Advisor / Sales In Cosmetics
    #
    #   Data Analyst Toronto, ON
    #       -> Data Analyst
    #
    # Require a comma + province/state token so ordinary title
    # words are not removed accidentally.
    # ---------------------------------------------------------

    trailing_geo_pattern = re.compile(
        r'(?i)\s+'
        r'[A-Z][A-Za-z.\'-]*(?:\s+[A-Z][A-Za-z.\'-]*){0,3}'
        r'\s*,\s*'
        r'(?:'
        r'Ontario|ON|'
        r'Quebec|QC|'
        r'Alberta|AB|'
        r'British\s+Columbia|BC|'
        r'Manitoba|MB|'
        r'Saskatchewan|SK|'
        r'Nova\s+Scotia|NS|'
        r'New\s+Brunswick|NB|'
        r'Newfoundland(?:\s+and\s+Labrador)?|NL|'
        r'Prince\s+Edward\s+Island|PE|'
        r'[A-Z]{2}'
        r')'
        r'\s*$'
    )

    geo_match = trailing_geo_pattern.search(best_title)

    if geo_match:
        possible_title = best_title[:geo_match.start()].strip()

        # Only perform the split when meaningful title text
        # remains on the left.
        if len(possible_title.split()) >= 2:
            best_title = possible_title

    # Final separator cleanup after structural normalization.
    best_title = re.sub(
        r'\s*[|,:;/-]+\s*$',
        '',
        best_title
    ).strip()

    # ---------------------------------------------------------
    # Final title sanitation before validation.
    #
    # Keep this gate deterministic and structural.  Do not require a title to
    # contain a word from a finite occupational dictionary: legitimate titles
    # such as IT Support, Senior Staff, Collections Agent, SQL/Oracle DBA, and
    # Freelance Photographer must remain eligible.
    # ---------------------------------------------------------

    # Clean explicit role/title labels before any rejection checks.
    # Examples: "Role: Sr. DevOps Engineer" -> "Sr. DevOps Engineer".
    best_title = re.sub(
        r'(?i)^\s*(?:current\s+role|project\s+role|key\s+role|job\s+title|'
        r'role|position|title)\s*(?::|[-–—|])\s*',
        '',
        best_title
    ).strip()

    # Repair common glued section headings only when meaningful CamelCase-like
    # title text follows immediately.
    best_title = re.sub(
        r'(?i)^(?:professional\s*experience|work\s*experience|employment\s*experience|'
        r'experience|education|technical\s*skills)(?=[A-Z][a-z])',
        '',
        best_title
    ).strip()

    compact_final_title = re.sub(
        r'\s+', ' ', best_title
    ).strip(' -–—|,:;()').lower()

    # V4: If the selected candidate collapsed to a bare Role/Position/Title
    # label, recover an already-scored explicit label/value candidate BEFORE
    # exact-label rejection.  This fixes layouts such as:
    #     Role: Sr. DevOps Engineer
    # without generating or rescoring any new candidate.
    if compact_final_title in {'role', 'position', 'job title', 'title'}:
        for fallback_candidate in scored_candidates:
            fallback_match = re.match(
                r'(?i)^\s*(?:current\s+role|project\s+role|key\s+role|job\s+title|'
                r'role|position|title)\s*(?::|[-–—|])\s*(.+?)\s*$',
                fallback_candidate.get('text', '')
            )
            if not fallback_match:
                continue
            fallback_title = fallback_match.group(1).strip(' -–—|,:;()')
            fallback_words = re.findall(r"[A-Za-z][A-Za-z0-9&+.'/-]*", fallback_title)
            if fallback_title and 1 <= len(fallback_words) <= 10:
                best_candidate = fallback_candidate
                best_title = fallback_title
                compact_final_title = re.sub(r'\s+', ' ', best_title).strip(' -–—|,:;()').lower()
                break

    # V5: conservative recovery from already-scored title evidence.
    #
    # Some layouts score an adjacent employer/location line above the actual
    # occupational title, or reduce an explicit Role:/Position:/Job Title: line
    # to its field label.  Before rejecting such a selected candidate, inspect
    # ONLY candidates that the existing scorer already produced.  This does not
    # create candidates or change scores/thresholds.
    v5_role_terms = {
        'developer', 'consultant', 'engineer', 'architect', 'analyst', 'manager',
        'administrator', 'specialist', 'technician', 'director', 'lead',
        'coordinator', 'officer', 'supervisor', 'agent', 'instructor', 'recruiter',
        'master', 'pm', 'accountant', 'auditor', 'clerk', 'cashier', 'scientist',
        'programmer', 'advisor', 'executive', 'associate', 'assistant', 'intern'
    }

    def _v5_clean_scored_title(candidate_text):
        text = re.sub(r'\s+', ' ', str(candidate_text or '')).strip()
        explicit = re.search(
            r'(?i)(?:^|[|;])\s*(?:current\s+role|project\s+role|key\s+role|job\s*title|role|position|title)'
            r'\s*(?::|[-–—|])\s*([^|;]+)',
            text
        )
        if explicit:
            text = explicit.group(1).strip()
        else:
            text = re.sub(
                r'(?i)^\s*(?:current\s+role|project\s+role|key\s+role|job\s*title|role|position|title)'
                r'\s*(?::|[-–—|])\s*', '', text
            ).strip()
        # Remove a trailing date range only when clearly separated from title text.
        text = re.sub(
            r'(?i)\s+(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|'
            r'Aug(?:ust)?|Sep(?:t(?:ember)?)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)\.?\s*'
            r'(?:[-/\'’ ]?\d{2}|,?\s*\d{4}).*$', '', text
        ).strip(' -–—|,:;()')
        return text

    def _v5_is_clean_occupational_title(title, candidate):
        words = re.findall(r"[A-Za-z][A-Za-z0-9&+.'/-]*", title)
        if not (1 <= len(words) <= 10):
            return False
        low = title.lower()
        if low in {
            'duration', 'employment summary', 'experience summary', 'work history',
            'work experience', 'professional experience', 'employment history',
            'technical skills', 'skills', 'professional', 'employment', 'experience',
            'responsibilities', 'responsibility', 'duties', 'career summary',
            'career history', 'projects', 'project', 'education', 'remote contract',
            'contract', 'servant leadership'
        }:
            return False
        if re.match(r'(?i)^\s*(?:duration|client|employer|company|responsibilities?|duties)\b', title):
            return False
        if re.search(
            r'(?i)\b(?:canada|usa|united\s+states|toronto|montreal|montréal|vancouver|'
            r'calgary|ottawa|ontario|quebec|alberta|british\s+columbia|scarborough)\b',
            title
        ) and not any(re.search(rf'(?i)\b{re.escape(term)}\b', low) for term in v5_role_terms):
            return False
        return bool(candidate.get('matched_titles')) or any(
            re.search(rf'(?i)\b{re.escape(term)}\b', low) for term in v5_role_terms
        )

    selected_needs_recovery = (
        compact_final_title in {
            'role', 'position', 'job title', 'title', 'duration', 'work history',
            'career history', 'experience', 'professional experience', 'work experience'
        }
        or (
            bool(re.search(
                r'(?i)\b(?:canada|toronto|montreal|montréal|vancouver|calgary|ottawa|'
                r'ontario|quebec|alberta|british\s+columbia|scarborough)\b',
                best_title
            ))
            and not _v5_is_clean_occupational_title(best_title, best_candidate)
        )
    )

    if selected_needs_recovery:
        recovery_options = []
        for candidate in scored_candidates:
            recovered = _v5_clean_scored_title(candidate.get('text', ''))
            if not _v5_is_clean_occupational_title(recovered, candidate):
                continue
            explicit_bonus = 40 if re.search(
                r'(?i)\b(?:job\s*title|role|position|title)\s*(?::|[-–—|])',
                candidate.get('text', '')
            ) else 0
            recovery_options.append((candidate.get('score', 0) + explicit_bonus, candidate, recovered))
        if recovery_options:
            recovery_options.sort(key=lambda item: item[0], reverse=True)
            _, recovered_candidate, recovered_title = recovery_options[0]
            best_candidate = recovered_candidate
            best_title = recovered_title
            compact_final_title = re.sub(r'\s+', ' ', best_title).strip(' -–—|,:;()').lower()

    # Exact section/field labels are never job titles.
    non_title_exact = {
        'duration', 'employment summary', 'experience summary', 'work history',
        'work experience', 'professional experience', 'employment history',
        'technical skills', 'skills', 'professional', 'employment', 'experience',
        'responsibilities', 'responsibility', 'duties', 'career summary',
        'career history', 'projects', 'project', 'education', 'remote contract',
        'contract', 'servant leadership'
    }
    if compact_final_title in non_title_exact:
        return _format_job_title_result(
            'N/A', confidence='LOW', score=best_candidate.get('score', 0),
            source=best_candidate.get('source', 'none'),
            reason='selected_candidate_is_section_or_field_label'
        )

    # A Responsibilities:/Duties: line describes work performed, not the role.
    # Reject the whole candidate rather than stripping the label and promoting
    # the duty text into a job title.
    if re.match(
        r'(?i)^\s*(?:responsibilities?|duties)\s*(?::|[-–—|])',
        best_title
    ):
        return _format_job_title_result(
            'N/A', confidence='LOW', score=best_candidate.get('score', 0),
            source=best_candidate.get('source', 'none'),
            reason='selected_candidate_is_responsibility_or_duties_text'
        )

    # If the selected text collapsed to a bare field label (for example
    # "Role"), recover only from an already-scored candidate that explicitly
    # carries Role:/Position:/Job Title: plus a non-empty value.  This does not
    # generate or rescore candidates; it only sanitizes existing title evidence.
    if compact_final_title in {'role', 'position', 'job title', 'title'}:
        for fallback_candidate in scored_candidates:
            fallback_match = re.match(
                r'(?i)^\s*(?:current\s+role|project\s+role|key\s+role|job\s+title|'
                r'role|position|title)\s*(?::|[-–—|])\s*(.+?)\s*$',
                fallback_candidate.get('text', '')
            )
            if not fallback_match:
                continue
            fallback_title = fallback_match.group(1).strip(' -–—|,:;()')
            fallback_words = re.findall(r"[A-Za-z][A-Za-z0-9&+.'/-]*", fallback_title)
            if fallback_title and 1 <= len(fallback_words) <= 10:
                best_candidate = fallback_candidate
                best_title = fallback_title
                compact_final_title = re.sub(r'\s+', ' ', best_title).strip(' -–—|,:;()').lower()
                break

    # V4: Duration-prefixed text is a field/value fragment, never a job title.
    # This catches collapsed layouts such as "Duration Offshore: ... Onsite: ..."
    # even when only one explicit field label survived extraction.
    if re.match(r'(?i)^\s*duration\b', best_title):
        return _format_job_title_result(
            'N/A', confidence='LOW', score=best_candidate.get('score', 0),
            source=best_candidate.get('source', 'none'),
            reason='selected_candidate_contains_concatenated_field_text'
        )

    # V4: When a slash-separated candidate contains a clean occupational title
    # on the left and an employer/location-shaped fragment on the right, keep
    # only the occupational prefix.  Do not split legitimate compound titles
    # such as "Business Analyst / Business System Analyst" unless the right
    # side carries employer/geography evidence.
    slash_match = re.match(r'^\s*(.+?)\s*/\s*(.+?)\s*$', best_title)
    if slash_match:
        left_part = slash_match.group(1).strip()
        right_part = slash_match.group(2).strip()
        left_lower = left_part.lower()
        right_lower = right_part.lower()
        left_has_role = bool(best_candidate.get('matched_titles')) or any(
            re.search(rf'(?i)\b{re.escape(term)}\b', left_lower)
            for term in (set(split_layout_title_terms) | {
                'developer','consultant','engineer','architect','analyst','manager',
                'administrator','specialist','technician','director','lead',
                'coordinator','officer','supervisor','agent','instructor','recruiter',
                'master','pm','accountant','auditor','clerk','cashier','scientist','programmer'
            })
        )
        right_has_employer_or_geo = (
            any(re.search(rf'(?i)\b{re.escape(term)}\b', right_lower)
                for term in split_layout_employer_terms)
            or bool(re.search(
                r'(?i)\b(?:canada|usa|united\s+states|toronto|montreal|montréal|'
                r'vancouver|calgary|ottawa|ontario|quebec|alberta|british\s+columbia)\b',
                right_part
            ))
            or bool(re.search(r'(?i)[-–—]\s*[A-Za-z .\'-]+,\s*(?:ON|QC|BC|AB|[A-Z]{2})\b', right_part))
        )
        if left_has_role and right_has_employer_or_geo:
            best_title = left_part
            compact_final_title = re.sub(r'\s+', ' ', best_title).strip(' -–—|,:;()').lower()

    # Reject concatenated field-record text rather than promoting an embedded
    # fragment as the job title.  Example: Client: ... Job Title: ... Employer:
    # ... Duration.  A clean leading Job Title:/Role:/Position: was already
    # stripped above and therefore is not affected by this check.
    embedded_field_labels = re.findall(
        r'(?i)\b(?:client|employer|company|duration|responsibilities?|duties|'
        r'job\s*title|position|role)\s*:',
        best_title
    )
    if len(embedded_field_labels) >= 2 or re.match(
        r'(?i)^\s*(?:client|employer|company|duration)\s*:', best_title
    ):
        return _format_job_title_result(
            'N/A', confidence='LOW', score=best_candidate.get('score', 0),
            source=best_candidate.get('source', 'none'),
            reason='selected_candidate_contains_concatenated_field_text'
        )

    # Reject employer/location-shaped values that survived earlier normalization.
    # Keep this structural: comma/hyphen geography is rejected only when the left
    # side does not itself look like a normal occupational title.
    generic_single_word_titles = {
        'developer', 'consultant', 'engineer', 'architect', 'analyst', 'manager',
        'administrator', 'specialist', 'technician', 'director', 'lead',
        'coordinator', 'officer', 'supervisor', 'agent', 'instructor', 'recruiter',
        'master', 'pm', 'accountant', 'auditor', 'clerk', 'cashier', 'scientist', 'programmer'
    }
    location_tail_match = re.match(
        r'(?i)^\s*(.+?)\s*(?:,|\s[-–—]\s)\s*'
        r'([A-Za-zÀ-ÿ .\'-]{2,40})(?:,\s*(?:ON|QC|BC|AB|MB|SK|NS|NB|NL|PE|[A-Z]{2}))?\s*$',
        best_title
    )
    if location_tail_match:
        left_side = location_tail_match.group(1).strip()
        left_words = re.findall(r"[A-Za-z][A-Za-z0-9&+./'-]*", left_side)
        left_lower = left_side.lower()
        left_has_title_signal = bool(best_candidate.get('matched_titles')) or any(
            re.search(rf'(?i)\b{re.escape(term)}\b', left_lower)
            for term in (set(split_layout_title_terms) | generic_single_word_titles)
        )
        location_tail = location_tail_match.group(2).strip()
        location_has_geo_evidence = bool(re.search(
            r'(?i)\b(?:canada|usa|united\s+states|toronto|montreal|montréal|'
            r'vancouver|calgary|ottawa|ontario|quebec|alberta|british\s+columbia)\b',
            location_tail
        )) or bool(re.search(
            r'(?i)(?:,\s*(?:ON|QC|BC|AB|MB|SK|NS|NB|NL|PE|[A-Z]{2})\b)',
            best_title
        ))
        # A plain two-word occupational title such as "Cashier Supervisor" or
        # "Collections Agent" must not be rejected merely because the last
        # word happens to satisfy the old free-text location pattern.
        if not left_has_title_signal and location_has_geo_evidence:
            return _format_job_title_result(
                'N/A', confidence='LOW', score=best_candidate.get('score', 0),
                source=best_candidate.get('source', 'none'),
                reason='selected_candidate_is_employer_location'
            )

    # Single-word, unmatched candidates from weak layout evidence are commonly
    # employer names.  Preserve a compact set of generic occupational nouns
    # (Developer, Consultant, etc.) even when the external title dictionary did
    # not match them; this is an exception to the fragment guard, not a global
    # title whitelist.
    final_words = re.findall(r"[A-Za-z][A-Za-z0-9&+./'-]*", best_title)
    single_word_lower = final_words[0].lower() if len(final_words) == 1 else ''
    if (
        len(final_words) == 1
        and single_word_lower not in generic_single_word_titles
        and not best_candidate.get('matched_titles')
        and best_candidate.get('source') in {'same-line-before-date', 'previous-line-1', 'previous-line-2'}
    ):
        return _format_job_title_result(
            'N/A', confidence='LOW', score=best_candidate.get('score', 0),
            source=best_candidate.get('source', 'none'),
            reason='selected_candidate_is_unmatched_single_word_fragment'
        )

    # ---------------------------------------------------------
    # 12. Final validation
    # ---------------------------------------------------------
    # Validate title length using lexical words only.
    #
    # Do not use str.split() here because PDF/DOCX extraction
    # can introduce standalone separators such as:
    #
    #   —   –   /   |
    #
    # These are not title words and should not make an otherwise
    # valid occupational title appear too long.
    # ---------------------------------------------------------

    title_lexical_words = re.findall(
        r"[A-Za-z][A-Za-z0-9&+.'/-]*",
        best_title
    )

    if len(title_lexical_words) > 10:
        print(
            "Selected candidate has more than 10 lexical "
            "title words. Returning N/A."
        )

        return _format_job_title_result(
            "N/A",
            confidence="LOW",
            score=best_candidate.get("score", 0),
            source=best_candidate.get("source", "none"),
            reason="selected_title_too_long"
        )
        
    # ---------------------------------------------------------
    # Reject structurally employer-like values selected as titles.
    #
    # Examples of structure:
    #
    # Dlawlor LLC
    # Radiation Solutions Inc.
    # ABC Technologies Ltd.
    # Example Corporation
    #
    # Important:
    # Do NOT reject legitimate titles containing organization-like
    # words when they also have an occupational role term:
    #
    # Solutions Architect
    # Technology Manager
    # Bank Operations Analyst
    # ---------------------------------------------------------

    final_title_lower = best_title.lower()

    final_title_has_role_term = any(
        re.search(
            rf'\b{re.escape(term)}\b',
            final_title_lower
        )
        for term in split_layout_title_terms
    )

    # Strong legal/company-name suffixes.
    employer_legal_suffix_pattern = re.compile(
        r'(?i)\b(?:'
        r'inc(?:orporated)?|'
        r'llc|'
        r'ltd|'
        r'limited|'
        r'corp(?:oration)?|'
        r'company|'
        r'co\.?'
        r')\.?\s*$'
    )

    # Common organization/entity words. These alone are not
    # enough to reject a title if a real occupational term exists.
    employer_entity_pattern = re.compile(
        r'(?i)\b(?:'
        r'technologies|technology|solutions|'
        r'consulting|services|systems|'
        r'bank|university|college|school|'
        r'hospital|clinic|institute|centre|center|'
        r'group|holdings|partners|enterprises'
        r')\b'
    )

    best_title_words = re.findall(
        r"[A-Za-z][A-Za-z0-9&+./'-]*",
        best_title
    )

    structurally_employer_like = (
        not final_title_has_role_term
        and 1 <= len(best_title_words) <= 12
        and (
            employer_legal_suffix_pattern.search(best_title)
            or employer_entity_pattern.search(best_title)
        )
    )

    if structurally_employer_like:

        print(
            "Selected candidate structurally appears "
            "to be an employer, not a job title: "
            f"{best_title}"
        )

        return _format_job_title_result(
            "N/A",
            confidence="LOW",
            score=best_candidate.get("score", 0),
            source=best_candidate.get("source", "none"),
            reason="selected_candidate_is_employer"
        )
        
    # ---------------------------------------------------------
    # 13. Confidence scoring for scalable processing
    # ---------------------------------------------------------

    best_score = best_candidate.get("score", 0)
    best_source = best_candidate.get("source", "unknown")

    second_score = (
        scored_candidates[1].get("score", 0)
        if len(scored_candidates) > 1
        else 0
    )

    score_margin = best_score - second_score

    final_lower = best_title.lower()

    confidence_title_terms = set(generic_terms) | {
        "founder", "owner", "president", "teacher", "coach",
        "executive", "sysadmin", "tutor", "instructor",
        "technologist", "supervisor", "researcher"
    }

    has_title_signal = bool(
        best_candidate.get("matched_titles")
    ) or any(
        re.search(
            rf'(?i)\b{re.escape(term)}\b',
            final_lower
        )
        for term in confidence_title_terms
    )

    strong_structural_sources = {
        "following-role-line",
        "standalone-date-following-role",
        "same-line-after-date",
        "same-line-before-date",
        "previous-line-1"
    }
    
    if (
        best_source in strong_structural_sources
        and best_score >= 110
        and score_margin >= 40
        and 1 <= len(best_title.split()) <= 8
    ):
        confidence = "HIGH"
        confidence_reason = (
            "strong_structural_layout_clean_title_and_clear_score_margin"
        )
        
    elif (
        best_score >= 160
        and has_title_signal
        and score_margin >= 30
    ):
        confidence = "HIGH"
        confidence_reason = "strong_title_signal_and_clear_score_margin"

    elif (
        best_score >= 120
        and has_title_signal
    ):
        confidence = "MEDIUM"
        confidence_reason = "plausible_title_but_weaker_structure_or_margin"

    else:
        confidence = "LOW"
        confidence_reason = "weak_or_ambiguous_title_evidence"

    final_title = best_title.title()

    print(f"\nFINAL MOST RECENT JOB TITLE: {best_title}")
    print(
        f"JOB TITLE CONFIDENCE: {confidence} | "
        f"Score={best_score} | Margin={score_margin} | "
        f"Source={best_source}"
    )
    print("==========================================\n")

    return _format_job_title_result(
        final_title,
        confidence=confidence,
        score=best_score,
        source=best_source,
        reason=confidence_reason,
        margin=score_margin
    )
    
def extract_education(resume_text):
    """
    Extract the highest and most recent educational degree from the resume text.
    """
    try:
        # Extract the education section using the extract_education_section function
        education_section = extract_education_section(resume_text)

        print(f"Relevant Education Section: {education_section}")

        # Define a list of education levels in descending order of priority
        education_levels = [            
            # Doctorate-level degrees
            "PhD", "Doctorate", "Doctor of Philosophy",

            # Master's-level degrees
            "Master", "Master's", "MSc", "M.Sc", "M.Sc.", "MS", "M.S", "M.S.", "MSEE", "MA", "MBA",

            # Bachelor's-level degrees
            "Bachelor", "Bachelor's", "BSc", "B.Sc", "B.Sc.", "BS", "B.S", "B.S.", "BA",

            # Associate-level degrees
            "Associate", "Associate's", "AA", "AS", "AAS",
        ]

        # Search for the highest degree in the education section
        for level in education_levels:
            if re.search(rf'\b{re.escape(level)}\b', education_section, re.IGNORECASE):
                return level

        # If no degree is found, return "N/A"
        return "N/A"

    except Exception as e:
        print(f"Error extracting education: {e}")
        return "N/A"

def extract_docx_text_in_document_order(doc):
    """
    Extract DOCX text while preserving the document's actual
    paragraph/table order.

    python-docx exposes doc.paragraphs and doc.tables separately,
    which loses layout order when a resume mixes paragraphs and
    tables. This walks the underlying document body sequentially.
    """

    from docx.text.paragraph import Paragraph
    from docx.table import Table
    from docx.oxml.text.paragraph import CT_P
    from docx.oxml.table import CT_Tbl

    text_parts = []

    # ---------------------------------------------------------
    # Extract visible Word header content first.
    #
    # Some resumes store the candidate name and contact
    # information in a header table rather than in the main
    # document body. Header content is stored in a separate
    # DOCX XML part and is therefore not included when walking
    # doc.element.body.
    # The below for section added on 09/10/2026
    # ---------------------------------------------------------
    for section in doc.sections:

        header = section.header

        # Header paragraphs
        for paragraph in header.paragraphs:

            header_text = paragraph.text.strip()

            if header_text:
                text_parts.append(header_text)

        # Header tables
        for table in header.tables:

            for row in table.rows:

                for cell in row.cells:

                    cell_text = cell.text.strip()

                    if cell_text:
                        text_parts.append(cell_text)

        # ---------------------------------------------------------
        # Extract additional visible text from raw DOCX header XML.
        #
        # Some Word resumes store visible header content inside
        # text boxes / shapes. python-docx does not expose that text
        # through header.paragraphs or header.tables.
        #
        # Read all w:t nodes from header XML parts as a generic
        # fallback.
        # Change #12
        # ---------------------------------------------------------
        try:
            from lxml import etree

            namespace = {
                "w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
            }

            for section in doc.sections:
                header_part = section.header.part

                root = etree.fromstring(
                    header_part.blob
                )

                header_xml_texts = root.xpath(
                    ".//w:t/text()",
                    namespaces=namespace
                )

                for header_xml_text in header_xml_texts:
                    header_xml_text = (
                        header_xml_text.strip()
                    )

                    if (
                        header_xml_text
                        and header_xml_text not in text_parts
                    ):
                        text_parts.append(
                            header_xml_text
                        )

        except Exception as e:
            print(
                f"Raw DOCX header XML extraction skipped: {e}"
            )

    for child in doc.element.body.iterchildren():

        if isinstance(child, CT_P):

            paragraph = Paragraph(child, doc)
            paragraph_text = paragraph.text.strip()

            # python-docx paragraph.text can omit text stored inside
            # Word Structured Document Tags (w:sdt / content controls).
            # If the normal paragraph text is empty, recover all w:t
            # text directly from that paragraph's XML.
            if not paragraph_text:
                xml_text_parts = child.xpath(".//w:t/text()")

                paragraph_text = " ".join(
                    part.strip()
                    for part in xml_text_parts
                    if part and part.strip()
                ).strip()

            if paragraph_text:
                text_parts.append(paragraph_text)

        elif isinstance(child, CT_Tbl):

            table = Table(child, doc)

            for row in table.rows:

                for cell in row.cells:

                    cell_text = cell.text.strip()

                    if cell_text:
                        text_parts.append(cell_text)

    return "\n".join(text_parts)

def extract_current_company_docx(resume_text):
    """
    Extract current company from DOCX resumes using the strong structural
    pattern: company/employer line immediately preceding a Position: line.
    """
    try:
        lines = [x.strip() for x in resume_text.splitlines()]

        for i, line in enumerate(lines):
            if not re.match(r'(?i)^Position\s*:\s*', line):
                continue

            # First Position: occurrence represents the current role.
            for j in range(i - 1, max(-1, i - 4), -1):
                company = lines[j].strip()

                if not company:
                    continue

                # Remove explicit company/employer labels.
                company = re.sub(
                    r'(?i)^(?:Company(?:\s+Name)?|Employer)\s*:\s*-?\s*',
                    '',
                    company
                ).strip()

                # Remove parenthesized employment date/location suffix.
                # Example: Salesforce1 Consulting: (April 2019 - Present) Grand Island, NY
                company = re.sub(
                    r'\s*:\s*\((?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|'
                    r'May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|'
                    r'Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)\.?\s+\d{4}'
                    r'\s*[-–—]\s*(?:Present|Current|Today|[^)]*)\).*$', '',
                    company,
                    flags=re.IGNORECASE
                ).strip()

                # Remove trailing date range beginning with a month.
                company = re.sub(
                    r'\s+(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|'
                    r'May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|'
                    r'Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)\.?\s+\d{4}'
                    r'\s*[-–—]\s*(?:Present|Current|Today|'
                    r'(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|'
                    r'May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|'
                    r'Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)\.?\s+\d{4})'
                    r'\s*$',
                    '',
                    company,
                    flags=re.IGNORECASE
                ).strip()

                # Ahmad-style: COMPANY – City, ST   July 2024 - Today
                company = re.sub(
                    r'\s+[–—-]\s+[^,\n]+,\s*[A-Z]{2}\s*$',
                    '',
                    company
                ).strip()

                return company or "N/A"

        return "N/A"

    except Exception as e:
        print(f"Error extracting current company from DOCX: {e}")
        return "N/A"


def extract_resume_text(resume_path):
    metadata = {
        'filename': os.path.basename(resume_path),
        # 'filename': file_name,
        'resume_text': "",  # Placeholder for the resume text
        'embedding': None,  # Placeholder for the embedding
        'years_of_experience': 'N/A', # Placeholder for the experience
        'phone_number': 'N/A',  # Placeholder for phone number
        'email': 'N/A',  # Placeholder for email
        'candidate_name': 'Unknown',  # Placeholder for candidate name
        'core_technologies': 'N/A',  # Placeholder for core technologies
        'most_recent_job_title': 'N/A',  # Placeholder for most recent job title
        'current_company': 'N/A',
        'previous_job_titles': 'N/A',
        'employment_status': 'REVIEW_REQUIRED',
        'job_title_confidence': 'LOW',
        'job_title_score': 0,
        'job_title_source': 'none',
        'job_title_requires_review': True,
        'education': 'N/A'
    }

    try:
        text = ""
        if resume_path.endswith(".pdf"):
            with open(resume_path, "rb") as file:
                reader = PyPDF2.PdfReader(file)
                for page in reader.pages:
                    text += page.extract_text() or ""

        elif resume_path.endswith(".docx"):
            doc = docx.Document(resume_path)
            text = extract_docx_text_in_document_order(doc)
    
        metadata['resume_text'] = text  # Store the resume text
        metadata['embedding'] = model.encode(text)

        phone_number = extract_phone_number(text)
        metadata['phone_number'] = phone_number

        email = extract_email_address(text)
        metadata['email'] = email

        # Extract core technologies and certifications
        # core_technologies = extract_core_technologies_and_certifications(text)
        core_technologies = extract_skills(text)
        metadata['core_technologies'] = core_technologies
        
        candidate_name = extract_candidate_name(text, resume_path)
        # candidate_name = extract_candidate_name(text, file_name)
        metadata['candidate_name'] = candidate_name

        education = extract_education(text)
        metadata['education'] = education
        
        experience_years = calculate_experience(text)
        metadata['years_of_experience'] = experience_years
        
        if resume_path.lower().endswith(".pdf"):
            employment = employment_validator.build_deterministic_records(resume_path)

            metadata['most_recent_job_title'] = employment.get('current_job_title') or 'N/A'
            metadata['current_company'] = employment.get('current_company') or 'N/A'
            metadata['previous_job_titles'] = "~~".join(
                employment.get('previous_job_titles', [])
            ) or 'N/A'
            metadata['employment_status'] = employment.get('status', 'REVIEW_REQUIRED')
            metadata['job_title_source'] = 'layout_candidate_engine_v1_3'
            metadata['job_title_requires_review'] = (
                metadata['employment_status'] != 'PASS'
            )
            metadata['job_title_confidence'] = (
                'HIGH' if metadata['employment_status'] == 'PASS' else 'REVIEW'
            )
            metadata['job_title_score'] = (
                100 if metadata['employment_status'] == 'PASS' else 0
            )

        else:
            metadata['current_company'] = extract_current_company_docx(text)
            job_title_details = extract_most_recent_job_title(text, return_details=True)
            metadata['most_recent_job_title'] = job_title_details['title']
            metadata['job_title_confidence'] = job_title_details['confidence']
            metadata['job_title_score'] = job_title_details['score']
            metadata['job_title_source'] = job_title_details['source']
            metadata['job_title_requires_review'] = job_title_details['requires_review']

    except Exception as e:
        print(f"Error processing {resume_path}: {e}")
        # print(f"Error processing {file_name}: {e}")

    return metadata

def custom_tokenize(text, phrases):
    tokens = word_tokenize(text.lower())
    phrase_tokens = []
    i = 0
    while i < len(tokens):
        matched = False
        for phrase in phrases:
            phrase_split = phrase.lower().split()
            if tokens[i:i+len(phrase_split)] == phrase_split:
                phrase_tokens.append('_'.join(phrase_split))
                i += len(phrase_split)
                matched = True
                break
        if not matched:
            phrase_tokens.append(tokens[i])
            i += 1
    return phrase_tokens

def extract_legacy_doc_text_from_stream(file_stream):
    """
    Extract text from legacy binary Microsoft Word .doc files.

    The Azure blob is received as an in-memory stream.
    Word COM requires a physical file, so the stream is written
    temporarily to disk, opened read-only by Microsoft Word,
    and removed after extraction.

    Change #17
    """
    import tempfile
    import win32com.client

    temp_path = None
    word = None
    doc = None

    try:
        # Make sure we read the stream from the beginning.
        file_stream.seek(0)

        with tempfile.NamedTemporaryFile(
            suffix=".doc",
            delete=False
        ) as temp_file:
            temp_file.write(file_stream.read())
            temp_path = temp_file.name

        word = win32com.client.DispatchEx(
            "Word.Application"
        )
        word.Visible = False
        word.DisplayAlerts = 0

        doc = word.Documents.Open(
            os.path.abspath(temp_path),
            ReadOnly=True
        )

        text = doc.Content.Text or ""

        print(
            "Legacy DOC text extracted: "
            f"{len(text)} characters"
        )

        return text

    finally:
        if doc is not None:
            doc.Close(False)

        if word is not None:
            word.Quit()

        if temp_path and os.path.exists(temp_path):
            os.remove(temp_path)

# This is the function that is utilized by the upload_to_chromadb file meaning it's utilized specifically with the Azure Blob Storage System
def extract_resume_text_from_stream(file_stream, file_name, last_modified):
    metadata = {
        'filename': file_name,
        'resume_text': "",
        'tokenized_text': None,
        'embedding': None,
        'years_of_experience': 'N/A',
        'phone_number': 'N/A',
        'email': 'N/A',
        'candidate_name': 'Unknown',
        'core_technologies': 'N/A',
        'most_recent_job_title': 'N/A',
        'job_title_confidence': 'LOW',
        'job_title_score': 0,
        'job_title_source': 'none',
        'job_title_requires_review': True,
        'previous_job_titles': 'N/A',
        'current_company': 'N/A',
        'employment_status': 'REVIEW_REQUIRED',
        'education': 'N/A',
        'last_modified': last_modified.isoformat() 
    }

    try:
        text = ""
        extension = file_name.split('.')[-1].lower()

        if extension == "pdf":
            file_stream.seek(0)
            pdf_bytes = file_stream.read()

            with tempfile.NamedTemporaryFile(
                suffix=".pdf",
                delete=False
            ) as temp_pdf:
                temp_pdf.write(pdf_bytes)
                temp_pdf_path = temp_pdf.name

            try:
                with open(temp_pdf_path, "rb") as pdf_file:
                    reader = PyPDF2.PdfReader(pdf_file)
                    for page in reader.pages:
                        text += page.extract_text() or ""

                employment = employment_validator.build_deterministic_records(
                    temp_pdf_path
                )
            finally:
                if os.path.exists(temp_pdf_path):
                    os.remove(temp_pdf_path)

        elif extension == "docx":
            doc = docx.Document(file_stream)
            text = extract_docx_text_in_document_order(doc)

        elif extension == "doc":
            text = extract_legacy_doc_text_from_stream(
                file_stream
            )      
            
        metadata['resume_text'] = text
        metadata['embedding'] = model.encode(text)
        
        # Temporary implementation to see if this improves the search function speed
        metadata['tokenized_text'] = custom_tokenize(text, phrases = [])
        
        metadata['phone_number'] = extract_phone_number(text)
        metadata['email'] = extract_email_address(text)
        metadata['core_technologies'] = extract_skills(text)
        metadata['candidate_name'] = extract_candidate_name(text, file_name)
        metadata['education'] = extract_education(text)
        metadata['years_of_experience'] = calculate_experience(text)
        if extension == "pdf":
            metadata['most_recent_job_title'] = employment.get('current_job_title') or 'N/A'
            metadata['current_company'] = employment.get('current_company') or 'N/A'
            metadata['previous_job_titles'] = "~~".join(
                employment.get('previous_job_titles', [])
            ) or 'N/A'
            metadata['employment_status'] = employment.get(
                'status', 'REVIEW_REQUIRED'
            )
            metadata['job_title_source'] = 'layout_candidate_engine_v1_3'
            metadata['job_title_requires_review'] = (
                metadata['employment_status'] != 'PASS'
            )
            metadata['job_title_confidence'] = (
                'HIGH' if metadata['employment_status'] == 'PASS' else 'REVIEW'
            )
            metadata['job_title_score'] = (
                100 if metadata['employment_status'] == 'PASS' else 0
            )
        else:
            metadata['current_company'] = extract_current_company_docx(text)
            job_title_details = extract_most_recent_job_title(
                text, return_details=True
            )
            metadata['most_recent_job_title'] = job_title_details['title']
            metadata['job_title_confidence'] = job_title_details['confidence']
            metadata['job_title_score'] = job_title_details['score']
            metadata['job_title_source'] = job_title_details['source']
            metadata['job_title_requires_review'] = job_title_details['requires_review']
            metadata['previous_job_titles'] = extract_previous_job_titles_docx(text)

            # Conservative DOCX employment PASS gate.
            # PASS only when the current title was found from strong
            # employment structure and no title review is required.
            company_ok = (
                metadata['current_company']
                and metadata['current_company'] not in ('N/A', 'Unknown')
            )
            previous_ok = (
                metadata['previous_job_titles']
                and metadata['previous_job_titles'] != 'N/A'
            )
            strong_title = (
                job_title_details['confidence'] == 'HIGH'
                and job_title_details['score'] >= 100
                and job_title_details['margin'] >= 50
                and not job_title_details['requires_review']
                and job_title_details['source'] == 'following-role-line'
            )

            metadata['employment_status'] = (
                'PASS'
                if strong_title and company_ok and previous_ok
                else 'REVIEW_REQUIRED'
            )

    except Exception as e:
        print(f"Error extracting text from {file_name}: {e}")

    return metadata

# This function is utilized for resumes that are contained in local folders and cannot work with the azure blob storage system
def process_resumes(resumes_folder):
    for filename in os.listdir(resumes_folder):
        if filename.endswith(".pdf") or filename.endswith(".docx"):
            resume_path = os.path.join(resumes_folder, filename)
            metadata = extract_resume_text(resume_path)
            print(f"Processed {resume_path}: {metadata['filename']}, JobTitle: {metadata['most_recent_job_title']}")
            # print(f"Processed {resume_path}: {metadata['filename']}")
            save_metadata_to_chromadb(metadata)
    
    if not os.listdir(resumes_folder):
        print("All files have been processed and moved to the Processed folder.")
    else:
        print("Some files were not processed.")

    print("\n--- Collection Summary ---")
    try:
        # Retrieve all documents and metadata from the collection
        all_resumes = collection.get(include=["metadatas"])

        # Check if the collection is empty
        if not all_resumes or not all_resumes['metadatas']:
            print("The collection is empty.")
            return

        for metadata in all_resumes['metadatas']:
            filename = metadata.get('filename', 'N/A')
            most_recent_job_title = metadata.get('most_recent_job_title', 'N/A')
            education = metadata.get('education', 'N/A')

            print(f"Filename: {filename}")
            print(f"Most Recent Job Title: {most_recent_job_title}")
            print(f"Education: {education}")
            print("---------------------------")
    except Exception as e:
        print(f"Error retrieving collection: {e}")

# This is the function that is utilized by the upload_to_chromadb file meaning it's utilized specifically with the Azure Blob Storage System
def process_resumes_regex_from_stream(file_stream, file_name, last_modified):
    """
    Process the resume file stream and save metadata to ChromaDB
    """    
    try:
        metadata = extract_resume_text_from_stream(file_stream, file_name, last_modified)
        print(f"Processed {file_name}: JobTitle: {metadata['most_recent_job_title']} | Name: {metadata['candidate_name']}")
        save_metadata_to_chromadb(metadata)

    except Exception as e:
        print(f"Failed to process {file_name}: {e}")

def build_regex_pattern(keywords):
    """
    Build a regex pattern that matches exact phrases (keywords with spaces).
    """
    patterns = []
    for keyword in keywords:
        # Escape the entire keyword or keyphrase and wrap it with \b for word boundaries
        keyphrase_pattern = r'\b' + re.escape(keyword) + r'\b'
        patterns.append(keyphrase_pattern)
    return '|'.join(patterns)

def extract_experience_section(resume_text, max_lines=40):
    """
    Extract employment/experience sections using structural
    section-heading detection.

    Supports:
        WORK EXPERIENCE
        Professional Experience
        W ORK EXPERIENCE
        W O R K E X P E R I E N C E
        WORKEXPERIENCESoftwareDeveloper

    Avoids treating ordinary prose such as:
        "leadership experience"
        "communication skills"
    as section boundaries.
    """

    if not resume_text:
        return ""

    # ---------------------------------------------------------
    # Canonical headings.
    # Comparison is performed after removing spaces and
    # non-alphabetic characters.
    # ---------------------------------------------------------

    experience_headings = {
        "PROFESSIONALEXPERIENCE",
        "PROFESSIONALWORKEXPERIENCE",
        "WORKEXPERIENCEANDACHIEVEMENTS",
        "RELATEDWORKEXPERIENCE",
        "EXPERIENCEHIGHLIGHTS",
        "WORKEXPERIENCE",
        "WORKINGEXPERIENCE",
        "WORKHISTORY",
        "WORKBACKGROUND",
        "EMPLOYMENTHISTORY",
        "EMPLOYMENTEXPERIENCE",
        "CAREERHISTORY",
        "CAREEREXPERIENCE",
        "RELEVANTEXPERIENCE",
        "EXPERIENCESUMMARY",
        "JOBHISTORY",
        "EXPERIENCE",
        "EXPERIENCES",
        "LEADERSHIPANDVOLUNTEERING",
        "LEADERSHIP",
    }

    excluded_headings = {
        "PROJECTS",
        "PROJECT",
        "VOLUNTEER",
        "VOLUNTEERING",
        "EXTRACURRICULAR",
        "AWARDS",
        "SKILLS",
        "TECHNICALSKILLS",
        "CERTIFICATIONS",
        "CERTIFICATES",
        "LICENSES",
        "ASSESSMENTS",
        "SUMMARY",
        "EDUCATION",
    }

    # Generic EXPERIENCE is allowed only when the line itself
    # structurally looks like a heading.
    generic_experience = {
        "EXPERIENCE",
        "EXPERIENCES",
    }

    # ---------------------------------------------------------
    # Normalize a candidate heading.
    #
    # Examples:
    #
    #   "W ORK EXPERIENCE"     -> "WORKEXPERIENCE"
    #   "W O R K EXPERIENCE"   -> "WORKEXPERIENCE"
    #   "Technical Skills"     -> "TECHNICALSKILLS"
    # ---------------------------------------------------------

    def compact_heading(text):
        """
        Normalize a possible section heading into a compact
        alphanumeric form.

        Examples:
            "Work Experience"              -> "WORKEXPERIENCE"
            "WORK-EXPERIENCE"              -> "WORKEXPERIENCE"
            "Leadership & Volunteering"    -> "LEADERSHIPANDVOLUNTEERING"
            "LEADERSHIP&VOLUNTEERING"      -> "LEADERSHIPANDVOLUNTEERING"
        """

        text = str(text or "").strip().upper()

        # Normalize ampersand semantically before removing punctuation.
        text = re.sub(r'\s*&\s*', 'AND', text)

        # Keep only letters and numbers.
        text = re.sub(r'[^A-Z0-9]+', '', text)

        return text        
        
    # ---------------------------------------------------------
    # Detect whether a complete line is a section heading.
    #
    # Important:
    # We do NOT search for heading words anywhere in prose.
    # The normalized whole line must equal a known heading.
    # ---------------------------------------------------------

    def exact_heading_type(line):
        stripped = (line or "").strip()

        if not stripped:
            return None

        compact = compact_heading(stripped)

        if compact in experience_headings:
            return "experience"

        if compact in excluded_headings:
            return "excluded"

        return None

    # ---------------------------------------------------------
    # Flexible character-spaced heading prefix.
    #
    # Allows:
    #
    #   WORK EXPERIENCE
    #   W ORK EXPERIENCE
    #   W O R K E X P E R I E N C E
    #
    # Anchored at the START of a line so prose elsewhere does
    # not trigger it.
    # ---------------------------------------------------------

    def flexible_prefix_pattern(heading):
        compact = re.sub(r"[^A-Za-z]", "", heading)

        return (
            r"^\s*"
            + r"\s*".join(
                re.escape(ch)
                for ch in compact
            )
        )

    strong_experience_headings = [
        "PROFESSIONAL EXPERIENCE",
        "PROFESSIONAL WORK EXPERIENCE",
        "WORK EXPERIENCE & ACHIEVEMENTS",
        "RELATED WORK EXPERIENCE",
        "EXPERIENCE HIGHLIGHTS",
        "VOLUNTEERING AND WORK EXPERIENCE",
        "WORK EXPERIENCE",
        "WORKING EXPERIENCE",
        "WORK HISTORY",
        "WORK BACKGROUND",
        "EMPLOYMENT HISTORY",
        "EMPLOYMENT EXPERIENCE",
        "CAREER HISTORY",
        "CAREER EXPERIENCE",
        "RELEVANT EXPERIENCE",
        "EXPERIENCE SUMMARY",
        "JOB HISTORY",
        "LEADERSHIP AND VOLUNTEERING",
    ]


    strong_experience_prefix_patterns = [
        (
            heading,
            re.compile(
                flexible_prefix_pattern(heading),
                re.IGNORECASE
            )
        )
        for heading in strong_experience_headings
    ]

    excluded_prefix_patterns = [
        (
            heading,
            re.compile(
                flexible_prefix_pattern(heading),
                re.IGNORECASE
            )
        )
        for heading in [
            "PROJECTS",
            "VOLUNTEER",
            "VOLUNTEERING",
            "EXTRACURRICULAR",
            "AWARDS",
            "SKILLS",
            "TECHNICAL SKILLS",
            "CERTIFICATIONS",
            "CERTIFICATES",
            "LICENSES",
            "ASSESSMENTS",
            "SUMMARY",
            "EDUCATION",
        ]
    ]

    # ---------------------------------------------------------
    # Repair uppercase section headings glued to the previous
    # sentence by PDF extraction.
    #
    # Examples:
    #
    #   literacy programsPROJECTS
    #   experience.SKILLS
    #
    # Do not do this for generic EXPERIENCE because that word
    # occurs naturally in prose.
    # ---------------------------------------------------------

    repair_headings = [
        "PROFESSIONAL EXPERIENCE",
        "PROFESSIONAL WORK EXPERIENCE",
        "WORK EXPERIENCE & ACHIEVEMENTS",
        "RELATED WORK EXPERIENCE",
        "EXPERIENCE HIGHLIGHTS",
        "WORK EXPERIENCE",
        "WORKING EXPERIENCE",
        "WORK HISTORY",
        "WORK BACKGROUND",
        "EMPLOYMENT HISTORY",
        "EMPLOYMENT EXPERIENCE",
        "CAREER HISTORY",
        "CAREER EXPERIENCE",
        "RELEVANT EXPERIENCE",
        "EXPERIENCE SUMMARY",
        "JOB HISTORY",
        "PROJECTS",
        "VOLUNTEER",
        "VOLUNTEERING",
        "EXTRACURRICULAR",
        "AWARDS",
        "SKILLS",
        "TECHNICAL SKILLS",
        "CERTIFICATIONS",
        "CERTIFICATES",
        "LICENSES",
        "ASSESSMENTS",
        "SUMMARY",
        "EDUCATION",
    ]

    normalized_text = resume_text

    for heading in repair_headings:
        normalized_text = re.sub(
            rf"(?<=[a-z0-9.,;:)])"
            rf"(?={re.escape(heading)}\b)",
            "\n",
            normalized_text
        )

    lines = normalized_text.splitlines()

    relevant_sections = []

    in_experience = False
    current_header = None
    current_lines = []

    # ---------------------------------------------------------
    # Save one completed experience section.
    # ---------------------------------------------------------

    def save_current_section():
        nonlocal current_header
        nonlocal current_lines

        if not current_header:
            return

        limited = current_lines[:max_lines]

        section_text = "\n".join(limited).strip()

        if section_text:
            relevant_sections.append(
                f"{current_header}\n{section_text}"
            )
        else:
            relevant_sections.append(
                current_header
            )

        current_header = None
        current_lines = []

    # ---------------------------------------------------------
    # Walk the document line by line.
    # ---------------------------------------------------------

    for raw_line in lines:

        line = raw_line.strip()

        if not line:
            if in_experience and current_lines:
                current_lines.append("")
            continue

        heading_type = exact_heading_type(line)

        # -----------------------------------------------------
        # Exact full-line experience heading.
        # -----------------------------------------------------

        if heading_type == "experience":

            if in_experience:
                save_current_section()

            current_header = line
            current_lines = []
            in_experience = True
            continue

        # -----------------------------------------------------
        # Exact full-line terminating heading.
        # -----------------------------------------------------

        if heading_type == "excluded":

            if in_experience:
                save_current_section()
                in_experience = False

            continue

        # -----------------------------------------------------
        # Strong experience heading at beginning of line.
        #
        # Handles:
        #
        #   W ORK EXPERIENCE
        #
        # and:
        #
        #   WORKEXPERIENCESoftware Developer
        # -----------------------------------------------------

        experience_prefix_match = None

        for heading, pattern in strong_experience_prefix_patterns:

            match = pattern.match(line)

            if not match:
                continue

            remainder = line[match.end():].strip()

            # If there is remainder, only accept a glued heading
            # when the remainder starts like a new PDF segment.
            if remainder:
                if not (
                    remainder[0].isupper()
                    or remainder[0].isdigit()
                    or remainder.startswith("-")
                    or remainder.startswith("|")
                    or remainder.startswith(":")
                ):
                    continue

            experience_prefix_match = (
                heading,
                match,
                remainder
            )
            break

        if experience_prefix_match:

            if in_experience:
                save_current_section()

            heading, match, remainder = experience_prefix_match

            current_header = line[:match.end()].strip()
            current_lines = []
            in_experience = True

            if remainder:
                remainder = remainder.lstrip(
                    " :-|"
                ).strip()

                if remainder:
                    current_lines.append(remainder)

            continue

        # -----------------------------------------------------
        # Terminating heading at beginning of line.
        #
        # Handles glued forms:
        #
        #   EDUCATIONUniversity of Waterloo
        #   PROJECTSEcoForecast
        #
        # But NOT:
        #
        #   communication skills
        # -----------------------------------------------------

        excluded_prefix_match = None

        for heading, pattern in excluded_prefix_patterns:

            match = pattern.match(line)

            if not match:
                continue

            remainder = line[match.end():].strip()

            if not remainder:
                excluded_prefix_match = (
                    heading,
                    match
                )
                break

            # For glued headings require clear PDF boundary
            # evidence immediately after the heading.
            if (
                remainder[0].isupper()
                or remainder[0].isdigit()
                or remainder.startswith("-")
                or remainder.startswith("|")
                or remainder.startswith(":")
            ):
                excluded_prefix_match = (
                    heading,
                    match
                )
                break

        if excluded_prefix_match:

            if in_experience:
                save_current_section()
                in_experience = False

            continue

        # -----------------------------------------------------
        # Ordinary content.
        # -----------------------------------------------------

        if in_experience:
            current_lines.append(raw_line.strip())

    # Save section if the resume ended while still inside it.
    if in_experience:
        save_current_section()

    if relevant_sections:
        return "\n\n".join(relevant_sections)

    # ---------------------------------------------------------
    # Conservative structural fallback for resumes that do not use a
    # canonical experience heading.  A date alone is never sufficient.
    # ---------------------------------------------------------
    month = (
        r'(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|'
        r'Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:t(?:ember)?)?|'
        r'Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)\.?'
    )
    current_terms = (
        r'(?:Present|Current|Today|Ongoing|Now|To\s+Date|'
        r'Till\s+Date|Till\s+Now|Continued|Continuing|Until\s+Date|Until\s+Now)'
    )
    date_atom = (
        rf'(?:{month}\s*,?\s*\d{{4}}|'
        rf'{month}\s*[\'’]\d{{2}}|'
        rf'{month}\s*[- ]\s*\d{{2}}|'
        rf'(?:0?[1-9]|1[0-2])/\d{{2,4}}|'
        rf'(?:19|20)\d{{2}})'
    )
    employment_range = re.compile(
        rf'(?i)\b{date_atom}\s*(?:[-\u2013\u2014]|to)\s*'
        rf'(?:{date_atom}|{current_terms})\b'
    )
    explicit_role = re.compile(r'(?i)\b(?:position|job\s*title|role|title|company|employer|client)\s*[:\-]')
    occupational_role = re.compile(
        r'(?i)\b(?:architect|engineer|developer|analyst|manager|consultant|'
        r'administrator|specialist|technician|director|lead|coordinator|'
        r'officer|supervisor|scientist|programmer|recruiter|agent|cashier|'
        r'advisor|executive|associate|assistant|intern)\b'
    )
    ambiguous_headings = {"PROFESSIONAL", "EMPLOYMENT"}

    def nearest_boundary_before(index):
        for j in range(index - 1, -1, -1):
            compact = compact_heading(lines[j])
            if compact in excluded_headings:
                return "excluded", j
            if compact in ambiguous_headings or compact in experience_headings:
                return "experience", j
        return None, None

    candidate_index = None
    candidate_start = None
    for idx, raw_line in enumerate(lines):
        if not employment_range.search(raw_line):
            continue
        boundary_type, boundary_index = nearest_boundary_before(idx)
        local_start = max(0, idx - 5)
        local_end = min(len(lines), idx + 6)
        context = "\n".join(lines[local_start:local_end])
        has_role_evidence = bool(explicit_role.search(context) or occupational_role.search(context))
        if not has_role_evidence:
            continue
        if boundary_type == "excluded":
            continue
        candidate_index = idx
        candidate_start = boundary_index if boundary_type == "experience" else local_start
        break

    if candidate_index is None:
        return ""

    fallback_lines = []
    for idx in range(candidate_start, min(len(lines), candidate_start + max_lines + 1)):
        if idx > candidate_start and compact_heading(lines[idx]) in excluded_headings:
            break
        fallback_lines.append(lines[idx].strip())

    fallback_text = "\n".join(fallback_lines).strip()
    if fallback_text:
        print("Using conservative structural experience fallback.")
    return fallback_text

def extract_education_section(resume_text, max_lines=10):
    """
    Extract the education section from the resume and limit the number of lines.
    """
    education_headers = [
        r'ACADEMIC QUALIFICATIONS', r'Academic Qualifications',
        r'EDUCATIONAL QUALIFICATIONS', r'Educational Qualifications',
        r'Education & Certifications', r'EDUCATION & CERTIFICATIONS',
        r'Education and Certifications', r'EDUCATION AND CERTIFICATIONS',
        r'ACADEMIC BACKGROUND', r'Academic Background',
        r'ACADEMIC HISTORY', r'Academic History',
        r'DIPLOMA', r'Diploma',
        r'EDUCATION', r'Education'
    ]

    excluded_headers = [
        r"Projects", r"PROJECTS",
        r"Volunteer", r"VOLUNTEER",
        r"Extracurricular", r"EXTRACURRICULAR",
        r"Awards", r"AWARDS",
        r"Skills", r"SKILLS",
        r"Certifications", r"CERTIFICATIONS",
        r"Certificates", r"CERTIFICATES",        
        r"Licenses", r"LICENSES",
        r"Assessments", r"ASSESSMENTS",
        r"Summary", r"SUMMARY"
    ]

    headers_pattern = build_regex_pattern(education_headers)
    excluded_pattern = build_regex_pattern(excluded_headers)

    # Split the resume text into sections based on headers
    sections = re.split(rf'(?i)({headers_pattern})', resume_text)

    relevant_sections = []
    for i in range(1, len(sections), 2):
        header = sections[i]
        content = sections[i + 1]

        # Stop parsing if an excluded header is found
        if re.search(rf'(?i)({excluded_pattern})', content):
            content = re.split(rf'(?i)({excluded_pattern})', content)[0]

        # Limit the number of lines to the first `max_lines` lines
        content_lines = content.splitlines()
        limited_content = "\n".join(content_lines[:max_lines])

        relevant_sections.append(f"{header}\n{limited_content.strip()}")

    # Combine the relevant sections into a single text block
    combined_text = '\n\n'.join(relevant_sections)

    return combined_text

def move_file_to_processed(filename):
    unprocessed_path = os.path.join(unprocessed_folder, filename)
    processed_path = os.path.join(processed_folder, filename)
    shutil.move(unprocessed_path, processed_path)
    print(f"Moved file {filename} to Processed folder.")

def save_metadata_to_chromadb(metadata):
    # Extract the embedding from the metadata
    embedding = metadata.pop('embedding')

    # Add tokenized text to the metadata
    tokenized_text = metadata.pop('tokenized_text', None)

    # Convert tokenized_text to a string with a custom separator if it's a list
    if isinstance(tokenized_text, list):
        metadata["tokenized_text"] = "~~".join(tokenized_text)  # Use double tilde (`~~`) as a separator

    # Filter metadata to include only supported types
    filtered_metadata = {k: v for k, v in metadata.items() if isinstance(v, (str, int, float, bool))}

    # Save or update the metadata in ChromaDB
    query_conditions = []
    email = filtered_metadata.get("email")
    phone_number = filtered_metadata.get("phone_number")

    if email and email != "N/A":
        query_conditions.append({"email": email})
        print(f"Checking for existing resumes with email: {email}")
    if phone_number and phone_number != "N/A":
        query_conditions.append({"phone_number": phone_number})
        print(f"Checking for existing resumes with phone number: {phone_number}")

    existing_resumes = None

    if query_conditions:
        if len(query_conditions) > 1:
            existing_resumes = collection.get(
                where={"$or": query_conditions},
                include=["documents", "metadatas"]
            )
        else:
            existing_resumes = collection.get(
                where=query_conditions[0],
                include=["documents", "metadatas"]
            )

    if existing_resumes and existing_resumes['metadatas']:
        print(f"Found matching resume(s) with the same email or phone number: {existing_resumes['metadatas']}")
    else:
        print("No matching resumes found with the same email or phone number.")
    
    print("\n--- Metadata for Resume ---")
    for key, value in metadata.items():
        if key != "resume_text":
            print(f"{key}: {value}")
    print("---------------------------")

    # If no matching resume is found by email or phone number, check by filename
    if not existing_resumes or not existing_resumes['metadatas']:
        existing_resumes = collection.get(
            where={"filename": filtered_metadata.get("filename")},
            include=["documents", "metadatas"]
        )

    if existing_resumes['metadatas']:
        # If a matching resume is found, update the existing entry
        # using the actual ChromaDB record ID, not the filename
        # stored inside metadata.       
        existing_id = existing_resumes['ids'][0]
        collection.update(
            ids=[existing_id],
            documents=[filtered_metadata['resume_text']],  # Update resume text in documents property of collection
            metadatas=[filtered_metadata],  # Update the metadata
            embeddings=[embedding]
        )
        print(f"Updated existing resume with filename: {existing_id}")
    else:
        # If no matching resume is found, add a new entry
        collection.add(
            documents=[filtered_metadata['resume_text']],
            metadatas=[filtered_metadata],
            ids=[str(filtered_metadata['filename'])],
            embeddings=[embedding]
        )
        print(f"Added new resume with filename: {filtered_metadata['filename']}")

# def save_metadata_to_chromadb(metadata):
#     # Extract the embedding from the metadata
#     embedding = metadata.pop('embedding')

#     # Add tokenized text to the metadata
#     tokenized_text = metadata.pop('tokenized_text', None)

#     # Check if a resume with the same email or phone number already exists
#     query_conditions = []
#     email = metadata.get("email")
#     phone_number = metadata.get("phone_number")

#     if email and email != "N/A":
#         query_conditions.append({"email": email})
#         print(f"Checking for existing resumes with email: {email}")
#     if phone_number and phone_number != "N/A":
#         query_conditions.append({"phone_number": phone_number})
#         print(f"Checking for existing resumes with phone number: {phone_number}")

#     existing_resumes = None

#     if query_conditions:
#         if len(query_conditions) > 1:
#             existing_resumes = collection.get(
#                 where={"$or": query_conditions},
#                 include=["documents", "metadatas"]
#             )
#         else:
#             existing_resumes = collection.get(
#                 where=query_conditions[0],
#                 include=["documents", "metadatas"]
#             )
    
#     if existing_resumes and existing_resumes['metadatas']:
#         print(f"Found matching resume(s) with the same email or phone number: {existing_resumes['metadatas']}")
#     else:
#         print("No matching resumes found with the same email or phone number.")

#     print("\n--- Metadata for Resume ---")
#     for key, value in metadata.items():
#         if key != "resume_text":
#             print(f"{key}: {value}")
#     print("---------------------------")

#     # If no matching resume is found by email or phone number, check by filename
#     if not existing_resumes or not existing_resumes['metadatas']:
#         existing_resumes = collection.get(
#             where={"filename": metadata.get("filename")},
#             include=["documents", "metadatas"]
#         )

#     if existing_resumes['metadatas']:
#         # If a matching resume is found, update the existing entry
#         existing_id = existing_resumes['metadatas'][0]['filename']
#         collection.update(
#             ids=[existing_id],
#             documents=[metadata['resume_text']], # Update resume text in documents property of collection
#             # metadatas=[{k: v for k, v in metadata.items() if isinstance(v, (str, int, float, bool))}], # Update the metadata
#             metadatas=[{**metadata, "tokenized_text": tokenized_text}],
#             embeddings=[embedding]
#         )
#         print(f"Updated existing resume with filename: {existing_id}")
#     else:
#         # If no matching resume is found, add a new entry
#         collection.add(
#             documents=[metadata['resume_text']],
#             # metadatas=[{k: v for k, v in metadata.items() if isinstance(v, (str, int, float, bool))}],
#             metadatas=[{**metadata, "tokenized_text": tokenized_text}],
#             ids=[str(metadata['filename'])],
#             embeddings=[embedding]
#         )
#         print(f"Added new resume with filename: {metadata['filename']}")
    
#     # Call this function if you have an "Unprocessed" and "Processed" folders within your local setup

#     # move_file_to_processed(metadata['filename'])

def print_collection_summary(collection):
    """
    Print the entire collection with filename, most recent job title, and education.
    """
    try:
        # Retrieve all documents and metadata from the collection
        all_resumes = collection.get(include=["metadatas"])

        # Check if the collection is empty
        if not all_resumes or not all_resumes['metadatas']:
            print("The collection is empty.")
            return

        print("\n--- Collection Summary ---")
        for metadata in all_resumes['metadatas']:
            filename = metadata.get('filename', 'N/A')
            most_recent_job_title = metadata.get('most_recent_job_title', 'N/A')
            education = metadata.get('education', 'N/A')
            candidate_name = metadata.get('candidate_name', 'N/A')
            tokenized_text = metadata.get('tokenized_text', 'N/A')
            core_technologies = metadata.get('core_technologies', 'N/A')

            print(f"Filename: {filename}")
            print(f"Most Recent Job Title: {most_recent_job_title}")
            print(f"Education: {education}")
            print(f"Candidate Name: {candidate_name}")
            print(f"Tokenized Text: {tokenized_text}")
            print(f"Skills: {core_technologies}")
            print("---------------------------")
    except Exception as e:
        print(f"Error retrieving collection: {e}")

with open('upload_regex_output.txt', 'w', encoding='utf-8') as f:
    sys.stdout = f
    if __name__ == "__main__":
            start_time = time.time()
            resumes_folder = unprocessed_folder
            # resumes_folder = 'C:/CloudResourcingWithChatbot-Changes(Copy)/pybackend/chroma/RawDataSmall'  # Path to your resumes folder for smaller sample size and avoiding "Unprocessed" and "Processed" folder
            process_resumes(resumes_folder)
            end_time = time.time()
            execution_time = end_time - start_time
            print("Metadata has been saved to ChromaDB.")
            print_collection_summary(collection)
            print(f"Execution time: {execution_time:.2f} seconds")
sys.stdout = sys.__stdout__