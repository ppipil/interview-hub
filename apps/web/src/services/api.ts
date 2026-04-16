import type {
  ApiResponse,
  ErrorResponse,
  CreateSessionRequest,
  CreateSessionResponse,
  InterviewFeedback,
  InterviewRole,
  Interviewer,
  SendMessageRequest,
  SendMessageResponse,
} from "../types";

const DEFAULT_API_BASE_URL = "http://127.0.0.1:8001";

const rawApiBaseUrl = import.meta.env.VITE_API_BASE_URL?.trim();
const apiBaseUrl = rawApiBaseUrl ? rawApiBaseUrl.replace(/\/$/, "") : DEFAULT_API_BASE_URL;

export class ApiClientError extends Error {
  readonly status: number;
  readonly response: ErrorResponse;

  constructor(status: number, response: ErrorResponse) {
    super(response.error.message);
    this.name = "ApiClientError";
    this.status = status;
    this.response = response;
  }
}

const isErrorResponse = (value: unknown): value is ErrorResponse => {
  if (!value || typeof value !== "object") {
    return false;
  }

  const candidate = value as Partial<ErrorResponse>;
  return (
    !!candidate.error &&
    typeof candidate.error === "object" &&
    typeof candidate.error.code === "string" &&
    typeof candidate.error.message === "string"
  );
};

const isApiResponse = <T>(value: unknown): value is ApiResponse<T> => {
  if (!value || typeof value !== "object") {
    return false;
  }

  return Object.prototype.hasOwnProperty.call(value, "data");
};

const buildUrl = (path: string) => `${apiBaseUrl}${path}`;

const buildError = (status: number, code: string, message: string) =>
  new ApiClientError(status, {
    error: {
      code,
      message,
    },
  });

const parsePayload = async (response: Response): Promise<unknown> => {
  const rawText = await response.text();

  if (!rawText) {
    return null;
  }

  try {
    return JSON.parse(rawText);
  } catch {
    return rawText;
  }
};

const request = async <T>(path: string, init?: RequestInit): Promise<ApiResponse<T>> => {
  let response: Response;

  try {
    response = await fetch(buildUrl(path), {
      ...init,
      headers: {
        Accept: "application/json",
        ...(init?.body ? { "Content-Type": "application/json" } : {}),
        ...(init?.headers ?? {}),
      },
    });
  } catch {
    throw buildError(0, "NETWORK_ERROR", "当前无法连接面试服务，请确认本地后端已经启动。");
  }

  const payload = await parsePayload(response);

  if (!response.ok) {
    if (isErrorResponse(payload)) {
      throw new ApiClientError(response.status, payload);
    }

    throw buildError(response.status, "HTTP_ERROR", `请求失败（${response.status}）。`);
  }

  if (!isApiResponse<T>(payload)) {
    throw buildError(response.status, "INVALID_RESPONSE", "服务返回格式异常，请稍后再试。");
  }

  return payload;
};

const withQuery = (path: string, params: Record<string, string | undefined>) => {
  const searchParams = new URLSearchParams();

  Object.entries(params).forEach(([key, value]) => {
    if (value) {
      searchParams.set(key, value);
    }
  });

  const query = searchParams.toString();
  return query ? `${path}?${query}` : path;
};

export const interviewApi = {
  getInterviewers: (role?: InterviewRole) =>
    request<Interviewer[]>(withQuery("/api/v1/interviewers", { role })),

  createInterviewSession: (payload: CreateSessionRequest) =>
    request<CreateSessionResponse>("/api/v1/interview-sessions", {
      method: "POST",
      body: JSON.stringify(payload),
    }),

  sendInterviewMessage: (sessionId: string, payload: SendMessageRequest) =>
    request<SendMessageResponse>(`/api/v1/interview-sessions/${sessionId}/messages`, {
      method: "POST",
      body: JSON.stringify(payload),
    }),

  getInterviewFeedback: (sessionId: string) =>
    request<InterviewFeedback>(`/api/v1/interview-sessions/${sessionId}/feedback`),
};
