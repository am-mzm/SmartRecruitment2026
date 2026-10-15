"""
/******************************************************************************************************************************************************************************
 *
 *                          Solution: Smart-Recruitment(Python)
 *                          Description: Handles the parsing, adding, and updating of the resumes metadata and text on to the ChromaDB collection(using regex expressions alongside AI)
 *                          Created Date: March 27, 2025
 *                          Created By: Areeb Khan
 *                          Last Updated Date: March 27, 2025
 *                          Last Updated By: Areeb Khan
 *                          Version: 1.0
 *
 ********************************************************************************************************************************************************************************/
"""
import os
import re
import json
import docx
import PyPDF2
import sys
import nltk
from nltk.tokenize import word_tokenize
import spacy
import chromadb
from docx import Document
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
import os
import time
from openai import AzureOpenAI

load_dotenv()

chromadb_host = os.getenv('CHROMADB_HOST')
chromadb_port = int(os.getenv('CHROMADB_PORT'))

# Initialize ChromaDB client
client = chromadb.HttpClient(host=chromadb_host, port=chromadb_port, settings=Settings(allow_reset=True, anonymized_telemetry=False))

# Delete the specified collection
collection_name = "smart_recruitment"

# Create the collection again
collection = client.get_or_create_collection(
    name=collection_name,
    metadata={
        "hnsw:space": "cosine",  # Specify the distance function
    }
)

# nltk.download('stopwords')
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

