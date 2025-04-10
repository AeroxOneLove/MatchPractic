from fastapi import APIRouter
from app.schemas import JobResume, JobVacancy
from app.schemas.result import MatchResult
from app.services.match_model import compare_text_with_ai


router = APIRouter()


@router.post("/vacancy_match", response_model=MatchResult)
async def match_vacancy(job: JobVacancy, resume: JobResume) -> MatchResult:
    result: dict[str, str | int]  = compare_text_with_ai(resume, job)
    return MatchResult(
        match_percentage=result["match_percentage"],
        matched=result["matched"],
        didnt_match=result["didnt_match"]
    )