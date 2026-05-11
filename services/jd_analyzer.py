"""
Layer 2: Job Description Analyzer
Extracts required vs preferred skills and experience requirements from JD text.
Runs locally — no API calls.
"""
import re
from dataclasses import dataclass, field
from typing import List
from utils.logger import get_logger

logger = get_logger(__name__)

# Patterns indicating required vs preferred
REQUIRED_INDICATORS = re.compile(
    r"(?i)(must\s*have|required|mandatory|essential|minimum|core\s*requirement|"
    r"key\s*responsibilit|you\s*will\s*need|expected|strong\s*proficiency|"
    r"deep\s*expertise|extensive\s*experience)",
)

PREFERRED_INDICATORS = re.compile(
    r"(?i)(nice\s*to\s*have|preferred|bonus|good\s*to\s*have|desirable|plus|"
    r"advantageous|familiarity\s*with|exposure\s*to|optional)",
)

EXPERIENCE_YEARS_PATTERN = re.compile(
    r"(\d+)\+?\s*(?:years?|yrs?)\s*(?:of)?\s*(?:experience|exp)?",
    re.IGNORECASE
)

@dataclass
class ParsedJobDescription:
    raw_text: str = ""
    required_skills: List[str] = field(default_factory=list)
    preferred_skills: List[str] = field(default_factory=list)
    all_skills: List[str] = field(default_factory=list)
    min_experience_years: int = 0
    role_title: str = ""

def analyze_jd(jd_text: str) -> ParsedJobDescription:
    """Parse a job description into structured requirements."""
    logger.info("Analyzing job description for requirements extraction.")
    
    parsed = ParsedJobDescription(raw_text=jd_text)
    
    # Extract role title (first non-empty line or line after "Title:")
    lines = [l.strip() for l in jd_text.split("\n") if l.strip()]
    for line in lines[:5]:
        title_match = re.match(r"(?:Title|Role|Position)\s*[:\-]\s*(.+)", line, re.IGNORECASE)
        if title_match:
            parsed.role_title = title_match.group(1).strip()
            break
    if not parsed.role_title and lines:
        parsed.role_title = lines[0][:80]
    
    # Extract experience requirement
    exp_matches = EXPERIENCE_YEARS_PATTERN.findall(jd_text)
    if exp_matches:
        parsed.min_experience_years = max(int(y) for y in exp_matches)
    
    # Split JD into blocks and classify
    blocks = _split_into_blocks(jd_text)
    
    current_category = "required"  # default assumption
    
    for block_header, block_content in blocks:
        # Determine category from header
        if PREFERRED_INDICATORS.search(block_header):
            current_category = "preferred"
        elif REQUIRED_INDICATORS.search(block_header):
            current_category = "required"
        
        # Extract skill-like tokens from block content
        skills = _extract_jd_skills(block_content)
        
        if current_category == "preferred":
            parsed.preferred_skills.extend(skills)
        else:
            parsed.required_skills.extend(skills)
    
    # ALWAYS also scan the full JD text to catch skills outside structured blocks
    full_scan_skills = _extract_jd_skills(jd_text)
    for skill in full_scan_skills:
        if skill not in parsed.required_skills and skill not in parsed.preferred_skills:
            parsed.required_skills.append(skill)
    
    # If still nothing, use the full scan
    if not parsed.required_skills and not parsed.preferred_skills:
        parsed.required_skills = full_scan_skills
    
    parsed.all_skills = list(set(parsed.required_skills + parsed.preferred_skills))
    
    # Deduplicate
    parsed.required_skills = list(dict.fromkeys(parsed.required_skills))
    parsed.preferred_skills = list(dict.fromkeys(parsed.preferred_skills))
    
    logger.info(
        f"JD Analysis: {len(parsed.required_skills)} required skills, "
        f"{len(parsed.preferred_skills)} preferred skills, "
        f"min experience: {parsed.min_experience_years} years."
    )
    return parsed

def _split_into_blocks(text: str) -> List[tuple]:
    """Split JD into header-content blocks."""
    lines = text.split("\n")
    blocks = []
    current_header = ""
    current_content_lines = []
    
    for line in lines:
        stripped = line.strip()
        # Detect section headers (short lines with keywords or ending with colon)
        is_header = (
            len(stripped) < 80
            and (stripped.endswith(":") or stripped.endswith("—"))
            or REQUIRED_INDICATORS.search(stripped)
            or PREFERRED_INDICATORS.search(stripped)
            or re.match(r"^[#⚙️🧠🧩⭐•\-]+\s*\w", stripped)
        )
        
        if is_header and stripped:
            if current_header or current_content_lines:
                blocks.append((current_header, "\n".join(current_content_lines)))
            current_header = stripped
            current_content_lines = []
        else:
            current_content_lines.append(stripped)
    
    # Final block
    if current_header or current_content_lines:
        blocks.append((current_header, "\n".join(current_content_lines)))
    
    return blocks

def _extract_jd_skills(text: str) -> List[str]:
    """Extract skill-like tokens from JD text."""
    # Common tech skills and patterns
    TECH_PATTERNS = re.compile(
        r"\b("
        r"Python|JavaScript|TypeScript|Java|Go|Rust|C\+\+|C#|PHP|Ruby|Swift|Kotlin|"
        r"React(?:\.js)?|Next(?:\.js)?|Vue(?:\.js)?|Angular|Node(?:\.js)?|Express(?:\.js)?|"
        r"Flask|FastAPI|Django|Laravel|Spring|Rails|"
        r"AWS|Azure|GCP|Docker|Kubernetes|Terraform|Ansible|Jenkins|"
        r"PostgreSQL|MongoDB|MySQL|Redis|Elasticsearch|DynamoDB|"
        r"Git|Linux|CI/CD|GraphQL|REST|gRPC|"
        r"LangChain|LangGraph|TensorFlow|PyTorch|"
        r"Machine\s*Learning|Deep\s*Learning|NLP|Computer\s*Vision|"
        r"HTML|CSS|TailwindCSS|SASS|"
        r"Celery|RabbitMQ|Kafka|"
        r"Datadog|Splunk|Prometheus|Grafana|"
        r"Spinnaker|ArgoCD|Helm|"
        r"Smart\s*Contracts|EVM|Blockchain|Solidity"
        r")\b",
        re.IGNORECASE
    )
    
    found = TECH_PATTERNS.findall(text)
    # Normalize
    return [s.strip() for s in found if s.strip()]
