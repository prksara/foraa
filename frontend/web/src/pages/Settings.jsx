import { useState, useEffect } from "react";
import {
  User,
  Heart,
  Shield,
  Bell,
  Monitor,
  Lock,
} from "lucide-react";
import SettingsSection from "../components/SettingsSection";
import SettingsRow from "../components/SettingsRow";
import * as api from "../api/client";

const sections = [
  { id: "account", label: "Account", icon: User },
  { id: "health", label: "Health Profile", icon: Heart },
  { id: "privacy", label: "Privacy", icon: Shield },
  { id: "notifications", label: "Notifications", icon: Bell },
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
  const [activeSection, setActiveSection] = useState("account");
  const [notifProduct, setNotifProduct] = useState(true);
  const [notifHealth, setNotifHealth] = useState(false);
  const [aiDataPref, setAiDataPref] = useState(true);
  const [profile, setProfile] = useState(null);

  useEffect(() => {
    api.fetchHealthProfile().then(p => {
      if (p) setProfile(p);
      else setProfile({});
    }).catch(console.error);
  }, []);

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
              <SettingsRow
                label="Name"
                description="Your display name"
              >
                <input type="text" placeholder="Your name" />
              </SettingsRow>
              <SettingsRow
                label="Email"
                description="Your email address"
              >
                <input type="email" placeholder="you@example.com" />
              </SettingsRow>
            </SettingsSection>
          )}

          {activeSection === "health" && (
            <SettingsSection
              title="Health Profile"
              description="Personal health information that helps Forraa provide better guidance. You can also view this in My Health."
            >
              <SettingsRow
                label="Date of birth"
                description="Used for age-appropriate recommendations"
              >
                <input 
                  type="date" 
                  value={profile?.date_of_birth || ""}
                  onChange={e => setProfile({...profile, date_of_birth: e.target.value})}
                />
              </SettingsRow>
              <SettingsRow
                label="Biological sex"
                description="Relevant for health reference ranges"
              >
                <select 
                  value={profile?.sex || ""}
                  onChange={e => setProfile({...profile, sex: e.target.value})}
                >
                  <option value="" disabled>Select</option>
                  <option value="female">Female</option>
                  <option value="male">Male</option>
                  <option value="other">Other</option>
                  <option value="prefer-not">Prefer not to say</option>
                </select>
              </SettingsRow>
              <SettingsRow
                label="Blood Type"
                description="Your blood group"
              >
                <input 
                  type="text" 
                  placeholder="e.g. O+, A-"
                  value={profile?.blood_type || ""}
                  onChange={e => setProfile({...profile, blood_type: e.target.value})}
                />
              </SettingsRow>
              <div style={{ marginTop: '1rem', display: 'flex', justifyContent: 'flex-end' }}>
                <button 
                   className="btn btn--primary" 
                   onClick={async () => {
                     await api.updateHealthProfile(profile);
                     alert("Profile saved!");
                   }}
                >
                  Save Profile
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
                <Toggle
                  active={aiDataPref}
                  onChange={setAiDataPref}
                />
              </SettingsRow>
              <SettingsRow
                label="Data retention"
                description="How long your conversation history is stored"
              >
                <select defaultValue="90">
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
                <Toggle active={true} />
              </SettingsRow>
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
                <Toggle
                  active={notifProduct}
                  onChange={setNotifProduct}
                />
              </SettingsRow>
              <SettingsRow
                label="Health reminders"
                description="Medication reminders, check-up prompts"
              >
                <Toggle
                  active={notifHealth}
                  onChange={setNotifHealth}
                />
              </SettingsRow>
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
                <select defaultValue="light">
                  <option value="light">Light</option>
                  <option value="dark">Dark</option>
                  <option value="system">System</option>
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
                description="Update your password"
              >
                <input type="password" placeholder="••••••••" />
              </SettingsRow>
              <SettingsRow
                label="Active sessions"
                description="Manage devices signed into your account"
              >
                <span className="settings-row__value">1 active</span>
              </SettingsRow>
            </SettingsSection>
          )}
        </div>
      </div>
    </div>
  );
}

export default Settings;