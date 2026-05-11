from fastapi import APIRouter, File, Form, UploadFile, HTTPException
from fastapi.responses import JSONResponse
import os
from typing import Optional, List
from services.resume_service import ResumeService
from utils.logger import get_logger
import json

logger = get_logger(__name__)
router = APIRouter()
resume_service = ResumeService()

# Allowed file extensions whitelist
ALLOWED_EXTENSIONS = {'.pdf', '.docx'}

def _validate_file_extension(filename: str) -> bool:
    """Check if file has an allowed extension."""
    if not filename:
        return False
    ext = os.path.splitext(filename)[1].lower()
    return ext in ALLOWED_EXTENSIONS

# ──────────────────────────────────────────────────────────
#  Health Check
# ──────────────────────────────────────────────────────────
@router.get("/health")
def health_check():
    """Health check endpoint for load balancers and monitoring."""
    return {"status": "healthy", "service": "ats-scoring-engine"}

# ──────────────────────────────────────────────────────────
#  CREATE — Screen a new resume
# ──────────────────────────────────────────────────────────
@router.post("/screen_resume", status_code=201)
def screen_resume(
    resume: UploadFile = File(...),
    job_desc: str = Form(...)
):
    """Upload a resume + JD and get ATS evaluation."""
    job_desc = job_desc.strip()
    
    if not resume.filename:
        raise HTTPException(status_code=400, detail="No file selected")

    if not _validate_file_extension(resume.filename):
        raise HTTPException(
            status_code=400, 
            detail=f"Unsupported file type. Only {', '.join(ALLOWED_EXTENSIONS)} files are accepted."
        )

    if len(job_desc) < 10:
        raise HTTPException(status_code=400, detail="Job description must be at least 10 characters long")

    logger.info("POST /screen_resume received")
    result = resume_service.process_single_resume(resume, job_desc)

    if result.error:
        raise HTTPException(status_code=500, detail={"file_name": result.file_name, "error": result.error})

    return result.model_dump()

# ──────────────────────────────────────────────────────────
#  READ — List all evaluations
# ──────────────────────────────────────────────────────────
@router.get("/evaluations")
def list_evaluations():
    """Get all evaluations."""
    logger.info("GET /evaluations")
    evaluations = resume_service.get_all_evaluations()
    return {
        "count": len(evaluations),
        "evaluations": evaluations,
    }

# ──────────────────────────────────────────────────────────
#  READ — Get a single evaluation by ID
# ──────────────────────────────────────────────────────────
@router.get("/evaluations/{evaluation_id}")
def get_evaluation(evaluation_id: str):
    """Get a single evaluation with full scoring data."""
    logger.info(f"GET /evaluations/{evaluation_id}")
    result = resume_service.get_evaluation_by_id(evaluation_id)

    if result is None:
        raise HTTPException(status_code=404, detail="Evaluation not found")

    return result

# ──────────────────────────────────────────────────────────
#  UPDATE — Re-score with new resume and/or JD
# ──────────────────────────────────────────────────────────
@router.put("/evaluations/{evaluation_id}")
def update_evaluation(
    evaluation_id: str,
    resume: Optional[UploadFile] = File(None),
    job_desc: Optional[str] = Form(None)
):
    """
    Update an existing evaluation.
    """
    logger.info(f"PUT /evaluations/{evaluation_id}")

    if resume and resume.filename:
        if not _validate_file_extension(resume.filename):
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported file type. Only {', '.join(ALLOWED_EXTENSIONS)} files are accepted."
            )

    jd_text = job_desc.strip() if job_desc else None
    if jd_text and len(jd_text) < 10:
        raise HTTPException(status_code=400, detail="Job description must be at least 10 characters long")

    if not resume and not jd_text:
        raise HTTPException(
            status_code=400,
            detail="Provide a new resume file and/or job description to update"
        )

    result = resume_service.update_evaluation(
        evaluation_id=evaluation_id,
        resume_file=resume,
        job_desc=jd_text,
    )

    if result.error:
        if "not found" in result.error.lower():
            raise HTTPException(status_code=404, detail=result.error)
        else:
            raise HTTPException(status_code=500, detail=result.error)

    return result.model_dump()

# ──────────────────────────────────────────────────────────
#  VERSION HISTORY
# ──────────────────────────────────────────────────────────
@router.get("/evaluations/{evaluation_id}/history")
def get_evaluation_history(evaluation_id: str):
    """Get version history for an evaluation."""
    logger.info(f"GET /evaluations/{evaluation_id}/history")
    history = resume_service.get_evaluation_history(evaluation_id)

    if history is None:
        raise HTTPException(status_code=404, detail="Evaluation not found")

    return {
        "evaluation_id": evaluation_id,
        "total_versions": len(history),
        "history": history,
    }

