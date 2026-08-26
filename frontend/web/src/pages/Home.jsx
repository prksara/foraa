import { useNavigate } from "react-router-dom";
import {
  FileText,
  MessageSquare,
  Activity,
  Heart,
  Apple,
  Sun,
} from "lucide-react";
import AskForraa from "../components/AskForraa";
import Card from "../components/Card";
import SectionHeader from "../components/SectionHeader";
import EmptyState from "../components/EmptyState";

const quickActions = [
  {
    icon: FileText,
    title: "Understand a report",
    desc: "Upload and analyze health documents",
    path: "/reports",
  },
  {
    icon: MessageSquare,
    title: "Ask a health question",
    desc: "Get clear, evidence-aware answers",
    path: "/assistant",
  },
  {
    icon: Activity,
    title: "Track a health metric",
    desc: "Log vitals, weight, and more",
    path: "/health",
  },
  {
    icon: Heart,
    title: "Review my health",
    desc: "See your health picture",
    path: "/health",
  },
  {
    icon: Apple,
    title: "Nutrition",
    desc: "Understand and improve your diet",
    path: "/nutrition",
  },
  {
    icon: Sun,
    title: "Wellness",
    desc: "Sleep, activity, and recovery",
    path: "/wellness",
  },
];

function getGreeting() {
  const hour = new Date().getHours();
  if (hour < 12) return "Good morning";
  if (hour < 17) return "Good afternoon";
  return "Good evening";
}

function Home() {
  const navigate = useNavigate();

  return (
    <div className="page">
      <div className="home-greeting">
        <h1 className="home-greeting__title">{getGreeting()}</h1>
        <p className="home-greeting__sub">Your health, understood.</p>
      </div>

      <AskForraa placeholder="Ask Forraa anything about your health..." />

      <div className="home-quick-actions">
        {quickActions.map((action, i) => (
          <button
            key={i}
            className="home-quick-card"
            onClick={() => navigate(action.path)}
          >
            <div className="home-quick-card__icon">
              <action.icon size={18} />
            </div>
            <div>
              <strong className="home-quick-card__title">
                {action.title}
              </strong>
              <p className="home-quick-card__desc">{action.desc}</p>
            </div>
          </button>
        ))}
      </div>

      <SectionHeader title="Health Overview" />

      <Card padding="lg">
        <EmptyState
          icon={<Heart size={24} />}
          title="No health data yet"
          description="Connect your health information or start a conversation with Forraa to begin building your health picture."
          action={{
            label: "Get started",
            onClick: () => navigate("/health"),
          }}
        />
      </Card>
    </div>
  );
}

export default Home;