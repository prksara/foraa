import { useState } from "react";
import { useNavigate } from "react-router-dom";
import {
  Heart,
  Activity,
  Moon,
  Droplets,
  Weight,
  Thermometer,
  Clock,
  Plus,
  FileText,
  Pill,
} from "lucide-react";
import Tabs from "../components/Tabs";
import Card from "../components/Card";
import HealthMetric from "../components/HealthMetric";
import EmptyState from "../components/EmptyState";
import AskForraa from "../components/AskForraa";
import SectionHeader from "../components/SectionHeader";

const tabs = [
  { id: "overview", label: "Overview" },
  { id: "vitals", label: "Vitals" },
  { id: "history", label: "History" },
  { id: "labs", label: "Lab Results" },
  { id: "medications", label: "Medications" },
  { id: "documents", label: "Documents" },
];

const healthMetrics = [
  { icon: Moon, name: "Sleep" },
  { icon: Activity, name: "Activity" },
  { icon: Weight, name: "Weight" },
  { icon: Heart, name: "Heart Rate" },
  { icon: Thermometer, name: "Blood Pressure" },
  { icon: Droplets, name: "Hydration" },
];

const tabEmptyStates = {
  vitals: {
    icon: Activity,
    title: "No vitals recorded yet",
    description:
      "Start tracking your vitals to see trends over time. Connect a device or add data manually.",
  },
  history: {
    icon: Clock,
    title: "No health history yet",
    description:
      "Your health timeline will appear here as you add data, upload reports, and interact with Forraa.",
  },
  labs: {
    icon: FileText,
    title: "No lab results yet",
    description:
      "Upload lab reports or connect your health records to see results here.",
  },
  medications: {
    icon: Pill,
    title: "No medications tracked",
    description:
      "Add your medications to keep a complete picture of your health.",
  },
  documents: {
    icon: FileText,
    title: "No documents yet",
    description:
      "Upload health documents to keep them organized and accessible.",
  },
};

function MyHealth() {
  const navigate = useNavigate();
  const [activeTab, setActiveTab] = useState("overview");

  return (
    <div className="page">
      <div className="page-header">
        <div>
          <h1 className="page-header__title">My Health</h1>
          <p className="page-header__desc">
            Your personal health overview
          </p>
        </div>
      </div>

      <Tabs tabs={tabs} activeTab={activeTab} onChange={setActiveTab} />

      {activeTab === "overview" && (
        <>
          <SectionHeader title="Health Snapshot" />

          <div className="health-metrics-grid">
            {healthMetrics.map((m, i) => (
              <HealthMetric
                key={i}
                icon={<m.icon size={16} />}
                name={m.name}
                value={null}
              />
            ))}
          </div>

          <div className="page-section">
            <SectionHeader title="Health Timeline" />
            <Card padding="lg">
              <EmptyState
                icon={<Clock size={24} />}
                title="No health events yet"
                description="Your health timeline will appear here as you add data, upload reports, and interact with Forraa."
              />
            </Card>
          </div>

          <div className="page-section">
            <AskForraa placeholder="Ask Forraa about your health..." />
          </div>
        </>
      )}

      {activeTab !== "overview" && tabEmptyStates[activeTab] && (
        <Card padding="lg">
          {(() => {
            const EmptyIcon = tabEmptyStates[activeTab].icon;
            return (
              <EmptyState
                icon={<EmptyIcon size={24} />}
                title={tabEmptyStates[activeTab].title}
                description={tabEmptyStates[activeTab].description}
                action={
                  activeTab === "labs" || activeTab === "documents"
                    ? {
                        label: "Upload a document",
                        onClick: () => navigate("/reports"),
                      }
                    : undefined
                }
              />
            );
          })()}
        </Card>
      )}
    </div>
  );
}

export default MyHealth;