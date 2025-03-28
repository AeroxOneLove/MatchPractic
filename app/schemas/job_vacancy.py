from pydantic import BaseModel


class JobVacancy(BaseModel):
    general_work_experience: float
    position: str
    skills: list[str]

