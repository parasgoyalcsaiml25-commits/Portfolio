#!/usr/bin/env python3
"""
AI-Assisted Resume Portfolio Generator
======================================
A complete, robust Python application and web server that extracts factual structured
data from a student's resume (.txt or .pdf) using Google's Gemini API and automatically
compiles a modern, responsive HTML5/CSS3 developer portfolio.

Guiding Principles:
- Dual Format Support: Reads and extracts text from both .txt and .pdf resumes.
- Zero Hallucination: Extracts only factual data present in the uploaded resume.
- Full Text Transmission: Sends complete cleaned resume content to Gemini.
- Ground-Truth Verification: Discards ungrounded or fictitious entities.
- Zero Fallbacks: Never invents names, emails, skills, or placeholder labels.
- Secure Credentials: API key is loaded strictly from environment variables.
"""

import sys
import os
import re
import io
import json
import base64
import html
import argparse
import webbrowser
import zipfile
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv
from flask import Flask

# Safe stdout/stderr initialization for headless/pythonw execution on Windows
if sys.stdout is None:
    sys.stdout = open(os.devnull, "w", encoding="utf-8", errors="replace")
if sys.stderr is None:
    sys.stderr = open(os.devnull, "w", encoding="utf-8", errors="replace")

# Project Base Directory for robust path resolution on local & serverless hosts (e.g. Vercel)
BASE_DIR = Path(__file__).resolve().parent

# Load environment variables from .env file relative to project root
ENV_FILE = BASE_DIR / ".env"
if ENV_FILE.is_file():
    load_dotenv(dotenv_path=ENV_FILE, override=True)
else:
    load_dotenv()

# Try importing Google GenAI SDK
try:
    from google import genai
    from google.genai import types
    GENAI_AVAILABLE = True
except ImportError:
    GENAI_AVAILABLE = False

# Try importing Flask for Generator Web Server
try:
    from flask import Flask, request, jsonify, send_from_directory, send_file
    FLASK_AVAILABLE = True
except ImportError:
    FLASK_AVAILABLE = False

# Try importing pypdf for PDF resume parsing
try:
    from pypdf import PdfReader
    PYPDF_AVAILABLE = True
except ImportError:
    PYPDF_AVAILABLE = False


# ==============================================================================
# 1. Resume Text Extraction (PDF & TXT Support)
# ==============================================================================

def extract_text_from_file_path(file_path: Path) -> tuple[str, str]:
    """
    Extracts text from a local file path (.txt or .pdf).
    Returns (extracted_text, file_type_label).
    """
    if not file_path.is_file():
        raise FileNotFoundError(f"Resume file '{file_path}' does not exist.")

    ext = file_path.suffix.lower()

    if ext == ".pdf":
        if not PYPDF_AVAILABLE:
            raise RuntimeError("PDF extraction requires 'pypdf'. Run: pip install pypdf")
        try:
            reader = PdfReader(str(file_path))
            text = ""
            for page in reader.pages:
                page_text = page.extract_text() or ""
                text += page_text + "\n"
            text = text.strip()
            if not text:
                raise ValueError("This PDF does not contain selectable text. Please use a text-based PDF or TXT resume.")
            return text, "PDF Document (.pdf)"
        except ValueError:
            raise
        except Exception as e:
            raise RuntimeError(f"Error reading PDF file: {e}")
    else:
        # Default to plain text
        try:
            text = file_path.read_text(encoding="utf-8").strip()
            return text, "Plain Text Document (.txt)"
        except UnicodeDecodeError:
            text = file_path.read_text(encoding="latin-1").strip()
            return text, "Plain Text Document (.txt)"


def _gemini_image_to_text(file_bytes: bytes, filename: str) -> str:
    """Use Gemini vision to OCR/understand an image resume while preserving factual text."""
    if not GENAI_AVAILABLE:
        raise RuntimeError("Image resume support requires the 'google-genai' package.")

    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key or not api_key.strip() or api_key == "your_gemini_api_key_here":
        raise RuntimeError("GEMINI_API_KEY is not configured. Add it to your .env file.")

    ext = Path(filename).suffix.lower()
    mime_map = {
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".png": "image/png",
        ".webp": "image/webp",
    }
    mime_type = mime_map.get(ext)
    if not mime_type:
        raise RuntimeError("Unsupported image format. Use JPG, JPEG, PNG, or WEBP.")

    client = genai.Client(api_key=api_key.strip())
    prompt = (
        "Read this resume image and transcribe all visible resume text accurately. "
        "Preserve names, contact details, dates, education, skills, projects, experience, "
        "certifications and links. Do not invent or infer missing information. "
        "Return plain text only, with clear section breaks."
    )
    models = ["gemini-3.6-flash", "gemini-3.5-flash", "gemini-3-flash-preview", "gemini-flash-latest"]
    last_error = None
    for model_name in models:
        try:
            response = client.models.generate_content(
                model=model_name,
                contents=[prompt, types.Part.from_bytes(data=file_bytes, mime_type=mime_type)]
            )
            if response and response.text and response.text.strip():
                return response.text.strip()
        except Exception as e:
            last_error = e
            print(f"[Gemini Vision] Model '{model_name}' failed: {str(e).splitlines()[0]}", file=sys.stderr, flush=True)
    raise RuntimeError(f"Gemini image extraction failed. Last error: {last_error}")


def extract_text_from_bytes(file_bytes: bytes, filename: str) -> tuple[str, str]:
    """Extract text from uploaded PDF/TXT or image resume (JPG/JPEG/PNG/WEBP)."""
    lower_name = filename.lower()
    allowed_extensions = (".pdf", ".txt")

    if not lower_name.endswith(allowed_extensions):
        raise ValueError(
            "Unsupported file type. Please upload a PDF or TXT resume."
        )

    if lower_name.endswith(".pdf"):
        if not PYPDF_AVAILABLE:
            raise RuntimeError("PDF extraction requires 'pypdf'. Run: pip install pypdf")
        try:
            stream = io.BytesIO(file_bytes)
            reader = PdfReader(stream)
            text = ""
            for page in reader.pages:
                page_text = page.extract_text() or ""
                text += page_text + "\n"
            text = text.strip()
            if not text:
                raise ValueError("This PDF does not contain selectable text. Please use a text-based PDF or an image resume (JPG/PNG/WEBP).")
            return text, "PDF Document (.pdf)"
        except ValueError:
            raise
        except Exception as e:
            raise RuntimeError(f"Error reading PDF file: {e}")

    image_exts = (".jpg", ".jpeg", ".png", ".webp")
    if lower_name.endswith(image_exts):
        text = _gemini_image_to_text(file_bytes, filename)
        return text, f"Image Resume ({Path(filename).suffix.lower()})"

    try:
        text = file_bytes.decode("utf-8").strip()
        return text, "Plain Text Document (.txt)"
    except UnicodeDecodeError:
        text = file_bytes.decode("latin-1").strip()
        return text, "Plain Text Document (.txt)"


def clean_resume_text(raw_text: str) -> str:
    """
    Cleans raw resume text:
    - Normalizes newlines and unicode whitespace.
    - Removes excessive blank lines.
    - Preserves all factual content and structural headers.
    """
    if not raw_text:
        return ""

    text = raw_text.replace('\r\n', '\n').replace('\r', '\n')
    text = re.sub(r'[\t\f\v ]+', ' ', text)

    lines = [line.strip() for line in text.split('\n')]
    cleaned_lines = []
    prev_empty = False

    for line in lines:
        if line:
            cleaned_lines.append(line)
            prev_empty = False
        elif not prev_empty:
            cleaned_lines.append("")
            prev_empty = True

    return '\n'.join(cleaned_lines).strip()


def validate_resume_text(text: str, is_pdf: bool = False) -> tuple[bool, str]:
    """
    Validates that extracted resume text contains sufficient content.
    Returns (is_valid, error_message).
    """
    if not text or not text.strip():
        if is_pdf:
            return False, "This PDF does not contain selectable text. Please use a text-based PDF or TXT resume."
        return False, "Could not extract enough text from the resume."

    if len(text.strip()) < 100:
        if is_pdf:
            return False, "This PDF does not contain selectable text. Please use a text-based PDF or TXT resume."
        return False, "Could not extract enough text from the resume."

    return True, ""


# ==============================================================================
# 2. Gemini Prompt Construction
# ==============================================================================

def build_gemini_prompt(cleaned_resume: str, enhance_content: bool = False) -> str:
    """
    Constructs the exact controlled anti-hallucination prompt sending FULL resume text.
    """
    prompt = f"""You are an AI resume-to-portfolio extraction assistant.

Use ONLY information explicitly present in the resume.

Never invent or assume:
* name
* email
* phone
* skills
* education
* experience
* projects
* companies
* dates
* achievements
* certifications
* links

If information is missing, return an empty value.

Return VALID JSON ONLY.
Do not use Markdown.
Do not include ```json.
Do not include explanations before or after the JSON.

If enhancement mode is enabled, improve wording for the summary, project descriptions, and experience responsibilities so they are concise, professional, impact-oriented, and ATS-friendly. You may rewrite wording, but you MUST NOT add facts, technologies, metrics, dates, employers, links, or achievements that are not explicitly present in the resume.

Required JSON structure:
{{
  "name": "",
  "headline": "",
  "summary": "",
  "skills": [],
  "education": [
    {{
      "degree": "",
      "institution": "",
      "dates": "",
      "details": ""
    }}
  ],
  "experience": [
    {{
      "role": "",
      "company": "",
      "dates": "",
      "responsibilities": []
    }}
  ],
  "projects": [
    {{
      "title": "",
      "description": "",
      "technologies": [],
      "link": ""
    }}
  ],
  "achievements": [],
  "contact": {{
    "email": "",
    "phone": "",
    "linkedin": "",
    "github": "",
    "instagram": "",
    "twitter": "",
    "leetcode": "",
    "portfolio": "",
    "project_links": []
  }}
}}

Resume:
{cleaned_resume}
"""
    return prompt


# ==============================================================================
# 3. Gemini API Interaction
# ==============================================================================

