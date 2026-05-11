"""
Layer 7: Weighted Score Calculator
Aggregates all individual layer scores into a single deterministic ATS score.
Uses a transparent, explainable weighted formula.
Runs locally — no API calls. Fully deterministic.
"""
from dataclasses import dataclass
from utils.logger import get_logger

logger = get_logger(__name__)

# Transparent scoring weights
WEIGHTS = {
    "semantic_match": 0.10,   # 10% - Contextual understanding
    "keyword_match": 0.40,    # 40% - Direct skill coverage
    "experience_fit": 0.20,   # 20% - Years + role relevance
    "impact_score": 0.15,     # 15% - Quantified achievements
    "format_score": 0.05,     # 5% - ATS readability (placeholder)
    "soft_skills": 0.10,      # 10% - Leadership, communication signals
}

@dataclass
class ScoreBreakdown:
    semantic_match: float = 0.0
    keyword_match: float = 0.0
    experience_fit: float = 0.0
    impact_score: float = 0.0
    format_score: float = 0.0
    soft_skills: float = 0.0

def calculate_final_score(
    semantic_score: float,
    keyword_score: float,
    experience_score: float,
    impact_score: float,
    resume_text: str = "",
) -> dict:
    """
    Calculate the final weighted ATS score.
    Returns: dict with ats_score, score_breakdown
    """
    # Format score: Basic heuristic for ATS-readability
    format_score = _compute_format_score(resume_text)
    
    # Soft skills: Basic detection from resume text
    soft_skills_score = _compute_soft_skills_score(resume_text)
    
    breakdown = ScoreBreakdown(
        semantic_match=round(semantic_score, 1),
        keyword_match=round(keyword_score, 1),
        experience_fit=round(experience_score, 1),
        impact_score=round(impact_score, 1),
        format_score=round(format_score, 1),
        soft_skills=round(soft_skills_score, 1),
    )
    
    # Weighted sum
    final_score = (
        breakdown.semantic_match * WEIGHTS["semantic_match"] +
        breakdown.keyword_match * WEIGHTS["keyword_match"] +
        breakdown.experience_fit * WEIGHTS["experience_fit"] +
        breakdown.impact_score * WEIGHTS["impact_score"] +
        breakdown.format_score * WEIGHTS["format_score"] +
        breakdown.soft_skills * WEIGHTS["soft_skills"]
    )
    
    final_score = max(0, min(100, round(final_score)))
    
    logger.info(
        f"Score calculation: final={final_score}, "
        f"semantic={breakdown.semantic_match}, keyword={breakdown.keyword_match}, "
        f"experience={breakdown.experience_fit}, impact={breakdown.impact_score}, "
        f"format={breakdown.format_score}, soft_skills={breakdown.soft_skills}"
    )
    
    return {
        "ats_score": final_score,
        "score_breakdown": {
            "semantic_match": breakdown.semantic_match,
            "keyword_match": breakdown.keyword_match,
            "experience_fit": breakdown.experience_fit,
            "impact_score": breakdown.impact_score,
            "format_score": breakdown.format_score,
            "soft_skills": breakdown.soft_skills,
        }
    }

def _compute_format_score(text: str) -> float:
    """Enhanced ATS-readability scoring."""
    if not text:
        return 0.0
    
    score = 40.0  # Base score for a readable file
    
    lines = text.split("\n")
    non_empty_lines = [l.strip() for l in lines if l.strip()]
    
    # Positive signals: Length and detail
    if len(non_empty_lines) > 25:
        score += 10
    
    # Structural signals: Bullet points
    bullet_count = sum(1 for l in non_empty_lines if l.startswith(("•", "◦", "-", "*", "–", "—")))
    if bullet_count >= 10:
        score += 15
    elif bullet_count >= 5:
        score += 5
    
    # Section signals: ALL CAPS headers
    headers = [l for l in non_empty_lines if l.isupper() and 3 < len(l) < 50]
    if len(headers) >= 4:
        score += 15
    elif len(headers) >= 2:
        score += 5
        
    # Consistency: Check if bullets are used across multiple sections
    if bullet_count > 15 and len(headers) >= 5:
        score += 10 # High quality structure bonus
    
    # Negative: very short resume
    if len(text) < 500:
        score -= 30
    
    # Negative: lack of structure (no headers or bullets)
    if len(headers) < 2 and bullet_count < 3:
        score -= 20
        
    return max(0, min(100, score))

def _compute_soft_skills_score(text: str) -> float:
    """Enhanced soft skill detection using professional vocabulary."""
    text_lower = text.lower()
    
    skill_categories = {
        "leadership": ["leadership", "managed", "led", "coordinated", "mentored", "supervised", "pioneered"],
        "collaboration": ["collaboration", "collaborated", "cross-functional", "stakeholder", "teamwork", "partnered"],
        "communication": ["communication", "presented", "authored", "published", "negotiated", "facilitated"],
        "problem_solving": ["problem-solving", "troubleshoot", "debugged", "resolved", "analytical", "optimized"],
        "agile": ["agile", "scrum", "sprint", "kanban", "velocity", "standup"],
    }
    
    categories_hit = 0
    total_matches = 0
    
    for category, keywords in skill_categories.items():
        matches = sum(1 for kw in keywords if kw in text_lower)
        if matches > 0:
            categories_hit += 1
            total_matches += matches
            
    # Base score: 20
    # +15 per category hit (max 75)
    # +2 per individual keyword match (max 15)
    score = 20 + (categories_hit * 15) + min(15, total_matches * 2)
    
    return float(max(0, min(100, score)))
