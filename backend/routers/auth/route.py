from fastapi import APIRouter, Depends
from ...db import db_instance
from sqlalchemy.ext.asyncio import AsyncSession
from backend.schemas.user import LoginCredentials

router = APIRouter(prefix="/api/auth")

@router.post("/login")
def login(credentials:LoginCredentials, db:AsyncSession=Depends(db_instance.get_db)):
	try:
		a

@router.post("/register")
def register(credentials):

