from fastapi import APIRouter, Request, HTTPException
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
import json

router = APIRouter()
templates = Jinja2Templates(directory="templates")

@router.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@router.get("/evaluations", response_class=HTMLResponse)
async def evaluations_page(request: Request):
    return templates.TemplateResponse("evaluations.html", {"request": request})

@router.get("/evaluation/{evaluation_id}/resume", response_class=HTMLResponse)
async def premium_resume(request: Request, evaluation_id: str):
    from models.database import EvaluationModel
    
    evaluation = EvaluationModel.get_by_id(evaluation_id)
    if not evaluation:
        raise HTTPException(status_code=404, detail="Evaluation not found.")
        
    eval_dict = evaluation.to_dict()
    if not eval_dict.get("optimized_resume_data"):
        raise HTTPException(status_code=404, detail="Optimized resume data not found for this evaluation.")

    try:
        data = json.loads(eval_dict["optimized_resume_data"])
        # The AI returns a JSON with a "structured_data" field
        structured_data = data.get("structured_data", {})
        if not structured_data:
            # Fallback if the whole object is the data
            structured_data = data

        return templates.TemplateResponse("premium_resume.html", {"request": request, "data": structured_data})
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error parsing resume data: {str(e)}")
