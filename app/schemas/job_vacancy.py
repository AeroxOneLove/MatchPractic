from pydantic import BaseModel, PositiveFloat


class JobVacancy(BaseModel):
    uuid: str
    title: str
    description: str
    requirements: str
    conditions: str
    salary: PositiveFloat
    employment_type: str