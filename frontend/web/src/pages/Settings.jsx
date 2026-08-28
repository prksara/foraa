import { useState, useEffect } from "react";
import { User, Heart, Shield, Bell, Monitor, Lock, Brain } from "lucide-react";
import SettingsSection from "../components/SettingsSection";
import SettingsRow from "../components/SettingsRow";
import * as api from "../api/client";
import { useToast } from "../contexts/ToastContext";

const sections = [
  { id: "account", label: "Account", icon: User },
  { id: "health", label: "Health Profile", icon: Heart },
  { id: "privacy", label: "Privacy", icon: Shield },
  { id: "notifications", label: "Notifications", icon: Bell },
  { id: "memory", label: "AI Memory", icon: Brain },
  { id: "appearance", label: "Appearance", icon: Monitor },
  { id: "security", label: "Security", icon: Lock },
];

function Toggle({ active = false, onChange }) {
  return (
    <button
      className={`toggle${active ? " active" : ""}`}
      onClick={() => onChange?.(!active)}
      aria-label="Toggle"
      type="button"
    />
  );
}

function Settings() {
  const { success, error } = useToast();
  const [activeSection, setActiveSection] = useState("account");

  // Preferences Data (from API)
  const [preferences, setPreferences] = useState({
    notif_product: true,
    notif_health: true,
    ai_data_pref: true,
    data_retention: "90",
    doc_storage: true,
    theme: "system",
    unit_preference: "metric",
  });
  const [prefsLoaded, setPrefsLoaded] = useState(false);

  // Profile Data
  const [profile, setProfile] = useState({
    date_of_birth: "",
    sex: "",
    blood_type: "",
  });
  const [isSaving, setIsSaving] = useState(false);

  useEffect(() => {
    api
      .fetchHealthProfile()
      .then((p) => {
        if (p)
          setProfile({
            date_of_birth: p.date_of_birth || "",
            sex: p.sex || "",
            blood_type: p.blood_type || "",
          });
      })
      .catch((e) => {
        console.error(e);
        error("Failed to load health profile");
      });
  }, []);

  const [memoryItems, setMemoryItems] = useState([]);

  useEffect(() => {
    api
      .fetchPreferences()
      .then((p) => {
        if (p) setPreferences(p);
        setPrefsLoaded(true);
      })
      .catch((e) => {
        console.error(e);
        error("Failed to load preferences");
      });
  }, []);

  useEffect(() => {
    if (activeSection === "memory") {
      api.fetchMemoryItems().then(setMemoryItems).catch(console.error);
    }
  }, [activeSection]);

  const handleDeleteMemory = async (id) => {
    try {
      await api.deleteMemoryItem(id);
      setMemoryItems(memoryItems.filter(m => m.id !== id));
      success("Memory deleted");
    } catch (e) {
      error("Failed to delete memory");
    }
  };

  // Save preferences and apply theme whenever they change
  useEffect(() => {
    if (!prefsLoaded) return;

    // Apply theme
    if (
      preferences.theme === "dark" ||
      (preferences.theme === "system" &&
        window.matchMedia("(prefers-color-scheme: dark)").matches)
    ) {
      document.body.classList.add("dark-theme");
    } else {
      document.body.classList.remove("dark-theme");
    }

    // Save to API
    api.updatePreferences(preferences).catch(e => {
        console.error("Failed to save preferences", e);
    });
  }, [preferences, prefsLoaded]);

  const updatePref = (key, value) => {
    setPreferences((prev) => ({ ...prev, [key]: value }));
  };

  const handleSaveProfile = async () => {
    setIsSaving(true);
    try {
      await api.updateHealthProfile(profile);
      success("Health profile updated successfully");
    } catch (e) {
      error("Failed to save health profile");
    } finally {
      setIsSaving(false);
    }
  };

  const handleExportData = async () => {
    try {
      const data = await api.exportHealthData();
      const blob = new Blob([JSON.stringify(data, null, 2)], { type: "application/json" });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `foraa_export_${new Date().toISOString().split("T")[0]}.json`;
      a.click();
      success("Data exported successfully");
    } catch (e) {
      error("Failed to export data");
    }
  };

  const handleDeleteAllData = async () => {
    if (window.confirm("Are you sure you want to delete ALL your health data? This action is irreversible.")) {
      try {
        await api.deleteAllHealthData();
        success("All health data deleted");
        window.location.reload();
      } catch (e) {
        error("Failed to delete health data");
      }
    }
  };

  return (
    <div className="page">
      <div className="page-header">
        <div>
          <h1 className="page-header__title">Settings</h1>
          <p className="page-header__desc">
            Manage your Forraa preferences and account.
          </p>
        </div>
      </div>

      <div className="settings-layout">
        <nav className="settings-nav">
          {sections.map((s) => (
            <button
              key={s.id}
              className={`settings-nav-item${
                activeSection === s.id ? " active" : ""
              }`}
              onClick={() => setActiveSection(s.id)}
            >
              <s.icon size={16} />
              {s.label}
            </button>
          ))}
        </nav>

        <div className="settings-content">
          {activeSection === "account" && (
            <SettingsSection
              title="Account"
              description="Your personal information."
            >
              <SettingsRow label="Name" description="Your display name">
                <input
                  type="text"
                  placeholder="Managed by authentication provider"
                  disabled
                />
              </SettingsRow>
              <SettingsRow label="Email" description="Your email address">
                <input
                  type="email"
                  placeholder="Managed by authentication provider"
                  disabled
                />
              </SettingsRow>
            </SettingsSection>
          )}

          {activeSection === "health" && (
            <SettingsSection
              title="Health Profile"
              description="Personal health information that helps Forraa provide better guidance."
            >
              <SettingsRow
                label="Date of birth"
                description="Used for age-appropriate recommendations"
              >
                <input
                  type="date"
                  value={profile.date_of_birth}
                  onChange={(e) =>
                    setProfile({ ...profile, date_of_birth: e.target.value })
                  }
                />
              </SettingsRow>
              <SettingsRow
                label="Biological sex"
                description="Relevant for health reference ranges"
              >
                <select
                  value={profile.sex}
                  onChange={(e) =>
                    setProfile({ ...profile, sex: e.target.value })
                  }
                >
                  <option value="" disabled>
                    Select
                  </option>
                  <option value="female">Female</option>
                  <option value="male">Male</option>
                  <option value="other">Other</option>
                  <option value="prefer-not">Prefer not to say</option>
                </select>
              </SettingsRow>
              <SettingsRow label="Blood Type" description="Your blood group">
                <input
                  type="text"
                  placeholder="e.g. O+, A-"
                  value={profile.blood_type}
                  onChange={(e) =>
                    setProfile({ ...profile, blood_type: e.target.value })
                  }
                />
              </SettingsRow>
              <div
                style={{
                  marginTop: "1rem",
                  display: "flex",
                  justifyContent: "flex-end",
                }}
              >
                <button
                  className="btn btn--primary"
                  onClick={handleSaveProfile}
                  disabled={isSaving}
                >
                  {isSaving ? "Saving..." : "Save Profile"}
                </button>
              </div>
            </SettingsSection>
          )}

          {activeSection === "privacy" && (
            <SettingsSection
              title="Privacy"
              description="Control how your data is used."
            >
              <SettingsRow
                label="AI data preferences"
                description="Allow Forraa to use your health data for personalized responses"
              >
                <Toggle active={preferences.ai_data_pref} onChange={(v) => updatePref("ai_data_pref", v)} />
              </SettingsRow>
              <SettingsRow
                label="Data retention"
                description="How long your conversation history is stored"
              >
                <select
                  value={preferences.data_retention}
                  onChange={(e) => updatePref("data_retention", e.target.value)}
                >
                  <option value="30">30 days</option>
                  <option value="90">90 days</option>
                  <option value="365">1 year</option>
                  <option value="forever">Indefinitely</option>
                </select>
              </SettingsRow>
              <SettingsRow
                label="Document storage"
                description="Keep uploaded reports and documents"
              >
                <Toggle active={preferences.doc_storage} onChange={(v) => updatePref("doc_storage", v)} />
              </SettingsRow>
              
              <div style={{ marginTop: "20px", paddingTop: "20px", borderTop: "1px solid var(--border)" }}>
                <h4 style={{ marginBottom: "10px", fontSize: "14px", color: "var(--text-primary)" }}>Data Management</h4>
                <div style={{ display: "flex", gap: "10px" }}>
                  <button className="btn btn--secondary" onClick={handleExportData}>
                    Export Data
                  </button>
                  <button className="btn btn--danger" onClick={handleDeleteAllData}>
                    Delete All Data
                  </button>
                </div>
              </div>
            </SettingsSection>
          )}

          {activeSection === "notifications" && (
            <SettingsSection
              title="Notifications"
              description="Choose what you want to be notified about."
            >
              <SettingsRow
                label="Product updates"
                description="New features and improvements"
              >
                <Toggle active={preferences.notif_product} onChange={(v) => updatePref("notif_product", v)} />
              </SettingsRow>
              <SettingsRow
                label="Health reminders"
                description="Medication reminders, check-up prompts"
              >
                <Toggle active={preferences.notif_health} onChange={(v) => updatePref("notif_health", v)} />
              </SettingsRow>
            </SettingsSection>
          )}

          {activeSection === "memory" && (
            <SettingsSection
              title="AI Memory"
              description="Explicit facts Forraa remembers about you across conversations."
            >
              {memoryItems.length === 0 ? (
                <p style={{ color: "var(--text-tertiary)" }}>No memories stored yet.</p>
              ) : (
                memoryItems.map((item) => (
                  <SettingsRow
                    key={item.id}
                    label={item.category}
                    description={item.content}
                  >
                    <button className="btn btn--danger" onClick={() => handleDeleteMemory(item.id)}>Delete</button>
                  </SettingsRow>
                ))
              )}
            </SettingsSection>
          )}

          {activeSection === "appearance" && (
            <SettingsSection
              title="Appearance"
              description="Customize the look and feel."
            >
              <SettingsRow
                label="Theme"
                description="Choose your preferred color scheme"
              >
                <select
                  value={preferences.theme}
                  onChange={(e) => updatePref("theme", e.target.value)}
                >
                  <option value="light">Light</option>
                  <option value="dark">Dark</option>
                  <option value="system">System</option>
                </select>
              </SettingsRow>
              <SettingsRow
                label="Unit Preference"
                description="Choose your preferred measurement units"
              >
                <select
                  value={preferences.unit_preference}
                  onChange={(e) => updatePref("unit_preference", e.target.value)}
                >
                  <option value="metric">Metric (kg, cm, °C)</option>
                  <option value="imperial">Imperial (lbs, in, °F)</option>
                </select>
              </SettingsRow>
            </SettingsSection>
          )}

          {activeSection === "security" && (
            <SettingsSection
              title="Security"
              description="Manage your account security."
            >
              <SettingsRow
                label="Password"
                description="Managed by your authentication provider"
              >
                <input type="password" placeholder="••••••••" disabled />
              </SettingsRow>
              <SettingsRow
                label="Active sessions"
                description="Manage devices signed into your account"
              >
                <span className="settings-row__value">1 active session</span>
              </SettingsRow>
            </SettingsSection>
          )}
        </div>
      </div>
    </div>
  );
}

export default Settings;