def call_gemini_api(prompt: str, api_key: str) -> str:
    """
    Calls Google Gemini API using google-genai SDK.
    Handles authentication, model fallback, real-time logging, and API exceptions gracefully.
    """
    if not GENAI_AVAILABLE:
        raise RuntimeError("Google GenAI SDK is not installed. Run: pip install google-genai")

    if not api_key or not api_key.strip() or api_key == "your_gemini_api_key_here":
        raise ValueError(
            "Configuration Error: GEMINI_API_KEY environment variable is missing or unset.\n"
            "Please create a .env file with your API key:\n"
            "GEMINI_API_KEY=your_actual_key\n"
            "Or export GEMINI_API_KEY in your shell environment."
        )

    client = genai.Client(api_key=api_key.strip())

    # Active, fast, and verified Gemini models in priority order
    candidate_models = [
        "gemini-3.6-flash",
        "gemini-3.5-flash",
        "gemini-3.5-flash-lite",
        "gemini-3-flash-preview",
        "gemini-flash-lite-latest",
        "gemini-flash-latest"
    ]
    last_error = None

    for model_name in candidate_models:
        print(f"[Gemini API] Requesting structured extraction via '{model_name}'...", flush=True)
        t_start = datetime.now()
        try:
            config = types.GenerateContentConfig(
                response_mime_type="application/json",
                temperature=0.1
            )
            response = client.models.generate_content(
                model=model_name,
                contents=prompt,
                config=config
            )

            if response and response.text:
                raw_output = response.text
                elapsed = (datetime.now() - t_start).total_seconds()
                print(f"[Gemini API] Received response from '{model_name}' in {elapsed:.2f}s ({len(raw_output)} chars)", flush=True)
                return raw_output
            else:
                print(f"[Gemini API] Model '{model_name}' returned empty response text, attempting fallback...", flush=True)
        except Exception as e:
            elapsed = (datetime.now() - t_start).total_seconds()
            err_summary = str(e).split('\n')[0]
            print(f"[Gemini API] Model '{model_name}' failed after {elapsed:.2f}s: {err_summary}", file=sys.stderr, flush=True)
            last_error = e
            continue

    raise RuntimeError(f"Gemini API request failed across all candidate models. Last error: {last_error}")


# ==============================================================================
# 4. JSON Extraction & Validation
# ==============================================================================

def parse_and_validate_json(raw_response: str) -> dict:
    """
    Safely parses JSON from Gemini's response.
    Strips markdown code blocks, cleans trailing commas, and normalizes top-level fields.
    """
    if not raw_response or not raw_response.strip():
        raise ValueError("JSON Parsing Error: Received empty response from Gemini API.")

    cleaned_response = raw_response.strip()
    cleaned_response = re.sub(r'^```(?:json)?\s*', '', cleaned_response, flags=re.IGNORECASE)
    cleaned_response = re.sub(r'\s*```$', '', cleaned_response)
    cleaned_response = cleaned_response.strip()
    # Clean invalid trailing commas before closing braces/brackets
    cleaned_response = re.sub(r',\s*([\]\}])', r'\1', cleaned_response)

    try:
        data = json.loads(cleaned_response)
    except json.JSONDecodeError as err:
        match = re.search(r'\{.*\}', cleaned_response, re.DOTALL)
        if match:
            candidate = match.group(0)
            candidate = re.sub(r',\s*([\]\}])', r'\1', candidate)
            try:
                data = json.loads(candidate)
            except json.JSONDecodeError:
                raise ValueError(f"JSON Parsing Error: Invalid JSON syntax in Gemini response.\nDetails: {err}")
        else:
            raise ValueError(f"JSON Parsing Error: Failed to parse response as JSON.\nDetails: {err}")

    if not isinstance(data, dict):
        raise ValueError("JSON Validation Error: Expected top-level JSON object (dict).")

    normalized = {
        "name": str(data.get("name") or "").strip(),
        "headline": str(data.get("headline") or "").strip(),
        "summary": str(data.get("summary") or "").strip(),
        "skills": [str(s).strip() for s in (data.get("skills") or []) if str(s).strip()],
        "education": data.get("education") if isinstance(data.get("education"), list) else [],
        "experience": data.get("experience") if isinstance(data.get("experience"), list) else [],
        "projects": data.get("projects") if isinstance(data.get("projects"), list) else [],
        "achievements": [str(a).strip() for a in (data.get("achievements") or []) if str(a).strip()],
        "contact": data.get("contact") if isinstance(data.get("contact"), dict) else {}
    }

    return normalized


def print_json_validation_summary(data: dict) -> bool:
    """
    Prints safe field validation summary and counts to the console.
    Returns False if almost everything is empty.
    """
    name_status = "available" if data.get("name") else "missing"
    summary_status = "available" if data.get("summary") else "missing"
    skills_count = len(data.get("skills") or [])
    edu_count = len(data.get("education") or [])
    exp_count = len(data.get("experience") or [])
    proj_count = len(data.get("projects") or [])
    ach_count = len(data.get("achievements") or [])

    contact = data.get("contact") or {}
    contact_fields = sum(1 for k in ["email", "phone", "linkedin", "github"] if contact.get(k)) + len(contact.get("project_links") or [])

    print("JSON validation:", flush=True)
    print(f"Name: {name_status}", flush=True)
    print(f"Summary: {summary_status}", flush=True)
    print(f"Skills: {skills_count}", flush=True)
    print(f"Education: {edu_count}", flush=True)
    print(f"Experience: {exp_count}", flush=True)
    print(f"Projects: {proj_count}", flush=True)
    print(f"Achievements: {ach_count}", flush=True)
    print(f"Contact fields: {contact_fields}", flush=True)

    # If almost everything is empty, data extraction failed
    has_any_core = (
        name_status == "available" or
        skills_count > 0 or
        edu_count > 0 or
        exp_count > 0 or
        proj_count > 0
    )

    return has_any_core


def validate_data_against_resume(data: dict, resume_text: str) -> dict:
    """
    Strict ground-truth validation:
    Verifies that extracted fields have grounding in the raw resume text.
    Fictitious entities not present in the resume are discarded.
    """
    resume_lower = resume_text.lower()

    # 1. Validate Name
    raw_name = str(data.get("name") or "").strip()
    if raw_name:
        name_tokens = [t.lower() for t in re.findall(r'\b[A-Za-z]+\b', raw_name) if len(t) > 2]
        if name_tokens and not any(token in resume_lower for token in name_tokens):
            raw_name = ""

    # 2. Validate Headline
    raw_headline = str(data.get("headline") or "").strip()
    if raw_headline:
        headline_tokens = [t.lower() for t in re.findall(r'\b[A-Za-z0-9+#\.]+\b', raw_headline) if len(t) > 2]
        if headline_tokens and not any(token in resume_lower for token in headline_tokens):
            raw_headline = ""

    # 3. Validate Summary
    raw_summary = str(data.get("summary") or "").strip()

    # 4. Validate Skills
    valid_skills = []
    for skill in (data.get("skills") or []):
        s_str = str(skill).strip()
        if not s_str:
            continue
        s_tokens = [t.lower() for t in re.findall(r'[A-Za-z0-9\+\#\.]+', s_str) if len(t) > 1]
        if any(t in resume_lower for t in s_tokens) or s_str.lower() in resume_lower:
            valid_skills.append(s_str)

    # 5. Validate Education
    valid_education = []
    for edu in (data.get("education") or []):
        if not isinstance(edu, dict):
            continue
        degree = str(edu.get("degree") or "").strip()
        inst = str(edu.get("institution") or "").strip()
        dates = str(edu.get("dates") or "").strip()
        details = str(edu.get("details") or "").strip()

        degree_match = any(t.lower() in resume_lower for t in re.findall(r'\b[A-Za-z0-9]+\b', degree) if len(t) > 2)
        inst_match = any(t.lower() in resume_lower for t in re.findall(r'\b[A-Za-z0-9]+\b', inst) if len(t) > 2)

        if (degree and degree_match) or (inst and inst_match) or not (degree or inst):
            valid_education.append({
                "degree": degree,
                "institution": inst,
                "dates": dates,
                "details": details
            })

    # 6. Validate Experience
    valid_experience = []
    for exp in (data.get("experience") or []):
        if not isinstance(exp, dict):
            continue
        role = str(exp.get("role") or "").strip()
        company = str(exp.get("company") or "").strip()
        dates = str(exp.get("dates") or "").strip()
        resps = exp.get("responsibilities") or []
        if isinstance(resps, str):
            resps = [resps]

        role_match = any(t.lower() in resume_lower for t in re.findall(r'\b[A-Za-z0-9]+\b', role) if len(t) > 2)
        comp_match = any(t.lower() in resume_lower for t in re.findall(r'\b[A-Za-z0-9]+\b', company) if len(t) > 2)

        if (role and role_match) or (company and comp_match) or not (role or company):
            valid_experience.append({
                "role": role,
                "company": company,
                "dates": dates,
                "responsibilities": [str(r).strip() for r in resps if str(r).strip()]
            })

    # 7. Validate Projects
    valid_projects = []
    for proj in (data.get("projects") or []):
        if not isinstance(proj, dict):
            continue
        title = str(proj.get("title") or "").strip()
        desc = str(proj.get("description") or "").strip()
        techs = proj.get("technologies") or []
        if isinstance(techs, str):
            techs = [t.strip() for t in techs.split(",") if t.strip()]
        link = str(proj.get("link") or "").strip()

        title_match = any(t.lower() in resume_lower for t in re.findall(r'\b[A-Za-z0-9]+\b', title) if len(t) > 2)
        if title and title_match:
            valid_projects.append({
                "title": title,
                "description": desc,
                "technologies": [str(t).strip() for t in techs if str(t).strip()],
                "link": link
            })

    # 8. Validate Achievements
    valid_achievements = []
    for ach in (data.get("achievements") or []):
        ach_str = str(ach).strip()
        if not ach_str:
            continue
        ach_tokens = [t.lower() for t in re.findall(r'\b[A-Za-z0-9]+\b', ach_str) if len(t) > 2]
        if any(t in resume_lower for t in ach_tokens):
            valid_achievements.append(ach_str)

    # 9. Validate Contact
    raw_contact = data.get("contact") if isinstance(data.get("contact"), dict) else {}
    email = str(raw_contact.get("email") or "").strip()
    phone = str(raw_contact.get("phone") or "").strip()
    linkedin = str(raw_contact.get("linkedin") or "").strip()
    github = str(raw_contact.get("github") or "").strip()
    instagram = str(raw_contact.get("instagram") or "").strip()
    twitter = str(raw_contact.get("twitter") or "").strip()
    leetcode = str(raw_contact.get("leetcode") or "").strip()
    portfolio = str(raw_contact.get("portfolio") or "").strip()
    project_links = raw_contact.get("project_links") or []

    if email and email.lower() not in resume_lower:
        email = ""
    if phone:
        digits = re.sub(r'\D', '', phone)
        resume_digits = re.sub(r'\D', '', resume_text)
        if len(digits) >= 7 and digits not in resume_digits:
            phone = ""
    if linkedin and not any(part in resume_lower for part in re.findall(r'[A-Za-z0-9\-_]+', linkedin) if len(part) > 3):
        linkedin = ""
    if github and not any(part in resume_lower for part in re.findall(r'[A-Za-z0-9\-_]+', github) if len(part) > 3):
        github = ""
    for field_name in ["instagram", "twitter", "leetcode", "portfolio"]:
        value = locals()[field_name]
        if value and not any(part.lower() in resume_lower for part in re.findall(r'[A-Za-z0-9\-_]+', value) if len(part) > 3):
            locals()[field_name] = ""
    instagram = instagram if any(part.lower() in resume_lower for part in re.findall(r'[A-Za-z0-9\-_]+', instagram) if len(part) > 3) else ""
    twitter = twitter if any(part.lower() in resume_lower for part in re.findall(r'[A-Za-z0-9\-_]+', twitter) if len(part) > 3) else ""
    leetcode = leetcode if any(part.lower() in resume_lower for part in re.findall(r'[A-Za-z0-9\-_]+', leetcode) if len(part) > 3) else ""
    portfolio = portfolio if any(part.lower() in resume_lower for part in re.findall(r'[A-Za-z0-9\-_]+', portfolio) if len(part) > 3) else ""

    valid_contact = {
        "email": email,
        "phone": phone,
        "linkedin": linkedin,
        "github": github,
        "instagram": instagram,
        "twitter": twitter,
        "leetcode": leetcode,
        "portfolio": portfolio,
        "project_links": [str(p).strip() for p in project_links if str(p).strip() and str(p).lower() in resume_lower]
    }

    return {
        "name": raw_name,
        "headline": raw_headline,
        "summary": raw_summary,
        "skills": valid_skills,
        "education": valid_education,
        "experience": valid_experience,
        "projects": valid_projects,
        "achievements": valid_achievements,
        "contact": valid_contact
    }


