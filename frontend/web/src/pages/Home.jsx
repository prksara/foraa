import { useState, useEffect } from "react";
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
import * as api from "../api/client";

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
  const [summary, setSummary] = useState(null);

  useEffect(() => {
    api.fetchHealthSummary().then(setSummary).catch(console.error);
  }, []);

  const hasData = summary && (summary.active_conditions_count > 0 || summary.active_medications_count > 0 || summary.allergies_count > 0 || summary.active_goals_count > 0);

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

      {hasData ? (
        <div className="health-metrics-grid">
          <Card padding="md" onClick={() => navigate("/health")}>
            <div style={{display: 'flex', alignItems: 'center', gap: '10px'}}>
              <Activity size={20} />
              <div>
                <strong>Active Conditions</strong>
                <div>{summary.active_conditions_count}</div>
              </div>
            </div>
          </Card>
          <Card padding="md" onClick={() => navigate("/health")}>
            <div style={{display: 'flex', alignItems: 'center', gap: '10px'}}>
              <Heart size={20} />
              <div>
                <strong>Active Medications</strong>
                <div>{summary.active_medications_count}</div>
              </div>
            </div>
          </Card>
          <Card padding="md" onClick={() => navigate("/health")}>
            <div style={{display: 'flex', alignItems: 'center', gap: '10px'}}>
              <Sun size={20} />
              <div>
                <strong>Active Goals</strong>
                <div>{summary.active_goals_count}</div>
              </div>
            </div>
          </Card>
        </div>
      ) : (
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
      )}
    </div>
  );
}

export default Home;