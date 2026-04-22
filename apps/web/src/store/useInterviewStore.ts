import { create } from "zustand";

import { ApiClientError, interviewApi } from "../services/api";
import { navigateToStage } from "../lib/navigation";
import type {
  CreateSessionResponse,
  InterviewFeedback,
  InterviewRole,
  InterviewSetupDraft,
  InterviewStage,
  Interviewer,
  RequestStatus,
  SendMessageResponse,
  Session,
  ConversationMessage,
} from "../types";

const DEFAULT_SETUP: InterviewSetupDraft = {
  role: null,
  mode: null,
  interviewerId: null,
  totalRounds: 3,
};

const createDefaultSetup = (): InterviewSetupDraft => ({
  ...DEFAULT_SETUP,
});

const getErrorMessage = (error: unknown) => {
  if (error instanceof ApiClientError) {
    return error.response.error.message;
  }

  if (error instanceof Error) {
    return error.message;
  }

  return "发生了一点意外，请稍后再试。";
};

const clampRounds = (totalRounds: number) => Math.min(10, Math.max(1, Math.floor(totalRounds)));

export interface InterviewStoreState {
  stage: InterviewStage;
  setup: InterviewSetupDraft;
  interviewers: Interviewer[];
  interviewersStatus: RequestStatus;
  interviewersError: string | null;
  session: Session | null;
  activeInterviewer: Interviewer | null;
  messages: ConversationMessage[];
  feedback: InterviewFeedback | null;
  createSessionStatus: RequestStatus;
  createSessionError: string | null;
  sendMessageStatus: RequestStatus;
  sendMessageError: string | null;
  feedbackStatus: RequestStatus;
  feedbackError: string | null;
  setStage: (stage: InterviewStage, options?: { updateUrl?: boolean; replace?: boolean }) => void;
  updateSetup: (patch: Partial<InterviewSetupDraft>) => void;
  fetchInterviewers: (role?: InterviewRole) => Promise<Interviewer[]>;
  startInterview: () => Promise<CreateSessionResponse | null>;
  submitAnswer: (content: string) => Promise<SendMessageResponse | null>;
  fetchFeedback: () => Promise<InterviewFeedback | null>;
  resetInterview: () => void;
  resetAll: () => void;
}

