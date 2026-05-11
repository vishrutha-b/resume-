"""
Resume Optimization Engine
Uses LLM to analyze gaps between resume and JD, then generates
an improved, ATS-optimized version of the resume.
"""
import json
import re
import time
import requests
from config.settings import Config
from utils.logger import get_logger

logger = get_logger(__name__)

OPTIMIZER_SYSTEM_PROMPT = """You are an elite ATS Resume Optimizer. Your goal is to rewrite the resume so it genuinely scores 95+ on ATS scanners — through legitimate optimization only.

-------------------------------------------
ABSOLUTE PROHIBITIONS (ZERO TOLERANCE):
-------------------------------------------
1. NEVER invent any metric, number, or percentage that does not exist in the original resume.
2. NEVER delete an existing bullet — you may only rephrase it.
3. NEVER change company names, job titles, locations, or dates.
4. NEVER add a technology the candidate has never used or mentioned.

-------------------------------------------
HOW TO ACHIEVE 95+ LEGITIMATELY:
-------------------------------------------

1. KEYWORD SATURATION (40% of Score)
   - Extract EVERY technical term from the JD and inject them verbatim.
   - Use the "Relevant Knowledge & Exposure" section for keywords that don't fit into experience.

2. QUANTIFIED IMPACT (15% of Score)
   - Every single bullet MUST contain a number, percentage, or scale metric.
   - Use patterns like "85% reduction", "$1.2M saved", "Managed 15+ engineers".

3. PROFESSIONAL FORMATTING (5% of Score)
   - Use ALL CAPS for section headers and exactly "- " for bullets.
   - Ensure at least 10 bullets and 5 section headers.

4. SEMANTIC ALIGNMENT (10% of Score)
   - Use the exact vocabulary and elite action verbs from the JD.

5. SOFT SKILLS (10% of Score)
   - Intersperse keywords like: Leadership, Mentored, Cross-functional, Stakeholder, Agile.

6. EXPERIENCE RELEVANCE (20% of Score)
   - Align job titles to show clear career progression.

-------------------------------------------
STRICT OUTPUT FORMAT FOR THE RESUME:
-------------------------------------------

CANDIDATE FULL NAME
City | Phone | Email | LinkedIn | GitHub
Job Title

PROFESSIONAL SUMMARY
Write 3-4 lines here using only facts from the resume.

TECHNICAL SKILLS
Languages: Java, Python, SQL
Frameworks: Spring Boot, FastAPI
Databases: MySQL, PostgreSQL
Tools: Git, Docker, Jenkins, AWS
Relevant Knowledge & Exposure: [Inject ALL missing JD keywords here]

PROFESSIONAL EXPERIENCE
**Job Title -- Company Name | City | Month Year - Month Year**
- Bullet point starting with action verb.
- Bullet point starting with action verb.

**Job Title -- Company Name | City | Month Year - Month Year**
- Bullet point.

PROJECTS
**Project Name -- Tech Stack**
- Bullet point describing impact or feature.

EDUCATION
**Degree -- University Name | City**
Year - Year | CGPA: X.X/10

CERTIFICATIONS
- Certification Name

[ANY OTHER EXISTING SECTIONS FROM ORIGINAL RESUME]
- e.g., SOFT SKILLS, LANGUAGES, AWARDS, PUBLICATIONS

FORMATTING RULES (mandatory):
- SECTION HEADERS: MUST BE ALL CAPS (e.g. PROFESSIONAL EXPERIENCE).
- BULLETS: Every bullet MUST start with "- ".
- BOLDING: Wrap **Job Titles** and **Project Names** in double asterisks.
- QUANTIFICATION: Ensure every project and job has at least one metric-driven bullet.
- NO COLONS after section headers.
- NO NUMBERED LISTS.
- AGGRESSIVE REPHRASING: Rewrite every bullet to be as strong and impactful as possible using elite industry verbs and exact JD keywords.

REALISTIC SCORING: Calculate a genuine `ats_score_estimate` based on how well you fulfilled the above criteria.

Return ONLY a single valid JSON object (no markdown, no extra text):
{
  "updated_resume": "FULL rewritten resume using the exact format above, with \\n for newlines",
  "ats_score_estimate": 84,
  "improvements_made": ["specific, honest changes you made"],
  "keyword_coverage": {
    "added": ["keywords legitimately added"],
    "still_missing": ["keywords that could not be added honestly without fabrication"]
  },
  "keyword_injection_plan": [
    {
      "keyword": "Design Patterns",
      "inject_in": "Professional Experience",
      "example": "Applied Factory and Singleton design patterns to improve code maintainability."
    }
  ],
  "bullet_rewrites": [
    {
      "original": "Built ticket management platform supporting 50K users.",
      "rewritten": "Engineered and deployed enterprise-grade ticket management platform supporting 50K concurrent users."
    }
  ],
  "score_justification": "Specific explanation of why this score is justified based on real content."
}"""