"""Functions for the Upload Resume Python File"""
def parse_single_date(date_str, current_date):
    """Parse a single date (e.g., "Sept 2018", "07/2024", or "Present")."""
    try:
        date_str = date_str.replace('Sept', 'Sep')
        print(f"Parsing date: {date_str}")

        # Handle "Present" or "Current"
        if date_str in ["Present", "PRESENT", "Current", "CURRENT", "To Date", "TO DATE", "Actually", "ACTUALLY"]:
            return current_date
        
        # if date_str.lower() in ["present", "current", "to date"]:
        #     return current_date

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
    """Calculate total years of experience from the resume text."""
    # Define the section headers to look for
    experience_section = re.search(
        r'(?i)(WORK EXPERIENCE|EXPERIENCE|PROFESSIONAL EXPERIENCE|WORK HISTORY|EMPLOYMENT HISTORY|Work Experience).*?(\n\n|\Z)',
        resume_text,
        re.DOTALL
    )
    experience_text = experience_section.group(0) if experience_section else resume_text
    
    experience_headers = [
        r'WORK EXPERIENCE', r'Work Experience',
        r'EXPERIENCE', r'Experience',
        r'EXPERIENCES', r'Experiences',
        r'PROFESSIONAL EXPERIENCE', r'Professional Experience',
        r'WORK HISTORY', r'Work History',
        r'EMPLOYMENT HISTORY', r'Employment History',
        r'CAREER HISTORY', r'Career History',
        r'JOB HISTORY', r'Job History',
        r'Work Background', r'WORK BACKGROUND'
        # r'EMPLOYMENT', r'Employment', 
        # r'CAREER', r'Career',
        # r'JOB', r'Job'
    ]

    exclude_keywords = [
        r"\bProjects\b", r"\bPROJECTS\b",
        r"\bVolunteer\b", r"\bVOLUNTEER\b",
        r"\bExtracurricular\b", r"\bEXTRACURRICULAR\b", # Just Added at 17/03/2025 at 4:25 pm
        r"\bCommunity Service\b", r"\bScouts\b",
        r"\bAwards\b", r"\bAWARDS\b", # Just Added at 17/03/2025 at 4:37 pm
        r"\bUNOFFICIAL\b", # Just Added at 18/03/2025 at 9:56 AM
        r"\bEducation\b", r"\bEDUCATION\b",
        r"\bSkills\b", r"\bSKILLS\b",
        r"\bCertifications\b", r"\bCERTIFICATIONS\b",
        r"\bLicenses\b", r"\bLICENSES\b",
        r"\bAssessments\b", r"\bASSESSMENTS\b",
        r"\bQualifications\b", r"\bQUALIFICATIONS\b"
        r"\bWork Term\b", r"\bPlanned Future Work Term\(s\)\b",
        r"\bAcademic\b", r"\bACADEMIC\b"
        # r"\bLeadership\b", r"\bLEADERSHIP\b", 
        # r"\bExtracurricular\b", r"\bEXTRACURRICULAR\b"
    ]

    date_pattern = r"""
    (?:(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sept(?:ember)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)\.?\s*,?\s*\d{4})  # Month name and year with optional comma and space
    |
    (?:\d{4})  # Year only
    |
    (?:(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sept(?:ember)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)\.?\s*,?\s*\d{4}\s*[-–to\s\n]+\s*(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sept(?:ember)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)\.?\s*,?\s*\d{4})  # Date range with optional comma and space
    |
    (?:\d{2}/\d{4})  # Month/Year format (e.g., "07/2024")
    |
    (?:\(\d{2}/\d{4}\))
    |
    (?:\bPresent\b|\bPRESENT\b|\bCurrent\b|\bCURRENT\b|\bTill Date\b|\bTO DATE\b|\bTo Date\b|\bActually\b|\bACTUALLY\b)  # Present, Current, Till Date, or To Date
    """

    date_matches = list(re.finditer(date_pattern, experience_text, re.VERBOSE))

    # Debugging: Print the dates found
    logging.info(f"Dates Found: {[match.group(0) for match in date_matches]}")
    print(f"Dates Found: {[match.group(0) for match in date_matches]}")

    intervals = []
    current_date = datetime.now()

    for i in range(0, len(date_matches), 2):
        start_date_str = date_matches[i].group(0)
        start_date = parse_single_date(start_date_str, current_date)
        if start_date is None:
            continue  # Skip invalid start dates
        print(f"Parsed Start Date: {start_date} from {start_date_str}")

        # Check if the start date has " -" or " to" beside it
        if not re.search(rf'{re.escape(start_date_str)}\s*[-–to]', experience_text):
            print(f"Skipping start date without interval indicator: {start_date_str}")
            continue  # Skip if it doesn't indicate an interval
        print(f"Valid Start Date: {start_date} from {start_date_str}")

        preceding_text = experience_text[:date_matches[i].start()]
        start_excluded_keyword_found = False
        start_experience_header_found = False

        # print(f"Preceding text: {preceding_text}")

        # Check for excluded keywords
        keyword_end_positions = []
        for keyword in exclude_keywords:
            match = re.finditer(rf'\b{keyword}\b', preceding_text) #Should the ignore case be removed here?
            for m in match:
                keyword_end_positions.append(m.end())
                start_excluded_keyword_found = True
                print(f"Found exclude keyword '{keyword}' before date: {start_date_str}")

        # Check for experience headers
        header_end_positions = []
        for header in experience_headers:
            match = re.finditer(rf'\b{header}\b', preceding_text) #Should the ignore case be removed here?
            for m in match:
                header_end_positions.append(m.end())
                start_experience_header_found = True
                print(f"Found experience header '{header}' before date: {start_date_str}")

        if start_excluded_keyword_found and start_experience_header_found:
            # Calculate the distance from the end of the keyword or header to the start of the date
            if keyword_end_positions:
                last_keyword_end_pos = max(keyword_end_positions)
            if header_end_positions:
                last_header_end_pos = max(header_end_positions)
            
            keyword_distance = date_matches[i].start() - last_keyword_end_pos
            header_distance = date_matches[i].start() - last_header_end_pos
            
            # print(f"Last keyword end position: {last_keyword_end_pos}, Last header end position: {last_header_end_pos}")
            # print(f"Keyword distance: {keyword_distance}, Header distance: {header_distance}")
            
            if keyword_distance < header_distance:
                print(f"Keyword is closer to the date than the header, skipping date: {start_date_str}")
                continue  # Skip if the keyword is closer to the date than the header
            else:
                print(f"Header is closer to the date than the keyword, continuing with date: {start_date_str}")
        elif start_excluded_keyword_found:
            print(f"No experience header found before date: {start_date_str}, skipping")
            continue  # Skip if no experience header appears before the current date

        # Ensure i + 1 is within the bounds of the date_matches list
        if i + 1 < len(date_matches):
            end_date_str = date_matches[i + 1].group(0)
            end_date = parse_single_date(end_date_str, current_date)
            
            if end_date is None:
                print(f"End date is None for {end_date_str}")
            elif end_date < start_date:
                print(f"End date {end_date} is earlier than start date {start_date}")
                end_date = datetime(start_date.year + 1, start_date.month, start_date.day)
                i -= 1  # Adjust the index to reprocess the next date as a start date
            
            if not re.search(rf'[-–to]\s*{re.escape(end_date_str)}', experience_text):
                print(f"Skipping end date without interval indicator: {end_date_str}")
                end_date = datetime(start_date.year + 1, start_date.month, start_date.day)  # Assume one year from start date
            
        else:
            # end_date = current_date  # Assume "Present" as the end date for the last job
            end_date = datetime(start_date.year + 1, start_date.month, start_date.day)
        print(f"Parsed End Date: {end_date} from {end_date_str if i + 1 < len(date_matches) else 'Present'}")

        # Check if the date is under an excluded section after parsing the end date
        if i + 1 < len(date_matches):
            preceding_text = experience_text[:date_matches[i + 1].start()]  # Change to check end date
            end_excluded_keyword_found = False
            end_experience_header_found = False

            # Check for excluded keywords
            keyword_end_positions = []
            for keyword in exclude_keywords:
                match = re.finditer(rf'\b{keyword}\b', preceding_text) #Should the ignore case be removed here
                for m in match:
                    keyword_end_positions.append(m.end())
                    end_excluded_keyword_found = True
                    print(f"Found exclude keyword '{keyword}' before date: {end_date_str}")

            # Check for experience headers
            header_end_positions = []
            for header in experience_headers:
                match = re.finditer(rf'\b{header}\b', preceding_text) #Should the ignore case be removed here
                for m in match:
                    header_end_positions.append(m.end())
                    end_experience_header_found = True
                    print(f"Found experience header '{header}' before date: {end_date_str}")

            if end_excluded_keyword_found and end_experience_header_found:
                # Calculate the distance from the end of the keyword or header to the start of the date
                if keyword_end_positions:
                    last_keyword_end_pos = max(keyword_end_positions)
                if header_end_positions:
                    last_header_end_pos = max(header_end_positions)
                
                keyword_distance = date_matches[i + 1].start() - last_keyword_end_pos
                header_distance = date_matches[i + 1].start() - last_header_end_pos
                
                # print(f"Last keyword end position: {last_keyword_end_pos}, Last header end position: {last_header_end_pos}")
                # print(f"Keyword distance: {keyword_distance}, Header distance: {header_distance}")
                
                if keyword_distance < header_distance:
                    print(f"Keyword is closer to the date than the header, skipping date: {end_date_str}")
                    continue  # Skip if the keyword is closer to the date than the header
                else:
                    print(f"Header is closer to the date than the keyword, continuing with date: {end_date_str}")
            elif end_excluded_keyword_found:
                print(f"No experience header found before date: {end_date_str}, skipping")
                continue  # Skip if no experience header appears before the current date


        if start_date and end_date:
            intervals.append((start_date, end_date))
            print(f"Added interval: {start_date} to {end_date}")

    total_experience = relativedelta()

    for start_date, end_date in intervals:
        interval_experience = relativedelta(end_date, start_date)
        print(f"Interval: {start_date} to {end_date}, Experience: {interval_experience}")

        # Convert negative intervals to positive
        if interval_experience.years < 0:
            interval_experience.years = abs(interval_experience.years)
        if interval_experience.months < 0:
            interval_experience.months = abs(interval_experience.months)
        if interval_experience.days < 0:
            interval_experience.days = abs(interval_experience.days)

        total_experience += interval_experience

    total_years = total_experience.years + (total_experience.months / 12) + (total_experience.days / 365.25)
    print(f"Total Experience: {total_experience}, Total Years: {total_years}")
    return max(round(total_years, 2), 0)

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
    