export const useInterviewStore = create<InterviewStoreState>((set, get) => ({
  stage: "home",
  setup: createDefaultSetup(),
  interviewers: [],
  interviewersStatus: "idle",
  interviewersError: null,
  session: null,
  activeInterviewer: null,
  messages: [],
  feedback: null,
  createSessionStatus: "idle",
  createSessionError: null,
  sendMessageStatus: "idle",
  sendMessageError: null,
  feedbackStatus: "idle",
  feedbackError: null,

  setStage: (stage, options) => {
    set({ stage });
    if (options?.updateUrl !== false) {
      navigateToStage(stage, { replace: options?.replace });
    }
  },

  updateSetup: (patch) => {
    set((state) => {
      const nextSetup: InterviewSetupDraft = {
        ...state.setup,
        ...patch,
      };

      if (typeof patch.totalRounds === "number") {
        nextSetup.totalRounds = clampRounds(patch.totalRounds);
      }

      const roleChanged =
        Object.prototype.hasOwnProperty.call(patch, "role") && patch.role !== state.setup.role;
      const modeChanged =
        Object.prototype.hasOwnProperty.call(patch, "mode") && patch.mode !== state.setup.mode;

      if (
        roleChanged ||
        modeChanged
      ) {
        nextSetup.interviewerId = null;
      }

      return {
        setup: nextSetup,
      };
    });
  },

  fetchInterviewers: async (role) => {
    set({
      interviewersStatus: "loading",
      interviewersError: null,
    });

    try {
      const response = await interviewApi.getInterviewers(role);
      const interviewerIds = new Set(response.data.map((interviewer) => interviewer.id));

      set((state) => ({
        interviewers: response.data,
        interviewersStatus: "success",
        setup: interviewerIds.has(state.setup.interviewerId ?? "")
          ? state.setup
          : { ...state.setup, interviewerId: null },
      }));

      return response.data;
    } catch (error) {
      const message = getErrorMessage(error);

      set({
        interviewersStatus: "error",
        interviewersError: message,
      });

      return [];
    }
  },

  startInterview: async () => {
    const { setup } = get();

    if (!setup.role || !setup.mode || !setup.interviewerId) {
      set({
        createSessionStatus: "error",
        createSessionError: "岗位、模式和面试官都选好之后才能开始挑战。",
      });

      return null;
    }

    set({
      createSessionStatus: "loading",
      createSessionError: null,
      sendMessageError: null,
      feedbackError: null,
      feedback: null,
    });

    try {
      const response = await interviewApi.createInterviewSession({
        role: setup.role,
        mode: setup.mode,
        interviewerId: setup.interviewerId,
        totalRounds: setup.totalRounds,
      });

      set({
        stage: "interview",
        session: response.data.session,
        activeInterviewer: response.data.interviewer,
        messages: [response.data.firstQuestion],
        feedback: null,
        createSessionStatus: "success",
        sendMessageStatus: "idle",
        feedbackStatus: "idle",
      });
      navigateToStage("interview");

      return response.data;
    } catch (error) {
      set({
        createSessionStatus: "error",
        createSessionError: getErrorMessage(error),
      });

      return null;
    }
  },

  submitAnswer: async (content) => {
    const { session } = get();

    if (!session) {
      set({
        sendMessageStatus: "error",
        sendMessageError: "当前还没有激活中的面试 Session。",
      });

      return null;
    }

    set({
      sendMessageStatus: "loading",
      sendMessageError: null,
    });

    try {
      const response = await interviewApi.sendInterviewMessage(session.id, {
        content,
        clientMessageId: crypto.randomUUID(),
      });

      set((state) => {
        const nextStage = response.data.shouldFetchFeedback ? "feedback" : state.stage;
        if (nextStage !== state.stage) {
          navigateToStage(nextStage);
        }

        return {
          session: response.data.session,
          messages: response.data.assistantMessage
            ? [...state.messages, response.data.userMessage, response.data.assistantMessage]
            : [...state.messages, response.data.userMessage],
          sendMessageStatus: "success",
          stage: nextStage,
        };
      });

      return response.data;
    } catch (error) {
      set({
        sendMessageStatus: "error",
        sendMessageError: getErrorMessage(error),
      });

      return null;
    }
  },

  fetchFeedback: async () => {
    const { session } = get();

    if (!session) {
      set({
        feedbackStatus: "error",
        feedbackError: "当前没有可读取反馈的 Session。",
      });

      return null;
    }

    set({
      feedbackStatus: "loading",
      feedbackError: null,
    });

    try {
      const response = await interviewApi.getInterviewFeedback(session.id);

      set({
        stage: "feedback",
        feedback: response.data,
        feedbackStatus: "success",
      });
      navigateToStage("feedback", { replace: true });

      return response.data;
    } catch (error) {
      set({
        feedbackStatus: "error",
        feedbackError: getErrorMessage(error),
      });

      return null;
    }
  },

  resetInterview: () => {
    set((state) => ({
      stage: "setup",
      session: null,
      activeInterviewer: null,
      messages: [],
      feedback: null,
      createSessionStatus: "idle",
      createSessionError: null,
      sendMessageStatus: "idle",
      sendMessageError: null,
      feedbackStatus: "idle",
      feedbackError: null,
      setup: {
        ...state.setup,
        totalRounds: clampRounds(state.setup.totalRounds),
      },
    }));
    navigateToStage("setup");
  },

  resetAll: () => {
    set({
      stage: "home",
      setup: createDefaultSetup(),
      interviewers: [],
      interviewersStatus: "idle",
      interviewersError: null,
      session: null,
      activeInterviewer: null,
      messages: [],
      feedback: null,
      createSessionStatus: "idle",
      createSessionError: null,
      sendMessageStatus: "idle",
      sendMessageError: null,
      feedbackStatus: "idle",
      feedbackError: null,
    });
    navigateToStage("home");
  },
}));

export const selectCanStartInterview = (state: InterviewStoreState) =>
  Boolean(state.setup.role && state.setup.mode && state.setup.interviewerId);

export const selectHasCompletedInterview = (state: InterviewStoreState) =>
  state.session?.status === "completed";
