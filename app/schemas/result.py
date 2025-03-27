from pydantic import BaseModel


class MatchResult(BaseModel):
    match_percentage: int
    matched: list[str]
    didnt_match: list[str]
