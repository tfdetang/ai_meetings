"""Custom exceptions for the AI Agent Meeting System"""

from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from .models import MeetingStatus


class ValidationError(Exception):
    """Input validation error"""
    def __init__(self, message: str, field: str):
        super().__init__(message)
        self.field = field


class NotFoundError(Exception):
    """Resource not found error"""
    def __init__(self, message: str, resource_type: str, resource_id: str):
        super().__init__(message)
        self.resource_type = resource_type
        self.resource_id = resource_id


class APIError(Exception):
    """API call error"""
    def __init__(self, message: str, provider: str, status_code: Optional[int] = None):
        super().__init__(message)
        self.provider = provider
        self.status_code = status_code


class MeetingStateError(Exception):
    """Meeting state error"""
    def __init__(self, message: str, current_state: 'MeetingStatus'):
        super().__init__(message)
        self.current_state = current_state


class PermissionError(Exception):
    """Permission error"""
    def __init__(self, message: str, required_role: str):
        super().__init__(message)
        self.required_role = required_role


class AgendaError(Exception):
    """Agenda operation error"""
    def __init__(self, message: str, agenda_id: str):
        super().__init__(message)
        self.agenda_id = agenda_id
