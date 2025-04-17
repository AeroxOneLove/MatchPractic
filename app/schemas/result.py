from pydantic import BaseModel


class MatchResult(BaseModel):
    match_percentage: int
    didnt_match: list[str]
