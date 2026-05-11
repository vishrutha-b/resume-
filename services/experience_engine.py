"""
Layer 5: Experience Evaluator
Parses employment dates, calculates total years, and validates
against JD requirements. Detects career progression and stale skills.
Runs locally — no API calls. Fully deterministic.
"""
import re
from datetime import datetime
from typing import List, Dict, Tuple
from dateutil import parser as date_parser
from utils.logger import get_logger

logger = get_logger(__name__)

def _get_current_date():
    """Get current date dynamically (not at import time)."""
    return datetime.now()

def compute_experience_score(
    resume_text: str,
    employment_dates: List[str],
    years_mentioned: List[int],
    min_required_years: int
) -> Dict:
    """
    Evaluate candidate experience against JD requirements.
    Returns: dict with score (0-100), total_years, stale_skills, career_progression
    """
    # Calculate total years of experience
    date_ranges = _extract_date_ranges(resume_text)
    total_years = _calculate_total_years(date_ranges)
    
    # Fallback: estimate from year mentions if date range parsing gave too little
    if total_years <= 1 and years_mentioned:
        # Filter to realistic work years (exclude education years if possible)
        work_years = [y for y in years_mentioned if y >= 2020]  # Rough heuristic
        if not work_years:
            work_years = years_mentioned
        min_year = min(work_years)
        max_year = max(work_years)
        estimated = max_year - min_year
        total_years = max(total_years, estimated)
    
    # Score based on experience vs requirement
    if min_required_years == 0:
        exp_score = 50.0  # No requirement specified, give lower default
    elif total_years >= min_required_years:
        # Meets or exceeds requirement
        overshoot = total_years - min_required_years
        exp_score = min(100.0, 65.0 + (overshoot * 3))
    else:
        # Below requirement — penalize proportionally
        ratio = total_years / max(min_required_years, 1)
        exp_score = max(10.0, ratio * 60.0)
    
    # Detect stale skills (roles > 3 years ago)
    stale_roles = []
    for start, end, role_text in date_ranges:
        if end and (_get_current_date() - end).days > (3 * 365):
            stale_roles.append(role_text[:80])
    
    # Career progression signal
    progression = _detect_career_progression(resume_text)
    if progression == "ascending":
        exp_score = min(100.0, exp_score + 5)
    
    logger.info(
        f"Experience evaluation: total_years={total_years}, "
        f"required={min_required_years}, score={exp_score:.1f}, "
        f"stale_roles={len(stale_roles)}, progression={progression}"
    )
    
    return {
        "score": round(exp_score, 1),
        "total_years": total_years,
        "stale_roles": stale_roles,
        "career_progression": progression,
    }

def _extract_date_ranges(text: str) -> List[Tuple]:
    """Extract date ranges like 'Sep 2025 - Feb 2026' from text."""
    pattern = re.compile(
        r"((?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|"
        r"Jul(?:y)?|Aug(?:ust)?|Sep(?:t(?:ember)?)?|Oct(?:ober)?|Nov(?:ember)?|"
        r"Dec(?:ember)?)\s*\d{4})"
        r"\s*[-–—to]+\s*"
        r"((?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|"
        r"Jul(?:y)?|Aug(?:ust)?|Sep(?:t(?:ember)?)?|Oct(?:ober)?|Nov(?:ember)?|"
        r"Dec(?:ember)?)\s*\d{4}|Present|Current|Now)",
        re.IGNORECASE
    )
    
    ranges = []
    # Get surrounding context for each match
    lines = text.split("\n")
    full_text_for_context = text
    
    for match in pattern.finditer(text):
        start_str = match.group(1)
        end_str = match.group(2)
        
        try:
            start_date = date_parser.parse(start_str, fuzzy=True)
            if end_str.lower() in ("present", "current", "now"):
                end_date = _get_current_date()
            else:
                end_date = date_parser.parse(end_str, fuzzy=True)
            
            # Get surrounding context (role/company name)
            pos = match.start()
            context_start = max(0, pos - 100)
            context = text[context_start:pos].strip()
            
            ranges.append((start_date, end_date, context))
        except (ValueError, OverflowError):
            continue
    
    return ranges

def _calculate_total_years(date_ranges: List[Tuple]) -> int:
    """Calculate total non-overlapping years of experience."""
    if not date_ranges:
        return 0
    
    # Sort by start date
    sorted_ranges = sorted(date_ranges, key=lambda x: x[0])
    
    total_months = 0
    last_end = None
    
    for start, end, _ in sorted_ranges:
        if end is None:
            continue
        if last_end and start < last_end:
            start = last_end  # Avoid counting overlapping periods
        if end > start:
            diff = (end.year - start.year) * 12 + (end.month - start.month)
            total_months += max(0, diff)
        last_end = max(last_end, end) if last_end else end
    
    return total_months // 12

def _detect_career_progression(text: str) -> str:
    """Detect if career shows upward progression."""
    text_lower = text.lower()
    
    senior_keywords = ["lead", "senior", "principal", "staff", "architect", "head", "director", "vp",
                       "manager", "chief", "distinguished"]
    junior_keywords = ["intern", "junior", "associate", "trainee", "fresher", "entry"]
    
    lines = text_lower.split("\n")
    
    # Look at role titles (rough heuristic)
    first_is_junior = False
    last_is_senior = False
    
    for i, line in enumerate(lines):
        if any(kw in line for kw in junior_keywords):
            if i > len(lines) // 2:  # Earlier in career (listed later)
                first_is_junior = True
        if any(kw in line for kw in senior_keywords):
            if i < len(lines) // 2:  # Current/recent role
                last_is_senior = True
    
    if first_is_junior and last_is_senior:
        return "ascending"
    elif last_is_senior:
        return "senior"
    elif first_is_junior:
        return "junior"
    else:
        return "lateral"
