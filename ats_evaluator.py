"""
Layer 8: LLM Enhancement Layer (Insight Generator)
The LLM NO LONGER decides the ATS score.
It receives pre-computed scores + parsed data and ONLY generates:
 - strong_points, key_gaps, recommendations, interview_questions, bs_flags
 - domain_fit, experience_fit (qualitative assessments)
"""
import json
import requests
import re
from config.settings import Config
from utils.logger import get_logger

logger = get_logger(__name__)

INSIGHT_SYSTEM_PROMPT = """You are an advanced HR Insights Engine.
You are given a candidate's resume, a job description, and PRE-COMPUTED scores from our deterministic scoring system.

Your job is NOT to compute scores. The scores are already locked in.
Your ONLY job is to generate human-readable insights for HR.

### RULES:
- Focus blindly on facts from the resume.
- Do NOT hallucinate skills the candidate doesn't have.
- Be strictly objective and professional.
- IMPORTANT: Your response must be a valid JSON object.
"""

def _redact_pii(text: str) -> str:
    """Redact emails and phone numbers from text to prevent PII leakage."""
    # Redact emails
    email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
    text = re.sub(email_pattern, '[REDACTED_EMAIL]', text)
    
    # Redact phone numbers (covers common formats like (123) 456-7890, 123-456-7890, etc.)
    phone_pattern = r'\(?\b\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b'
    text = re.sub(phone_pattern, '[REDACTED_PHONE]', text)
    
    return text


class InsightGenerator:
    def __init__(self):
        self.api_key = Config.GROQ_API_KEY
        self.base_url = Config.GROQ_BASE_URL
        self.model = Config.LLM_MODEL
        if not self.api_key:
            logger.warning("GROQ_API_KEY is not set. LLM insights will fail.")

    def generate_insights(
        self,
        resume_text: str,
        jd_text: str,
        ats_score: int,
        score_breakdown: dict,
        matched_skills: list,
        missing_skills: list,
        verifiability_score: int,
    ) -> dict:
        """Generate qualitative insights using the LLM. Scores are NOT generated here."""
        logger.info(f"Generating LLM insights using model {self.model}")

        # Redact PII before sending to LLM
        safe_resume_text = _redact_pii(resume_text)

        context = (
            f"### PRE-COMPUTED SCORES (DO NOT CHANGE THESE):\n"
            f"ATS Score: {ats_score}/100\n"
            f"Score Breakdown: {json.dumps(score_breakdown)}\n"
            f"Verifiability: {verifiability_score}/100\n"
            f"Matched Skills: {', '.join(matched_skills)}\n"
            f"Missing Skills: {', '.join(missing_skills)}\n\n"
            f"### RESUME TEXT:\n{safe_resume_text}\n\n"
            f"### JOB DESCRIPTION:\n{jd_text}\n\n"
            f"Generate the insights based on the above data."
        )

        try:
            # JSON Schema for Structured Outputs
            response_format = {
                "type": "json_schema",
                "json_schema": {
                    "name": "insight_response",
                    "strict": True,
                    "schema": {
                        "type": "object",
                        "properties": {
                            "strong_points": { "type": "array", "items": { "type": "string" } },
                            "key_gaps": { "type": "array", "items": { "type": "string" } },
                            "recommendations": { "type": "array", "items": { "type": "string" } },
                            "interview_questions": { "type": "array", "items": { "type": "string" } },
                            "bs_flags": { "type": "array", "items": { "type": "string" } },
                            "domain_fit": { "type": "string", "enum": ["Low", "Medium", "High"] },
                            "experience_fit": { "type": "string", "enum": ["Low", "Medium", "High"] }
                        },
                        "required": ["strong_points", "key_gaps", "recommendations", "interview_questions", "bs_flags", "domain_fit", "experience_fit"],
                        "additionalProperties": False
                    }
                }
            }

            # Note: Groq doesn't support json_schema response_format, use json_object instead
            response = requests.post(
                url=f"{self.base_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                },
                data=json.dumps({
                    "model": self.model,
                    "messages": [
                        {"role": "system", "content": INSIGHT_SYSTEM_PROMPT},
                        {"role": "user", "content": context}
                    ],
                    "response_format": {"type": "json_object"},
                    "max_tokens": 1024
                }),
                timeout=30
            )
            response.raise_for_status()
            data = response.json()

            content = data["choices"][0]["message"]["content"].strip()

            parsed = json.loads(content)
            parsed = _sanitize_insights(parsed)  # Validate before returning
            logger.info("LLM insights generated successfully.")
            return parsed

        except requests.exceptions.RequestException as e:
            logger.error(f"LLM API request failed during insight generation: {e}")
            return _fallback_insights(missing_skills)
        except (json.JSONDecodeError, KeyError) as e:
            logger.error(f"Failed to parse LLM insight response: {e}")
            return _fallback_insights(missing_skills)


# Valid values for Literal fields
_VALID_FIT_VALUES = {"Low", "Medium", "High"}

def _sanitize_insights(parsed: dict) -> dict:
    """Ensure LLM-generated insights conform to schema constraints."""
    # Clamp domain_fit and experience_fit to valid Literal values
    if parsed.get("domain_fit") not in _VALID_FIT_VALUES:
        parsed["domain_fit"] = "Medium"
    if parsed.get("experience_fit") not in _VALID_FIT_VALUES:
        parsed["experience_fit"] = "Medium"

    # Ensure list fields are actually lists
    for key in ["strong_points", "key_gaps", "recommendations", "interview_questions", "bs_flags"]:
        if not isinstance(parsed.get(key), list):
            parsed[key] = []

    return parsed


def _fallback_insights(missing_skills: list) -> dict:
    """Provide deterministic fallback insights if LLM fails."""
    return {
        "strong_points": ["Resume parsed successfully"],
        "key_gaps": missing_skills[:5] if missing_skills else ["No major gaps detected"],
        "recommendations": ["Strengthen quantifiable achievements with metrics"],
        "interview_questions": ["Describe your most impactful technical project and the metrics you achieved."],
        "bs_flags": [],
        "domain_fit": "Medium",
        "experience_fit": "Medium",
    }
