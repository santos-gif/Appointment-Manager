from fastapi import APIRouter

from backend.schemas.user import LoginCredentials

router = APIRouter(prefix="/api/auth")

@router("/login")
def login(credentials:LoginCredentials):
	
def register(credentials)
