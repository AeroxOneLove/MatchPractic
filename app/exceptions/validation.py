from fastapi import HTTPException
from app.schemas import JobResume, JobVacancy

def validate_request(job: JobVacancy, resume: JobResume):
    if resume.general_work_experience < 0:
        raise HTTPException(status_code=400, detail="Опыт работы не может быть отрицательным")
    
    if job.general_work_experience < 0:
        raise HTTPException(status_code=400, detail="Опыт в вакансии не может быть отрицательным")
    
    if not resume.skills or not job.skills:
        raise HTTPException(status_code=400, detail="Навыки не могут быть пустыми")
