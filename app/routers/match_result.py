from fastapi import APIRouter
from app.schemas import MatchResult
from app.services import match_results_store



router = APIRouter()

@router.get("/match_results", response_model=list[MatchResult])
async def get_match_results() -> list[MatchResult]:
    return match_results_store  
