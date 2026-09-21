import enum
import uuid
from sqlalchemy import JSON, Uuid
from sqlalchemy.dialects.postgresql import JSONB, UUID as PG_UUID


# Universal UUID type: native PG UUID on PostgreSQL, string with auto-uuid conversion on SQLite
def UuidType():
    return Uuid(as_uuid=True).with_variant(PG_UUID(as_uuid=True), "postgresql")


# Universal JSON type: JSONB on PostgreSQL, standard JSON on SQLite
def JsonType():
    return JSON().with_variant(JSONB, "postgresql")
