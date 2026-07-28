"""
governance_service/app/api/routes/feedback.py
-----------------------------------------------
POST /api/v1/feedback  — Submit user feedback (from Member 4 Next.js)
"""

from __future__ import annotations

import hashlib

from fastapi import APIRouter, Body

from governance_service.app.analytics.adapter import analytics_adapter
from governance_service.app.analytics.events import EventType, build_feedback_submitted
from governance_service.app.utils.id_generator import new_event_id, new_request_id
from governance_service.app.utils.logger import get_logger

from shared.schemas.governance import FeedbackRequest, FeedbackResponse

log = get_logger(__name__)
router = APIRouter()


@router.post(
    "/feedback",
    response_model=FeedbackResponse,
    summary="Submit user feedback for a response",
    description=(
        "Records rating and helpfulness. Comment text is hashed before storage "
        "— the raw comment is never persisted."
    ),
)
async def submit_feedback(request: FeedbackRequest = Body(...)) -> FeedbackResponse:
    log.info(
        "Feedback received",
        extra={
            "request_id": request.request_id,
            "rating": request.rating,
            "helpful": request.helpful,
            "user_role": request.user_role,
        },
    )

    # Hash comment — never store raw free text
    comment_hash = None
    if request.comment:
        comment_hash = hashlib.sha256(request.comment.encode()).hexdigest()

    feedback_id = new_event_id()

    stored = analytics_adapter.write_feedback(
        feedback_id=feedback_id,
        request_id=request.request_id,
        original_request_id=request.original_request_id,
        rating=request.rating,
        helpful=request.helpful,
        user_role=request.user_role,
        comment_hash=comment_hash,
    )

    # Also emit a KPI event
    analytics_adapter.capture(
        event_type=EventType.FEEDBACK_SUBMITTED,
        properties=build_feedback_submitted(
            request_id=request.request_id,
            original_request_id=request.original_request_id,
            rating=request.rating,
            helpful=request.helpful,
            user_role=request.user_role,
        ),
        request_id=request.request_id,
        user_role=request.user_role,
    )

    return FeedbackResponse(
        request_id=request.request_id,
        stored=stored,
        message="Thank you for your feedback. It helps us improve MediTrust AI.",
    )
