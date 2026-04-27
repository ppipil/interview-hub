from __future__ import annotations

from typing import List, Literal, Optional

from pydantic import BaseModel, Field

InterviewRole = Literal["frontend", "backend", "product_manager", "operations", "data_analyst"]
InterviewMode = Literal["guided", "real"]
InterviewerType = Literal["system", "avatar"]
InterviewerProvider = Literal["doubao", "secondme_legacy", "secondme_visitor"]
SessionStatus = Literal["pending", "in_progress", "completed", "failed"]
MessageRole = Literal["assistant", "user"]
InterviewStageKey = Literal["intro", "fundamentals", "project", "system_design", "behavioral", "closing"]
QuestionBankScopeType = Literal["interviewer", "global"]


class ApiErrorDetail(BaseModel):
  field: str
  message: str


class ApiErrorPayload(BaseModel):
  code: str
  message: str
  details: Optional[List[ApiErrorDetail]] = None


class ErrorResponse(BaseModel):
  error: ApiErrorPayload


class Interviewer(BaseModel):
  id: str
  type: InterviewerType
  provider: InterviewerProvider
  name: str
  title: str
  description: str
  avatarUrl: str
  tags: List[str] = Field(default_factory=list)
  supportedRoles: List[InterviewRole] = Field(default_factory=list)
  supportedModes: List[InterviewMode] = Field(default_factory=list)
  persona: Optional[str] = None
  promptStrategy: Optional[str] = None
  skillPrompt: Optional[str] = None
  interviewFlow: Optional[str] = None


class AdminInterviewer(BaseModel):
  id: str
  type: InterviewerType
  provider: InterviewerProvider
  name: str
  title: str
  description: str
  avatarUrl: str
  tags: List[str] = Field(default_factory=list)
  supportedRoles: List[InterviewRole] = Field(default_factory=list)
  supportedModes: List[InterviewMode] = Field(default_factory=list)
  persona: Optional[str] = None
  promptStrategy: Optional[str] = None
  skillPrompt: Optional[str] = None
  interviewFlow: Optional[str] = None
  enabled: bool = True
  profileExists: bool = False
  hasAvatarApiKey: bool = False
  avatarApiKey: Optional[str] = None
  avatarApiKeyMasked: Optional[str] = None
  updatedAt: Optional[str] = None
  ownedQuestions: List["AdminQuestionBankQuestion"] = Field(default_factory=list)


class AdminQuestionBankQuestion(BaseModel):
  id: str
  scopeType: QuestionBankScopeType
  interviewerId: Optional[str] = None
  role: InterviewRole
  stageKey: InterviewStageKey
  question: str
  referenceAnswer: Optional[str] = None
  tags: List[str] = Field(default_factory=list)
  enabled: bool = True
  sortOrder: int


class UpsertQuestionBankQuestionRequest(BaseModel):
  role: InterviewRole
  stageKey: InterviewStageKey
  question: str = Field(min_length=1, max_length=2000)
  referenceAnswer: Optional[str] = Field(default=None, max_length=4000)
  tags: List[str] = Field(default_factory=list)
  enabled: bool = True
  sortOrder: Optional[int] = None


class UpsertAdminInterviewerRequest(BaseModel):
  id: str = Field(min_length=2, max_length=80)
  type: InterviewerType
  provider: Optional[InterviewerProvider] = None
  name: str = Field(min_length=1, max_length=80)
  title: str = Field(min_length=1, max_length=120)
  description: str = Field(min_length=1, max_length=500)
  avatarUrl: Optional[str] = None
  tags: List[str] = Field(default_factory=list)
  supportedRoles: List[InterviewRole] = Field(default_factory=list)
  supportedModes: List[InterviewMode] = Field(default_factory=list)
  persona: Optional[str] = None
  promptStrategy: Optional[str] = None
  skillPrompt: Optional[str] = None
  interviewFlow: Optional[str] = None
  avatarApiKey: Optional[str] = None
  enabled: bool = True
  ownedQuestions: Optional[List[UpsertQuestionBankQuestionRequest]] = None


class UpsertGlobalQuestionBankRequest(BaseModel):
  role: InterviewRole
  questions: List[UpsertQuestionBankQuestionRequest] = Field(default_factory=list)


class GlobalQuestionBankResponse(BaseModel):
  role: InterviewRole
  questions: List[AdminQuestionBankQuestion] = Field(default_factory=list)


class Session(BaseModel):
  id: str
  role: InterviewRole
  mode: InterviewMode
  interviewerId: str
  status: SessionStatus
  currentRound: int
  totalRounds: int
  startedAt: str
  finishedAt: Optional[str] = None


class ConversationMessage(BaseModel):
  id: str
  role: MessageRole
  content: str
  round: int
  createdAt: str


class CreateSessionRequest(BaseModel):
  role: InterviewRole
  mode: InterviewMode
  interviewerId: str
  totalRounds: Optional[int] = 3


class CreateSessionResponse(BaseModel):
  session: Session
  interviewer: Interviewer
  firstQuestion: ConversationMessage


class SendMessageRequest(BaseModel):
  content: str
  clientMessageId: Optional[str] = None


class SendMessageResponse(BaseModel):
  session: Session
  userMessage: ConversationMessage
  assistantMessage: Optional[ConversationMessage] = None
  shouldFetchFeedback: bool


class FeedbackDimension(BaseModel):
  key: str
  label: str
  score: int
  comment: str


class RoundReview(BaseModel):
  round: int
  question: str
  answer: str
  note: str
  evaluation: str
  referenceAnswer: str


class InterviewFeedback(BaseModel):
  sessionId: str
  summary: str
  dimensions: List[FeedbackDimension]
  strengths: List[str]
  improvements: List[str]
  suggestedAnswer: str
  roundReviews: List[RoundReview]
  generatedAt: str


class InterviewersEnvelope(BaseModel):
  data: List[Interviewer]


class AdminInterviewersEnvelope(BaseModel):
  data: List[AdminInterviewer]


class AdminInterviewerEnvelope(BaseModel):
  data: AdminInterviewer


class GlobalQuestionBankEnvelope(BaseModel):
  data: GlobalQuestionBankResponse


class CreateSessionEnvelope(BaseModel):
  data: CreateSessionResponse


class SendMessageEnvelope(BaseModel):
  data: SendMessageResponse


class FeedbackEnvelope(BaseModel):
  data: InterviewFeedback
