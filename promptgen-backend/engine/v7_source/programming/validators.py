from .models import OverrideRequest


def validate_override_request(req: OverrideRequest) -> OverrideRequest:
    if not req.override_id or not req.coach_id or not req.client_id:
        raise ValueError("override_id, coach_id, and client_id are required")
    if not isinstance(req.justification_note, str):
        raise ValueError("justification_note must be a string")
    return req
