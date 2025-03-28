from pydantic import BaseModel


class MatchResult(BaseModel):
    match_percentage: float
    matched: list[str]
    didnt_match: list[str]