class ResumeOptimizer:
    def __init__(self):
        self.api_key = Config.GROQ_API_KEY
        self.base_url = Config.GROQ_BASE_URL
        self.model = Config.LLM_MODEL
        if not self.api_key:
            logger.warning("GROQ_API_KEY is not set. Resume optimization will fail.")

    def optimize(
        self,
        resume_text: str,
        jd_text: str,
        previous_evaluation: dict,
    ) -> dict:
        """
        Generate an optimized resume based on the original resume, JD, and ATS evaluation feedback.

        Args:
            resume_text: Original resume text
            jd_text: Job description text
            previous_evaluation: Dict with ats_score, score_breakdown, skill_match, key_gaps, etc.

        Returns:
            Dict with updated_resume, improvements_made, keyword_coverage, ats_score_estimate
        """
        logger.info(f"Optimizing resume using model {self.model}")

        # Build context with evaluation feedback
        eval_summary = self._build_evaluation_summary(previous_evaluation)

        # Extract specific data for targeted injection
        missing_skills = []
        if isinstance(previous_evaluation.get('skill_match'), dict):
            missing_skills = previous_evaluation['skill_match'].get('missing', [])
        
        missing_skills_str = ", ".join(missing_skills) if missing_skills else "None"

        user_prompt = (
            f"### ORIGINAL RESUME (DO NOT COPY — REWRITE COMPLETELY):\n{resume_text}\n\n"
            f"### JOB DESCRIPTION (ALIGN ALL CONTENT TO THIS):\n{jd_text}\n\n"
            f"### PREVIOUS ATS EVALUATION (YOUR TARGET METRICS):\n{eval_summary}\n\n"
            f"### REQUIRED EXACT KEYWORDS TO INJECT (CRITICAL FOR 95+ SCORE):\n{missing_skills_str}\n\n"
            f"TASK: Analyze the gaps and generate a COMPLETELY REWRITTEN, HIGH-IMPACT, ATS-OPTIMIZED RESUME that is guaranteed to score 95+ on strict external ATS parsers.\n"
            f"1. You MUST integrate the exact Job Title into the Summary.\n"
            f"2. You MUST inject ALL REQUIRED EXACT KEYWORDS naturally into the Skills section and Work Experience bullet points.\n"
            f"3. Every section must be visibly improved. Do NOT return the original with minor edits.\n"
            f"Return ONLY valid JSON with the updated_resume field containing the FULL rewritten resume as a single string with \\n for newlines."
        )

        try:
            # Fallback chain
            models_to_try = [
                self.model,                     # e.g. llama-3.3-70b-versatile
                "llama-3.1-8b-instant"          # high limits
            ]
            
            response = None
            used_model = None
            
            for current_model in models_to_try:
                logger.info(f"Attempting API call with model: {current_model}")
                response = requests.post(
                    url=f"{self.base_url}/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json"
                    },
                    data=json.dumps({
                        "model": current_model,
                        "messages": [
                            {"role": "system", "content": OPTIMIZER_SYSTEM_PROMPT},
                            {"role": "user", "content": user_prompt}
                        ],
                        "max_tokens": 1500,
                        "response_format": {"type": "json_object"}
                    }),
                    timeout=120
                )
                if response.status_code in [429, 413, 400]:
                    logger.warning(f"Model {current_model} failed with {response.status_code}. Instantly failing over to next model.")
                    continue
                
                response.raise_for_status()
                used_model = current_model
                break
            else:
                return self._fallback_response("Rate limited by Groq API. Please wait 1 minute and try again.")
            
            logger.info(f"Optimization succeeded using model: {used_model}")

            data = response.json()

            # Check for API-level errors
            if "error" in data:
                error_msg = data["error"].get("message", str(data["error"]))
                logger.error(f"API returned error: {error_msg}")
                return self._fallback_response(f"API error: {error_msg}")

            # Check for empty/missing choices
            if not data.get("choices") or len(data["choices"]) == 0:
                logger.error(f"API returned no choices. Full response: {json.dumps(data)[:500]}")
                return self._fallback_response("API returned empty response (no choices)")

            content = data["choices"][0]["message"]["content"]
            if not content or not content.strip():
                logger.error("API returned empty content")
                return self._fallback_response("API returned empty content")

            content = content.strip()

            # Check finish reason for truncation
            finish_reason = data["choices"][0].get("finish_reason", "unknown")
            if finish_reason == "length":
                logger.warning("LLM response was TRUNCATED (finish_reason=length). Output may be incomplete.")

            logger.info(f"Raw LLM response length: {len(content)}, finish_reason: {finish_reason}")
            logger.info(f"First 300 chars: {content[:300]}")
            logger.info(f"Last 200 chars: {content[-200:]}")

            # Sanitize markdown wrapping
            content = self._strip_markdown_fences(content)

            # Extract the JSON
            parsed = self._extract_json(content, truncated=(finish_reason == "length"))
            parsed = self._sanitize_output(parsed)
            logger.info("Resume optimization completed successfully.")
            return parsed

        except requests.exceptions.RequestException as e:
            logger.error(f"LLM API request failed during resume optimization: {e}")
            return self._fallback_response(str(e))
        except (json.JSONDecodeError, KeyError, ValueError) as e:
            logger.error(f"Failed to parse LLM optimization response: {e}")
            logger.error(f"Content that failed to parse (first 500 chars): {content[:500] if content else 'EMPTY'}")
            return self._fallback_response(f"Failed to parse LLM response: {e}")

    def _strip_markdown_fences(self, content: str) -> str:
        """Remove markdown code fences from LLM output."""
        content = content.strip()
        # Remove ```json ... ``` wrapping
        if content.startswith("```json"):
            content = content[7:]
        elif content.startswith("```"):
            content = content[3:]
        if content.endswith("```"):
            content = content[:-3]
        return content.strip()

    def _extract_json(self, content: str, truncated: bool = False) -> dict:
        """
        Robustly extract JSON from LLM response.
        Strategy: try direct parse → brace extraction with repair → regex field extraction.
        """
        logger.info(f"_extract_json: content length={len(content)}, truncated={truncated}")

        # Strategy 1: Direct parse
        try:
            result = json.loads(content)
            if isinstance(result, dict) and result.get("updated_resume"):
                logger.info("Strategy 1 (direct parse) succeeded")
                return result
            logger.info("Strategy 1 parsed but missing updated_resume, trying other strategies")
        except json.JSONDecodeError as e:
            logger.info(f"Strategy 1 failed: {e}")

        # Strategy 2: Find JSON block using first { and last }
        first_brace = content.find('{')
        last_brace = content.rfind('}')
        if first_brace != -1 and last_brace > first_brace:
            json_candidate = content[first_brace:last_brace + 1]
            try:
                result = json.loads(json_candidate)
                if isinstance(result, dict) and result.get("updated_resume"):
                    logger.info("Strategy 2 (first-last brace) succeeded")
                    return result
                logger.info("Strategy 2 parsed but missing updated_resume")
            except json.JSONDecodeError as e:
                logger.info(f"Strategy 2 failed: {e}")

                # Strategy 2b: Try to repair truncated JSON
                if truncated:
                    repaired = self._repair_truncated_json(json_candidate)
                    if repaired:
                        logger.info("Strategy 2b (truncated JSON repair) succeeded")
                        return repaired

        # Strategy 3: Smart field extraction (most robust for malformed JSON)
        logger.warning("JSON parsing failed, falling back to smart field extraction")
        result = self._extract_fields_from_raw(content)

        if result.get("updated_resume"):
            logger.info("Strategy 3 (field extraction) succeeded")
            return result

        # Strategy 4: If all else fails, try to use everything between first { and end as resume
        logger.warning("All JSON strategies failed. Attempting raw text extraction.")
        raw_resume = self._extract_resume_text_raw(content)
        if raw_resume and len(raw_resume) > 100:
            logger.info("Strategy 4 (raw text extraction) succeeded")
            return {
                "updated_resume": raw_resume,
                "improvements_made": ["Resume was optimized but response format was non-standard"],
                "keyword_coverage": {"matched_percent": 0, "added": [], "still_missing": []},
                "ats_score_estimate": 0,
                "score_justification": "Score unavailable due to response format issues"
            }

        raise ValueError("Could not extract resume from LLM response using any strategy")

    def _repair_truncated_json(self, json_str: str) -> dict:
        """Attempt to repair truncated JSON by closing open strings/brackets."""
        try:
            # Count open brackets and quotes
            in_string = False
            escape_next = False
            brace_depth = 0
            bracket_depth = 0

            for char in json_str:
                if escape_next:
                    escape_next = False
                    continue
                if char == '\\':
                    escape_next = True
                    continue
                if char == '"' and not escape_next:
                    in_string = not in_string
                    continue
                if in_string:
                    continue
                if char == '{':
                    brace_depth += 1
                elif char == '}':
                    brace_depth -= 1
                elif char == '[':
                    bracket_depth += 1
                elif char == ']':
                    bracket_depth -= 1

            # Close open structures
            repair = json_str
            if in_string:
                repair += '"'
            for _ in range(bracket_depth):
                repair += ']'
            for _ in range(brace_depth):
                repair += '}'

            result = json.loads(repair)
            if isinstance(result, dict):
                return result
        except (json.JSONDecodeError, Exception) as e:
            logger.info(f"Truncated JSON repair failed: {e}")
        return None

    def _extract_fields_from_raw(self, content: str) -> dict:
        """Extract individual JSON fields using robust regex patterns."""
        result = {}

        # Extract updated_resume - most important field
        # Try multiple patterns from most specific to most generic
        resume_text = None

        # Pattern 1: Standard JSON string value for updated_resume
        # Match "updated_resume": "..." handling escaped characters
        match = re.search(r'"updated_resume"\s*:\s*"', content)
        if match:
            start = match.end()
            # Walk forward finding the end of the string value
            resume_text = self._extract_json_string_value(content, start)

        if not resume_text:
            # Pattern 2: Try to find resume content between known markers
            match = re.search(r'"updated_resume"\s*:\s*"(.*?)(?:"\s*,\s*"(?:improvements_made|keyword_coverage|ats_score))', content, re.DOTALL)
            if match:
                resume_text = match.group(1)

        if resume_text:
            # Unescape JSON string escapes
            resume_text = resume_text.replace('\\n', '\n').replace('\\"', '"').replace('\\t', '\t').replace('\\\\', '\\')
            result["updated_resume"] = resume_text

        # Extract improvements_made array
        improvements_match = re.search(r'"improvements_made"\s*:\s*\[(.*?)\]', content, re.DOTALL)
        if improvements_match:
            items = re.findall(r'"((?:[^"\\]|\\.)*)"', improvements_match.group(1))
            result["improvements_made"] = [item.replace('\\n', '\n').replace('\\"', '"') for item in items]
        else:
            result["improvements_made"] = []

        # Extract ats_score_estimate
        score_match = re.search(r'"ats_score_estimate"\s*:\s*(\d+)', content)
        result["ats_score_estimate"] = int(score_match.group(1)) if score_match else 0

        # Extract keyword_coverage
        kc_match = re.search(r'"keyword_coverage"\s*:\s*\{(.*?)\}', content, re.DOTALL)
        if kc_match:
            kc_text = kc_match.group(1)
            added = re.findall(r'"added"\s*:\s*\[(.*?)\]', kc_text, re.DOTALL)
            missing = re.findall(r'"still_missing"\s*:\s*\[(.*?)\]', kc_text, re.DOTALL)
            pct_match = re.search(r'"matched_percent"\s*:\s*(\d+)', kc_text)
            result["keyword_coverage"] = {
                "matched_percent": int(pct_match.group(1)) if pct_match else 0,
                "added": re.findall(r'"((?:[^"\\]|\\.)*)"', added[0]) if added else [],
                "still_missing": re.findall(r'"((?:[^"\\]|\\.)*)"', missing[0]) if missing else [],
            }
        else:
            result["keyword_coverage"] = {"matched_percent": 0, "added": [], "still_missing": []}

        # Extract updated_score_breakdown
        usb_match = re.search(r'"updated_score_breakdown"\s*:\s*\{(.*?)\}', content, re.DOTALL)
        if usb_match:
            usb_text = usb_match.group(1)
            result["updated_score_breakdown"] = {
                "keyword_match": int(re.search(r'"keyword_match"\s*:\s*(\d+)', usb_text).group(1)) if re.search(r'"keyword_match"\s*:\s*(\d+)', usb_text) else 0,
                "experience_relevance": int(re.search(r'"experience_relevance"\s*:\s*(\d+)', usb_text).group(1)) if re.search(r'"experience_relevance"\s*:\s*(\d+)', usb_text) else 0,
                "formatting_structure": int(re.search(r'"formatting_structure"\s*:\s*(\d+)', usb_text).group(1)) if re.search(r'"formatting_structure"\s*:\s*(\d+)', usb_text) else 0,
                "projects_impact": int(re.search(r'"projects_impact"\s*:\s*(\d+)', usb_text).group(1)) if re.search(r'"projects_impact"\s*:\s*(\d+)', usb_text) else 0,
                "skills_match": int(re.search(r'"skills_match"\s*:\s*(\d+)', usb_text).group(1)) if re.search(r'"skills_match"\s*:\s*(\d+)', usb_text) else 0,
            }

        # Extract score_justification
        justification_match = re.search(r'"score_justification"\s*:\s*"((?:[^"\\]|\\.)*)"', content)
        result["score_justification"] = justification_match.group(1) if justification_match else ""

        return result

    def _extract_json_string_value(self, content: str, start: int) -> str:
        """Extract a JSON string value starting from position after opening quote."""
        i = start
        chars = []
        escape_next = False

        while i < len(content):
            char = content[i]
            if escape_next:
                chars.append('\\')
                chars.append(char)
                escape_next = False
                i += 1
                continue
            if char == '\\':
                escape_next = True
                i += 1
                continue
            if char == '"':
                # End of string
                return ''.join(chars)
            chars.append(char)
            i += 1

        # If we reached end without closing quote (truncated), return what we have
        result = ''.join(chars)
        if len(result) > 50:
            logger.warning(f"JSON string value was truncated (no closing quote found), extracted {len(result)} chars")
            return result
        return None

    def _extract_resume_text_raw(self, content: str) -> str:
        """Last resort: try to extract any resume-like text from the response."""
        # If the model just returned the resume text directly (no JSON)
        # Check if it looks like resume content (has section headers like SUMMARY, EXPERIENCE, etc.)
        resume_indicators = ['SUMMARY', 'EXPERIENCE', 'SKILLS', 'EDUCATION', 'PROJECTS']
        indicator_count = sum(1 for ind in resume_indicators if ind in content.upper())

        if indicator_count >= 2:
            # Looks like raw resume text
            # Strip any JSON-like wrapping
            text = content.strip()
            if text.startswith('{'):
                # Try to extract just the resume part
                match = re.search(r'"updated_resume"\s*:\s*"?(.*)', text, re.DOTALL)
                if match:
                    text = match.group(1).rstrip('"}')
            return text.replace('\\n', '\n').replace('\\"', '"')
        return None


    def _build_evaluation_summary(self, evaluation: dict) -> str:
        """Build a human-readable evaluation summary for the LLM prompt."""
        lines = []
        lines.append(f"ATS Score: {evaluation.get('ats_score', 'N/A')}/100")

        breakdown = evaluation.get('score_breakdown', {})
        if breakdown:
            lines.append(f"Score Breakdown: {json.dumps(breakdown)}")

        skill_match = evaluation.get('skill_match', {})
        if skill_match:
            matched = skill_match.get('matched', [])
            missing = skill_match.get('missing', [])
            lines.append(f"Matched Skills: {', '.join(matched) if matched else 'None'}")
            lines.append(f"Missing Skills: {', '.join(missing) if missing else 'None'}")

        key_gaps = evaluation.get('key_gaps', [])
        if key_gaps:
            lines.append(f"Key Gaps: {', '.join(key_gaps)}")

        strong_points = evaluation.get('strong_points', [])
        if strong_points:
            lines.append(f"Strong Points: {', '.join(strong_points)}")

        bs_flags = evaluation.get('bs_flags', [])
        if bs_flags:
            lines.append(f"BS Flags: {', '.join(bs_flags)}")

        recommendations = evaluation.get('recommendations', [])
        if recommendations:
            lines.append(f"Recommendations: {', '.join(recommendations)}")

        return "\n".join(lines)


    def _sanitize_output(self, parsed: dict) -> dict:
        """Validate and sanitize LLM output."""
        # Ensure required fields exist
        if not isinstance(parsed.get("updated_resume"), str):
            parsed["updated_resume"] = ""
        if not isinstance(parsed.get("improvements_made"), list):
            parsed["improvements_made"] = []
        if not isinstance(parsed.get("keyword_coverage"), dict):
            parsed["keyword_coverage"] = {"matched_percent": 0, "added": [], "still_missing": []}
        if not isinstance(parsed.get("score_justification"), str):
            parsed["score_justification"] = ""
        if not isinstance(parsed.get("updated_score_breakdown"), dict):
            parsed["updated_score_breakdown"] = {
                "keyword_match": 0,
                "experience_relevance": 0,
                "formatting_structure": 0,
                "projects_impact": 0,
                "skills_match": 0
            }

        # Ensure structured_data exists
        if not isinstance(parsed.get("structured_data"), dict):
            parsed["structured_data"] = {}

        # Clamp score
        try:
            parsed["ats_score_estimate"] = max(0, min(100, int(parsed.get("ats_score_estimate", 0))))
        except (ValueError, TypeError):
            parsed["ats_score_estimate"] = 0

        # Ensure keyword_coverage sub-fields
        kc = parsed["keyword_coverage"]
        if not isinstance(kc, dict):
            kc = {"matched_percent": 0, "added": [], "still_missing": []}
            parsed["keyword_coverage"] = kc
        if not isinstance(kc.get("matched_percent"), (int, float)):
            kc["matched_percent"] = 0
        if not isinstance(kc.get("added"), list):
            kc["added"] = []
        if not isinstance(kc.get("still_missing"), list):
            kc["still_missing"] = []

        # Clean up the resume text
        resume = parsed.get("updated_resume")
        if resume:
            # Remove any leftover JSON artifacts
            resume = resume.strip()
            # Remove trailing incomplete JSON
            if resume.endswith(','):
                resume = resume[:-1].strip()
            # Post-processing: Ensure dashed lines after headers
            parsed["updated_resume"] = resume

        return parsed

    def _fallback_response(self, error_msg: str) -> dict:
        """Return a structured error response if LLM fails."""
        return {
            "updated_resume": "",
            "improvements_made": [],
            "keyword_coverage": {"added": [], "still_missing": []},
            "ats_score_estimate": 0,
            "error": f"Optimization failed: {error_msg}"
        }
