from fastapi import APIRouter
from app.routers.vacancy_route import router as vacancy_router
from app.routers.match_result import router as match_result_router



routers = APIRouter()
router_list = [
    vacancy_router,
    match_result_router
]

for router in router_list:
    routers.include_router(router)