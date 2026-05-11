from pydantic import BaseModel, Field
from typing import List, Optional, Literal, Dict, Any


class ScoreBreakdown(BaseModel):
    semantic_match: float = Field(ge=0, le=100, description="Embedding-based contextual similarity")
    keyword_match: float = Field(ge=0, le=100, description="Direct skill keyword coverage")
    experience_fit: float = Field(ge=0, le=100, description="Years + role relevance")
    impact_score: float = Field(ge=0, le=100, description="Quantified achievements")
    format_score: float = Field(ge=0, le=100, description="ATS readability")
    soft_skills: float = Field(ge=0, le=100, description="Leadership, communication signals")


class SkillMatch(BaseModel):
    matched: List[str] = Field(default_factory=list)
    missing: List[str] = Field(default_factory=list)
    partial: List[str] = Field(default_factory=list)
    implicit: List[str] = Field(default_factory=list, description="Skills implicitly matched")
    stale: List[str] = Field(default_factory=list, description="Skills not used recently (>3 years ago)")


class ReadabilityMetrics(BaseModel):
    avg_sentence_length: float = Field(default=0, description="Average words per sentence (target: 12-20)")
    reading_grade_level: float = Field(default=0, description="Flesch-Kincaid grade level (target: 8-12)")
    skill_density_percent: float = Field(default=0, description="% of words that are skills (target: 25-40%)")
    quantification_rate_percent: float = Field(default=0, description="% of bullets with numbers (target: 50-75%)")
    overused_buzzwords: List[str] = Field(default_factory=list, description="Overused weak words found")
    found_sections: List[str] = Field(default_factory=list, description="Sections detected in resume")
    missing_sections: List[str] = Field(default_factory=list, description="Standard sections not found")
    section_coverage_score: int = Field(default=0, ge=0, le=100, description="% of required sections present")


class ATSResponseSchema(BaseModel):
    ats_score: int = Field(ge=0, le=100, description="Overall ATS suitability score")
    score_breakdown: ScoreBreakdown = Field(description="Transparent score breakdown per layer")
    verifiability_score: int = Field(ge=0, le=100, description="Score based on hard metrics vs buzzwords")
    skill_match: SkillMatch
    readability: ReadabilityMetrics = Field(default_factory=ReadabilityMetrics, description="Content quality metrics")
    bs_flags: List[str] = Field(default_factory=list, description="Unverified or exaggerated claims")
    interview_questions: List[str] = Field(default_factory=list, description="Questions probing gaps and verifying claims")
    domain_fit: Literal["Low", "Medium", "High"] = Field(description="Domain alignment")
    experience_fit: Literal["Low", "Medium", "High"] = Field(description="Seniority alignment")
    key_gaps: List[str] = Field(default_factory=list)
    strong_points: List[str] = Field(default_factory=list)
    recommendations: List[str] = Field(default_factory=list)


class ResultEnvelope(BaseModel):
    file_name: str
    evaluation_id: Optional[str] = None
    version: int = 1
    evaluation: Optional[ATSResponseSchema] = None
    error: Optional[str] = None