def extract_candidate_name(resume_text, filename):
    """
    Extracts candidate name by removing 'Resume', 'CV' from start or end of filename
    """
    try:
        # Extract base filename without extension
        base_name = os.path.splitext(os.path.basename(filename))[0]

         # Remove 'Resume', 'CV', 'Profile' from start and end (case-insensitive)
        base_name = re.sub(r'^(resume|cv|profile|student)', '', base_name, flags=re.IGNORECASE)
        base_name = re.sub(r'(resume|cv|profile|student)$', '', base_name, flags=re.IGNORECASE)
        
        # Replace underscores and hyphens with spaces
        base_name = base_name.replace('_', ' ').replace('-', ' ')
        base_name = re.sub(r"'s\s*", ' ', base_name)

        # Split the name into words
        words = re.findall(r'[A-Z]?[a-z]+|[A-Z]+(?=[A-Z][a-z]|\d|\W|$)|\d+', base_name)
        #words = re.findall(r'\b[A-Z][a-z]*(?:\s+[A-Z][a-z]*)*\b', base_name)
        
        # Capitalize each word
        words = [word.capitalize() for word in words]        
        if len(words) >= 3 and len(words[2]) <= 5:
            candidate_name = ' '.join(words[:3])
        else:
            candidate_name = ' '.join(words[:2])
            
        return candidate_name if candidate_name else "Unknown"

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

