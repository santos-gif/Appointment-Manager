
from backend.schemas.user import LoginCredentials
from sqlalchemy.ext.asyncio import AsyncSession

class AuthValidator:
	@staticmethod
	def validate_login(credentials:LoginCredentials, db:AsyncSession) -> LoginCredentials
		