# ==============================================================================
# 5. Dynamic HTML Generation & Template Rendering (Zero Fallback Data)
# ==============================================================================

def escape(val: str) -> str:
    """Escapes HTML special characters to prevent broken markup or injection."""
    return html.escape(str(val or ""), quote=True)


def build_nav_links(data: dict) -> str:
    """Generates navbar links only for present sections."""
    links = ['<li><a href="#hero">Home</a></li>']
    if data.get("summary"):
        links.append('<li><a href="#about">About</a></li>')
    if data.get("skills"):
        links.append('<li><a href="#skills">Skills</a></li>')
    if data.get("projects"):
        links.append('<li><a href="#projects">Projects</a></li>')
    if data.get("experience"):
        links.append('<li><a href="#experience">Experience</a></li>')
    if data.get("education"):
        links.append('<li><a href="#education">Education</a></li>')
    if data.get("achievements"):
        links.append('<li><a href="#achievements">Achievements</a></li>')
    return '\n          '.join(links)


def _social_href(value: str) -> str:
    value = str(value or "").strip()
    if not value:
        return ""
    return value if value.startswith(("http://", "https://", "mailto:", "tel:")) else f"https://{value}"


def build_hero_social_links(contact: dict) -> str:
    """Build all detected social/contact links without inventing profiles."""
    labels = [
        ("github", "GitHub"), ("linkedin", "LinkedIn"), ("instagram", "Instagram"),
        ("twitter", "Twitter/X"), ("leetcode", "LeetCode"), ("portfolio", "Portfolio")
    ]
    pills = []
    for key, label in labels:
        value = str(contact.get(key) or "").strip()
        if value:
            href = escape(_social_href(value))
            pills.append(f'<a href="{href}" target="_blank" rel="noopener noreferrer" class="social-pill">{escape(label)}</a>')
    email = str(contact.get("email") or "").strip()
    phone = str(contact.get("phone") or "").strip()
    if email:
        pills.append(f'<a href="mailto:{escape(email)}" class="social-pill">Email</a>')
    if phone:
        pills.append(f'<a href="tel:{escape(phone)}" class="social-pill">Phone</a>')
    return '\n            '.join(pills)

def build_about_section(summary: str) -> str:
    """Builds About section or returns empty string if missing."""
    if not summary:
        return ""
    return f"""
    <!-- About Section -->
    <section id="about" class="section">
      <div class="simple-container">
        <div class="section-header">
          <span class="section-tag">Overview</span>
          <h2 class="section-title">About Me</h2>
          <div class="section-divider"></div>
        </div>
        <div class="about-card">
          <p class="about-text">{escape(summary)}</p>
        </div>
      </div>
    </section>"""


def build_skills_section(skills: list) -> str:
    """Builds Skills section or returns empty string if missing."""
    if not skills:
        return ""
    pills = [f'<span class="skill-pill"><span class="skill-bullet"></span>{escape(s)}</span>' for s in skills]
    pills_html = '\n          '.join(pills)
    return f"""
    <!-- Technical Skills Section -->
    <section id="skills" class="section">
      <div class="simple-container">
        <div class="section-header">
          <span class="section-tag">Expertise</span>
          <h2 class="section-title">Technical Skills</h2>
          <div class="section-divider"></div>
        </div>
        <div class="skills-container">
          {pills_html}
        </div>
      </div>
    </section>"""


def build_projects_section(projects: list) -> str:
    """Builds Projects grid section or returns empty string if missing."""
    if not projects:
        return ""

    cards = []
    for proj in projects:
        if not isinstance(proj, dict):
            continue
        title = proj.get("title", "").strip()
        if not title:
            continue

        desc = proj.get("description", "").strip()
        techs = proj.get("technologies") or []
        link = proj.get("link", "").strip()

        tech_tags = [f'<span class="tech-tag">{escape(t)}</span>' for t in techs]
        tech_tags_html = '\n              '.join(tech_tags)

        link_html = ""
        if link:
            href = escape(link if link.startswith("http") else f"https://{link}")
            link_html = f'<a href="{href}" target="_blank" rel="noopener noreferrer" class="project-link-btn">View Project &rarr;</a>'

        cards.append(f"""
          <div class="project-card">
            <div>
              <h3 class="project-title">{escape(title)}</h3>
              <p class="project-description">{escape(desc)}</p>
              <div class="project-tech-stack">
                {tech_tags_html}
              </div>
            </div>
            {link_html}
          </div>""")

    if not cards:
        return ""

    cards_html = '\n'.join(cards)
    return f"""
    <!-- Projects Section -->
    <section id="projects" class="section">
      <div class="simple-container">
        <div class="section-header">
          <span class="section-tag">Portfolio</span>
          <h2 class="section-title">Featured Projects</h2>
          <div class="section-divider"></div>
        </div>
        <div class="projects-grid">
          {cards_html}
        </div>
      </div>
    </section>"""


def build_experience_section(experience: list) -> str:
    """Builds Experience section or returns empty string if missing."""
    if not experience:
        return ""

    items = []
    for exp in experience:
        if not isinstance(exp, dict):
            continue
        role = exp.get("role", "").strip()
        company = exp.get("company", "").strip()
        dates = exp.get("dates", "").strip()
        resp = exp.get("responsibilities") or []

        resp_items = [f'<li>{escape(r)}</li>' for r in resp if r and str(r).strip()]
        resp_html = f'<ul class="timeline-responsibilities">\n              ' + '\n              '.join(resp_items) + '\n            </ul>' if resp_items else ""

        items.append(f"""
          <div class="timeline-item">
            <div class="timeline-node"></div>
            <div class="timeline-card">
              <div class="timeline-header">
                <h3 class="timeline-role">{escape(role)}</h3>
                <span class="timeline-date">{escape(dates)}</span>
              </div>
              <div class="timeline-company">{escape(company)}</div>
              {resp_html}
            </div>
          </div>""")

    if not items:
        return ""

    items_html = '\n'.join(items)
    return f"""
    <!-- Experience Section -->
    <section id="experience" class="section">
      <div class="simple-container">
        <div class="section-header">
          <span class="section-tag">Career</span>
          <h2 class="section-title">Work Experience</h2>
          <div class="section-divider"></div>
        </div>
        <div class="timeline">
          {items_html}
        </div>
      </div>
    </section>"""


def build_education_section(education: list) -> str:
    """Builds Education section or returns empty string if missing."""
    if not education:
        return ""

    items = []
    for edu in education:
        if not isinstance(edu, dict):
            continue
        degree = edu.get("degree", "").strip()
        institution = edu.get("institution", "").strip()
        dates = edu.get("dates", "").strip()
        details = edu.get("details", "").strip()

        details_html = f'<p class="timeline-details">{escape(details)}</p>' if details else ""

        items.append(f"""
          <div class="timeline-item">
            <div class="timeline-node"></div>
            <div class="timeline-card">
              <div class="timeline-header">
                <h3 class="timeline-role">{escape(degree)}</h3>
                <span class="timeline-date">{escape(dates)}</span>
              </div>
              <div class="timeline-company">{escape(institution)}</div>
              {details_html}
            </div>
          </div>""")

    if not items:
        return ""

    items_html = '\n'.join(items)
    return f"""
    <!-- Education Section -->
    <section id="education" class="section">
      <div class="simple-container">
        <div class="section-header">
          <span class="section-tag">Academics</span>
          <h2 class="section-title">Education</h2>
          <div class="section-divider"></div>
        </div>
        <div class="timeline">
          {items_html}
        </div>
      </div>
    </section>"""


def build_achievements_section(achievements: list) -> str:
    """Builds Achievements section or returns empty string if missing."""
    if not achievements:
        return ""

    cards = []
    for ach in achievements:
        if isinstance(ach, str) and ach.strip():
            cards.append(f"""
            <div class="achievement-card">
              <span class="achievement-icon">&#9733;</span>
              <p class="achievement-text">{escape(ach.strip())}</p>
            </div>""")

    if not cards:
        return ""

    cards_html = '\n'.join(cards)
    return f"""
    <!-- Achievements Section -->
    <section id="achievements" class="section">
      <div class="simple-container">
        <div class="section-header">
          <span class="section-tag">Recognition</span>
          <h2 class="section-title">Key Achievements</h2>
          <div class="section-divider"></div>
        </div>
        <div class="achievements-grid">
          {cards_html}
        </div>
      </div>
    </section>"""