def extract_most_recent_job_title(resume_text):
    azure_openai_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
    azure_openai_api_key = os.getenv("AZURE_OPENAI_API_KEY")
    azure_openai_deployment = os.getenv("AZURE_OPENAI_DEPLOYMENT")
    azure_openai_api_version = os.getenv("AZURE_OPENAI_API_VERSION")
    azure_openai_prompt = os.getenv("AZURE_OPENAI_PROMPT")
    azure_openai_system_message = os.getenv("AZURE_OPENAI_SYSTEM_MESSAGE")
    max_tokens = int(os.getenv("AZURE_OPENAI_API_MAX_TOKENS", 1000))
    temperature = float(os.getenv("AZURE_OPENAI_API_TEMPERATURE", 0.7))
    top_p = float(os.getenv("AZURE_OPENAI_API_TOP_P", 0.95))
    frequency_penalty = float(os.getenv("AZURE_OPENAI_API_FREQUENCY_PENALTY", 0))
    presence_penalty = float(os.getenv("AZURE_OPENAI_API_PRESENCE_PENALTY", 0))
    stop = os.getenv("AZURE_OPENAI_API_STOP", None)
    stream = os.getenv("AZURE_OPENAI_API_STREAM", "False").lower() == "true"

    client = AzureOpenAI(
        azure_endpoint=azure_openai_endpoint,
        api_key=azure_openai_api_key,
        api_version=azure_openai_api_version,
    )

    prompt = f"{azure_openai_prompt}\n{resume_text}"

    # Define the chat messages
    chat_prompt = [
        {"role": "system", "content": azure_openai_system_message},
        {"role": "user", "content": prompt}
    ]

    # Call the Azure OpenAI model
    completion = client.chat.completions.create(
        model=azure_openai_deployment,
        messages=chat_prompt,
        max_tokens=max_tokens,
        temperature=temperature,
        top_p=top_p,
        frequency_penalty=frequency_penalty,
        presence_penalty=presence_penalty,
        stop=stop,
        stream=stream
    )

    # Extract the response text
    response_text = completion.choices[0].message.content.strip() 
    print("\n--- Azure OpenAI Model Output ---")
    print(response_text)
    print("-----------------------------------\n")

    lines = [line.strip() for line in response_text.split("\n") if line.strip()]

    # Remove any introductory sentence(s) or irrelevant lines
    lines = [
        line for line in lines
        if not line.lower().startswith("here are the most recent job titles")
        and not line.lower().startswith("in the order they appear")
    ]

    # Ensure the output is in the format "index; job title; education"
    parsed_output = []
    for line in lines:
        if ";" in line:  # Check if the line contains a semicolon
            # Remove asterisks (*) and leading/trailing spaces
            cleaned_line = line.lstrip("*").strip()
            
            # Split into index, job title, and education
            parts = cleaned_line.split(";", 2)  # Split using semicolons
            if len(parts) == 3:
                # Sanitize the index and other parts
                parts[0] = parts[0].strip()  # Ensure the index is clean
                parts[1] = parts[1].strip()  # Clean job title
                parts[2] = parts[2].strip()  # Clean education
                cleaned_line = ";".join(parts)  # Rejoin the sanitized parts
                parsed_output.append(cleaned_line)  # Add the cleaned line
            else:
                print(f"Skipping malformed line: {line}")

    print(f"Extracted Job Titles and Education: {parsed_output}")
    return parsed_output

