from fastapi import APIRouter
from app.schemas import MatchResult
from app.services import compare_text_with_ai



router = APIRouter()

@router.get("/match_results", response_model=list[MatchResult])
async def get_match_results() -> list[MatchResult]:
    return compare_text_with_ai