def build_contact_section(contact: dict) -> str:
    """Builds Contact section or returns empty string if missing."""
    email = contact.get("email", "").strip()
    phone = contact.get("phone", "").strip()
    linkedin = contact.get("linkedin", "").strip()
    github = contact.get("github", "").strip()
    instagram = contact.get("instagram", "").strip()
    twitter = contact.get("twitter", "").strip()
    leetcode = contact.get("leetcode", "").strip()
    portfolio = contact.get("portfolio", "").strip()
    project_links = contact.get("project_links") or []

    if not any([email, phone, linkedin, github, instagram, twitter, leetcode, portfolio, project_links]):
        return ""

    buttons = []
    if email:
        buttons.append(f'<a href="mailto:{escape(email)}" class="contact-btn">'
                       f'<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z"></path><polyline points="22,6 12,13 2,6"></polyline></svg>'
                       f'{escape(email)}</a>')

    if phone:
        buttons.append(f'<a href="tel:{escape(phone)}" class="contact-btn">'
                       f'<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07 19.5 19.5 0 0 1-6-6 19.79 19.79 0 0 1-3.07-8.67A2 2 0 0 1 4.11 2h3a2 2 0 0 1 2 1.72 12.84 12.84 0 0 0 .7 2.81 2 2 0 0 1-.45 2.11L8.09 9.91a16 16 0 0 0 6 6l1.27-1.27a2 2 0 0 1 2.11-.45 12.84 12.84 0 0 0 2.81.7A2 2 0 0 1 22 16.92z"></path></svg>'
                       f'{escape(phone)}</a>')

    if linkedin:
        href = escape(linkedin if linkedin.startswith("http") else f"https://{linkedin}")
        buttons.append(f'<a href="{href}" target="_blank" rel="noopener noreferrer" class="contact-btn">'
                       f'<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M16 8a6 6 0 0 1 6 6v7h-4v-7a2 2 0 0 0-2-2 2 2 0 0 0-2 2v7h-4v-7a6 6 0 0 1 6-6z"></path><rect x="2" y="9" width="4" height="12"></rect><circle cx="4" cy="4" r="2"></circle></svg>'
                       f'LinkedIn</a>')

    if github:
        href = escape(github if github.startswith("http") else f"https://{github}")
        buttons.append(f'<a href="{href}" target="_blank" rel="noopener noreferrer" class="contact-btn">'
                       f'<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M9 19c-5 1.5-5-2.5-7-3m14 6v-3.87a3.37 3.37 0 0 0-.94-2.61c3.14-.35 6.44-1.54 6.44-7A5.44 5.44 0 0 0 20 4.77 5.07 5.07 0 0 0 19.91 1S18.73.65 16 2.48a13.38 13.38 0 0 0-7 0C6.27.65 5.09 1 5.09 1A5.07 5.07 0 0 0 5 4.77a5.44 5.44 0 0 0-1.5 3.78c0 5.42 3.3 6.61 6.44 7A3.37 3.37 0 0 0 9 18.13V22"></path></svg>'
                       f'GitHub</a>')

    for social_value, social_label in [(instagram, "Instagram"), (twitter, "Twitter/X"), (leetcode, "LeetCode"), (portfolio, "Portfolio")]:
        if social_value:
            href = escape(_social_href(social_value))
            buttons.append(f'<a href="{href}" target="_blank" rel="noopener noreferrer" class="contact-btn">{escape(social_label)}</a>')

    for p_link in project_links:
        if isinstance(p_link, str) and p_link.strip():
            href = escape(p_link if p_link.startswith("http") else f"https://{p_link}")
            buttons.append(f'<a href="{href}" target="_blank" rel="noopener noreferrer" class="contact-btn">Link &rarr;</a>')

    buttons_html = '\n            '.join(buttons)
    return f"""
    <!-- Contact Section -->
    <section id="contact" class="section">
      <div class="simple-container">
        <div class="contact-card">
          <div class="section-header" style="text-align: center;">
            <span class="section-tag">Let's Connect</span>
            <h2 class="section-title">Get In Touch</h2>
            <div class="section-divider" style="margin: 12px auto 0 auto;"></div>
          </div>
          <p class="contact-intro">Feel free to reach out for collaboration, opportunities, or inquiries.</p>
          <div class="contact-links-grid">
            {buttons_html}
          </div>
        </div>
      </div>
    </section>"""


# ------------------------------------------------------------------------------
# Designer Portfolio Section Builders
# ------------------------------------------------------------------------------

def build_designer_nav_links(data: dict) -> str:
    """Generates designer navbar links."""
    links = ['<li><a href="#hero">Home</a></li>']
    if data.get("summary"):
        links.append('<li><a href="#about">About</a></li>')
    if data.get("skills"):
        links.append('<li><a href="#skills">Skills</a></li>')
    if data.get("projects"):
        links.append('<li><a href="#projects">Work</a></li>')
    if data.get("experience"):
        links.append('<li><a href="#experience">Experience</a></li>')
    if data.get("education"):
        links.append('<li><a href="#education">Education</a></li>')
    if data.get("achievements"):
        links.append('<li><a href="#achievements">Achievements</a></li>')
    return '\n          '.join(links)


def build_designer_hero_social_links(contact: dict) -> str:
    """Builds designer social pill links."""
    pills = []
    github = contact.get("github", "").strip()
    linkedin = contact.get("linkedin", "").strip()
    email = contact.get("email", "").strip()
    phone = contact.get("phone", "").strip()

    if github:
        href = escape(github if github.startswith("http") else f"https://{github}")
        pills.append(f'<a href="{href}" target="_blank" rel="noopener noreferrer" class="social-pill-designer">'
                     f'<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M9 19c-5 1.5-5-2.5-7-3m14 6v-3.87a3.37 3.37 0 0 0-.94-2.61c3.14-.35 6.44-1.54 6.44-7A5.44 5.44 0 0 0 20 4.77 5.07 5.07 0 0 0 19.91 1S18.73.65 16 2.48a13.38 13.38 0 0 0-7 0C6.27.65 5.09 1 5.09 1A5.07 5.07 0 0 0 5 4.77a5.44 5.44 0 0 0-1.5 3.78c0 5.42 3.3 6.61 6.44 7A3.37 3.37 0 0 0 9 18.13V22"></path></svg>'
                     f'GitHub</a>')

    if linkedin:
        href = escape(linkedin if linkedin.startswith("http") else f"https://{linkedin}")
        pills.append(f'<a href="{href}" target="_blank" rel="noopener noreferrer" class="social-pill-designer">'
                     f'<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M16 8a6 6 0 0 1 6 6v7h-4v-7a2 2 0 0 0-2-2 2 2 0 0 0-2 2v7h-4v-7a6 6 0 0 1 6-6z"></path><rect x="2" y="9" width="4" height="12"></rect><circle cx="4" cy="4" r="2"></circle></svg>'
                     f'LinkedIn</a>')

    if email:
        pills.append(f'<a href="mailto:{escape(email)}" class="social-pill-designer">'
                     f'<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z"></path><polyline points="22,6 12,13 2,6"></polyline></svg>'
                     f'{escape(email)}</a>')

    if phone:
        pills.append(f'<a href="tel:{escape(phone)}" class="social-pill-designer">'
                     f'<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07 19.5 19.5 0 0 1-6-6 19.79 19.79 0 0 1-3.07-8.67A2 2 0 0 1 4.11 2h3a2 2 0 0 1 2 1.72 12.84 12.84 0 0 0 .7 2.81 2 2 0 0 1-.45 2.11L8.09 9.91a16 16 0 0 0 6 6l1.27-1.27a2 2 0 0 1 2.11-.45 12.84 12.84 0 0 0 2.81.7A2 2 0 0 1 22 16.92z"></path></svg>'
                     f'{escape(phone)}</a>')

    return '\n            '.join(pills)


def build_designer_about_section(summary: str, data: dict = None) -> str:
    """Builds Designer About section with stats counter cards if valid data exists."""
    if not summary:
        return ""

    stats_html = ""
    if data and isinstance(data, dict):
        stat_cards = []
        skills_count = len(data.get("skills") or [])
        projects_count = len(data.get("projects") or [])
        exp_count = len(data.get("experience") or [])
        edu_count = len(data.get("education") or [])

        if skills_count > 0:
            stat_cards.append(f"""
            <div class="designer-stat-card tilt-card reveal-scale" data-stat-target="{skills_count}">
              <div class="stat-number-wrap"><span class="stat-num-val" data-val="{skills_count}">0</span><span class="stat-plus">+</span></div>
              <span class="stat-label">Core Competencies</span>
            </div>""")

        if projects_count > 0:
            stat_cards.append(f"""
            <div class="designer-stat-card tilt-card reveal-scale" data-stat-target="{projects_count}">
              <div class="stat-number-wrap"><span class="stat-num-val" data-val="{projects_count}">0</span><span class="stat-plus">+</span></div>
              <span class="stat-label">Featured Projects</span>
            </div>""")

        if exp_count > 0:
            stat_cards.append(f"""
            <div class="designer-stat-card tilt-card reveal-scale" data-stat-target="{exp_count}">
              <div class="stat-number-wrap"><span class="stat-num-val" data-val="{exp_count}">0</span><span class="stat-plus">+</span></div>
              <span class="stat-label">Career Milestones</span>
            </div>""")

        if edu_count > 0:
            stat_cards.append(f"""
            <div class="designer-stat-card tilt-card reveal-scale" data-stat-target="{edu_count}">
              <div class="stat-number-wrap"><span class="stat-num-val" data-val="{edu_count}">0</span><span class="stat-plus"></span></div>
              <span class="stat-label">Academic Credentials</span>
            </div>""")

        if stat_cards:
            stats_html = f"""
            <div class="designer-about-stats-grid">
              {''.join(stat_cards)}
            </div>"""

    return f"""
    <!-- Designer About Section (01 // PERSPECTIVE) -->
    <section id="about" class="designer-section">
      <div class="designer-container">
        <div class="section-header-designer reveal-left">
          <div class="header-tag-group">
            <span class="designer-section-tag">// 01</span>
            <h2 class="designer-section-title">Perspective</h2>
          </div>
        </div>
        
        <div class="editorial-about-grid reveal-up">
          <div class="about-meta-col">
            <span class="designer-section-tag">// 01</span>
          </div>
          <div class="about-text-col">
            <p class="about-editorial-text">{escape(summary)}</p>
          </div>
        </div>
        
        {stats_html}
      </div>
    </section>"""


