import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import {
  Apple,
  Flame,
  Beef,
  Wheat,
  Droplets,
  UtensilsCrossed,
} from "lucide-react";
import Card from "../components/Card";
import SectionHeader from "../components/SectionHeader";
import HealthMetric from "../components/HealthMetric";
import EmptyState from "../components/EmptyState";
import AskForraa from "../components/AskForraa";
import Button from "../components/Button";
import * as api from "../api/client";

const nutritionMetrics = [
  { icon: Flame, name: "Calories" },
  { icon: Beef, name: "Protein" },
  { icon: Wheat, name: "Fiber" },
  { icon: Droplets, name: "Water" },
  { icon: UtensilsCrossed, name: "Meals" },
];

const suggestions = [
  "What should I eat after a workout?",
  "Help me understand my diet",
  "High-protein meal ideas",
];

function Nutrition() {
  const navigate = useNavigate();
  const [measurements, setMeasurements] = useState([]);
  const [showLogEntry, setShowLogEntry] = useState(false);
  const [newEntry, setNewEntry] = useState({
    type: "Calories",
    value: "",
    unit: "kcal",
  });

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      setMeasurements(await api.fetchMeasurements());
    } catch (err) {
      console.error("Failed to load measurements", err);
    }
  };

  const handleLogEntry = async () => {
    if (!newEntry.value) return;
    try {
      await api.createMeasurement({
        ...newEntry,
        value: parseFloat(newEntry.value),
      });
      setShowLogEntry(false);
      setNewEntry({ type: "Calories", value: "", unit: "kcal" });
      loadData();
    } catch (err) {
      console.error("Failed to create measurement", err);
    }
  };

  const today = new Date().toDateString();
  const todaysMeasurements = measurements.filter(
    (m) => new Date(m.measured_at).toDateString() === today,
  );

  const getTodayTotal = (type) => {
    const vals = todaysMeasurements.filter(
      (m) => m.type.toLowerCase() === type.toLowerCase(),
    );
    return vals.reduce((acc, curr) => acc + curr.value, 0);
  };

  return (
    <div className="page">
      <div className="page-header">
        <div>
          <h1 className="page-header__title">Nutrition</h1>
          <p className="page-header__desc">
            Make better decisions about what you eat.
          </p>
        </div>
      </div>

      <SectionHeader title="Nutrition Overview" />

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
          name="Water"
          value={`${getTodayTotal("Water")} L`}
        />
        <HealthMetric
          icon={<UtensilsCrossed size={16} />}
          name="Meals"
          value={`${getTodayTotal("Meal")}`}
        />
      </div>

      <div className="page-section">
        <div
          style={{
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
            marginBottom: "1rem",
          }}
        >
          <SectionHeader title="Nutrition Log" />
          <Button variant="primary" onClick={() => setShowLogEntry(true)}>
            Log Entry
          </Button>
        </div>

        {showLogEntry && (
          <div
            style={{
              marginBottom: "20px",
              padding: "15px",
              background: "var(--surface-50)",
              borderRadius: "8px",
            }}
          >
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
              style={{ marginRight: "10px", padding: "8px" }}
            >
              <option value="Calories">Calories</option>
              <option value="Protein">Protein</option>
              <option value="Fiber">Fiber</option>
              <option value="Water">Water</option>
              <option value="Meal">Meal</option>
            </select>
            <input
              type="number"
              placeholder="Amount"
              value={newEntry.value}
              onChange={(e) =>
                setNewEntry({ ...newEntry, value: e.target.value })
              }
              style={{ marginRight: "10px", padding: "8px", width: "100px" }}
            />
            <span style={{ marginRight: "10px" }}>{newEntry.unit}</span>
            <Button onClick={handleLogEntry}>Save</Button>
            <Button variant="ghost" onClick={() => setShowLogEntry(false)}>
              Cancel
            </Button>
          </div>
        )}


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
            <ul style={{ listStyle: "none", padding: 0 }}>
              {todaysMeasurements.map((m) => (
                <li
                  key={m.id}
                  style={{
                    padding: "10px",
                    borderBottom: "1px solid var(--border)",
                  }}
                >
                  <strong>{m.type}</strong>: {m.value} {m.unit}
                </li>
              ))}
            </ul>
          )}

      </div>

      <div className="page-section">
        <SectionHeader title="Ask Forraa about nutrition" />
        <AskForraa
          placeholder="Ask Forraa about nutrition..."
          suggestions={suggestions}
        />
      </div>
    </div>
  );
}

export default Nutrition;
