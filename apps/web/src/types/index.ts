export const INTERVIEW_ROLES = [
  "frontend",
  "backend",
  "product_manager",
  "operations",
  "data_analyst",
] as const;

export const INTERVIEW_MODES = ["guided", "real"] as const;

export const INTERVIEWER_TYPES = ["system", "avatar"] as const;
export const INTERVIEWER_PROVIDERS = ["doubao", "secondme_legacy", "secondme_visitor"] as const;

export const SESSION_STATUSES = [
  "pending",
  "in_progress",
  "completed",
  "failed",
] as const;

export const MESSAGE_ROLES = ["assistant", "user"] as const;
export const INTERVIEW_STAGE_KEYS = [
  "intro",
  "fundamentals",
  "project",
  "system_design",
  "behavioral",
  "closing",
] as const;
export const QUESTION_BANK_SCOPE_TYPES = ["interviewer", "global"] as const;

export const REQUEST_STATUSES = ["idle", "loading", "success", "error"] as const;

export const INTERVIEW_STAGES = ["home", "setup", "interview", "feedback"] as const;

export type InterviewRole = (typeof INTERVIEW_ROLES)[number];
export type InterviewMode = (typeof INTERVIEW_MODES)[number];
export type InterviewerType = (typeof INTERVIEWER_TYPES)[number];
export type InterviewerProvider = (typeof INTERVIEWER_PROVIDERS)[number];
export type SessionStatus = (typeof SESSION_STATUSES)[number];
export type MessageRole = (typeof MESSAGE_ROLES)[number];
export type InterviewStageKey = (typeof INTERVIEW_STAGE_KEYS)[number];
export type QuestionBankScopeType = (typeof QUESTION_BANK_SCOPE_TYPES)[number];
export type RequestStatus = (typeof REQUEST_STATUSES)[number];
export type InterviewStage = (typeof INTERVIEW_STAGES)[number];

export interface ApiResponse<T> {
  data: T;
}

export interface ApiErrorDetail {
  field: string;
  message: string;
}

export interface ApiErrorPayload {
  code: string;
  message: string;
  details?: ApiErrorDetail[];
}

export interface ErrorResponse {
  error: ApiErrorPayload;
}

export interface Interviewer {
  id: string;
  type: InterviewerType;
  provider: InterviewerProvider;
  name: string;
  title: string;
  description: string;
  avatarUrl: string;
  tags?: string[];
  supportedRoles?: InterviewRole[];
  supportedModes: InterviewMode[];
  persona?: string | null;
  promptStrategy?: string | null;
  skillPrompt?: string | null;
  interviewFlow?: string | null;
}

export interface AdminInterviewer extends Interviewer {
  enabled: boolean;
  profileExists: boolean;
  hasAvatarApiKey: boolean;
  avatarApiKey?: string | null;
  avatarApiKeyMasked?: string | null;
  updatedAt?: string | null;
  ownedQuestions: AdminQuestionBankQuestion[];
}

export interface AdminQuestionBankQuestion {
  id: string;
  scopeType: QuestionBankScopeType;
  interviewerId?: string | null;
  role: InterviewRole;
  stageKey: InterviewStageKey;
  question: string;
  referenceAnswer?: string | null;
  tags: string[];
  enabled: boolean;
  sortOrder: number;
}

export interface UpsertQuestionBankQuestionRequest {
  role: InterviewRole;
  stageKey: InterviewStageKey;
  question: string;
  referenceAnswer?: string | null;
  tags: string[];
  enabled: boolean;
  sortOrder?: number | null;
}

export interface UpsertAdminInterviewerRequest {
  id: string;
  type: InterviewerType;
  provider?: InterviewerProvider | null;
  name: string;
  title: string;
  description: string;
  avatarUrl?: string | null;
  tags: string[];
  supportedRoles: InterviewRole[];
  supportedModes: InterviewMode[];
  persona?: string | null;
  promptStrategy?: string | null;
  skillPrompt?: string | null;
  interviewFlow?: string | null;
  avatarApiKey?: string | null;
  enabled: boolean;
  ownedQuestions?: UpsertQuestionBankQuestionRequest[] | null;
}

export interface GlobalQuestionBankResponse {
  role: InterviewRole;
  questions: AdminQuestionBankQuestion[];
}

export interface UpsertGlobalQuestionBankRequest {
  role: InterviewRole;
  questions: UpsertQuestionBankQuestionRequest[];
}

export interface Session {
  id: string;
  role: InterviewRole;
  mode: InterviewMode;
  interviewerId: string;
  status: SessionStatus;
  currentRound: number;
  totalRounds: number;
  startedAt: string;
  finishedAt?: string | null;
}

export interface ConversationMessage {
  id: string;
  role: MessageRole;
  content: string;
  round: number;
  createdAt: string;
}

export interface CreateSessionRequest {
  role: InterviewRole;
  mode: InterviewMode;
  interviewerId: string;
  totalRounds?: number;
}

export interface CreateSessionResponse {
  session: Session;
  interviewer: Interviewer;
  firstQuestion: ConversationMessage;
}

export interface SendMessageRequest {
  content: string;
  clientMessageId?: string | null;
}

export interface SendMessageResponse {
  session: Session;
  userMessage: ConversationMessage;
  assistantMessage?: ConversationMessage | null;
  shouldFetchFeedback: boolean;
}

export interface FeedbackDimension {
  key: string;
  label: string;
  score: number;
  comment: string;
}

export interface RoundReview {
  round: number;
  question: string;
  answer: string;
  note: string;
  evaluation: string;
  referenceAnswer: string;
}

export interface InterviewFeedback {
  sessionId: string;
  summary: string;
  dimensions: FeedbackDimension[];
  strengths: string[];
  improvements: string[];
  suggestedAnswer: string;
  roundReviews: RoundReview[];
  generatedAt: string;
}

export interface InterviewSetupDraft {
  role: InterviewRole | null;
  mode: InterviewMode | null;
  interviewerId: string | null;
  totalRounds: number;
}
