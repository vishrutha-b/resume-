"""
Resume Service — Master Orchestrator
Runs all 8 layers in sequence:
  L1: Smart Parser → L2: JD Analyzer → L3: Semantic Engine →
  L4: Keyword Engine → L5: Experience Engine → L6: Impact Detector →
  L7: Score Calculator → L8: LLM Insight Generator
"""
import os
import uuid
import json
import shutil
from fastapi import UploadFile
from utils.resume_parser import extract_text_from_pdf, extract_text_from_docx
from utils.logger import get_logger
from config.settings import Config
from services.resume_parser_v2 import parse_resume
from services.jd_analyzer import analyze_jd
from services.semantic_engine import compute_semantic_score
from services.keyword_engine import compute_keyword_score
from services.experience_engine import compute_experience_score
from services.impact_detector import compute_impact_score
from services.score_calculator import calculate_final_score
from services.readability_engine import compute_readability
from ats_evaluator import InsightGenerator
from models.schemas import (
    ResultEnvelope, ATSResponseSchema, ScoreBreakdown, SkillMatch, ReadabilityMetrics
)
from typing import Optional

logger = get_logger(__name__)


class ResumeService:
    def __init__(self):
        self.insight_generator = InsightGenerator()

    def _extract_text(self, file_path: str, filename: str) -> str:
        if filename.endswith(".pdf"):
            return extract_text_from_pdf(file_path)
        elif filename.endswith(".docx"):
            return extract_text_from_docx(file_path)
        else:
            raise ValueError(f"Unsupported file type for file {filename}")

    # ──────────────────────────────────────────────────────────
    #  CREATE — Process a new resume upload
    # ──────────────────────────────────────────────────────────
    def process_single_resume(self, resume_file: UploadFile, job_desc: str) -> ResultEnvelope:
        filename = resume_file.filename
        unique_filename = f"{uuid.uuid4().hex[:8]}_{filename}"
        file_path = os.path.join(Config.UPLOAD_FOLDER, unique_filename)

        try:
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(resume_file.file, buffer)
            logger.info(f"Saved uploaded file {filename}")

            resume_text = self._extract_text(file_path, filename)
            logger.info(f"Extracted text for {filename} (Length: {len(resume_text)})")

            evaluation = self._run_pipeline(resume_text, job_desc)

            # Persist to database
            eval_id = None
            version = 1
            try:
                from models.database import EvaluationModel

                eval_record = EvaluationModel(
                    candidate_filename=filename,
                    ats_score=evaluation.ats_score,
                    raw_json_data=json.dumps(evaluation.model_dump()),
                    resume_text=resume_text,
                    job_description=job_desc,
                    version=1,
                )
                eval_id = eval_record.save()
                logger.info(f"Persisted Evaluation id={eval_id} to Database.")
            except Exception as e:
                logger.error(f"Failed to persist evaluation to DB: {e}")

            return ResultEnvelope(
                file_name=filename,
                evaluation_id=eval_id,
                version=version,
                evaluation=evaluation,
            )

        except Exception as e:
            logger.error(f"Error processing {filename}: {e}")
            return ResultEnvelope(file_name=filename, error=str(e))
        finally:
            if os.path.exists(file_path):
                os.remove(file_path)
                logger.info(f"Cleaned up file {filename}")

    # ──────────────────────────────────────────────────────────
    #  UPDATE — Re-score an existing evaluation
    # ──────────────────────────────────────────────────────────
    def update_evaluation(
        self,
        evaluation_id: str,
        resume_file: Optional[UploadFile] = None,
        job_desc: Optional[str] = None,
    ) -> ResultEnvelope:
        from models.database import EvaluationModel, EvaluationVersionModel

        eval_record = EvaluationModel.get_by_id(evaluation_id)
        if not eval_record:
            return ResultEnvelope(file_name="", error=f"Evaluation {evaluation_id} not found")

        eval_dict = eval_record.to_dict()

        if not resume_file and not job_desc:
            return ResultEnvelope(
                file_name=eval_dict.get("candidate_filename", ""),
                error="Provide a new resume file and/or a new job description to update"
            )

        file_path = None
        try:
            # Snapshot current version to history
            version_snapshot = EvaluationVersionModel(
                evaluation_id=eval_dict["id"],
                version=eval_dict.get("version", 1),
                candidate_filename=eval_dict.get("candidate_filename"),
                ats_score=eval_dict.get("ats_score"),
                raw_json_data=eval_dict.get("raw_json_data", "{}"),
                job_description=eval_dict.get("job_description"),
            )
            version_snapshot.save()
            logger.info(f"Snapshotted evaluation {evaluation_id} version {eval_dict.get('version')}")

            # Determine resume text
            if resume_file:
                filename = resume_file.filename
                unique_filename = f"{uuid.uuid4().hex[:8]}_{filename}"
                file_path = os.path.join(Config.UPLOAD_FOLDER, unique_filename)
                with open(file_path, "wb") as buffer:
                    shutil.copyfileobj(resume_file.file, buffer)
                
                resume_text = self._extract_text(file_path, filename)
                eval_record._data["candidate_filename"] = filename
                eval_record._data["resume_text"] = resume_text
                logger.info(f"Re-extracted text from new file: {filename}")
            else:
                resume_text = eval_dict.get("resume_text")
                filename = eval_dict.get("candidate_filename")
                if not resume_text:
                    return ResultEnvelope(
                        file_name=filename,
                        error="No stored resume text found. Please upload a new resume file."
                    )

            # Determine JD
            jd_text = job_desc if job_desc else eval_dict.get("job_description")
            if not jd_text:
                return ResultEnvelope(
                    file_name=filename,
                    error="No job description found. Please provide a job description."
                )

            # Re-run the full 8-layer pipeline
            logger.info(f"Re-scoring evaluation {evaluation_id} with pipeline...")
            evaluation = self._run_pipeline(resume_text, jd_text)

            # Update the evaluation record
            eval_record._data["ats_score"] = evaluation.ats_score
            eval_record._data["raw_json_data"] = json.dumps(evaluation.model_dump())
            eval_record._data["job_description"] = jd_text
            eval_record._data["version"] = eval_dict.get("version", 1) + 1

            eval_record.save()
            logger.info(
                f"Updated evaluation {evaluation_id} to version {eval_record._data['version']}, "
                f"new score={evaluation.ats_score}"
            )

            return ResultEnvelope(
                file_name=filename,
                evaluation_id=eval_record._data["_id"],
                version=eval_record._data["version"],
                evaluation=evaluation,
            )

        except Exception as e:
            logger.error(f"Error updating evaluation {evaluation_id}: {e}")
            return ResultEnvelope(
                file_name=eval_dict.get("candidate_filename", ""),
                error=str(e),
            )
        finally:
            if file_path and os.path.exists(file_path):
                os.remove(file_path)

    # ──────────────────────────────────────────────────────────
    #  READ — Retrieve evaluations (no user filtering)
    # ──────────────────────────────────────────────────────────
    def get_all_evaluations(self) -> list:
        """Get all evaluations."""
        from models.database import get_db, EvaluationModel
        db = get_db()
        docs = db.evaluations.find().sort("created_at", -1)
        return [EvaluationModel(**doc).to_summary() for doc in docs]

    def get_evaluation_by_id(self, evaluation_id: str) -> Optional[dict]:
        """Get a single evaluation with full data."""
        from models.database import EvaluationModel
        eval_record = EvaluationModel.get_by_id(evaluation_id)
        if not eval_record:
            return None
        return eval_record.to_full()

    def get_evaluation_history(self, evaluation_id: str) -> Optional[list]:
        """Get version history for an evaluation."""
        from models.database import get_db, EvaluationModel, EvaluationVersionModel
        eval_record = EvaluationModel.get_by_id(evaluation_id)
        if not eval_record:
            return None

        eval_dict = eval_record.to_dict()
        db = get_db()
        versions = list(db.evaluation_versions.find({"evaluation_id": evaluation_id}).sort("version", -1))

        current = {
            "version": eval_dict.get("version"),
            "ats_score": eval_dict.get("ats_score"),
            "candidate_filename": eval_dict.get("candidate_filename"),
            "is_current": True,
            "created_at": eval_dict.get("updated_at") or eval_dict.get("created_at"),
        }

        history = [current] + [EvaluationVersionModel(**v).to_dict() for v in versions]
        return history

    # ──────────────────────────────────────────────────────────
    #  PIPELINE — 8-layer scoring engine
    # ──────────────────────────────────────────────────────────
    def _run_pipeline(self, resume_text: str, jd_text: str) -> ATSResponseSchema:
        """Execute the complete 8-layer scoring pipeline."""

        logger.info("=== Layer 1: Smart Resume Parser ===")
        parsed_resume = parse_resume(resume_text)

        logger.info("=== Layer 2: JD Analyzer ===")
        parsed_jd = analyze_jd(jd_text)

        logger.info("=== Layer 3: Semantic Matching Engine ===")
        semantic_score = compute_semantic_score(resume_text, jd_text)

        logger.info("=== Layer 4: Keyword Intelligence ===")
        keyword_result = compute_keyword_score(
            resume_skills=parsed_resume.extracted_skills,
            resume_full_text=resume_text,
            required_skills=parsed_jd.required_skills,
            preferred_skills=parsed_jd.preferred_skills,
        )

        logger.info("=== Layer 5: Experience Evaluator ===")
        experience_result = compute_experience_score(
            resume_text=resume_text,
            employment_dates=parsed_resume.employment_dates,
            years_mentioned=parsed_resume.years_mentioned,
            min_required_years=parsed_jd.min_experience_years,
        )

        logger.info("=== Layer 6: Impact Detector ===")
        impact_result = compute_impact_score(resume_text)

        logger.info("=== Layer 6b: Readability Engine ===")
        readability_result = compute_readability(
            resume_text=resume_text,
            extracted_skills=parsed_resume.extracted_skills,
        )

        logger.info("=== Layer 7: Score Calculator ===")
        score_result = calculate_final_score(
            semantic_score=semantic_score,
            keyword_score=keyword_result["score"],
            experience_score=experience_result["score"],
            impact_score=impact_result["score"],
            resume_text=resume_text,
        )

        logger.info("=== Layer 8: LLM Insight Generator ===")
        insights = self.insight_generator.generate_insights(
            resume_text=resume_text,
            jd_text=jd_text,
            ats_score=score_result["ats_score"],
            score_breakdown=score_result["score_breakdown"],
            matched_skills=keyword_result["matched"],
            missing_skills=keyword_result["missing"],
            verifiability_score=impact_result["verifiability_score"],
        )

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
            readability=ReadabilityMetrics(**readability_result),
            bs_flags=insights.get("bs_flags", []) + keyword_result.get("stuffing_flags", []),
            interview_questions=insights.get("interview_questions", []),
            domain_fit=insights.get("domain_fit", "Medium"),
            experience_fit=insights.get("experience_fit", "Medium"),
            key_gaps=insights.get("key_gaps", []),
            strong_points=insights.get("strong_points", []),
            recommendations=insights.get("recommendations", []),
        )

        logger.info(f"=== Pipeline Complete: ATS Score = {evaluation.ats_score} ===")
        return evaluation
