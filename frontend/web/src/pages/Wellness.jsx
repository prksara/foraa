import { Moon, Activity, Battery, Brain, CalendarCheck } from "lucide-react";
import Card from "../components/Card";
import SectionHeader from "../components/SectionHeader";
import HealthMetric from "../components/HealthMetric";
import EmptyState from "../components/EmptyState";
import AskForraa from "../components/AskForraa";

const wellnessMetrics = [
  { icon: Moon, name: "Sleep" },
  { icon: Activity, name: "Activity" },
  { icon: Battery, name: "Recovery" },
  { icon: Brain, name: "Mindfulness" },
];

const suggestions = [
  "How can I improve my sleep?",
  "What's a good recovery routine?",
  "Help me build a daily wellness habit",
];

function Wellness() {
  return (
    <div className="page">
      <div className="page-header">
        <div>
          <h1 className="page-header__title">Wellness</h1>
          <p className="page-header__desc">Your mind, body, and rest.</p>
        </div>
      </div>

      <SectionHeader title="Today's Wellness" />

      <div className="health-metrics-grid">
        {wellnessMetrics.map((m, i) => (
          <HealthMetric
            key={i}
            icon={<m.icon size={16} />}
            name={m.name}
            value={null}
          />
        ))}
      </div>

      <div className="page-section">
        <SectionHeader title="Daily Habits" />
        <Card padding="lg">
          <EmptyState
            icon={<CalendarCheck size={24} />}
            title="No habits tracked yet"
            description="Build your daily wellness routine. Track sleep, activity, recovery, and mindfulness to see patterns over time."
          />
        </Card>
      </div>

      <div className="page-section">
        <SectionHeader title="Ask Forraa about your wellbeing" />
        <AskForraa
          placeholder="Ask Forraa about wellness..."
          suggestions={suggestions}
        />
      </div>
    </div>
  );
}

export default Wellness;
