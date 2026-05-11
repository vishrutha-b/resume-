"""
Test script: Runs the full 8-layer enterprise ATS pipeline.
Uses the same resume text and JD from previous tests.
"""
import json
import sys
import os

# Ensure project root is in path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from services.resume_parser_v2 import parse_resume
from services.jd_analyzer import analyze_jd
from services.semantic_engine import compute_semantic_score
from services.keyword_engine import compute_keyword_score
from services.experience_engine import compute_experience_score
from services.impact_detector import compute_impact_score
from services.score_calculator import calculate_final_score
from ats_evaluator import InsightGenerator
from models.schemas import ATSResponseSchema, ScoreBreakdown, SkillMatch

RESUME_TEXT = """
SUMMARY
webxspark | AlanChris06 | alanchris.me
Full-stack engineer with experience building production-grade web systems, AI-assisted workflows, and scalable backend services.

SKILLS
Languages: JavaScript, TypeScript, Python, PHP, SQL
Frontend: React.js, Next.js, HTML, CSS, TailwindCSS
Backend: Flask, FastAPI, Node.js, Express.js, Laravel
AI & Systems: LangChain, LangGraph, MCP
Distributed Systems & Blockchain: Smart Contracts, EVM-based systems
Infra & Data: PostgreSQL, MySQL, MongoDB, Redis, Docker, AWS, OCI, Linux, Git

WORK EXPERIENCE
Neeve — DevOps / AI Systems Intern (Sep 2025 - Feb 2026, Chennai)
- Designed and operated an internal Slack-based AI assistant that automated operational workflows by orchestrating tools across multiple backend systems.
- Engineered a production-ready execution pipeline to safely route, execute, and aggregate results from multiple services while maintaining low-latency.

Internal AI Automation Platform (Sep 2025 - Dec 2025)
- Led the full design and implementation of an enterprise-grade AI automation platform.
- Architected a modular tool execution framework with admin-defined access policies, tool discovery, and encrypted data routing.

HCLTech — Digital Technology Intern (Jul 2025 - Aug 2025, Chennai)
- Built an automated data pipeline for internal reporting.

MITSquare Technologies — Web Developer Intern (Oct 2023 - Dec 2023, Bangalore)
- Built responsive React-based dashboards and integrated them with backend APIs.

PROJECTS
AI Emergency Call Management System
- Developed an AI-powered emergency response platform that classifies incoming calls using NLP and routes them to the appropriate emergency services.
- Patent: Automated Call Management System Using AI for Emergency Services (2024)

EthGlobal Bangkok 2024 Hackathon — Winner
- Built an on-chain, privacy-preserving AI agent system using EVM-based smart contracts.

EDUCATION
SRM Institute of Science and Technology — B.Tech Computer Science (2022-2026)
GPA: 9.0/10.0

PUBLICATIONS & PATENTS
- Patent: Automated Call Management System Using AI for Emergency Services (2024)
- Published research on AI-assisted automation systems
"""

JOB_DESC = """
Title: Full Stack Developer

We are looking for a Full Stack Developer with strong experience in JavaScript, TypeScript, React.js, Node.js, and Python.

Required Skills:
- JavaScript / TypeScript
- React.js or Next.js
- Node.js / Express.js
- Python (Flask or FastAPI)
- PostgreSQL or MongoDB
- Docker
- AWS or cloud platforms
- Git

Preferred Skills:
- LangChain or AI/ML frameworks
- Kubernetes
- CI/CD pipelines
- Redis
- GraphQL

Experience:
- 2+ years of relevant experience in full-stack development
- Strong problem solving skills
"""