# ──────────────────────────────────────────────────────────
#  OPTIMIZE — AI-powered resume improvement
# ──────────────────────────────────────────────────────────
@router.post("/evaluations/{evaluation_id}/optimize")
def optimize_resume(evaluation_id: str):
    """
    Generate an AI-optimized version of a previously evaluated resume.
    """
    logger.info(f"POST /evaluations/{evaluation_id}/optimize")

    from models.database import EvaluationModel
    from services.resume_optimizer import ResumeOptimizer

    eval_record = EvaluationModel.get_by_id(evaluation_id)
    if not eval_record:
        raise HTTPException(status_code=404, detail=f"Evaluation {evaluation_id} not found")
        
    eval_dict = eval_record.to_dict()

    if not eval_dict.get("resume_text"):
        raise HTTPException(status_code=400, detail="No stored resume text. Please re-upload the resume.")

    if not eval_dict.get("job_description"):
        raise HTTPException(status_code=400, detail="No stored job description. Please update with a JD first.")

    evaluation_data = json.loads(eval_dict.get("raw_json_data", "{}"))

    optimizer = ResumeOptimizer()
    
    result = optimizer.optimize(
        resume_text=eval_dict["resume_text"],
        jd_text=eval_dict["job_description"],
        previous_evaluation=evaluation_data,
    )
    
    if result.get("error") or not result.get("updated_resume"):
        raise HTTPException(status_code=500, detail=result.get("error", "Failed to optimize"))

    # Calculate TRUE new ATS score using our 8-layer deterministic engine
    try:
        from services.resume_service import ResumeService
        rs = ResumeService()
        logger.info("Calculating mathematically proven ATS score for optimized resume...")
        new_eval = rs._run_pipeline(result.get("updated_resume", ""), eval_dict["job_description"])
        
        # Honest score from the pipeline
        final_score = new_eval.ats_score
        
        result["ats_score_estimate"] = final_score
        logger.info(f"Original Score: {eval_dict.get('ats_score')} -> Optimized Honest Score: {final_score}")
    except Exception as e:
        logger.error(f"Failed to calculate true ATS score for optimized resume: {e}")

    # Save to database
    eval_record._data["optimized_resume_text"] = result.get("updated_resume", "")
    eval_record._data["optimized_resume_data"] = json.dumps(result)
    eval_record.save()
    
    logger.info(f"Saved optimized resume for evaluation {evaluation_id}")

    result["evaluation_id"] = evaluation_id
    result["original_score"] = eval_dict.get("ats_score")

    return result

# ──────────────────────────────────────────────────────────
#  GET OPTIMIZED — Retrieve the saved optimized resume
# ──────────────────────────────────────────────────────────
@router.get("/evaluations/{evaluation_id}/optimized")
def get_optimized_resume(evaluation_id: str):
    """
    Retrieve the saved optimized resume for an evaluation.
    """
    from models.database import EvaluationModel

    eval_record = EvaluationModel.get_by_id(evaluation_id)
    if not eval_record:
        raise HTTPException(status_code=404, detail=f"Evaluation {evaluation_id} not found")

    eval_dict = eval_record.to_dict()

    if not eval_dict.get("optimized_resume_text"):
        raise HTTPException(status_code=404, detail="No optimized resume found. Call POST /api/evaluations/{id}/optimize first.")

    optimization_data = {}
    if eval_dict.get("optimized_resume_data"):
        optimization_data = json.loads(eval_dict.get("optimized_resume_data"))

    return {
        "evaluation_id": evaluation_id,
        "original_score": eval_dict.get("ats_score"),
        "updated_resume": eval_dict.get("optimized_resume_text"),
        "improvements_made": optimization_data.get("improvements_made", []),
        "keyword_coverage": optimization_data.get("keyword_coverage", {}),
        "ats_score_estimate": optimization_data.get("ats_score_estimate", 0),
        "score_justification": optimization_data.get("score_justification", ""),
    }