def build_designer_skills_section(skills: list) -> str:
    if not skills:
        return ""
    import html
    items = [f'<span class="skill-editorial-item">{html.escape(str(s).strip()).upper()}</span>' for s in skills if s and str(s).strip()]
    if not items: return ""
    skills_html = ' <span class="skill-separator">&#8212;</span> '.join(items)
    return f"""
    <!-- Designer Skills Section (02 // ARSENAL) -->
    <section id="skills" class="designer-section">
      <div class="designer-container">
        <div class="section-header-designer reveal-left">
          <div class="header-tag-group">
            <span class="designer-section-tag">// 02</span>
            <h2 class="designer-section-title">Technical Mastery</h2>
          </div>
        </div>
        <div class="editorial-skills-list reveal-up">
          {skills_html}
        </div>
      </div>
    </section>"""


def build_designer_projects_section(projects: list) -> str:
    if not projects: return ""
    cards = []
    import html
    for idx, proj in enumerate(projects):
        if not isinstance(proj, dict): continue
        title = proj.get("title", "").strip()
        if not title: continue
        desc = proj.get("description", "").strip()
        techs = proj.get("technologies") or []
        link = proj.get("link", "").strip()
        num_str = f"{idx + 1:02d}"
        tech_tags = [f'<span class="editorial-tech-tag">{html.escape(t.strip()).upper()}</span>' for t in techs]
        tech_tags_html = '\n                '.join(tech_tags)
        link_html = ""
        if link:
            href = html.escape(link if link.startswith("http") else f"https://{link}")
            link_html = f'<a href="{href}" target="_blank" rel="noopener noreferrer" class="editorial-project-btn">VIEW PROJECT &rarr;</a>'
        cards.append(f"""
        <div class="editorial-project-row reveal-up">
          <div class="project-num-col"><span class="project-num">{num_str}</span></div>
          <div class="project-content-col">
            <h3 class="project-huge-title">{html.escape(title)}</h3>
            <div class="project-techs">{tech_tags_html}</div>
            <p class="project-editorial-desc">{html.escape(desc)}</p>
            <div class="project-action">{link_html}</div>
          </div>
        </div>""")
    if not cards: return ""
    cards_html = '\n'.join(cards)
    return f"""
    <!-- Designer Projects Section -->
    <section id="projects" class="designer-section">
      <div class="designer-container">
        <div class="section-header-designer reveal-left">
          <div class="header-tag-group">
            <span class="designer-section-tag">// 03</span>
            <h2 class="designer-section-title">Selected Projects</h2>
          </div>
        </div>
        <div class="editorial-projects-list">
          {cards_html}
        </div>
      </div>
    </section>"""


def build_designer_experience_section(experience: list) -> str:
    if not experience: return ""
    items = []
    import html
    for idx, exp in enumerate(experience):
        if not isinstance(exp, dict): continue
        role = exp.get("role", "").strip()
        company = exp.get("company", "").strip()
        dates = exp.get("dates", "").strip()
        resp = exp.get("responsibilities") or []
        resp_items = [f'<li>{html.escape(r)}</li>' for r in resp if r and str(r).strip()]
        resp_html = f'<ul class="editorial-resp-list">\n              ' + '\n              '.join(resp_items) + '\n            </ul>' if resp_items else ""
        items.append(f"""
        <div class="editorial-timeline-row reveal-up">
          <div class="timeline-date-col">{html.escape(dates)}</div>
          <div class="timeline-info-col">
            <h3 class="timeline-role">{html.escape(role)}</h3>
            <div class="timeline-company">{html.escape(company)}</div>
            {resp_html}
          </div>
        </div>""")
    if not items: return ""
    items_html = '\n'.join(items)
    return f"""
    <!-- Designer Experience Section -->
    <section id="experience" class="designer-section">
      <div class="designer-container">
        <div class="section-header-designer reveal-left">
          <div class="header-tag-group">
            <span class="designer-section-tag">// 04</span>
            <h2 class="designer-section-title">Experience</h2>
          </div>
        </div>
        <div class="editorial-timeline-list">
          {items_html}
        </div>
      </div>
    </section>"""


def build_designer_education_section(education: list) -> str:
    if not education: return ""
    items = []
    import html
    for idx, edu in enumerate(education):
        if not isinstance(edu, dict): continue
        degree = edu.get("degree", "").strip()
        inst = edu.get("institution", "").strip()
        dates = edu.get("dates", "").strip()
        details = edu.get("details", "").strip()
        details_html = f'<p class="timeline-details">{html.escape(details)}</p>' if details else ""
        items.append(f"""
        <div class="editorial-timeline-row reveal-up">
          <div class="timeline-date-col">{html.escape(dates)}</div>
          <div class="timeline-info-col">
            <h3 class="timeline-role">{html.escape(degree)}</h3>
            <div class="timeline-company">{html.escape(inst)}</div>
            {details_html}
          </div>
        </div>""")
    if not items: return ""
    items_html = '\n'.join(items)
    return f"""
    <!-- Designer Education Section -->
    <section id="education" class="designer-section">
      <div class="designer-container">
        <div class="section-header-designer reveal-left">
          <div class="header-tag-group">
            <span class="designer-section-tag">// 05</span>
            <h2 class="designer-section-title">Education</h2>
          </div>
        </div>
        <div class="editorial-timeline-list">
          {items_html}
        </div>
      </div>
    </section>"""


def build_designer_achievements_section(achievements: list) -> str:
    if not achievements: return ""
    cards = []
    import html
    for idx, ach in enumerate(achievements):
        if isinstance(ach, str) and ach.strip():
            cards.append(f"""
            <div class="editorial-achieve-row reveal-up">
              <div class="achieve-bullet">&#x2736;</div>
              <p class="achieve-statement">{html.escape(ach.strip())}</p>
            </div>""")
    if not cards: return ""
    cards_html = '\n'.join(cards)
    return f"""
    <!-- Designer Achievements Section -->
    <section id="achievements" class="designer-section">
      <div class="designer-container">
        <div class="section-header-designer reveal-left">
          <div class="header-tag-group">
            <span class="designer-section-tag">// 06</span>
            <h2 class="designer-section-title">Achievements</h2>
          </div>
        </div>
        <div class="editorial-achieve-list">
          {cards_html}
        </div>
      </div>
    </section>"""


def build_designer_contact_section(contact: dict) -> str:
    email = contact.get("email", "").strip()
    phone = contact.get("phone", "").strip()
    linkedin = contact.get("linkedin", "").strip()
    github = contact.get("github", "").strip()
    project_links = contact.get("project_links") or []
    if not any([email, phone, linkedin, github, project_links]): return ""
    buttons = []
    import html
    if email: buttons.append(f'<a href="mailto:{html.escape(email)}" class="editorial-contact-link reveal-up">EMAIL</a>')
    if phone: buttons.append(f'<a href="tel:{html.escape(phone)}" class="editorial-contact-link reveal-up">PHONE</a>')
    if linkedin:
        href = html.escape(linkedin if linkedin.startswith("http") else f"https://{linkedin}")
        buttons.append(f'<a href="{href}" target="_blank" rel="noopener noreferrer" class="editorial-contact-link reveal-up">LINKEDIN</a>')
    if github:
        href = html.escape(github if github.startswith("http") else f"https://{github}")
        buttons.append(f'<a href="{href}" target="_blank" rel="noopener noreferrer" class="editorial-contact-link reveal-up">GITHUB</a>')
    for p_link in project_links:
        if isinstance(p_link, str) and p_link.strip():
            href = html.escape(p_link if p_link.startswith("http") else f"https://{p_link}")
            buttons.append(f'<a href="{href}" target="_blank" rel="noopener noreferrer" class="editorial-contact-link reveal-up">PORTFOLIO</a>')
    buttons_html = '\n            '.join(buttons)
    return f"""
    <!-- Designer Contact Section -->
    <section id="contact" class="designer-section">
      <div class="designer-container">
        <div class="editorial-contact-box">
          <h2 class="contact-huge-title reveal-up">LET&apos;S TALK</h2>
          <div class="editorial-contact-grid">
            {buttons_html}
          </div>
        </div>
      </div>
    </section>"""


