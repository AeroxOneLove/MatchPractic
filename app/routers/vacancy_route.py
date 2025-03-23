from fastapi import APIRouter
from app.schemas import JobResume, JobVacancy


router = APIRouter()


@router.post("/vacancy_route", response_model=list)
async def match_vacancy(job: JobVacancy, resume: JobResume):
    result = job
    result2 = resume
    return result, result2

