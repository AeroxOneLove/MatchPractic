from fastapi import APIRouter

from app.schemas import JobResume, JobVacancy
from app.schemas.result import MatchResult
from app.services.match_service import MatchService
from app.services.summarization_service import SummarizationService

router = APIRouter()
match_service = MatchService()
summarization_service = SummarizationService()


@router.post("/vacancy_match", response_model=MatchResult)
async def match_vacancy(job: JobVacancy, resume: JobResume):
    result = await match_service.compare_resume_vacancy(resume.dict(), job.dict())
    return MatchResult(match_percentage=result["match"], didnt_match=result.get("didnt_match", []))


@router.post("/summary", response_model=str)
async def summary(vacancy: JobVacancy):
    vacancy_text = (
        f"{vacancy.title}."
        f"{vacancy.description}."
        f"{vacancy.requirements}."
        f"{vacancy.conditions}."
        f"Зарплата: {vacancy.salary} рублей."
    )
    summary = summarization_service.generate_summary(vacancy_text)
    return str(summary)
