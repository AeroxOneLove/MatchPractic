from datetime import date
from typing import Optional

from pydantic import BaseModel



class ExperienceResponse(BaseModel):
    uuid: str
    company_name: str
    position: str
    start_date: date
    end_date: Optional[date] = None


class JobResume(BaseModel):
    uuid: str
    full_name: str
    position: str
    skills: list[str]
    experiences: list[ExperienceResponse]
    about_me: str
