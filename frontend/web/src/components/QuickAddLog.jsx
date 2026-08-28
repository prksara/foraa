import { useState } from "react";
import { Plus, X, Activity, Moon, Droplets, Thermometer } from "lucide-react";
import * as api from "../api/client";
import { useToast } from "../contexts/ToastContext";
import Button from "./Button";

export default function QuickAddLog({ onSave }) {
  const { success, error } = useToast();
  const [isOpen, setIsOpen] = useState(false);
  const [activeTab, setActiveTab] = useState(null); // 'vitals', 'sleep', 'water', 'symptom'
  
  // States for forms
  const [weight, setWeight] = useState("");
  const [water, setWater] = useState("");
  const [symptom, setSymptom] = useState("");
  const [sleep, setSleep] = useState("");
  
  const [isSaving, setIsSaving] = useState(false);

  const toggleOpen = () => {
    setIsOpen(!isOpen);
    setActiveTab(null);
  };

  const handleSaveMeasurement = async (type, value, unit) => {
    if (!value) return;
    setIsSaving(true);
    try {
      await api.createMeasurement({ type, value: parseFloat(value), unit });
      success(`${type} saved.`);
      setIsOpen(false);
      onSave && onSave();
    } catch (err) {
      error(`Failed to save ${type}`);
    } finally {
      setIsSaving(false);
    }
  };

  const handleSaveSleep = async () => {
    if (!sleep) return;
    setIsSaving(true);
    try {
      await api.createLifestyle({ category: "sleep", summary: `${sleep} hours`, details: `{"duration": ${sleep}}` });
      success(`Sleep saved.`);
      setIsOpen(false);
      onSave && onSave();
    } catch (err) {
      error(`Failed to save sleep`);
    } finally {
      setIsSaving(false);
    }
  };

  const handleSaveSymptom = async () => {
    if (!symptom) return;
    setIsSaving(true);
    try {
      await api.createTimelineEvent({ event_type: "symptom", title: symptom, source_type: "user" });
      success(`Symptom saved.`);
      setIsOpen(false);
      onSave && onSave();
    } catch (err) {
      error(`Failed to save symptom`);
    } finally {
      setIsSaving(false);
    }
  };

  if (!isOpen) {
    return (
      <button 
        onClick={toggleOpen}
        style={{
          position: "fixed",
          bottom: "24px",
          right: "24px",
          width: "56px",
          height: "56px",
          borderRadius: "28px",
          background: "var(--color-accent)",
          color: "white",
          border: "none",
          boxShadow: "0 4px 12px rgba(0,0,0,0.15)",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          cursor: "pointer",
          zIndex: 100
        }}
      >
        <Plus size={24} />
      </button>
    );
  }

  return (
    <div style={{
      position: "fixed",
      bottom: "24px",
      right: "24px",
      width: "320px",
      background: "var(--color-surface)",
      border: "1px solid var(--color-border)",
      borderRadius: "16px",
      boxShadow: "0 8px 32px rgba(0,0,0,0.12)",
      zIndex: 100,
      overflow: "hidden",
      display: "flex",
      flexDirection: "column"
    }}>
      <div style={{ padding: "16px", display: "flex", justifyContent: "space-between", alignItems: "center", borderBottom: "1px solid var(--color-border)" }}>
        <h3 style={{ fontSize: "16px", fontWeight: "var(--weight-semibold)", margin: 0 }}>Quick Log</h3>
        <button onClick={toggleOpen} style={{ background: "none", border: "none", cursor: "pointer", color: "var(--color-text-secondary)" }}>
          <X size={20} />
        </button>
      </div>
      
      <div style={{ padding: "16px", display: "flex", flexDirection: "column", gap: "12px" }}>
        {!activeTab ? (
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "12px" }}>
            <button onClick={() => setActiveTab('weight')} style={{ padding: "16px 8px", background: "var(--color-background)", border: "1px solid var(--color-border)", borderRadius: "8px", display: "flex", flexDirection: "column", alignItems: "center", gap: "8px", cursor: "pointer" }}>
              <Activity size={20} style={{ color: "var(--color-accent)" }} />
              <span style={{ fontSize: "12px", fontWeight: "var(--weight-medium)" }}>Weight</span>
            </button>
            <button onClick={() => setActiveTab('sleep')} style={{ padding: "16px 8px", background: "var(--color-background)", border: "1px solid var(--color-border)", borderRadius: "8px", display: "flex", flexDirection: "column", alignItems: "center", gap: "8px", cursor: "pointer" }}>
              <Moon size={20} style={{ color: "var(--color-accent)" }} />
              <span style={{ fontSize: "12px", fontWeight: "var(--weight-medium)" }}>Sleep</span>
            </button>
            <button onClick={() => setActiveTab('water')} style={{ padding: "16px 8px", background: "var(--color-background)", border: "1px solid var(--color-border)", borderRadius: "8px", display: "flex", flexDirection: "column", alignItems: "center", gap: "8px", cursor: "pointer" }}>
              <Droplets size={20} style={{ color: "var(--color-accent)" }} />
              <span style={{ fontSize: "12px", fontWeight: "var(--weight-medium)" }}>Water</span>
            </button>
            <button onClick={() => setActiveTab('symptom')} style={{ padding: "16px 8px", background: "var(--color-background)", border: "1px solid var(--color-border)", borderRadius: "8px", display: "flex", flexDirection: "column", alignItems: "center", gap: "8px", cursor: "pointer" }}>
              <Thermometer size={20} style={{ color: "var(--color-accent)" }} />
              <span style={{ fontSize: "12px", fontWeight: "var(--weight-medium)" }}>Symptom</span>
            </button>
          </div>
        ) : (
          <div>
            <div style={{ display: "flex", alignItems: "center", gap: "8px", marginBottom: "16px", cursor: "pointer" }} onClick={() => setActiveTab(null)}>
              <span style={{ color: "var(--color-text-secondary)", fontSize: "12px" }}>← Back</span>
            </div>

            {activeTab === 'weight' && (
              <div style={{ display: "flex", gap: "8px", alignItems: "center" }}>
                <input type="number" placeholder="Weight" value={weight} onChange={e => setWeight(e.target.value)} style={{ flex: 1, padding: "8px 12px", borderRadius: "8px", border: "1px solid var(--color-border)", background: "var(--color-background)", color: "var(--color-text)" }} />
                <span style={{ fontSize: "14px", color: "var(--color-text-secondary)" }}>kg</span>
                <Button onClick={() => handleSaveMeasurement("weight", weight, "kg")} disabled={isSaving}>Save</Button>
              </div>
            )}

            {activeTab === 'water' && (
              <div style={{ display: "flex", gap: "8px", alignItems: "center" }}>
                <input type="number" placeholder="Amount" value={water} onChange={e => setWater(e.target.value)} style={{ flex: 1, padding: "8px 12px", borderRadius: "8px", border: "1px solid var(--color-border)", background: "var(--color-background)", color: "var(--color-text)" }} />
                <span style={{ fontSize: "14px", color: "var(--color-text-secondary)" }}>L</span>
                <Button onClick={() => handleSaveMeasurement("hydration", water, "L")} disabled={isSaving}>Save</Button>
              </div>
            )}

            {activeTab === 'sleep' && (
              <div style={{ display: "flex", gap: "8px", alignItems: "center" }}>
                <input type="number" placeholder="Hours" value={sleep} onChange={e => setSleep(e.target.value)} style={{ flex: 1, padding: "8px 12px", borderRadius: "8px", border: "1px solid var(--color-border)", background: "var(--color-background)", color: "var(--color-text)" }} />
                <Button onClick={handleSaveSleep} disabled={isSaving}>Save</Button>
              </div>
            )}

            {activeTab === 'symptom' && (
              <div style={{ display: "flex", gap: "8px", alignItems: "center" }}>
                <input type="text" placeholder="e.g. Headache" value={symptom} onChange={e => setSymptom(e.target.value)} style={{ flex: 1, padding: "8px 12px", borderRadius: "8px", border: "1px solid var(--color-border)", background: "var(--color-background)", color: "var(--color-text)" }} />
                <Button onClick={handleSaveSymptom} disabled={isSaving}>Save</Button>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
