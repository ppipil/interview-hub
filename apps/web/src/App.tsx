import { useEffect, useState } from "react";

import { useInterviewStore } from "./store/useInterviewStore";
import { HomePage } from "./pages/HomePage";
import { SetupPage } from "./pages/SetupPage";
import { InterviewPage } from "./pages/InterviewPage";
import { FeedbackPage } from "./pages/FeedbackPage";
import { AdminInterviewersPage } from "./pages/AdminInterviewersPage";
import { InterviewerQuestionnairePage } from "./pages/InterviewerQuestionnairePage";

const App = () => {
  const stage = useInterviewStore((state) => state.stage);
  const [pathname, setPathname] = useState(() => window.location.pathname);

  useEffect(() => {
    const syncPathname = () => setPathname(window.location.pathname);

    window.addEventListener("popstate", syncPathname);
    return () => window.removeEventListener("popstate", syncPathname);
  }, []);

  if (pathname === "/admin/interviewers") {
    return <AdminInterviewersPage />;
  }

  if (pathname === "/interviewer-questionnaire") {
    return <InterviewerQuestionnairePage />;
  }

  switch (stage) {
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
