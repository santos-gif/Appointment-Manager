from typing import Any, Optional
from fastapi import HTTPException, status


class DomainException(Exception):
    """Base class for all domain-specific business logic errors."""
    def __init__(self, message: str, code: str = "DOMAIN_ERROR", details: Optional[Any] = None):
        super().__init__(message)
        self.message = message
        self.code = code
        self.details = details or {}


class NodeNotFoundException(DomainException):
    def __init__(self, node_id: str):
        super().__init__(f"Hierarchical node {node_id} was not found.", code="NODE_NOT_FOUND")


class AccessDeniedException(DomainException):
    def __init__(self, message: str = "Access to the requested node is forbidden by visibility guardrails."):
        super().__init__(message, code="ACCESS_DENIED")


class DoubleBookingException(DomainException):
    def __init__(self, message: str = "Target resource has already been booked for this timeslot."):
        super().__init__(message, code="DOUBLE_BOOKING_CONFLICT")


class IntentEscalationRequiredException(DomainException):
    def __init__(self, triage_project_id: str, message: str = "Direct booking forbidden. Routing intent through intake triage pipeline."):
        super().__init__(message, code="INTENT_ESCALATION_REQUIRED", details={"triage_project_id": triage_project_id})


class InvalidTokenException(DomainException):
    def __init__(self, message: str = "Authentication token is invalid or expired."):
        super().__init__(message, code="INVALID_TOKEN")
