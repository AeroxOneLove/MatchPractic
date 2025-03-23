from pydantic import BaseModel, UUID4

    
class JobResume(BaseModel):
    general_work_experience: int
    uuid: UUID4
    position: str
    skills: list[str]
    about_me: str

