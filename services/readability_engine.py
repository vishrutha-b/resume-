"""
Readability Engine
Computes text-based quality metrics:
- Average sentence length
- Reading grade level (Flesch-Kincaid)
- Skill density (% of words that are skills)
- Quantification rate (% of bullets with numbers)
- Overused buzzwords detection
Runs locally — no API calls. Fully deterministic.
"""
import re
from typing import Dict, List
from utils.logger import get_logger

logger = get_logger(__name__)

# Overused buzzwords that weaken resume impact
OVERUSED_BUZZWORDS = [
    "increased", "leveraged", "utilized", "synergy", "innovative",
    "passionate", "dynamic", "proactive", "results-driven", "self-starter",
    "team player", "fast learner", "go-getter", "detail-oriented",
    "hardworking", "motivated", "experienced", "skilled", "proficient",
    "responsible for", "helped", "assisted", "worked on", "involved in",
    "participated in", "contributed to", "managed", "led", "handled",
    "streamlined", "optimized", "transformed", "revolutionized",
    "cutting-edge", "state-of-the-art", "world-class", "best-in-class",
    "thought leader", "change agent", "guru", "ninja", "rockstar", "wizard"
]

# Standard ATS sections to check presence
EXPECTED_SECTIONS = {
    "Professional Summary": r"(?i)\b(summary|objective|about\s*me|profile|professional\s*summary)\b",
    "Technical Skills": r"(?i)\b(skills|technical\s*skills|core\s*competencies|technologies|tech\s*stack)\b",
    "Professional Experience": r"(?i)\b(experience|work\s*experience|professional\s*experience|employment)\b",
    "Education": r"(?i)\b(education|academic|qualification|degree)\b",
    "Projects": r"(?i)\b(projects|personal\s*projects|key\s*projects)\b",
    "Certifications": r"(?i)\b(certifications?|licenses?|credentials?)\b",
    "Soft Skills": r"(?i)\b(soft\s*skills|interpersonal|communication\s*skills)\b",
    "Awards": r"(?i)\b(awards?|honors?|recognition|achievements?)\b",
    "Volunteer Experience": r"(?i)\b(volunteer|community\s*service|pro\s*bono)\b",
    "Publications": r"(?i)\b(publications?|papers?|research|patents?)\b",
    "Professional Affiliations": r"(?i)\b(affiliations?|memberships?|associations?|societies)\b",
    "Languages": r"(?i)\b(languages?|spoken\s*languages?|language\s*proficiency)\b",
    "Contact Information": r"(?i)\b(contact|email|phone|linkedin|github|address)\b",
}

REQUIRED_SECTIONS = {
    "Professional Summary", "Technical Skills", "Professional Experience",
    "Education", "Projects"
}


def compute_readability(resume_text: str, extracted_skills: List[str] = None) -> Dict:
    """
    Compute readability and content quality metrics from resume text.
    Returns a dict of metrics.
    """
    lines = [l.strip() for l in resume_text.split("\n") if l.strip()]
    sentences = _split_sentences(resume_text)
    words = resume_text.split()

    # 1. Average sentence length
    if sentences:
        avg_sentence_length = round(sum(len(s.split()) for s in sentences) / len(sentences), 1)
    else:
        avg_sentence_length = 0

    # 2. Reading grade level (Flesch-Kincaid Grade Level approximation)
    syllable_count = sum(_count_syllables(w) for w in words)
    if len(sentences) > 0 and len(words) > 0:
        fk_grade = round(
            0.39 * (len(words) / len(sentences)) +
            11.8 * (syllable_count / max(len(words), 1)) - 15.59,
            1
        )
        reading_grade = max(1, min(20, fk_grade))
    else:
        reading_grade = 0

    # 3. Skill density
    skill_set = set(s.lower() for s in (extracted_skills or []))
    if skill_set and len(words) > 0:
        skill_words = sum(1 for w in words if w.lower().strip(".,;:") in skill_set)
        skill_density = round((skill_words / len(words)) * 100, 1)
    else:
        skill_density = 0.0

    # 4. Quantification rate
    bullet_lines = [l for l in lines if len(l) > 20]
    number_pattern = re.compile(r"\d")
    quantified_bullets = [l for l in bullet_lines if number_pattern.search(l)]
    quantification_rate = round(
        (len(quantified_bullets) / len(bullet_lines)) * 100, 1
    ) if bullet_lines else 0.0

    # 5. Overused buzzwords
    found_buzzwords = []
    text_lower = resume_text.lower()
    for buzzword in OVERUSED_BUZZWORDS:
        if buzzword in text_lower:
            found_buzzwords.append(buzzword)

    # 6. Section analysis
    found_sections = []
    missing_sections = []
    for section_name, pattern in EXPECTED_SECTIONS.items():
        if re.search(pattern, resume_text):
            found_sections.append(section_name)
        else:
            missing_sections.append(section_name)

    # Section coverage score
    required_found = [s for s in found_sections if s in REQUIRED_SECTIONS]
    section_coverage_score = round((len(required_found) / len(REQUIRED_SECTIONS)) * 100)

    logger.info(
        f"Readability: avg_sentence={avg_sentence_length}, grade={reading_grade}, "
        f"skill_density={skill_density}%, quantification={quantification_rate}%, "
        f"buzzwords={len(found_buzzwords)}, sections={len(found_sections)}"
    )

    return {
        "avg_sentence_length": avg_sentence_length,
        "reading_grade_level": reading_grade,
        "skill_density_percent": skill_density,
        "quantification_rate_percent": quantification_rate,
        "overused_buzzwords": found_buzzwords[:10],
        "found_sections": found_sections,
        "missing_sections": missing_sections,
        "section_coverage_score": section_coverage_score,
    }


def _split_sentences(text: str) -> List[str]:
    """Split text into sentences."""
    sentences = re.split(r'(?<=[.!?])\s+', text)
    return [s.strip() for s in sentences if len(s.strip()) > 10]


def _count_syllables(word: str) -> int:
    """Approximate syllable count for a word."""
    word = word.lower().strip(".,;:\"'")
    if not word:
        return 0
    count = len(re.findall(r'[aeiou]', word))
    count -= len(re.findall(r'[aeiou]{2}', word))
    if word.endswith('e') and not word.endswith('le'):
        count -= 1
    return max(1, count)
