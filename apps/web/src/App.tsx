import { useInterviewStore } from "./store/useInterviewStore";
import { HomePage } from "./pages/HomePage";
import { SetupPage } from "./pages/SetupPage";
import { InterviewPage } from "./pages/InterviewPage";
import { FeedbackPage } from "./pages/FeedbackPage";

const App = () => {
  const stage = useInterviewStore((state) => state.stage);

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
