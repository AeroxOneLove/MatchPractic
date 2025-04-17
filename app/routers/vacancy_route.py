from fastapi import APIRouter
from app.schemas import JobResume, JobVacancy
from app.schemas.result import MatchResult
from app.services.match_model import MatchService

router = APIRouter()
match_service = MatchService()


@router.post("/vacancy_match", response_model=MatchResult)
async def match_vacancy(job: JobVacancy, resume: JobResume):
    result = await match_service.compare_resume_vacancy(resume.dict(), job.dict())
    return MatchResult(match_percentage=result["match"], didnt_match=result.get("didnt_match", []))
