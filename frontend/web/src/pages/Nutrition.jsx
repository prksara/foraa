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
        {nutritionMetrics.map((m, i) => (
          <HealthMetric
            key={i}
            icon={<m.icon size={16} />}
            name={m.name}
            value={null}
          />
        ))}
      </div>

      <div className="page-section">
        <SectionHeader title="Meal History" />
        <Card padding="lg">
          <EmptyState
            icon={<UtensilsCrossed size={24} />}
            title="Start building your nutrition picture"
            description="Add your first meal or connect your nutrition data to see your daily intake and trends."
          />
        </Card>
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