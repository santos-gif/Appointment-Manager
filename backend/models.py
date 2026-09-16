from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import UUID as SQLUUID
import uuid
class Base(DeclarativeBase):
	pass

class User(Base):
	__tablename__ = "users"
	id: Mapped[uuid.UUID] = mapped_column(
		SQLUUID(as_uuid=True),
		primary_key=True,
		default=uuid.uuid4
	)
	email: Mapped[str] = mapped_column(unique=True)
	username: Mapped[str] = mapped_column(unique=True, index=True)
	name: Mapped[str] = mapped_column()
	password: Mapped[str] = mapped_column()
