"""
Layer 1: Smart Resume Parser
Detects sections (Skills, Experience, Education, Projects) and extracts structured data.
Runs locally — no API calls.
"""
import re
from dataclasses import dataclass, field
from typing import List, Dict, Optional
from utils.logger import get_logger

logger = get_logger(__name__)

# Common section header patterns (case-insensitive)
SECTION_PATTERNS = {
    "summary": r"(?i)\b(summary|objective|about\s*me|profile|professional\s*summary)\b",
    "skills": r"(?i)\b(skills|technical\s*skills|core\s*competencies|technologies|tech\s*stack)\b",
    "experience": r"(?i)\b(experience|work\s*experience|professional\s*experience|employment|work\s*history)\b",
    "education": r"(?i)\b(education|academic|qualification|degree)\b",
    "projects": r"(?i)\b(projects|personal\s*projects|key\s*projects)\b",
    "certifications": r"(?i)\b(certifications?|licenses?|credentials?)\b",
    "achievements": r"(?i)\b(achievements?|awards?|honors?|accomplishments?)\b",
    "publications": r"(?i)\b(publications?|patents?|research)\b",
}

# Date patterns for extracting employment timelines
DATE_PATTERN = re.compile(
    r"(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|"
    r"Jul(?:y)?|Aug(?:ust)?|Sep(?:t(?:ember)?)?|Oct(?:ober)?|Nov(?:ember)?|"
    r"Dec(?:ember)?)\s*\d{4}",
    re.IGNORECASE
)

YEAR_PATTERN = re.compile(r"\b((?:19|20)\d{2})\b")

@dataclass
class ParsedResume:
    raw_text: str = ""
    summary: str = ""
    skills_text: str = ""
    experience_text: str = ""
    education_text: str = ""
    projects_text: str = ""
    certifications_text: str = ""
    achievements_text: str = ""
    publications_text: str = ""
    extracted_skills: List[str] = field(default_factory=list)
    employment_dates: List[str] = field(default_factory=list)
    years_mentioned: List[int] = field(default_factory=list)

def parse_resume(raw_text: str) -> ParsedResume:
    """Parse raw resume text into structured sections."""
    logger.info("Starting smart resume parsing with section detection.")
    
    parsed = ParsedResume(raw_text=raw_text)
    lines = raw_text.split("\n")
    
    # Detect section boundaries
    section_map: Dict[int, str] = {}
    for i, line in enumerate(lines):
        stripped = line.strip()
        if not stripped or len(stripped) > 80:  # Skip blank or very long lines
            continue
        for section_name, pattern in SECTION_PATTERNS.items():
            if re.search(pattern, stripped):
                section_map[i] = section_name
                break
    
    # Sort section start lines
    sorted_sections = sorted(section_map.items())
    
    # Extract text for each section
    for idx, (start_line, section_name) in enumerate(sorted_sections):
        # End line is either next section or end of document
        if idx + 1 < len(sorted_sections):
            end_line = sorted_sections[idx + 1][0]
        else:
            end_line = len(lines)
        
        section_content = "\n".join(lines[start_line + 1 : end_line]).strip()
        
        attr_name = f"{section_name}_text" if section_name != "summary" else "summary"
        if hasattr(parsed, attr_name):
            setattr(parsed, attr_name, section_content)
    
    # If no sections detected, treat entire text as summary + experience
    if not sorted_sections:
        logger.warning("No sections detected, treating full text as unstructured resume.")
        parsed.summary = raw_text[:500]
        parsed.experience_text = raw_text
    
    # Extract skill tokens from skills section
    if parsed.skills_text:
        parsed.extracted_skills = _extract_skill_tokens(parsed.skills_text)
    
    # Extract employment dates from experience section
    parsed.employment_dates = DATE_PATTERN.findall(raw_text)
    parsed.years_mentioned = [int(y) for y in YEAR_PATTERN.findall(raw_text)]
    
    logger.info(
        f"Parsed resume: {len(sorted_sections)} sections detected, "
        f"{len(parsed.extracted_skills)} skills extracted, "
        f"{len(parsed.employment_dates)} dates found."
    )
    return parsed

def _extract_skill_tokens(skills_text: str) -> List[str]:
    """Extract individual skill tokens from a skills section."""
    # Split by common delimiters: commas, pipes, bullets, newlines, semicolons
    raw_tokens = re.split(r"[,|•◦\n;]+", skills_text)
    
    skills = []
    for token in raw_tokens:
        # First, remove common category prefixes like "Languages: ", "Frontend: ", etc.
        # We do this BEFORE stripping punctuation so the colon is still there.
        token = re.sub(r"^[\w\s&/]+\s*:\s*", "", token.strip())
        
        # Clean up remaining token: remove non-alphanumeric except for common tech symbols
        cleaned = re.sub(r"[^\w\s.#+\-/]", "", token).strip()
        
        if cleaned and len(cleaned) > 1 and len(cleaned) < 60:
            # Avoid adding things that are just "etc" or "and"
            if cleaned.lower() not in ["etc", "and", "with", "other", "using"]:
                skills.append(cleaned)
    
    # Deduplicate while preserving order
    return list(dict.fromkeys(skills))
