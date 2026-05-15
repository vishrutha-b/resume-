"""
Layer 4: Keyword Intelligence Engine
Performs direct keyword overlap, weighted scoring (required vs preferred),
synonym matching, and keyword stuffing detection.
Runs locally — no API calls. Fully deterministic.
"""
import re
from typing import List, Dict
from utils.logger import get_logger

logger = get_logger(__name__)

# Synonym/implicit mapping: if JD asks for key, resume having any value counts
IMPLICIT_SKILL_MAP = {
    "aws": ["ec2", "s3", "lambda", "rds", "iam", "eks", "cloudfront", "sqs", "sns", "dynamodb", "cloudwatch"],
    "gcp": ["bigquery", "cloud run", "gke", "cloud functions", "pub/sub"],
    "azure": ["azure devops", "azure functions", "cosmos db", "blob storage"],
    "kubernetes": ["k8s", "eks", "gke", "aks", "helm", "kubectl"],
    "ci/cd": ["jenkins", "github actions", "gitlab ci", "circleci", "argocd", "spinnaker", "travis ci"],
    "docker": ["containerization", "docker compose", "dockerfile"],
    "machine learning": ["ml", "deep learning", "neural networks", "tensorflow", "pytorch", "scikit-learn"],
    "react": ["react.js", "reactjs", "react native"],
    "node": ["node.js", "nodejs", "express", "express.js"],
    "python": ["flask", "fastapi", "django", "boto3"],
    "javascript": ["js", "es6", "es2015", "ecmascript"],
    "typescript": ["ts"],
    "database": ["postgresql", "postgres", "mysql", "mongodb", "redis", "sqlite", "dynamodb"],
    "nosql": ["mongodb", "dynamodb", "cassandra", "couchdb", "redis"],
    "sql": ["postgresql", "mysql", "sqlite", "sql server", "oracle"],
    "ai agents": ["langchain", "langgraph", "tool orchestration", "mcp", "autogen"],
    "blockchain": ["smart contracts", "solidity", "evm", "ethereum", "web3"],
    "devops": ["ci/cd", "terraform", "ansible", "docker", "kubernetes", "monitoring"],
}

def compute_keyword_score(
    resume_skills: List[str],
    resume_full_text: str,
    required_skills: List[str],
    preferred_skills: List[str],
) -> Dict:
    """
    Compute keyword matching score with weighted categories.
    Required skills = 2x weight vs Preferred skills.
    Returns: dict with score, matched, missing, partial, implicit, stuffing_flags
    """
    resume_text_lower = resume_full_text.lower()
    resume_skills_lower = [s.lower() for s in resume_skills]
    
    matched = []
    missing = []
    partial = []
    implicit = []
    
    # Check required skills (weight = 2)
    required_hits = 0
    for skill in required_skills:
        skill_lower = skill.lower()
        match_result = _check_skill_match(skill_lower, resume_skills_lower, resume_text_lower)
        
        if match_result == "exact":
            matched.append(skill)
            required_hits += 1
        elif match_result == "implicit":
            implicit.append(skill)
            required_hits += 1.0  # Implicit matches are valid synonyms, give full credit
        elif match_result == "partial":
            partial.append(skill)
            required_hits += 0.5  # Partial = 50% credit
        else:
            missing.append(skill)
    
    # Check preferred skills (weight = 1)
    preferred_hits = 0
    for skill in preferred_skills:
        skill_lower = skill.lower()
        match_result = _check_skill_match(skill_lower, resume_skills_lower, resume_text_lower)
        
        if match_result == "exact":
            matched.append(skill)
            preferred_hits += 1
        elif match_result == "implicit":
            implicit.append(skill)
            preferred_hits += 1.0
        elif match_result == "partial":
            partial.append(skill)
            preferred_hits += 0.5
        else:
            missing.append(skill)
    
    # Calculate weighted score
    total_required = max(len(required_skills), 1)
    total_preferred = max(len(preferred_skills), 1)
    
    required_pct = (required_hits / total_required) * 100
    preferred_pct = (preferred_hits / total_preferred) * 100
    
    # Dynamically adjust weights if one category is empty
    if len(required_skills) == 0 and len(preferred_skills) == 0:
        keyword_score = 100.0  # No requirements means perfect match
    elif len(preferred_skills) == 0:
        keyword_score = required_pct  # 100% weight to required
    elif len(required_skills) == 0:
        keyword_score = preferred_pct  # 100% weight to preferred
    else:
        # 70% weight to required, 30% to preferred
        keyword_score = (required_pct * 0.7) + (preferred_pct * 0.3)
        
    keyword_score = min(100.0, max(0.0, keyword_score))
    
    # Detect keyword stuffing
    stuffing_flags = _detect_keyword_stuffing(resume_full_text)
    
    # Deduplicate
    matched = list(dict.fromkeys(matched))
    missing = list(dict.fromkeys(missing))
    partial = list(dict.fromkeys(partial))
    implicit = list(dict.fromkeys(implicit))
    
    logger.info(
        f"Keyword analysis: score={keyword_score:.1f}, "
        f"matched={len(matched)}, missing={len(missing)}, "
        f"implicit={len(implicit)}, partial={len(partial)}"
    )
    
    return {
        "score": round(keyword_score, 1),
        "matched": matched,
        "missing": missing,
        "partial": partial,
        "implicit": implicit,
        "stuffing_flags": stuffing_flags,
    }

