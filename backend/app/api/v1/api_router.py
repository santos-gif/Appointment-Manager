from fastapi import APIRouter
from app.api.v1.auth_router import router as auth_router
from app.api.v1.nodes_router import router as nodes_router
from app.api.v1.availability_router import router as availability_router
from app.api.v1.booking_router import router as booking_router
from app.api.v1.search_router import router as search_router
from app.api.v1.integrations_router import router as integrations_router

api_router = APIRouter()

api_router.include_router(auth_router)
api_router.include_router(nodes_router)
api_router.include_router(availability_router)
api_router.include_router(booking_router)
api_router.include_router(search_router)
api_router.include_router(integrations_router)
