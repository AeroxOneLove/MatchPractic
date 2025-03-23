from fastapi import APIRouter
from app.schemas import MatchResult


router = APIRouter()


@router.get("/match_results", response_model=list[MatchResult])
async def get_match_results():
    match_results_store = [
  {
    "Match percentage": 30,
    "Matched": [
      "Python"
    ],
    "Possible match": [
      "GitHub",
      "Git",
      "CI/CD"
    ],
    "Didn't match": [
      "experience (от 10 лет)",
      "region (Rostov)",
      "education (Высшее)",
      "skills [SQL, Vue.js, RestApi, Node.js, Express, PostgreSQL, MongoDB, Docker, Kubernetes, Scala]"
    ]
  }
]
    return match_results_store