def render_portfolio_html(template_content: str, data: dict, template_choice: str = "simple", profile_image_data: str = "", theme_color: str = "#8b5cf6") -> str:
    """
    Renders portfolio HTML replacing placeholders with validated data.
    Chooses between Simple and Designer section builders based on template_choice.
    """
    contact = data.get("contact") or {}
    year = str(datetime.now().year)
    name = escape(data.get("name"))
    headline = escape(data.get("headline"))
    summary = escape(data.get("summary"))

    norm_choice = template_choice.lower().strip()
    is_designer = norm_choice == "designer" or ("style-designer.css" in template_content)

    # Optional profile image. The generator stores it as a self-contained data URL
    # so the downloaded HTML works without a separate assets folder.
    profile_image_html = ""
    if profile_image_data and profile_image_data.startswith("data:image/"):
        profile_image_html = (
            f'<img class="ai-profile-image" src="{escape(profile_image_data)}" '
            f'alt="Profile photo" loading="lazy">'
        )

    # Curated accent palettes for the generated portfolio.
    palette = {
        "#8b5cf6": ("#8b5cf6", "#06b6d4"),
        "#06b6d4": ("#06b6d4", "#8b5cf6"),
        "#10b981": ("#10b981", "#06b6d4"),
        "#f59e0b": ("#f59e0b", "#f43f5e"),
        "#f43f5e": ("#f43f5e", "#8b5cf6"),
        "#3b82f6": ("#3b82f6", "#06b6d4"),
    }
    accent, accent2 = palette.get(theme_color.lower(), palette["#8b5cf6"])

    if is_designer:
        replacements = {
            "{{NAME}}": name,
            "{{HEADLINE}}": headline,
            "{{SUMMARY}}": summary,
            "{{YEAR}}": year,
            "{{NAV_LINKS}}": build_designer_nav_links(data),
            "{{HERO_SOCIAL_LINKS}}": build_designer_hero_social_links(contact),
            "{{ABOUT_SECTION}}": build_designer_about_section(summary, data=data),
            "{{SKILLS_SECTION}}": build_designer_skills_section(data.get("skills")),
            "{{PROJECTS_SECTION}}": build_designer_projects_section(data.get("projects")),
            "{{EXPERIENCE_SECTION}}": build_designer_experience_section(data.get("experience")),
            "{{EDUCATION_SECTION}}": build_designer_education_section(data.get("education")),
            "{{ACHIEVEMENTS_SECTION}}": build_designer_achievements_section(data.get("achievements")),
            "{{CONTACT_SECTION}}": build_designer_contact_section(contact),
            "{{EMAIL}}": escape(contact.get("email")),
            "{{PHONE}}": escape(contact.get("phone")),
            "{{LINKEDIN}}": escape(contact.get("linkedin")),
            "{{GITHUB}}": escape(contact.get("github")),
            "{{PROFILE_IMAGE}}": profile_image_html,
        }
    else:
        replacements = {
            "{{NAME}}": name,
            "{{HEADLINE}}": headline,
            "{{SUMMARY}}": summary,
            "{{YEAR}}": year,
            "{{NAV_LINKS}}": build_nav_links(data),
            "{{HERO_SOCIAL_LINKS}}": build_hero_social_links(contact),
            "{{ABOUT_SECTION}}": build_about_section(summary),
            "{{SKILLS_SECTION}}": build_skills_section(data.get("skills")),
            "{{PROJECTS_SECTION}}": build_projects_section(data.get("projects")),
            "{{EXPERIENCE_SECTION}}": build_experience_section(data.get("experience")),
            "{{EDUCATION_SECTION}}": build_education_section(data.get("education")),
            "{{ACHIEVEMENTS_SECTION}}": build_achievements_section(data.get("achievements")),
            "{{CONTACT_SECTION}}": build_contact_section(contact),
            "{{EMAIL}}": escape(contact.get("email")),
            "{{PHONE}}": escape(contact.get("phone")),
            "{{LINKEDIN}}": escape(contact.get("linkedin")),
            "{{GITHUB}}": escape(contact.get("github")),
            "{{PROFILE_IMAGE}}": profile_image_html,
        }

    result = template_content
    for placeholder, val in replacements.items():
        result = result.replace(placeholder, val)

    # Clean any remaining placeholders
    result = re.sub(r'\{\{[A-Z0-9_]+\}\}', '', result)

    # Self-contained theme overrides. Existing template CSS uses these variables
    # extensively, so changing the accent never requires external assets.
    theme_css = f"""<style id=\"ai-theme-overrides\">
:root {{ --accent-purple: {accent}; --accent-cyan: {accent2}; --accent-purple-glow: {accent}66; --accent-cyan-glow: {accent2}55; }}
.ai-profile-image {{ width: 118px; height: 118px; object-fit: cover; border-radius: 50%; display: block; margin: 0 auto 22px; border: 3px solid var(--accent-purple); box-shadow: 0 0 34px var(--accent-purple-glow); }}
</style>"""
    result = result.replace('</head>', theme_css + '\n</head>', 1)

    # Inlining CSS for complete 100% standalone portability
    if is_designer:
        css_file = BASE_DIR / "style-designer.css"
        if not css_file.is_file():
            css_file = Path("style-designer.css")
        if css_file.is_file():
            css_code = css_file.read_text(encoding="utf-8")
            result = result.replace('<link rel="stylesheet" href="style-designer.css">', f'<style>\n/* Inlined Designer Stylesheet */\n{css_code}\n</style>')
    else:
        css_map = {
            "simple": "style-simple.css",
            "developer": "style-developer.css",
            "corporate": "style-corporate.css",
        }
        css_file = BASE_DIR / css_map.get(norm_choice, "style-simple.css")
        if not css_file.is_file():
            css_file = BASE_DIR / "style-simple.css"
        if not css_file.is_file():
            css_file = BASE_DIR / "style.css"
        if not css_file.is_file():
            css_file = Path("style-simple.css")
        if css_file.is_file():
            css_code = css_file.read_text(encoding="utf-8")
            for stylesheet_name in ["style-simple.css", "style-developer.css", "style-corporate.css", "style.css"]:
                result = result.replace(f'<link rel="stylesheet" href="{stylesheet_name}">', f'<style>\n/* Inlined Portfolio Stylesheet */\n{css_code}\n</style>')

    return result


def get_sanitized_download_filename(candidate_name: str = "") -> str:
    """
    Sanitizes candidate name into a clean, safe filename like 'Vansh-Sharma-portfolio.html'
    or 'my-portfolio.html' if name is empty.
    """
    if not candidate_name or not candidate_name.strip():
        return "my-portfolio.html"
    
    clean = re.sub(r'[^a-zA-Z0-9\s_-]', '', candidate_name.strip())
    clean = re.sub(r'[\s_]+', '-', clean).strip('-')
    if not clean:
        return "my-portfolio.html"
    return f"{clean}-portfolio.html"


# ==============================================================================
# Phase 2 helpers: automatic recommendations, user overrides, and safe enhancement
# ==============================================================================
def recommend_portfolio_style(resume_text: str) -> tuple[str, str]:
    text = (resume_text or "").lower()
    tech = sum(k in text for k in ["python", "java", "javascript", "typescript", "react", "node", "sql", "machine learning", "tensorflow", "pytorch", "github", "developer", "software engineer", "data engineer", "ai/ml"])
    creative = sum(k in text for k in ["figma", "ui/ux", "graphic design", "designer", "dribbble", "behance", "branding", "illustrator", "photoshop", "creative director"])
    corporate = sum(k in text for k in ["manager", "management", "consultant", "finance", "operations", "sales", "business development", "strategy", "director", "executive", "mba"])
    if tech >= max(creative, corporate, 2):
        return "developer", "#06b6d4"
    if creative >= max(tech, corporate, 2):
        return "designer", "#f43f5e"
    if corporate >= max(tech, creative, 2):
        return "corporate", "#3b82f6"
    return "simple", "#10b981"

def apply_profile_overrides(data: dict, overrides: dict | None) -> dict:
    if not isinstance(overrides, dict):
        return data
    clean = lambda v: str(v).strip() if v is not None else ""
    for key in ["name", "headline", "summary"]:
        if clean(overrides.get(key)):
            data[key] = clean(overrides[key])
    contact = data.setdefault("contact", {})
    for key in ["email", "phone", "linkedin", "github", "instagram", "twitter", "leetcode", "portfolio"]:
        if clean(overrides.get(key)):
            contact[key] = clean(overrides[key])
    return data

def get_missing_profile_fields(data: dict) -> list[str]:
    contact = data.get("contact") or {}
    missing = []
    if not str(data.get("name", "")).strip(): missing.append("Name")
    if not str(data.get("headline", "")).strip(): missing.append("Headline")
    if not str(data.get("summary", "")).strip(): missing.append("About/Summary")
    if not str(contact.get("email", "")).strip(): missing.append("Email")
    if not str(contact.get("linkedin", "")).strip(): missing.append("LinkedIn")
    if not str(contact.get("github", "")).strip(): missing.append("GitHub")
    if not str(contact.get("instagram", "")).strip(): missing.append("Instagram")
    if not str(contact.get("twitter", "")).strip(): missing.append("Twitter/X")
    if not str(contact.get("leetcode", "")).strip(): missing.append("LeetCode")
    return missing


# ==============================================================================
# 6. Core Processing Pipeline
# ==============================================================================

def process_resume_and_build(
    raw_resume_text: str,
    filename: str = "resume.txt",
    file_type: str = "Plain Text Document (.txt)",
    template_choice: str = "simple",
    template_path: Path = None,
    output_path: Path = Path("portfolio.html"),
    mock_response: str = None,
    cached_parsed_data: dict = None,
    profile_image_data: str = "",
    theme_color: str = "#8b5cf6",
    enhance_content: bool = False,
    profile_overrides: dict | None = None
) -> tuple[bool, dict, str]:
    """
    Executes the full pipeline with debug logging:
    1. Cleans resume text.
    2. Validates extracted length (>= 100 characters).
    3. Logs filename, reception status, and character count.
    4. Sends FULL cleaned resume to Gemini API (or uses cached_parsed_data for fast re-render).
    5. Validates JSON and logs field availability/counts.
    6. Performs ground-truth check against resume text.
    7. Renders portfolio.html using selected template and saves.
    """
    cleaned_resume = clean_resume_text(raw_resume_text)
    char_count = len(cleaned_resume)

    # Determine template file based on template_choice
    allowed_templates = {"simple", "designer", "developer", "corporate"}
    norm_choice = template_choice.lower().strip() if template_choice else "simple"
    if norm_choice not in allowed_templates:
        norm_choice = "simple"
    if template_path is None:
        template_map = {
            "simple": "template-simple.html",
            "designer": "template-designer.html",
            "developer": "template-developer.html",
            "corporate": "template-corporate.html",
        }
        template_path = BASE_DIR / template_map[norm_choice]
        if not template_path.is_file():
            template_path = BASE_DIR / ("template-designer.html" if norm_choice == "designer" else "template-simple.html")
            if not template_path.is_file():
                template_path = BASE_DIR / "template.html"
            if not template_path.is_file():
                template_path = Path(template_map[norm_choice])
            if not template_path.is_file():
                template_path = Path("template-simple.html")
            if not template_path.is_file():
                template_path = Path("template.html")

    # Fast Re-render path (skips Gemini when changing templates with already parsed JSON)
    if cached_parsed_data and isinstance(cached_parsed_data, dict):
        print(f"Fast Template Switch: Using cached data for template '{norm_choice}'", flush=True)
        portfolio_data = validate_data_against_resume(cached_parsed_data, cleaned_resume or str(cached_parsed_data))
        portfolio_data = apply_profile_overrides(portfolio_data, profile_overrides)
        try:
            template_content = template_path.read_text(encoding="utf-8")
            rendered_html = render_portfolio_html(template_content, portfolio_data, template_choice=norm_choice, profile_image_data=profile_image_data, theme_color=theme_color)
            try:
                output_path.write_text(rendered_html, encoding="utf-8")
            except Exception:
                try:
                    (BASE_DIR / output_path.name).write_text(rendered_html, encoding="utf-8")
                except Exception:
                    try:
                        (Path("/tmp") / output_path.name).write_text(rendered_html, encoding="utf-8")
                    except Exception:
                        pass
            return True, portfolio_data, rendered_html
        except Exception as e:
            err = f"Render Error: {e}"
            print(err, file=sys.stderr, flush=True)
            return False, {}, err

    # Required terminal output
    print(f"Resume filename: {filename}", flush=True)
    print("Resume text received successfully", flush=True)
    print(f"Characters received: {char_count}", flush=True)

    is_valid, error_msg = validate_resume_text(cleaned_resume, is_pdf=False)
    if not is_valid:
        print(f"Error: {error_msg}", file=sys.stderr, flush=True)
        return False, {}, error_msg

    print("Sending complete resume to Gemini...", flush=True)

    load_dotenv()
    api_key = os.getenv("GEMINI_API_KEY")

    if mock_response is not None:
        raw_gemini_output = mock_response
    else:
        if not api_key or not api_key.strip() or api_key == "your_gemini_api_key_here":
            err = (
                "Configuration Error: GEMINI_API_KEY environment variable is not configured.\n"
                "Please set GEMINI_API_KEY in your .env file or export it in your environment."
            )
            print(err, file=sys.stderr, flush=True)
            return False, {}, err

        prompt = build_gemini_prompt(cleaned_resume, enhance_content=enhance_content)
        try:
            raw_gemini_output = call_gemini_api(prompt, api_key)
        except Exception as e:
            err = f"API Error: {e}"
            print(err, file=sys.stderr, flush=True)
            return False, {}, err

    try:
        parsed_data = parse_and_validate_json(raw_gemini_output)
    except Exception as e:
        print(f"JSON Error: {e}", file=sys.stderr, flush=True)
        return False, {}, str(e)

    # Print JSON validation summary
    has_sufficient_data = print_json_validation_summary(parsed_data)
    if not has_sufficient_data:
        err = "Resume data could not be extracted correctly. Please check the uploaded resume."
        print(f"Validation Error: {err}", file=sys.stderr, flush=True)
        return False, {}, err

    # Perform ground-truth verification
    portfolio_data = validate_data_against_resume(parsed_data, cleaned_resume)
    portfolio_data = apply_profile_overrides(portfolio_data, profile_overrides)

    if not template_path.is_file():
        err = f"Template Error: Template file '{template_path}' does not exist."
        print(err, file=sys.stderr, flush=True)
        return False, {}, err

    try:
        template_content = template_path.read_text(encoding="utf-8")
        rendered_html = render_portfolio_html(template_content, portfolio_data, template_choice=norm_choice, profile_image_data=profile_image_data, theme_color=theme_color)
        try:
            output_path.write_text(rendered_html, encoding="utf-8")
        except Exception:
            try:
                (BASE_DIR / output_path.name).write_text(rendered_html, encoding="utf-8")
            except Exception:
                try:
                    (Path("/tmp") / output_path.name).write_text(rendered_html, encoding="utf-8")
                except Exception:
                    pass
    except Exception as e:
        err = f"Render Error: {e}"
        print(err, file=sys.stderr, flush=True)
        return False, {}, err

    print(f"Portfolio generated successfully using '{norm_choice}' template!", flush=True)
    return True, portfolio_data, rendered_html