# Same implementation except with the gemini model
 
# def extract_most_recent_job_title(resume_text):
#     """Extract the most recent job title from the resume using Gemini 2.0 Flash."""

#     # Initialize the Gemini client
#     api_key = "AIzaSyAyPlGJPQ8ARLePscLlq8EOv59JadJZy6w"  # Replace with your actual API key
#     client = genai.Client(api_key=api_key)

#     # Define the model and input
#     model = "gemini-2.0-flash-lite"
#     contents = [
#         types.Content(
#             role="user",
#             parts=[
#                 # types.Part.from_text(text=f"""
#                 # Extract the most recent job title for each resume in the following text. 
#                 # Each resume starts with its filename, followed by the experience section. 
#                 # Each resume is separated by "--- Resume Separator ---". 
#                 # Output the filename, followed by a comma, and then the most recent job title:
#                 # "filename, job title"
#                 # {resume_text}
#                 # """),
#                 types.Part.from_text(text=f"""
#                 Extract the most recent job title and the highest and most recent educational degree for each resume in the following text. 
#                 Each resume starts with its filename, followed by the experience and education sections. 
#                 Each resume is separated by "--- Resume Separator ---". 
#                 Focus only on text that genuinely resembles a job title and an educational degree.
#                 Output the filename, followed by a comma, the most recent job title, another comma, and the highest educational degree, in the format:
#                 "filename, job title, education"
#                 {resume_text}
#                 """),
#             ],
#         ),
#     ]

#     # Define the generation configuration
#     generate_content_config = types.GenerateContentConfig(
#         temperature=1,
#         top_p=0.95,
#         top_k=40,
#         max_output_tokens=8192,
#         response_mime_type="text/plain",
#     )

#     # Call the Gemini model and process the response
#     # most_recent_job_title = None
#     response_text = ""
#     print("\n--- Gemini Model Output ---")
#     for chunk in client.models.generate_content_stream(
#         model=model,
#         contents=contents,
#         config=generate_content_config,
#     ):
#         # print(chunk.text, end="")  # Print the response for debugging
#         # most_recent_job_title = chunk.text.strip()  # Extract the response text
#         print(chunk.text, end="")  # Print the response for debugging
#         response_text += chunk.text  # Accumulate the response text
#     print("\n-----------------------------------\n")

#     # Split the response into individual lines
#     lines = [line.strip() for line in response_text.split("\n") if line.strip()]

#     # Remove any introductory sentence(s) or irrelevant lines
#     lines = [
#         line for line in lines
#         if not line.lower().startswith("here are the most recent job titles")
#         and not line.lower().startswith("in the order they appear")
#     ]

#     # Ensure the output is in the format "filename, job title, education"
#     parsed_output = []
#     for line in lines:
#         if "," in line:  # Check if the line contains a comma
#             # Remove asterisks (*) and leading/trailing spaces
#             cleaned_line = line.lstrip("*").strip()
            
#             # Sanitize the filename by removing backslashes
#             parts = cleaned_line.split(",", 2)  # Split into filename, job title, and education
#             if len(parts) > 0:
#                 parts[0] = parts[0].replace("\\", "")  # Remove backslashes from the filename
#             cleaned_line = ",".join(parts)  # Rejoin the sanitized parts
            
#             parsed_output.append(cleaned_line)  # Add the cleaned line

#     print(f"Extracted Job Titles and Education: {parsed_output}")
#     return parsed_output


def extract_education(resume_text):
    """Extract highest education level (dummy implementation)."""
    education_levels = ["PhD", "Master", "Bachelor", "Diploma"]
    for level in education_levels:
        if level.lower() in resume_text.lower():
            return level
    return "N/A"

