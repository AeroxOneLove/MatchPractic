from datetime import date
from typing import Optional
from pydantic import BaseModel, UUID4

    
class JobResume(BaseModel):
    start_date: date
    end_date: Optional[date] = None
    uuid: UUID4
    position: str
    skills: list[str]
    about_me: str