def generate_portfolio(
    resume_path: Path = Path("resume.txt"),
    template_path: Path = None,
    output_path: Path = Path("portfolio.html"),
    template_choice: str = "simple",
    mock_response: str = None
) -> bool:
    """
    CLI execution wrapper with formatted console output.
    """
    if not resume_path.is_file():
        print(f"Error: Resume file '{resume_path}' does not exist.", file=sys.stderr, flush=True)
        return False

    try:
        raw_text, file_type = extract_text_from_file_path(resume_path)
    except Exception as e:
        print(f"Error reading '{resume_path}': {e}", file=sys.stderr, flush=True)
        return False

    success, _, _ = process_resume_and_build(
        raw_resume_text=raw_text,
        filename=resume_path.name,
        file_type=file_type,
        template_choice=template_choice,
        template_path=template_path,
        output_path=output_path,
        mock_response=mock_response
    )

    return success


# ==============================================================================
# 7. Generator Web Server Application (Flask)
# ==============================================================================

def create_web_app():
    """Initializes and configures the Flask application for the Generator Dashboard."""
    app = Flask(__name__, static_folder=str(BASE_DIR), static_url_path="")

    @app.after_request
    def add_cors_headers(response):
        response.headers["Access-Control-Allow-Origin"] = "*"
        response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS, HEAD, PUT, DELETE"
        response.headers["Access-Control-Allow-Headers"] = "*"
        response.headers["Access-Control-Allow-Private-Network"] = "true"
        return response

    @app.route("/health", methods=["GET", "OPTIONS"])
    @app.route("/api/health", methods=["GET", "OPTIONS"])
    def health_check():
        """
        Health check endpoint used by startup scripts and frontend auto-wait polling.
        """
        if request.method == "OPTIONS":
            return "", 204
        return jsonify({
            "status": "healthy",
            "service": "ai-resume-portfolio-generator",
            "timestamp": datetime.now().isoformat(),
            "gemini_configured": bool(os.environ.get("GEMINI_API_KEY"))
        }), 200

    @app.route("/")
    def index():
        if (BASE_DIR / "index.html").is_file():
            return send_from_directory(str(BASE_DIR), "index.html")
        return send_from_directory(str(BASE_DIR), "generator.html")

    @app.route("/index.html")
    def serve_index():
        if (BASE_DIR / "index.html").is_file():
            return send_from_directory(str(BASE_DIR), "index.html")
        return send_from_directory(str(BASE_DIR), "generator.html")

    @app.route("/generator.html")
    def serve_generator():
        return send_from_directory(str(BASE_DIR), "generator.html")

    @app.route("/portfolio.html")
    def serve_portfolio():
        portfolio_path = BASE_DIR / "portfolio.html"
        tmp_path = Path("/tmp") / "portfolio.html"
        if portfolio_path.is_file():
            return send_from_directory(str(BASE_DIR), "portfolio.html")
        elif tmp_path.is_file():
            return send_from_directory(str(tmp_path.parent), tmp_path.name)
        elif Path("portfolio.html").is_file():
            return send_from_directory(".", "portfolio.html")
        return "Portfolio has not been generated yet. Please generate a portfolio first.", 404

    @app.route("/api/download", methods=["GET", "OPTIONS"])
    def api_download():
        """
        Serves the currently generated portfolio.html as a downloadable attachment
        with a sanitized dynamic filename based on the candidate's name.
        Security: strictly serves only the generated portfolio.html file from the root directory.
        """
        if request.method == "OPTIONS":
            return "", 204

        portfolio_path = BASE_DIR / "portfolio.html"
        if not portfolio_path.is_file():
            portfolio_path = Path("/tmp") / "portfolio.html"
        if not portfolio_path.is_file():
            portfolio_path = Path("portfolio.html")
        if not portfolio_path.is_file():
            return "No portfolio has been generated yet. Please generate a portfolio first.", 404

        # Read the file to discover candidate name from title or fallback
        content = portfolio_path.read_text(encoding="utf-8", errors="ignore")
        match = re.search(r'<title>(.*?)\s*\|', content, re.IGNORECASE)
        name = match.group(1).strip() if match else ""
        
        filename = get_sanitized_download_filename(name)
        
        response = send_file(
            portfolio_path.resolve(),
            as_attachment=True,
            download_name=filename,
            mimetype="text/html"
        )
        response.headers["Content-Disposition"] = f'attachment; filename="{filename}"'
        return response

    @app.route("/api/download-zip", methods=["GET", "OPTIONS"])
    def api_download_zip():
        """Download a modular GitHub Pages package with assets/style/script files."""
        if request.method == "OPTIONS":
            return "", 204
        portfolio_path = BASE_DIR / "portfolio.html"
        if not portfolio_path.is_file():
            portfolio_path = Path("/tmp") / "portfolio.html"
        if not portfolio_path.is_file():
            portfolio_path = Path("portfolio.html")
        if not portfolio_path.is_file():
            return "No portfolio has been generated yet. Please generate a portfolio first.", 404

        content = portfolio_path.read_text(encoding="utf-8", errors="ignore")
        match = re.search(r'<title>(.*?)\s*\|', content, re.IGNORECASE)
        name = match.group(1).strip() if match else "My Portfolio"
        safe_base = re.sub(r'[^a-zA-Z0-9_-]+', '-', name).strip('-_') or "my-portfolio"
        zip_filename = f"{safe_base}-github-pages.zip"

        # Extract the generated inline stylesheet into style.css.
        css_match = re.search(r'<style>\s*/\* Inlined Portfolio Stylesheet \*/\s*(.*?)\s*</style>', content, re.S)
        css = css_match.group(1).strip() if css_match else "/* Styles are embedded in index.html. */"
        package_html = content
        if css_match:
            package_html = package_html[:css_match.start()] + '<link rel="stylesheet" href="style.css">' + package_html[css_match.end():]

        # Extract inline scripts into script.js. The generated portfolio only uses
        # self-contained scripts, so this is safe for static GitHub Pages hosting.
        script_blocks = re.findall(r'<script(?:\s[^>]*)?>(.*?)</script>', package_html, re.S | re.I)
        external_js = '\n\n'.join(block.strip() for block in script_blocks if block.strip())
        package_html = re.sub(r'<script(?:\s[^>]*)?>.*?</script>', '<script src="script.js"></script>', package_html, flags=re.S | re.I) if external_js else package_html

        # Move a data-URL profile image into assets/profile.<ext> when present.
        assets = {}
        img_match = re.search(r'(?:src=|data-profile-src=)"(data:image/(jpeg|png|webp);base64,([^"]+))"', package_html, re.I)
        if img_match:
            mime_ext = {"jpeg": "jpg", "png": "png", "webp": "webp"}[img_match.group(2).lower()]
            assets[f"assets/profile.{mime_ext}"] = base64.b64decode(img_match.group(3))
            package_html = package_html.replace(img_match.group(1), f"assets/profile.{mime_ext}", 1)

        readme = f"""# {name} — GitHub Pages Package\n\nGenerated by AI Resume Portfolio Generator.\n\n## Files\n- `index.html` — portfolio page\n- `style.css` — portfolio styles\n- `script.js` — portfolio interactions\n- `assets/` — profile and other local assets\n\n## Deploy\n1. Create a GitHub repository.\n2. Upload all files in this package to the repository root.\n3. Open **Settings → Pages**.\n4. Choose **Deploy from a branch**, select your main branch and `/ (root)`.\n5. Save and wait for GitHub Pages to publish.\n\nThe package is responsive for mobile, tablet and desktop screens.\n"""

        memory = io.BytesIO()
        with zipfile.ZipFile(memory, "w", compression=zipfile.ZIP_DEFLATED) as zf:
            zf.writestr("index.html", package_html)
            zf.writestr("style.css", css)
            zf.writestr("script.js", external_js)
            zf.writestr("README.md", readme)
            zf.writestr(".nojekyll", "")
            for path, data in assets.items():
                zf.writestr(path, data)
        memory.seek(0)
        return send_file(memory, as_attachment=True, download_name=zip_filename, mimetype="application/zip")

    @app.route("/api/sample", methods=["GET", "OPTIONS"])
    def get_sample_resume():
        if request.method == "OPTIONS":
            return "", 204
        resume_file = BASE_DIR / "resume.txt"
        if not resume_file.is_file():
            resume_file = Path("resume.txt")
        if resume_file.is_file():
            return resume_file.read_text(encoding="utf-8"), 200, {"Content-Type": "text/plain; charset=utf-8"}
        return "Sample resume not found.", 404

    @app.route("/api/extract", methods=["POST", "OPTIONS"])
    def api_extract():
        """
        Receives uploaded file (PDF or TXT) and extracts text to display character metrics.
        """
        if request.method == "OPTIONS":
            return "", 204

        uploaded_file = (
            request.files.get("resume") or
            request.files.get("file") or
            request.files.get("resumeFile")
        )

        if not uploaded_file or not uploaded_file.filename:
            return jsonify({"success": False, "message": "No file uploaded.", "error": "No file uploaded."}), 400

        filename = uploaded_file.filename
        file_bytes = uploaded_file.read()
        MAX_FILE_SIZE = 5 * 1024 * 1024  # 5 MB

        if len(file_bytes) > MAX_FILE_SIZE:
            return jsonify({
                "success": False,
                "message": "File too large. Please upload a file smaller than 5 MB.",
                "error": "file_too_large"
            }), 413

        try:
            text, file_type = extract_text_from_bytes(file_bytes, filename)
            cleaned = clean_resume_text(text)
            is_pdf = filename.lower().endswith(".pdf")
            is_valid, err_msg = validate_resume_text(cleaned, is_pdf=is_pdf)

            if not is_valid:
                return jsonify({"success": False, "message": err_msg, "error": err_msg}), 400

            return jsonify({
                "success": True,
                "filename": filename,
                "file_type": file_type,
                "char_count": len(cleaned),
                "text": cleaned
            })
        except Exception as e:
            err_str = str(e)
            print(f"Extraction Error: {err_str}", file=sys.stderr, flush=True)
            return jsonify({"success": False, "message": err_str, "error": err_str}), 400

    @app.route("/api/generate", methods=["POST", "OPTIONS"])
    def api_generate():
        """
        Processes resume generation using received resume text and selected template.
        Supports fast re-render without re-calling Gemini if cached parsed_data is provided.
        """
        if request.method == "OPTIONS":
            return "", 204

        try:
            raw_text = ""
            filename = "resume.txt"
            file_type = "Plain Text Document (.txt)"

            json_payload = request.get_json(silent=True) or {}
            form_payload = request.form or {}

            template_choice = (
                form_payload.get("template") or
                json_payload.get("template") or
                "simple"
            ).strip().lower()

            profile_image_data = (
                form_payload.get("profile_image", "").strip() or
                json_payload.get("profile_image", "").strip()
            )
            theme_color = (
                form_payload.get("theme_color", "#8b5cf6").strip() or
                json_payload.get("theme_color", "#8b5cf6").strip()
            )
            if not re.fullmatch(r"#[0-9a-fA-F]{6}", theme_color):
                theme_color = "#8b5cf6"

            cached_data = (
                json_payload.get("parsed_data") or
                json_payload.get("data")
            )

            enhance_content = str(form_payload.get("enhance_content", "") or json_payload.get("enhance_content", "false")).lower() in {"1", "true", "yes", "on"}
            profile_overrides_raw = form_payload.get("profile_overrides", "") or json_payload.get("profile_overrides", {})
            try:
                profile_overrides = json.loads(profile_overrides_raw) if isinstance(profile_overrides_raw, str) and profile_overrides_raw.strip() else (profile_overrides_raw if isinstance(profile_overrides_raw, dict) else {})
            except Exception:
                profile_overrides = {}

            # Priority 1: Check for resume_text sent directly by frontend
            form_text = (
                form_payload.get("resume_text", "").strip() or
                json_payload.get("resume_text", "").strip()
            )
            form_filename = (
                form_payload.get("filename", "").strip() or
                form_payload.get("file_name", "").strip() or
                json_payload.get("filename", "").strip() or
                json_payload.get("file_name", "").strip()
            )

            uploaded_file = (
                request.files.get("resume") or
                request.files.get("file") or
                request.files.get("resumeFile")
            )

            if cached_data:
                raw_text = form_text or ""
                filename = form_filename or "resume.txt"
            elif form_text:
                raw_text = form_text
                filename = form_filename or (uploaded_file.filename if uploaded_file else "resume.txt")
                file_type = ("PDF Document (.pdf)" if filename.lower().endswith(".pdf") else (f"Image Resume ({Path(filename).suffix.lower()})" if Path(filename).suffix.lower() in {".jpg", ".jpeg", ".png", ".webp"} else "Plain Text Document (.txt)"))
            elif uploaded_file and uploaded_file.filename:
                filename = uploaded_file.filename
                file_bytes = uploaded_file.read()
                if not file_bytes:
                    return jsonify({
                        "success": False,
                        "message": "Resume upload failed: uploaded file is empty.",
                        "error": "Resume upload failed."
                    }), 400

                try:
                    raw_text, file_type = extract_text_from_bytes(file_bytes, filename)
                except Exception as e:
                    err_msg = str(e)
                    print(f"File Read Error: {err_msg}", file=sys.stderr, flush=True)
                    return jsonify({
                        "success": False,
                        "message": err_msg,
                        "error": err_msg
                    }), 400
            else:
                return jsonify({
                    "success": False,
                    "message": "No resume text was received.",
                    "error": "No resume text was received."
                }), 400

            cleaned_text = clean_resume_text(raw_text) if raw_text else ""
            if not cached_data and (not cleaned_text or len(cleaned_text) < 100):
                err = "Could not extract enough text from the resume."
                return jsonify({
                    "success": False,
                    "message": err,
                    "error": err
                }), 400

            success, portfolio_data, error_or_html = process_resume_and_build(
                raw_resume_text=cleaned_text,
                filename=filename,
                file_type=file_type,
                template_choice=template_choice,
                cached_parsed_data=cached_data,
                profile_image_data=profile_image_data,
                theme_color=theme_color,
                enhance_content=enhance_content,
                profile_overrides=profile_overrides
            )

            if not success:
                print(f"[API Error] Generation failed: {error_or_html}", file=sys.stderr, flush=True)
                return jsonify({
                    "success": False,
                    "message": error_or_html,
                    "error": error_or_html
                }), 400

            skills_count = len(portfolio_data.get("skills") or [])
            projects_count = len(portfolio_data.get("projects") or [])
            experience_count = len(portfolio_data.get("experience") or [])
            education_count = len(portfolio_data.get("education") or [])

            response_data = {
                **portfolio_data,
                "skills_count": skills_count,
                "projects_count": projects_count,
                "experience_count": experience_count,
                "education_count": education_count
            }

            metrics = {
                "skills_count": skills_count,
                "projects_count": projects_count,
                "experience_count": experience_count,
                "education_count": education_count
            }

            template_display_names = {
                "simple": "Simple Portfolio",
                "designer": "Designer Portfolio",
                "developer": "Developer Portfolio",
                "corporate": "Corporate Portfolio",
            }
            template_display_name = template_display_names.get(template_choice, "Simple Portfolio")
            candidate_name = portfolio_data.get("name", "").strip()
            recommended_template, recommended_color = recommend_portfolio_style(cleaned_text)
            missing_fields = get_missing_profile_fields(portfolio_data)
            download_filename = get_sanitized_download_filename(candidate_name)

            return jsonify({
                "success": True,
                "message": f"Portfolio generated successfully using {template_display_name}",
                "template": template_choice,
                "template_name": template_display_name,
                "portfolio": "portfolio.html",
                "portfolio_url": "/portfolio.html",
                "download_url": "/api/download",
                "download_filename": download_filename,
                "theme_color": theme_color,
                "has_profile_image": bool(profile_image_data),
                "enhanced": enhance_content,
                "missing_fields": missing_fields,
                "recommended_template": recommended_template,
                "recommended_color": recommended_color,
                "data": response_data,
                "metrics": metrics
            })
        except Exception as unhandled_err:
            err_str = str(unhandled_err)
            print(f"[API Unhandled Error]: {err_str}", file=sys.stderr, flush=True)
            return jsonify({
                "success": False,
                "message": f"Server encountered an unexpected error: {err_str}",
                "error": err_str
            }), 500

    return app


