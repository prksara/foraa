import { useState, useEffect } from "react";
import {
  Moon,
  Activity,
  Battery,
  Brain,
  CalendarCheck,
  Plus,
  Trash2,
  CheckCircle2,
  Sparkles,
} from "lucide-react";
import SectionHeader from "../components/SectionHeader";
import HealthMetric from "../components/HealthMetric";
import EmptyState from "../components/EmptyState";
import AskForraa from "../components/AskForraa";
import TrendChart from "../components/TrendChart";
import Button from "../components/Button";
import * as api from "../api/client";
import { useToast } from "../contexts/ToastContext";

const suggestions = [
  "How can I optimize my sleep consistency?",
  "What is an effective evening wind-down routine?",
  "How does stress impact resting heart rate and recovery?",
  "Help me build a realistic daily mindfulness habit",
];

function Wellness() {
  const { success, error } = useToast?.() || { success: () => {}, error: () => {} };
  const [measurements, setMeasurements] = useState([]);
  const [lifestyleEntries, setLifestyleEntries] = useState([]);
  const [goals, setGoals] = useState([]);
  const [showLogModal, setShowLogModal] = useState(false);
  const [logType, setLogType] = useState("sleep");
  const [logValue, setLogValue] = useState("");
  const [logNotes, setLogNotes] = useState("");

  const loadData = async () => {
    try {
      const [meas, life, g] = await Promise.all([
        api.fetchMeasurements().catch(() => []),
        api.fetchLifestyle().catch(() => []),
        api.fetchGoals().catch(() => []),
      ]);
      setMeasurements(meas || []);
      setLifestyleEntries(life || []);
      setGoals(g || []);
    } catch (err) {
      console.error("Failed to load wellness data", err);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const today = new Date().toDateString();
  const todaysMeasurements = measurements.filter(
    (m) => new Date(m.measured_at || m.created_at).toDateString() === today
  );

  const getLatestOrTodayValue = (type) => {
    const todayMatch = todaysMeasurements.find(
      (m) => m.type.toLowerCase() === type.toLowerCase()
    );
    if (todayMatch) return todayMatch;
    const anyMatch = measurements.find(
      (m) => m.type.toLowerCase() === type.toLowerCase()
    );
    return anyMatch || null;
  };

  const sleepMeas = getLatestOrTodayValue("sleep");
  const activityMeas = getLatestOrTodayValue("activity") || getLatestOrTodayValue("exercise");
  const mindfulnessMeas = getLatestOrTodayValue("mindfulness") || getLatestOrTodayValue("meditation");
  const heartRateMeas = getLatestOrTodayValue("heart_rate");

  const handleSaveLog = async (e) => {
    e.preventDefault();
    if (!logValue) return;

    const val = parseFloat(logValue);
    if (isNaN(val)) return;

    let unit = "hrs";
    let metricType = logType;

    if (logType === "sleep") {
      metricType = "sleep";
      unit = "hrs";
    } else if (logType === "activity") {
      metricType = "activity";
      unit = "mins";
    } else if (logType === "mindfulness") {
      metricType = "mindfulness";
      unit = "mins";
    } else if (logType === "recovery") {
      metricType = "recovery";
      unit = "%";
    }

    try {
      await api.createMeasurement({
        type: metricType,
        value: val,
        unit,
        notes: logNotes || undefined,
      });

      // Also record a timeline event for visibility
      await api.createTimelineEvent({
        event_type: "lifestyle",
        title: `Logged ${metricType.charAt(0).toUpperCase() + metricType.slice(1)}: ${val} ${unit}`,
        description: logNotes || undefined,
        confidence: 1.0,
      });

      setShowLogModal(false);
      setLogValue("");
      setLogNotes("");
      loadData();
    } catch (err) {
      console.error("Failed to save wellness log", err);
    }
  };

  const handleDeleteEntry = async (id) => {
    try {
      await api.deleteMeasurement(id);
      loadData();
    } catch (err) {
      console.error("Failed to delete entry", err);
    }
  };

  const wellnessHabits = lifestyleEntries.filter((item) =>
    ["sleep", "exercise", "general", "caffeine", "alcohol"].includes(item.category?.toLowerCase())
  );

  return (
    <div className="page">
      <div className="page-header" style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start" }}>
        <div>
          <h1 className="page-header__title">Wellness</h1>
          <p className="page-header__desc">Rest, movement, mindfulness, and daily recovery.</p>
        </div>
        <Button variant="primary" onClick={() => setShowLogModal(true)}>
          <Plus size={16} style={{ marginRight: 6 }} /> Log Wellness
        </Button>
      </div>

      {showLogModal && (
        <div
          style={{
            marginBottom: "24px",
            padding: "20px",
            background: "var(--color-surface)",
            border: "1px solid var(--color-border)",
            borderRadius: "12px",
            boxShadow: "var(--shadow-sm)",
          }}
        >
          <h3 style={{ fontSize: "16px", fontWeight: 600, marginBottom: "12px" }}>
            Log Wellness Metric
          </h3>
          <form onSubmit={handleSaveLog} style={{ display: "flex", flexDirection: "column", gap: "12px" }}>
            <div style={{ display: "flex", gap: "12px", flexWrap: "wrap" }}>
              <div style={{ flex: "1 1 180px" }}>
                <label style={{ display: "block", fontSize: "12px", color: "var(--color-text-secondary)", marginBottom: "4px" }}>
                  Category
                </label>
                <select
                  value={logType}
                  onChange={(e) => setLogType(e.target.value)}
                  style={{
                    width: "100%",
                    padding: "8px 12px",
                    borderRadius: "8px",
                    border: "1px solid var(--color-border)",
                    background: "var(--color-surface)",
                    color: "var(--color-text)",
                  }}
                >
                  <option value="sleep">Sleep (Hours)</option>
                  <option value="activity">Active Movement (Minutes)</option>
                  <option value="mindfulness">Mindfulness / Meditation (Minutes)</option>
                  <option value="recovery">Recovery / Readiness Score (%)</option>
                </select>
              </div>

              <div style={{ flex: "1 1 120px" }}>
                <label style={{ display: "block", fontSize: "12px", color: "var(--color-text-secondary)", marginBottom: "4px" }}>
                  Value
                </label>
                <input
                  type="number"
                  step="0.1"
                  placeholder="e.g. 7.5"
                  value={logValue}
                  onChange={(e) => setLogValue(e.target.value)}
                  required
                  style={{
                    width: "100%",
                    padding: "8px 12px",
                    borderRadius: "8px",
                    border: "1px solid var(--color-border)",
                    background: "var(--color-surface)",
                    color: "var(--color-text)",
                  }}
                />
              </div>

              <div style={{ flex: "2 1 240px" }}>
                <label style={{ display: "block", fontSize: "12px", color: "var(--color-text-secondary)", marginBottom: "4px" }}>
                  Notes (Optional)
                </label>
                <input
                  type="text"
                  placeholder="e.g. Felt well-rested, no caffeine after 2pm"
                  value={logNotes}
                  onChange={(e) => setLogNotes(e.target.value)}
                  style={{
                    width: "100%",
                    padding: "8px 12px",
                    borderRadius: "8px",
                    border: "1px solid var(--color-border)",
                    background: "var(--color-surface)",
                    color: "var(--color-text)",
                  }}
                />
              </div>
            </div>

            <div style={{ display: "flex", gap: "10px", justifyContent: "flex-end", marginTop: "8px" }}>
              <Button variant="ghost" type="button" onClick={() => setShowLogModal(false)}>
                Cancel
              </Button>
              <Button variant="primary" type="submit">
                Save Entry
              </Button>
            </div>
          </form>
        </div>
      )}

      <SectionHeader title="Today's Wellness Snapshot" />

      <div className="health-metrics-grid">
        <HealthMetric
          icon={<Moon size={16} />}
          name="Sleep Duration"
          value={sleepMeas ? `${sleepMeas.value} ${sleepMeas.unit}` : "Not logged"}
        />
        <HealthMetric
          icon={<Activity size={16} />}
          name="Physical Activity"
          value={activityMeas ? `${activityMeas.value} ${activityMeas.unit}` : "Not logged"}
        />
        <HealthMetric
          icon={<Brain size={16} />}
          name="Mindfulness"
          value={mindfulnessMeas ? `${mindfulnessMeas.value} ${mindfulnessMeas.unit}` : "Not logged"}
        />
        <HealthMetric
          icon={<Battery size={16} />}
          name="Resting HR / Recovery"
          value={heartRateMeas ? `${heartRateMeas.value} bpm` : "72 bpm (est)"}
        />
      </div>

      <div style={{ marginTop: "32px" }}>
        <TrendChart metric="sleep" category="measurement" title="Sleep Duration Trends" days={30} />
      </div>

      <div className="page-section" style={{ marginTop: "32px" }}>
        <SectionHeader title="Tracked Wellness Habits & Lifestyle Routines" />

        {wellnessHabits.length === 0 ? (
          <EmptyState
            icon={<CalendarCheck size={24} />}
            title="No habits tracked yet"
            description="Build your daily wellness routine. Track sleep habits, activity goals, and mindfulness routines in My Health."
            action={{
              label: "Log a Wellness Entry",
              onClick: () => setShowLogModal(true),
            }}
          />
        ) : (
          <div
            style={{
              display: "grid",
              gridTemplateColumns: "repeat(auto-fill, minmax(280px, 1fr))",
              gap: "16px",
            }}
          >
            {wellnessHabits.map((item) => (
              <div
                key={item.id}
                style={{
                  background: "var(--color-surface)",
                  border: "1px solid var(--color-border)",
                  borderRadius: "12px",
                  padding: "16px",
                  display: "flex",
                  flexDirection: "column",
                  justifyContent: "space-between",
                }}
              >
                <div>
                  <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "8px" }}>
                    <span
                      style={{
                        padding: "2px 8px",
                        borderRadius: "99px",
                        background: "var(--color-accent-light, #eef7f5)",
                        color: "var(--color-accent, #168A70)",
                        fontSize: "11px",
                        fontWeight: 600,
                        textTransform: "uppercase",
                      }}
                    >
                      {item.category}
                    </span>
                    <CheckCircle2 size={16} color="var(--color-accent, #168A70)" />
                  </div>
                  <strong style={{ fontSize: "14px", display: "block", marginBottom: "4px" }}>
                    {item.summary}
                  </strong>
                  {item.details && (
                    <p style={{ fontSize: "13px", color: "var(--color-text-secondary)", margin: 0 }}>
                      {item.details}
                    </p>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      <div className="page-section" style={{ marginTop: "36px" }}>
        <SectionHeader title="Ask Forraa about your wellbeing" />
        <AskForraa
          placeholder="Ask Forraa about wellness, sleep, recovery, or habits..."
          suggestions={suggestions}
        />
      </div>
    </div>
  );
}

export default Wellness;
