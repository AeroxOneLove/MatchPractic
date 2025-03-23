from pydantic import BaseModel


class JobVacancy(BaseModel):
    general_work_experience: int
    position: str
    skills: list[str]

