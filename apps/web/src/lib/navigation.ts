import type { InterviewStage } from "../types";

export const STAGE_PATHS: Record<InterviewStage, string> = {
  home: "/",
  setup: "/setup",
  interview: "/interview",
  feedback: "/feedback",
};

const STAGES_BY_PATH = new Map<string, InterviewStage>(
  Object.entries(STAGE_PATHS).map(([stage, path]) => [path, stage as InterviewStage]),
);

export const normalizePathname = (pathname: string) => {
  if (!pathname || pathname === "/") {
    return "/";
  }

  return pathname.replace(/\/+$/, "") || "/";
};

export const getStageFromPathname = (pathname: string): InterviewStage | null =>
  STAGES_BY_PATH.get(normalizePathname(pathname)) ?? null;

export const navigateToPath = (path: string, options?: { replace?: boolean }) => {
  if (typeof window === "undefined") {
    return;
  }

  const normalizedPath = normalizePathname(path);
  if (normalizePathname(window.location.pathname) === normalizedPath) {
    return;
  }

  const updateHistory = options?.replace ? window.history.replaceState : window.history.pushState;
  updateHistory.call(window.history, {}, "", normalizedPath);
  window.dispatchEvent(new PopStateEvent("popstate"));
};

export const navigateToStage = (stage: InterviewStage, options?: { replace?: boolean }) => {
  navigateToPath(STAGE_PATHS[stage], options);
};