# ──────────────────────────────────────────────────────────
#  DOWNLOAD — Optimized resume as PDF
# ──────────────────────────────────────────────────────────
@router.get("/evaluations/{evaluation_id}/optimized/download")
def download_optimized_resume(evaluation_id: str):
    """
    Download the optimized resume as a PDF file.
    """
    from models.database import EvaluationModel
    from fastapi.responses import StreamingResponse
    from fpdf import FPDF
    import io

    eval_record = EvaluationModel.get_by_id(evaluation_id)
    if not eval_record:
        raise HTTPException(status_code=404, detail=f"Evaluation {evaluation_id} not found")

    eval_dict = eval_record.to_dict()

    if not eval_dict.get("optimized_resume_text"):
        raise HTTPException(status_code=404, detail="No optimized resume found. Call POST /api/evaluations/{id}/optimize first.")

    try:
        resume_text = eval_dict.get("optimized_resume_text")
        filename = eval_dict.get("candidate_filename", "resume").rsplit('.', 1)[0]

        def sanitize(text):
            # Map known Unicode chars to safe ASCII equivalents
            replacements = {
                '\u2022': '-',   # bullet •
                '\u2018': "'",   # left single quote
                '\u2019': "'",   # right single quote
                '\u201c': '"',   # left double quote
                '\u201d': '"',   # right double quote
                '\u2013': '-',   # en dash
                '\u2014': '-',   # em dash
                '\u2026': '...', # ellipsis
                '\u00a0': ' ',   # non-breaking space
                '\ufeff': '',    # BOM
                '\u2192': '->',  # right arrow →
                '\u2190': '<-',  # left arrow ←
                '\u2713': 'v',   # checkmark ✓
                '\u2714': 'v',   # heavy checkmark ✔
                '\u2715': 'x',   # cross ✕
                '\u2716': 'x',   # heavy cross ✖
                '\u2550': '=',   # box drawing double horizontal ═
                '\u2551': '|',   # box drawing double vertical ║
                '\u25cf': '-',   # black circle ●
                '\u25cb': '-',   # white circle ○
                '\u25aa': '-',   # black small square ▪
                '\u25ab': '-',   # white small square ▫
                '\u00e2': 'a',   # â
                '\u2019': "'",
            }
            for old, new in replacements.items():
                text = text.replace(old, new)
            # Final fallback: strip any character outside printable latin-1
            return text.encode('latin-1', errors='ignore').decode('latin-1')

        resume_text = sanitize(resume_text)
        filename_clean = sanitize(filename)

        pdf = FPDF()
        pdf.set_auto_page_break(auto=True, margin=20)
        pdf.add_page()

        lines = resume_text.split('\n')

        import re
        def render_rich_text(pdf_obj, text, line_height=6):
            parts = re.split(r'(\*\*.*?\*\*)', text)
            for part in parts:
                if part.startswith('**') and part.endswith('**'):
                    bold_text = part[2:-2]
                    pdf_obj.set_font("Helvetica", "B", 10)
                    pdf_obj.write(line_height, bold_text)
                    pdf_obj.set_font("Helvetica", "", 10)
                else:
                    pdf_obj.write(line_height, part)
            pdf_obj.ln(line_height)

        # Track whether we've output the name/contact header (first 3 lines)
        header_lines_remaining = 3

        for line in lines:
            stripped = line.strip()

            # Blank line
            if not stripped:
                pdf.ln(3)
                continue

            # First 3 lines: name, contact, job title header block
            if header_lines_remaining > 0:
                if header_lines_remaining == 3:
                    # Candidate name — large bold centered
                    pdf.set_font("Helvetica", "B", 16)
                    pdf.set_text_color(30, 30, 30)
                    pdf.cell(0, 10, stripped, new_x="LMARGIN", new_y="NEXT", align="C")
                elif header_lines_remaining == 2:
                    # Contact line — small centered
                    pdf.set_font("Helvetica", "", 9)
                    pdf.set_text_color(80, 80, 80)
                    pdf.cell(0, 6, stripped, new_x="LMARGIN", new_y="NEXT", align="C")
                elif header_lines_remaining == 1:
                    # Job title — medium italic centered
                    pdf.set_font("Helvetica", "I", 11)
                    pdf.set_text_color(59, 130, 246)
                    pdf.cell(0, 7, stripped, new_x="LMARGIN", new_y="NEXT", align="C")
                    pdf.ln(2)
                    pdf.set_draw_color(59, 130, 246)
                    pdf.set_line_width(0.6)
                    pdf.line(20, pdf.get_y(), 190, pdf.get_y())
                    pdf.ln(4)
                header_lines_remaining -= 1
                continue

            # ALL CAPS section header (e.g. PROFESSIONAL EXPERIENCE)
            is_section_header = (
                stripped.isupper() and 3 < len(stripped) < 60
                and not stripped.startswith('-')
            )

            # Bold job title / project line (wrapped in ** or contains --)
            is_bold_line = stripped.startswith('**') and stripped.endswith('**')

            # Skill category line (e.g. "Languages: Java, Python")
            is_skill_category = (
                ':' in stripped
                and not stripped.startswith('-')
                and len(stripped) < 120
                and stripped.split(':')[0].replace(' ', '').isalpha()
            )

            if is_section_header:
                pdf.set_x(pdf.l_margin)
                pdf.ln(5)
                pdf.set_font("Helvetica", "B", 12)
                pdf.set_text_color(59, 130, 246)
                pdf.cell(0, 8, stripped, new_x="LMARGIN", new_y="NEXT")
                pdf.set_draw_color(200, 200, 200)
                pdf.set_line_width(0.3)
                pdf.line(pdf.l_margin, pdf.get_y(), 190, pdf.get_y())
                pdf.ln(3)
                pdf.set_text_color(50, 50, 50)

            elif is_bold_line:
                # Job title / project title line — bold, dark
                inner = stripped[2:-2]
                pdf.set_x(pdf.l_margin)
                pdf.ln(3)
                pdf.set_font("Helvetica", "B", 10)
                pdf.set_text_color(30, 30, 30)
                pdf.multi_cell(0, 6, inner)
                pdf.set_text_color(50, 50, 50)

            elif stripped.startswith('- '):
                # Bullet point — indented with bullet character
                bullet_text = stripped[2:].strip()
                pdf.set_x(pdf.l_margin)
                pdf.set_font("Helvetica", "", 10)
                pdf.set_text_color(50, 50, 50)
                # Write bullet marker in a fixed-width cell then the text
                page_width = pdf.w - pdf.l_margin - pdf.r_margin
                bullet_marker_w = 6
                text_w = page_width - bullet_marker_w
                pdf.set_x(pdf.l_margin + 3)
                pdf.cell(bullet_marker_w, 6, "-", border=0)
                pdf.set_x(pdf.l_margin + 3 + bullet_marker_w)
                pdf.multi_cell(text_w, 6, bullet_text)

            elif is_skill_category:
                # Skills sub-category: bold label, regular value — use multi_cell for safety
                pdf.set_x(pdf.l_margin)
                colon_idx = stripped.index(':')
                label = stripped[:colon_idx + 1]
                value = stripped[colon_idx + 1:].strip()
                combined = f"{label} {value}"
                pdf.set_font("Helvetica", "", 10)
                pdf.set_text_color(50, 50, 50)
                # Measure label width to render bold portion
                pdf.set_font("Helvetica", "B", 10)
                label_w = pdf.get_string_width(label + " ")
                pdf.set_font("Helvetica", "", 10)
                page_w = pdf.w - pdf.l_margin - pdf.r_margin
                # Render as single multi_cell with bold label inlined
                pdf.set_font("Helvetica", "B", 10)
                pdf.write(6, label + " ")
                pdf.set_font("Helvetica", "", 10)
                remaining_w = page_w - pdf.get_string_width(label + " ")
                if remaining_w > 10:
                    pdf.multi_cell(0, 6, value)
                else:
                    pdf.ln(6)
                    pdf.set_x(pdf.l_margin)
                    pdf.multi_cell(0, 6, value)

            else:
                # Regular text line
                pdf.set_x(pdf.l_margin)
                pdf.set_font("Helvetica", "", 10)
                pdf.set_text_color(50, 50, 50)
                if '**' in stripped:
                    render_rich_text(pdf, stripped)
                else:
                    pdf.multi_cell(0, 6, stripped)

        pdf.ln(8)
        pdf.set_font("Helvetica", "I", 8)
        pdf.set_text_color(150, 150, 150)
        pdf.cell(0, 5, "Generated by Aura ATS Resume Optimization Engine", align="C")

        pdf_bytes = pdf.output()
        pdf_buffer = io.BytesIO(pdf_bytes)
        pdf_buffer.seek(0)

        safe_filename = filename_clean.replace(' ', '_') + '_optimized.pdf'

        return StreamingResponse(
            pdf_buffer, 
            media_type="application/pdf", 
            headers={"Content-Disposition": f"attachment; filename={safe_filename}"}
        )

    except Exception as e:
        logger.error(f"PDF generation failed for evaluation {evaluation_id}: {e}")
        raise HTTPException(status_code=500, detail=f"PDF generation failed: {str(e)}")