def extract_resume_text(resume_path):
    metadata = {
        'filename': os.path.basename(resume_path),
        'resume_text': "",  # Placeholder for the resume text
        'embedding': None,  # Placeholder for the embedding
        'years_of_experience': 'N/A', # Placeholder for the experience
        'phone_number': 'N/A',  # Placeholder for phone number
        'email': 'N/A',  # Placeholder for email
        'candidate_name': 'Unknown',  # Placeholder for candidate name
        # 'location': 'N/A',  # Placeholder for location
        'core_technologies': 'N/A',  # Placeholder for core technologies
        'most_recent_job_title': 'N/A',  # Placeholder for most recent job title
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
            for para in doc.paragraphs:
                text += para.text + " "

        metadata['resume_text'] = text  # Store the resume text
        metadata['embedding'] = model.encode(text)

        phone_number = extract_phone_number(text)
        metadata['phone_number'] = phone_number

        email = extract_email_address(text)
        metadata['email'] = email

        # Extract core technologies and certifications
        core_technologies = extract_skills(text)
        metadata['core_technologies'] = core_technologies
        
        candidate_name = extract_candidate_name(text, resume_path)
        metadata['candidate_name'] = candidate_name
        
        experience_years = calculate_experience(text)
        metadata['years_of_experience'] = experience_years
    except Exception as e:
        print(f"Error processing {resume_path}: {e}")

    return metadata

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

def extract_experience_section(resume_text, max_lines=10):
    """
    Extract the experience section from the resume and limit the number of words.
    """
    # Define experience headers and excluded headers
    experience_headers = [
        r'PROFESSIONAL EXPERIENCE', r'Professional Experience',
        r'WORK EXPERIENCE', r'Work Experience',
        r'WORKING EXPERIENCE', r'Working Experience',
        r'WORK HISTORY', r'Work History',
        r'WORK BACKGROUND', r'Work Background',
        r'EMPLOYMENT HISTORY', r'Employment History',
        r'CAREER HISTORY', r'Career History',
        r'JOB HISTORY', r'Job History',
        r'EXPERIENCE', r'Experience',
        r'EXPERIENCES', r'Experiences',
    ]

    education_headers = [
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

    headers_pattern = build_regex_pattern(experience_headers + education_headers)
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

def process_resumes(resumes_folder, batch_size=9, max_resumes_per_iteration=40):
    resumes = []
    all_metadata = []

    # Collect all resumes in the folder
    for filename in os.listdir(resumes_folder):
        if filename.endswith(".pdf") or filename.endswith(".docx"):
            resume_path = os.path.join(resumes_folder, filename)
            resumes.append(resume_path)

    # Split resumes into chunks of `max_resumes_per_iteration`
    resume_chunks = [
        resumes[i:i + max_resumes_per_iteration]
        for i in range(0, len(resumes), max_resumes_per_iteration)
    ]

    print("\n--- Resume Chunks ---")
    for chunk_index, chunk in enumerate(resume_chunks, start=1):
        print(f"Chunk {chunk_index}:")
        for resume in chunk:
            print(f"  - {resume}")
    print("---------------------\n")

    # Process each chunk of resumes
    for chunk_index, current_chunk in enumerate(resume_chunks):
        print(f"\n--- Processing Chunk {chunk_index + 1}/{len(resume_chunks)} ---")
        metadata_list = []  # Reset metadata list for each chunk

        # Process resumes one by one for metadata
        # for resume_path in current_chunk:
        for resume_index, resume_path in enumerate(current_chunk, start=1):
            try:
                metadata = extract_resume_text(resume_path)  # Extract metadata for each resume
                experience_section = extract_experience_section(metadata['resume_text'])

                # formatted_experience_section = f"{metadata['filename']}\n\n{experience_section}\n\n--- Resume Separator ---"
                formatted_experience_section = f"{resume_index}\n\n{experience_section}\n\n--- Resume Separator ---"
                metadata['experience_section'] = formatted_experience_section  # Add the formatted experience section

                metadata_list.append(metadata)  # Collect metadata for later job title extraction
                # print(f"Processed {resume_path}: {metadata['filename']}")
                print(f"Processed {resume_path}: Index {resume_index}")
                # save_metadata_to_chromadb(metadata) # Just added here
            except Exception as e:
                print(f"Error processing {resume_path}: {e}")

        # Extract job titles in batches of `batch_size`
        for i in range(0, len(metadata_list), batch_size):
            batch_metadata = metadata_list[i:i + batch_size]
            batch_texts = [metadata['experience_section'] for metadata in batch_metadata]

            # Combine texts for batch job title extraction
            combined_text = "\n\n".join(batch_texts)

            # print(f"Combined Text: {combined_text}")
            print(f"\n--- Combined Text for Batch {i // batch_size + 1} ---")
            print(combined_text)
            print("-----------------------------------")

            try:
                # Extract job titles and education for the batch
                job_titles_and_education = extract_most_recent_job_title(combined_text)

                for metadata, job_entry in zip(batch_metadata, job_titles_and_education):
                    # Parse the job entry (e.g., "1; Software Engineer; Bachelor of Science")
                    parts = job_entry.split(";", 2)  # Split using semicolons instead of commas
                    if len(parts) == 3:
                        metadata['most_recent_job_title'] = parts[1].strip()
                        metadata['education'] = parts[2].strip()
                    else:
                        metadata['most_recent_job_title'] = "N/A"
                        metadata['education'] = "N/A"
                    print(f"Processed Index {parts[0]}: JobTitle: {metadata['most_recent_job_title']}, Education: {metadata['education']}")
                    save_metadata_to_chromadb(metadata)  # Save metadata to ChromaDB
            except Exception as e:
                print(f"Error processing batch {i // batch_size + 1}: {e}")

            # Add a delay to avoid exceeding rate limits
            # time.sleep(4)
        all_metadata.extend(metadata_list)

        # Add a delay of 1 minute after processing each chunk of 50 resumes
        print(f"Completed processing {len(current_chunk)} resumes in Chunk {chunk_index + 1}. Adding a 1-minute delay...")
        time.sleep(15)

    print("\n--- Final Metadata for Entire Collection ---")
    for metadata in all_metadata:
        print(f"Filename: {metadata['filename']}, JobTitle: {metadata['most_recent_job_title']}, Education: {metadata['education']}")
    print("-------------------------------------------")


def move_file_to_processed(filename):
    unprocessed_path = os.path.join(unprocessed_folder, filename)
    processed_path = os.path.join(processed_folder, filename)
    shutil.move(unprocessed_path, processed_path)
    print(f"Moved file {filename} to Processed folder.")

def save_metadata_to_chromadb(metadata):
    # Extract the embedding from the metadata
    embedding = metadata.pop('embedding')

    # Check if a resume with the same email or phone number already exists
    query_conditions = []
    email = metadata.get("email")
    phone_number = metadata.get("phone_number")

    if email and email != "N/A":
        query_conditions.append({"email": email})
        print(f"Checking for existing resumes with email: {email}")
    if phone_number and phone_number != "N/A":
        query_conditions.append({"phone_number": phone_number})
        print(f"Checking for existing resumes with phone number: {phone_number}")

    existing_resumes = None
    # if query_conditions:
    #     existing_resumes = collection.get(
    #         where={"$or": query_conditions},
    #         include=["documents", "metadatas"]
    #     )
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
            where={"filename": metadata.get("filename")},
            include=["documents", "metadatas"]
        )

    if existing_resumes['metadatas']:
        # If a matching resume is found, update the existing entry
        existing_id = existing_resumes['metadatas'][0]['filename']
        collection.update(
            ids=[existing_id],
            documents=[metadata['resume_text']],
            metadatas=[{k: v for k, v in metadata.items() if isinstance(v, (str, int, float, bool))}],
            embeddings=[embedding]
        )
        print(f"Updated existing resume with filename: {existing_id}")
    else:
        # If no matching resume is found, add a new entry
        collection.add(
            documents=[metadata['resume_text']],
            metadatas=[{k: v for k, v in metadata.items() if isinstance(v, (str, int, float, bool))}],
            ids=[str(metadata['filename'])],
            embeddings=[embedding]
        )
        print(f"Added new resume with filename: {metadata['filename']}")
    
    # move_file_to_processed(metadata['filename'])

with open('upload_output.txt', 'w', encoding='utf-8') as f:
    sys.stdout = f
    if __name__ == "__main__":
            start_time = time.time()
            # resumes_folder = unprocessed_folder
            resumes_folder = 'C:/CloudResourcingWithChatbot-Changes(Copy)/pybackend/chroma/RawData'  # Path to your resumes folder
            process_resumes(resumes_folder)
            end_time = time.time()
            execution_time = end_time - start_time
            print("Metadata has been saved to ChromaDB.")
            print(f"Execution time: {execution_time:.2f} seconds")
sys.stdout = sys.__stdout__