def run_pipeline():
    print("=" * 60)
    print("ENTERPRISE ATS — 8-LAYER SCORING PIPELINE")
    print("=" * 60)

    # Layer 1
    print("\n[Layer 1] Smart Resume Parser...")
    parsed_resume = parse_resume(RESUME_TEXT)
    print(f"  Sections detected: skills={bool(parsed_resume.skills_text)}, exp={bool(parsed_resume.experience_text)}, edu={bool(parsed_resume.education_text)}")
    print(f"  Skills extracted: {parsed_resume.extracted_skills[:10]}")
    print(f"  Dates found: {parsed_resume.employment_dates[:5]}")

    # Layer 2
    print("\n[Layer 2] JD Analyzer...")
    parsed_jd = analyze_jd(JOB_DESC)
    print(f"  Required: {parsed_jd.required_skills}")
    print(f"  Preferred: {parsed_jd.preferred_skills}")
    print(f"  Min Experience: {parsed_jd.min_experience_years} years")

    # Layer 3
    print("\n[Layer 3] Semantic Matching Engine...")
    semantic_score = compute_semantic_score(RESUME_TEXT, JOB_DESC)
    print(f"  Semantic Score: {semantic_score}/100")

    # Layer 4
    print("\n[Layer 4] Keyword Intelligence...")
    keyword_result = compute_keyword_score(
        resume_skills=parsed_resume.extracted_skills,
        resume_full_text=RESUME_TEXT,
        required_skills=parsed_jd.required_skills,
        preferred_skills=parsed_jd.preferred_skills,
    )
    print(f"  Keyword Score: {keyword_result['score']}/100")
    print(f"  Matched: {keyword_result['matched']}")
    print(f"  Missing: {keyword_result['missing']}")
    print(f"  Implicit: {keyword_result['implicit']}")

    # Layer 5
    print("\n[Layer 5] Experience Evaluator...")
    experience_result = compute_experience_score(
        resume_text=RESUME_TEXT,
        employment_dates=parsed_resume.employment_dates,
        years_mentioned=parsed_resume.years_mentioned,
        min_required_years=parsed_jd.min_experience_years,
    )
    print(f"  Experience Score: {experience_result['score']}/100")
    print(f"  Total Years: {experience_result['total_years']}")
    print(f"  Progression: {experience_result['career_progression']}")

    # Layer 6
    print("\n[Layer 6] Impact Detector...")
    impact_result = compute_impact_score(RESUME_TEXT)
    print(f"  Impact Score: {impact_result['score']}/100")
    print(f"  Verifiability: {impact_result['verifiability_score']}/100")
    print(f"  Quantified Claims: {impact_result['quantified_claims'][:3]}")

    # Layer 7
    print("\n[Layer 7] Score Calculator...")
    score_result = calculate_final_score(
        semantic_score=semantic_score,
        keyword_score=keyword_result["score"],
        experience_score=experience_result["score"],
        impact_score=impact_result["score"],
        resume_text=RESUME_TEXT,
    )
    print(f"  FINAL ATS SCORE: {score_result['ats_score']}/100")
    print(f"  Breakdown: {json.dumps(score_result['score_breakdown'], indent=2)}")

    # Layer 8
    print("\n[Layer 8] LLM Insight Generator...")
    generator = InsightGenerator()
    insights = generator.generate_insights(
        resume_text=RESUME_TEXT,
        jd_text=JOB_DESC,
        ats_score=score_result["ats_score"],
        score_breakdown=score_result["score_breakdown"],
        matched_skills=keyword_result["matched"],
        missing_skills=keyword_result["missing"],
        verifiability_score=impact_result["verifiability_score"],
    )
    print(f"  Domain Fit: {insights.get('domain_fit')}")
    print(f"  Experience Fit: {insights.get('experience_fit')}")
    print(f"  Strong Points: {insights.get('strong_points', [])[:3]}")
    print(f"  Key Gaps: {insights.get('key_gaps', [])[:3]}")

    # Assemble final response
    evaluation = ATSResponseSchema(
        ats_score=score_result["ats_score"],
        score_breakdown=ScoreBreakdown(**score_result["score_breakdown"]),
        verifiability_score=impact_result["verifiability_score"],
        skill_match=SkillMatch(
            matched=keyword_result["matched"],
            missing=keyword_result["missing"],
            partial=keyword_result["partial"],
            implicit=keyword_result["implicit"],
            stale=experience_result.get("stale_roles", []),
        ),
        bs_flags=insights.get("bs_flags", []),
        interview_questions=insights.get("interview_questions", []),
        domain_fit=insights.get("domain_fit", "Medium"),
        experience_fit=insights.get("experience_fit", "Medium"),
        key_gaps=insights.get("key_gaps", []),
        strong_points=insights.get("strong_points", []),
        recommendations=insights.get("recommendations", []),
    )

    output = evaluation.model_dump()
    print("\n" + "=" * 60)
    print("FINAL JSON OUTPUT:")
    print("=" * 60)
    print(json.dumps(output, indent=2))

    # Save to file
    with open("real_output_v2.json", "w") as f:
        json.dump(output, f, indent=2)
    print(f"\nSaved output to real_output_v2.json")

if __name__ == "__main__":
    run_pipeline()