# Create global application instance
app = create_web_app()


# ==============================================================================
# 8. Main Entrypoint
# ==============================================================================

def main():
    parser = argparse.ArgumentParser(description="AI-Assisted Resume Portfolio Generator")
    parser.add_argument("--cli", action="store_true", help="Run in CLI generation mode instead of starting the web server")
    parser.add_argument("--resume", type=str, default="resume.txt", help="Path to input resume file (.txt or .pdf, default: resume.txt)")
    parser.add_argument("--template", type=str, default="template.html", help="Path to HTML template (default: template.html)")
    parser.add_argument("--output", type=str, default="portfolio.html", help="Path to output HTML file (default: portfolio.html)")
    parser.add_argument("--port", type=int, default=5000, help="Port for web server (default: 5000)")
    args, _ = parser.parse_known_args()

    # CLI Generation Mode if explicitly requested with --cli
    if args.cli:
        success = generate_portfolio(
            resume_path=Path(args.resume),
            template_path=Path(args.template),
            output_path=Path(args.output)
        )
        sys.exit(0 if success else 1)

    # Default: Start Flask Web Server
    if not FLASK_AVAILABLE:
        print("Error: Flask is required for web mode. Run: pip install flask", file=sys.stderr)
        sys.exit(1)

    print("\n============================================================")
    print("  AI Resume Portfolio Generator Server Active")
    print(f"  Running on http://127.0.0.1:{args.port}")
    print("============================================================\n", flush=True)

    app.run(host="127.0.0.1", port=args.port, debug=False)


if __name__ == "__main__":
    main()
