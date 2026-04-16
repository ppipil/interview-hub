export const INTERVIEW_ROLES = [
  "frontend",
  "backend",
  "product_manager",
  "operations",
  "data_analyst",
] as const;

export const INTERVIEW_MODES = ["guided", "real"] as const;

export const INTERVIEWER_TYPES = ["system", "avatar"] as const;

export const SESSION_STATUSES = [
  "pending",
  "in_progress",
  "completed",
  "failed",
] as const;

export const MESSAGE_ROLES = ["assistant", "user"] as const;

export const REQUEST_STATUSES = ["idle", "loading", "success", "error"] as const;

export const INTERVIEW_STAGES = ["home", "setup", "interview", "feedback"] as const;

export type InterviewRole = (typeof INTERVIEW_ROLES)[number];
export type InterviewMode = (typeof INTERVIEW_MODES)[number];
export type InterviewerType = (typeof INTERVIEWER_TYPES)[number];
export type SessionStatus = (typeof SESSION_STATUSES)[number];
export type MessageRole = (typeof MESSAGE_ROLES)[number];
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
  name: string;
  title: string;
  description: string;
  avatarUrl: string;
  tags?: string[];
  supportedRoles?: InterviewRole[];
  supportedModes: InterviewMode[];
  persona?: string | null;
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
