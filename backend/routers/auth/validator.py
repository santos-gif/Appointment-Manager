
from sqlalchemy import select

from .exceptions import InvalidCredentialsException
from ...models import User
from backend.schemas.user import LoginCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from .helpers import verify_password
class AuthValidator:
	@staticmethod
	async def validate_login(credentials:LoginCredentials, db:AsyncSession) -> LoginCredentials
		query = select(User).where(User.email == credentials.email)
		result = await db.execute(query)
		user = result.scalar_one_or_none()

		if not user or not verify_password(credentials.password, user.password):
			raise InvalidCredentialsException()

		return credentials
