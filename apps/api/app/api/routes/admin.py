from __future__ import annotations

from fastapi import APIRouter, Depends, Response, status

from app.dependencies import get_admin_interviewer_service
from app.models.api import AdminInterviewerEnvelope, AdminInterviewersEnvelope, UpsertAdminInterviewerRequest
from app.services.admin_interviewers import AdminInterviewerService

router = APIRouter(prefix="/api/v1/admin", tags=["Admin"])


@router.get("/interviewers", response_model=AdminInterviewersEnvelope)
def list_admin_interviewers(
  service: AdminInterviewerService = Depends(get_admin_interviewer_service),
) -> AdminInterviewersEnvelope:
  return AdminInterviewersEnvelope(data=service.list_interviewers())


@router.post(
  "/interviewers",
  response_model=AdminInterviewerEnvelope,
  status_code=status.HTTP_201_CREATED,
)
def create_or_update_admin_interviewer(
  payload: UpsertAdminInterviewerRequest,
  service: AdminInterviewerService = Depends(get_admin_interviewer_service),
) -> AdminInterviewerEnvelope:
  return AdminInterviewerEnvelope(data=service.upsert_interviewer(payload))


@router.put("/interviewers/{interviewer_id}", response_model=AdminInterviewerEnvelope)
def update_admin_interviewer(
  interviewer_id: str,
  payload: UpsertAdminInterviewerRequest,
  service: AdminInterviewerService = Depends(get_admin_interviewer_service),
) -> AdminInterviewerEnvelope:
  normalized_payload = payload.model_copy(update={"id": interviewer_id})
  return AdminInterviewerEnvelope(data=service.upsert_interviewer(normalized_payload))


@router.delete("/interviewers/{interviewer_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_admin_interviewer(
  interviewer_id: str,
  service: AdminInterviewerService = Depends(get_admin_interviewer_service),
) -> Response:
  service.delete_interviewer(interviewer_id)
  return Response(status_code=status.HTTP_204_NO_CONTENT)