def _check_skill_match(skill: str, resume_skills: list, resume_text: str) -> str:
    """Check if a JD skill matches the resume. Returns: 'exact', 'implicit', 'partial', or 'none'."""
    # Exact match in skill tokens or substrings
    if skill in resume_skills or skill in resume_text:
        return "exact"
    
    # Check word boundaries in full text
    try:
        pattern = re.compile(r"\b" + re.escape(skill) + r"\b", re.IGNORECASE)
        if pattern.search(resume_text):
            return "exact"
    except re.error:
        pass
    
    # Fallback: strip dots and try (handles React.js vs Reactjs)
    skill_stripped = skill.replace(".", "").lower()
    if skill_stripped in resume_text.replace(".", "").lower():
        return "exact"
    
    # Check implicit mapping
    for broad_skill, sub_skills in IMPLICIT_SKILL_MAP.items():
        if skill == broad_skill or broad_skill in skill:
            # Check if resume has any sub-skill
            for sub in sub_skills:
                sub_pattern = re.compile(r"\b" + re.escape(sub) + r"\b", re.IGNORECASE)
                if sub_pattern.search(resume_text):
                    return "implicit"
        # Reverse: skill is a sub-skill of a broader category
        if skill in sub_skills:
            broad_pattern = re.compile(r"\b" + re.escape(broad_skill) + r"\b", re.IGNORECASE)
            if broad_pattern.search(resume_text):
                return "implicit"
    
    # Partial match — check if any part of the skill phrase exists
    skill_words = skill.split()
    if len(skill_words) > 1:
        matches = sum(1 for w in skill_words if w in resume_text)
        if matches >= len(skill_words) * 0.5:
            return "partial"
    
    return "none"

def _detect_keyword_stuffing(text: str) -> List[str]:
    """Detect if skills appear suspiciously often (>10 times in a resume context)."""
    flags = []
    words = re.findall(r"\b\w+\b", text.lower())
    word_counts = {}
    for w in words:
        if len(w) > 3:
            word_counts[w] = word_counts.get(w, 0) + 1
    
    tech_keywords = {"react", "python", "java", "aws", "docker", "kubernetes", "node", "flask", "angular"}
    for keyword in tech_keywords:
        # Threshold raised to 10: legitimate ATS-optimized resumes repeat keywords across sections
        if word_counts.get(keyword, 0) > 10:
            flags.append(f"'{keyword}' appears {word_counts[keyword]} times — possible keyword stuffing")
    
    return flags
