from fastapi import APIRouter
from app.routers.vacancy_route import router as vacancy_router


routers = APIRouter()
router_list = [
    vacancy_router,
]

for router in router_list:
    routers.include_router(router)