from fastapi import APIRouter, Depends

from .exceptions import InvalidCredentialsException
from ...db import db_instance
from .validator import AuthValidator
from sqlalchemy.ext.asyncio import AsyncSession
from backend.schemas.user import LoginCredentials

router = APIRouter(prefix="/api/auth")

@router.post("/login")
async def login(credentials:LoginCredentials, db:AsyncSession=Depends(db_instance.get_db)):
	await AuthValidator.validate_login(credentials, db)
	





@router.post("/register")
def register(credentials):

