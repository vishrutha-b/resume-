"""
Layer 6: Impact Detector
Scans resume for quantified, measurable achievements (percentages,
dollar amounts, scale metrics) vs vague buzzword claims.
Directly feeds the verifiability_score.
Runs locally — no API calls. Fully deterministic.
"""
import re
from typing import Dict, List
from utils.logger import get_logger

logger = get_logger(__name__)

# Patterns for quantified achievements
QUANTIFIED_PATTERNS = [
    re.compile(r"\d+%", re.IGNORECASE),                            # 85%, 300%
    re.compile(r"\$[\d,.]+[KMB]?", re.IGNORECASE),                 # $50K, $1.2M
    re.compile(r"\d+[xX]\s*(?:increase|growth|improvement|faster)", re.IGNORECASE),  # 3x faster
    re.compile(r"(?:reduced|decreased|cut|saved|improved|increased|grew|boosted)\s+(?:by\s+)?\d+", re.IGNORECASE),
    re.compile(r"\d+(?:,\d{3})*\+?\s*(?:users|customers|clients|transactions|requests|servers|instances)", re.IGNORECASE),
    re.compile(r"(?:top|ranked)\s*\d+", re.IGNORECASE),            # top 5, ranked #1
    re.compile(r"\d+\s*(?:team\s*members?|engineers?|developers?|reports?)", re.IGNORECASE),  # managed 12 engineers
]

# Elite impact verbs (strong signals of ATS optimization and senior capability)
ELITE_VERBS_PATTERNS = [
    re.compile(r"\b(?:Architected|Spearheaded|Orchestrated|Engineered|Pioneered|Masterminded|Transformed|Revolutionized|Championed|Spearheading)\b", re.IGNORECASE)
]

# Buzzword/vague patterns
BUZZWORD_PATTERNS = [
    re.compile(r"\b(?:results[\s-]driven|highly\s+motivated|team\s+player|fast\s+learner|self[\s-]starter|go[\s-]getter)\b", re.IGNORECASE),
    re.compile(r"\b(?:synerg|leverage|paradigm|disrupt|innovative|cutting[\s-]?edge|state[\s-]of[\s-]the[\s-]art|world[\s-]?class)\b", re.IGNORECASE),
    re.compile(r"\b(?:passionate|driven|dynamic|proactive|visionary|guru|ninja|rockstar|wizard)\b", re.IGNORECASE),
    re.compile(r"\b(?:tremendous|exceptional|outstanding|unparalleled|unprecedented)\b", re.IGNORECASE),
]

def compute_impact_score(resume_text: str) -> Dict:
    """
    Analyze resume for measurable impact vs vague claims.
    Returns: dict with score (0-100), quantified_claims, vague_claims, verifiability_score
    """
    lines = resume_text.split("\n")
    
    quantified_claims = []
    elite_claims = []
    vague_claims = []
    
    for line in lines:
        stripped = line.strip()
        if not stripped or len(stripped) < 10:
            continue
        
        # Check for quantified achievements
        has_quantified = False
        for pattern in QUANTIFIED_PATTERNS:
            if pattern.search(stripped):
                quantified_claims.append(stripped[:120])
                has_quantified = True
                break
        # Check for elite verbs if not quantified
        has_elite = False
        if not has_quantified:
            for pattern in ELITE_VERBS_PATTERNS:
                if pattern.search(stripped):
                    elite_claims.append(stripped[:120])
                    has_elite = True
                    break

        # Check for buzzwords (only if not already quantified or elite)
        if not has_quantified and not has_elite:
            for pattern in BUZZWORD_PATTERNS:
                if pattern.search(stripped):
                    vague_claims.append(stripped[:120])
                    break
    
    # Deduplicate
    quantified_claims = list(dict.fromkeys(quantified_claims))
    elite_claims = list(dict.fromkeys(elite_claims))
    vague_claims = list(dict.fromkeys(vague_claims))
    
    strong_claims = len(quantified_claims) + len(elite_claims)
    
    # Base score on absolute number of strong claims (5+ is excellent)
    if strong_claims == 0:
        impact_score = 40.0
        verifiability = 40
    elif strong_claims == 1:
        impact_score = 60.0
    elif strong_claims == 2:
        impact_score = 75.0
    elif strong_claims >= 3:
        # 3+ claims = 100
        impact_score = 100.0
        
    verifiability = min(100, strong_claims * 20)
    
    # Minor penalty for excessive buzzwords (only if extreme)
    if len(vague_claims) > 4:
        impact_score = max(0.0, impact_score - (len(vague_claims) - 4) * 2)
    
    logger.info(
        f"Impact analysis: quantified={len(quantified_claims)}, elite={len(elite_claims)}, "
        f"vague={len(vague_claims)}, score={impact_score:.1f}, "
        f"verifiability={verifiability}"
    )
    
    return {
        "score": round(impact_score, 1),
        "verifiability_score": verifiability,
        "quantified_claims": (quantified_claims + elite_claims)[:5],  # Cap at 5 for output
        "vague_claims": vague_claims[:3],             # Cap at 3
    }
