import { useEffect, useState } from "react";

import { useInterviewStore } from "./store/useInterviewStore";
import { getStageFromPathname, normalizePathname } from "./lib/navigation";
import { HomePage } from "./pages/HomePage";
import { SetupPage } from "./pages/SetupPage";
import { InterviewPage } from "./pages/InterviewPage";
import { FeedbackPage } from "./pages/FeedbackPage";
import { AdminInterviewersPage } from "./pages/AdminInterviewersPage";
import { InterviewerQuestionnairePage } from "./pages/InterviewerQuestionnairePage";

const App = () => {
  const stage = useInterviewStore((state) => state.stage);
  const setStage = useInterviewStore((state) => state.setStage);
  const [pathname, setPathname] = useState(() => window.location.pathname);
  const normalizedPathname = normalizePathname(pathname);
  const routedStage = getStageFromPathname(normalizedPathname);
  const activeStage = routedStage ?? stage;

  useEffect(() => {
    const syncPathname = () => setPathname(window.location.pathname);

    window.addEventListener("popstate", syncPathname);
    return () => window.removeEventListener("popstate", syncPathname);
  }, []);

  useEffect(() => {
    if (routedStage && routedStage !== stage) {
      setStage(routedStage, { updateUrl: false });
    }
  }, [routedStage, setStage, stage]);

  if (normalizedPathname === "/admin/interviewers") {
    return <AdminInterviewersPage />;
  }

  if (normalizedPathname === "/interviewer-questionnaire") {
    return <InterviewerQuestionnairePage />;
  }

  switch (activeStage) {
    case "home":
      return <HomePage />;
    case "setup":
      return <SetupPage />;
    case "interview":
      return <InterviewPage />;
    case "feedback":
      return <FeedbackPage />;
    default:
      return <HomePage />;
  }
};

export default App;
