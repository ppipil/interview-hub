from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, status

from app.dependencies import get_interview_service
from app.models.api import (
  CreateSessionEnvelope,
  CreateSessionRequest,
  FeedbackEnvelope,
  InterviewRole,
  InterviewersEnvelope,
  SendMessageEnvelope,
  SendMessageRequest,
)
from app.services.interview import InterviewService

router = APIRouter(prefix="/api/v1")


@router.get("/interviewers", response_model=InterviewersEnvelope, tags=["Interviewers"])
def list_interviewers(
  role: Optional[InterviewRole] = None,
  service: InterviewService = Depends(get_interview_service),
) -> InterviewersEnvelope:
  return InterviewersEnvelope(data=service.list_interviewers(role))


@router.post(
  "/interview-sessions",
  response_model=CreateSessionEnvelope,
  status_code=status.HTTP_201_CREATED,
  tags=["Sessions"],
)
async def create_session(
  payload: CreateSessionRequest,
  service: InterviewService = Depends(get_interview_service),
) -> CreateSessionEnvelope:
  return CreateSessionEnvelope(data=await service.create_session(payload))


@router.post(
  "/interview-sessions/{session_id}/messages",
  response_model=SendMessageEnvelope,
  tags=["Messages"],
)
async def send_message(
  session_id: str,
  payload: SendMessageRequest,
  service: InterviewService = Depends(get_interview_service),
) -> SendMessageEnvelope:
  return SendMessageEnvelope(data=await service.send_message(session_id, payload))


@router.get(
  "/interview-sessions/{session_id}/feedback",
  response_model=FeedbackEnvelope,
  tags=["Feedback"],
)
async def get_feedback(
  session_id: str,
  service: InterviewService = Depends(get_interview_service),
) -> FeedbackEnvelope:
  return FeedbackEnvelope(data=await service.get_feedback(session_id))
