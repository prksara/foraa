import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import {
  Apple,
  Flame,
  Beef,
  Wheat,
  Droplets,
  UtensilsCrossed,
  Plus,
  Trash2,
} from "lucide-react";
import SectionHeader from "../components/SectionHeader";
import HealthMetric from "../components/HealthMetric";
import EmptyState from "../components/EmptyState";
import AskForraa from "../components/AskForraa";
import TrendChart from "../components/TrendChart";
import Button from "../components/Button";
import * as api from "../api/client";

const suggestions = [
  "What are high-protein, nutrient-dense breakfast options?",
  "How much dietary fiber should I aim for daily?",
  "Help me calculate my optimal daily water intake based on activity",
  "How does sugar intake affect energy crashes?",
];

function Nutrition() {
  const navigate = useNavigate();
  const [measurements, setMeasurements] = useState([]);
  const [showLogEntry, setShowLogEntry] = useState(false);
  const [newEntry, setNewEntry] = useState({
    type: "Calories",
    value: "",
    unit: "kcal",
    notes: "",
  });

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      const data = await api.fetchMeasurements();
      setMeasurements(data || []);
    } catch (err) {
      console.error("Failed to load measurements", err);
    }
  };

  const handleLogEntry = async (e) => {
    if (e) e.preventDefault();
    if (!newEntry.value) return;
    try {
      await api.createMeasurement({
        type: newEntry.type,
        value: parseFloat(newEntry.value),
        unit: newEntry.unit,
        notes: newEntry.notes || undefined,
      });

      // Also record timeline event
      await api.createTimelineEvent({
        event_type: "lifestyle",
        title: `Nutrition Log: ${newEntry.type} (${newEntry.value} ${newEntry.unit})`,
        description: newEntry.notes || undefined,
        confidence: 1.0,
      });

      setShowLogEntry(false);
      setNewEntry({ type: "Calories", value: "", unit: "kcal", notes: "" });
      loadData();
    } catch (err) {
      console.error("Failed to create measurement", err);
    }
  };

  const handleDeleteEntry = async (id) => {
    try {
      await api.deleteMeasurement(id);
      loadData();
    } catch (err) {
      console.error("Failed to delete measurement", err);
    }
  };

  const today = new Date().toDateString();
  const nutritionTypes = ["calories", "protein", "fiber", "water", "meal", "carbs", "fat"];

  const todaysMeasurements = measurements.filter(
    (m) =>
      nutritionTypes.includes(m.type.toLowerCase()) &&
      new Date(m.measured_at || m.created_at).toDateString() === today
  );

  const getTodayTotal = (type) => {
    const vals = todaysMeasurements.filter(
      (m) => m.type.toLowerCase() === type.toLowerCase()
    );
    return vals.reduce((acc, curr) => acc + (parseFloat(curr.value) || 0), 0);
  };

  return (
    <div className="page">
      <div className="page-header" style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start" }}>
        <div>
          <h1 className="page-header__title">Nutrition</h1>
          <p className="page-header__desc">
            Track daily macros, hydration, and nutritional patterns.
          </p>
        </div>
        <Button variant="primary" onClick={() => setShowLogEntry(true)}>
          <Plus size={16} style={{ marginRight: 6 }} /> Log Nutrition
        </Button>
      </div>

      <SectionHeader title="Today's Nutrition Summary" />

      <div className="health-metrics-grid">
        <HealthMetric
          icon={<Flame size={16} />}
          name="Calories"
          value={`${getTodayTotal("Calories")} kcal`}
        />
        <HealthMetric
          icon={<Beef size={16} />}
          name="Protein"
          value={`${getTodayTotal("Protein")} g`}
        />
        <HealthMetric
          icon={<Wheat size={16} />}
          name="Fiber"
          value={`${getTodayTotal("Fiber")} g`}
        />
        <HealthMetric
          icon={<Droplets size={16} />}
          name="Hydration"
          value={`${getTodayTotal("Water")} L`}
        />
        <HealthMetric
          icon={<UtensilsCrossed size={16} />}
          name="Meals Logged"
          value={`${getTodayTotal("Meal")}`}
        />
      </div>

      {showLogEntry && (
        <div
          style={{
            marginTop: "24px",
            marginBottom: "24px",
            padding: "20px",
            background: "var(--color-surface)",
            border: "1px solid var(--color-border)",
            borderRadius: "12px",
            boxShadow: "var(--shadow-sm)",
          }}
        >
          <h3 style={{ fontSize: "16px", fontWeight: 600, marginBottom: "12px" }}>
            Add Nutrition Log
          </h3>
          <form onSubmit={handleLogEntry} style={{ display: "flex", flexDirection: "column", gap: "12px" }}>
            <div style={{ display: "flex", gap: "12px", flexWrap: "wrap" }}>
              <div style={{ flex: "1 1 160px" }}>
                <label style={{ display: "block", fontSize: "12px", color: "var(--color-text-secondary)", marginBottom: "4px" }}>
                  Nutrient / Metric
                </label>
                <select
                  value={newEntry.type}
                  onChange={(e) => {
                    const type = e.target.value;
                    const unit =
                      type === "Calories"
                        ? "kcal"
                        : type === "Water"
                        ? "L"
                        : type === "Meal"
                        ? "count"
                        : "g";
                    setNewEntry({ ...newEntry, type, unit });
                  }}
                  style={{
                    width: "100%",
                    padding: "8px 12px",
                    borderRadius: "8px",
                    border: "1px solid var(--color-border)",
                    background: "var(--color-surface)",
                    color: "var(--color-text)",
                  }}
                >
                  <option value="Calories">Calories (kcal)</option>
                  <option value="Protein">Protein (g)</option>
                  <option value="Fiber">Fiber (g)</option>
                  <option value="Water">Water (L)</option>
                  <option value="Meal">Meal (Count)</option>
                  <option value="Carbs">Carbohydrates (g)</option>
                  <option value="Fat">Fat (g)</option>
                </select>
              </div>

              <div style={{ flex: "1 1 120px" }}>
                <label style={{ display: "block", fontSize: "12px", color: "var(--color-text-secondary)", marginBottom: "4px" }}>
                  Amount ({newEntry.unit})
                </label>
                <input
                  type="number"
                  step="0.1"
                  placeholder="e.g. 500"
                  value={newEntry.value}
                  onChange={(e) =>
                    setNewEntry({ ...newEntry, value: e.target.value })
                  }
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

              <div style={{ flex: "2 1 220px" }}>
                <label style={{ display: "block", fontSize: "12px", color: "var(--color-text-secondary)", marginBottom: "4px" }}>
                  Food Item / Notes (Optional)
                </label>
                <input
                  type="text"
                  placeholder="e.g. Greek yogurt with blueberries & chia seeds"
                  value={newEntry.notes}
                  onChange={(e) =>
                    setNewEntry({ ...newEntry, notes: e.target.value })
                  }
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
              <Button variant="ghost" type="button" onClick={() => setShowLogEntry(false)}>
                Cancel
              </Button>
              <Button variant="primary" type="submit">
                Save Entry
              </Button>
            </div>
          </form>
        </div>
      )}

      <div style={{ marginTop: "32px" }}>
        <TrendChart metric="calories" category="measurement" title="Calorie Intake Trends" days={30} />
      </div>

      <div className="page-section" style={{ marginTop: "32px" }}>
        <SectionHeader title="Today's Nutrition Entries" />

        {todaysMeasurements.length === 0 ? (
          <EmptyState
            icon={<UtensilsCrossed size={24} />}
            title="Start building your nutrition picture"
            description="Add your first meal or nutrition entry to see your daily intake and trends."
            action={{
              label: "Log Nutrition",
              onClick: () => setShowLogEntry(true),
            }}
          />
        ) : (
          <ul style={{ listStyle: "none", padding: 0, marginTop: "12px" }}>
            {todaysMeasurements.map((m) => (
              <li
                key={m.id}
                style={{
                  display: "flex",
                  justifyContent: "space-between",
                  alignItems: "center",
                  padding: "12px 16px",
                  background: "var(--color-surface)",
                  border: "1px solid var(--color-border)",
                  borderRadius: "8px",
                  marginBottom: "8px",
                }}
              >
                <div>
                  <strong>{m.type}</strong>: {m.value} {m.unit}
                  {m.notes && (
                    <span style={{ marginLeft: "12px", color: "var(--color-text-secondary)", fontSize: "13px" }}>
                      — {m.notes}
                    </span>
                  )}
                </div>
                <Button
                  variant="ghost"
                  onClick={() => handleDeleteEntry(m.id)}
                  style={{ color: "var(--color-error, #c0392b)", padding: "4px 8px" }}
                  title="Delete entry"
                >
                  <Trash2 size={14} />
                </Button>
              </li>
            ))}
          </ul>
        )}
      </div>

      <div className="page-section" style={{ marginTop: "36px" }}>
        <SectionHeader title="Ask Forraa about nutrition" />
        <AskForraa
          placeholder="Ask Forraa about nutrition, meal plans, or macros..."
          suggestions={suggestions}
        />
      </div>
    </div>
  );
}

export default Nutrition;
