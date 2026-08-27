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

  const hasData =
    summary &&
    (summary.active_conditions_count > 0 ||
      summary.active_medications_count > 0 ||
      summary.allergies_count > 0 ||
      summary.active_goals_count > 0);

  return (
    <div className="page">
      <div className="home-greeting">
        <h1 className="home-greeting__title">{getGreeting()}</h1>
        <p className="home-greeting__sub">Your health command center.</p>
      </div>

      <AskForraa placeholder="Ask Forraa anything about your health..." />

      <div className="home-quick-actions" style={{ display: "flex", gap: "12px", overflowX: "auto", paddingBottom: "8px", marginBottom: "32px", scrollbarWidth: "none" }}>
        {quickActions.map((action, i) => (
          <button
            key={i}
            className="home-quick-action-pill"
            onClick={() => navigate(action.path)}
            style={{ display: "flex", alignItems: "center", gap: "8px", padding: "8px 16px", background: "var(--color-surface)", border: "1px solid var(--color-border)", borderRadius: "var(--radius-full)", whiteSpace: "nowrap", transition: "all var(--ease-fast)" }}
          >
            <action.icon size={14} style={{ color: "var(--color-accent)" }} />
            <span style={{ fontSize: "13px", fontWeight: "var(--weight-medium)" }}>{action.title}</span>
          </button>
        ))}
      </div>

      <div className="home-grid" style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "24px", alignItems: "start" }}>
        {/* Left Column */}
        <div style={{ display: "flex", flexDirection: "column", gap: "24px" }}>
          <section>
            <SectionHeader title="Health Overview" />
            {hasData ? (
              <div className="health-metrics-grid" style={{ gridTemplateColumns: "repeat(auto-fill, minmax(140px, 1fr))" }}>
                <Card padding="md" onClick={() => navigate("/health")}>
                  <div style={{ display: "flex", flexDirection: "column", gap: "8px" }}>
                    <Activity size={18} style={{ color: "var(--color-accent)" }} />
                    <div>
                      <div style={{ fontSize: "20px", fontWeight: "var(--weight-semibold)" }}>{summary.active_conditions_count}</div>
                      <div style={{ fontSize: "12px", color: "var(--color-text-secondary)" }}>Conditions</div>
                    </div>
                  </div>
                </Card>
                <Card padding="md" onClick={() => navigate("/health")}>
                  <div style={{ display: "flex", flexDirection: "column", gap: "8px" }}>
                    <Heart size={18} style={{ color: "var(--color-accent)" }} />
                    <div>
                      <div style={{ fontSize: "20px", fontWeight: "var(--weight-semibold)" }}>{summary.active_medications_count}</div>
                      <div style={{ fontSize: "12px", color: "var(--color-text-secondary)" }}>Medications</div>
                    </div>
                  </div>
                </Card>
                <Card padding="md" onClick={() => navigate("/health")}>
                  <div style={{ display: "flex", flexDirection: "column", gap: "8px" }}>
                    <Sun size={18} style={{ color: "var(--color-accent)" }} />
                    <div>
                      <div style={{ fontSize: "20px", fontWeight: "var(--weight-semibold)" }}>{summary.active_goals_count}</div>
                      <div style={{ fontSize: "12px", color: "var(--color-text-secondary)" }}>Goals</div>
                    </div>
                  </div>
                </Card>
              </div>
            ) : (
              <Card padding="md">
                <EmptyState
                  icon={<Heart size={20} />}
                  title="No health data yet"
                  description="Connect your health information to begin."
                  action={{
                    label: "Get started",
                    onClick: () => navigate("/health"),
                  }}
                />
              </Card>
            )}
          </section>
        </div>

        {/* Right Column */}
        <div style={{ display: "flex", flexDirection: "column", gap: "24px" }}>
          <section>
            <SectionHeader title="Recent Activity" />
            <Card padding="md">
              <EmptyState
                  icon={<Activity size={20} />}
                  title="No recent activity"
                  description="Activity will appear here when you log health data."
                />
            </Card>
          </section>

          <section>
            <SectionHeader title="Recent Reports" />
            <Card padding="md">
              <EmptyState
                  icon={<FileText size={20} />}
                  title="No recent reports"
                  description="Upload a report to see it here."
                  action={{
                    label: "Upload Report",
                    onClick: () => navigate("/reports"),
                  }}
                />
            </Card>
          </section>
        </div>
      </div>
    </div>
  );
}

export default Home;
