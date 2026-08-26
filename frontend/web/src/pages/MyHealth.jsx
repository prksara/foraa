import { useState, useEffect } from "react";
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
  Trash2,
} from "lucide-react";
import Tabs from "../components/Tabs";
import Card from "../components/Card";
import HealthMetric from "../components/HealthMetric";
import EmptyState from "../components/EmptyState";
import SectionHeader from "../components/SectionHeader";
import Button from "../components/Button";
import * as api from "../api/client";

const tabs = [
  { id: "overview", label: "Overview" },
  { id: "profile", label: "Profile" },
  { id: "conditions", label: "Conditions" },
  { id: "allergies", label: "Allergies" },
  { id: "medications", label: "Medications" },
  { id: "goals", label: "Goals" },
  { id: "measurements", label: "Measurements" }
];

function MyHealth() {
  const [activeTab, setActiveTab] = useState("overview");
  
  // Data States
  const [summary, setSummary] = useState(null);
  const [profile, setProfile] = useState(null);
  const [conditions, setConditions] = useState([]);
  const [allergies, setAllergies] = useState([]);
  const [medications, setMedications] = useState([]);
  const [goals, setGoals] = useState([]);
  const [measurements, setMeasurements] = useState([]);

  // Form states (simple inline forms)
  const [showAddCondition, setShowAddCondition] = useState(false);
  const [newCondition, setNewCondition] = useState({ name: "", status: "active" });

  const [showAddAllergy, setShowAddAllergy] = useState(false);
  const [newAllergy, setNewAllergy] = useState({ substance: "", severity: "moderate", status: "active" });

  const [showAddMedication, setShowAddMedication] = useState(false);
  const [newMedication, setNewMedication] = useState({ name: "", dose: "", status: "active" });

  const [showAddGoal, setShowAddGoal] = useState(false);
  const [newGoal, setNewGoal] = useState({ title: "", category: "general" });

  // Load initial data
  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      setSummary(await api.fetchHealthSummary());
      setProfile(await api.fetchHealthProfile());
      setConditions(await api.fetchConditions());
      setAllergies(await api.fetchAllergies());
      setMedications(await api.fetchMedications());
      setGoals(await api.fetchGoals());
      setMeasurements(await api.fetchMeasurements());
    } catch (err) {
      console.error("Failed to load health data", err);
    }
  };

  // Handlers
  const handleAddCondition = async () => {
    if (!newCondition.name) return;
    await api.createCondition(newCondition);
    setNewCondition({ name: "", status: "active" });
    setShowAddCondition(false);
    loadData();
  };
  const handleDeleteCondition = async (id) => {
    await api.deleteCondition(id);
    loadData();
  };

  const handleAddAllergy = async () => {
    if (!newAllergy.substance) return;
    await api.createAllergy(newAllergy);
    setNewAllergy({ substance: "", severity: "moderate", status: "active" });
    setShowAddAllergy(false);
    loadData();
  };
  const handleDeleteAllergy = async (id) => {
    await api.deleteAllergy(id);
    loadData();
  };

  const handleAddMedication = async () => {
    if (!newMedication.name) return;
    await api.createMedication(newMedication);
    setNewMedication({ name: "", dose: "", status: "active" });
    setShowAddMedication(false);
    loadData();
  };
  const handleDeleteMedication = async (id) => {
    await api.deleteMedication(id);
    loadData();
  };

  const handleAddGoal = async () => {
    if (!newGoal.title) return;
    await api.createGoal(newGoal);
    setNewGoal({ title: "", category: "general" });
    setShowAddGoal(false);
    loadData();
  };
  const handleDeleteGoal = async (id) => {
    await api.deleteGoal(id);
    loadData();
  };

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
        <div style={{display: 'flex', flexDirection: 'column', gap: '20px'}}>
          <SectionHeader title="Health Snapshot" />
          <div className="health-metrics-grid">
            <HealthMetric icon={<Activity size={16} />} name="Active Conditions" value={summary?.active_conditions_count || 0} />
            <HealthMetric icon={<Pill size={16} />} name="Active Medications" value={summary?.active_medications_count || 0} />
            <HealthMetric icon={<Heart size={16} />} name="Allergies" value={summary?.allergies_count || 0} />
            <HealthMetric icon={<Thermometer size={16} />} name="Active Goals" value={summary?.active_goals_count || 0} />
          </div>
        </div>
      )}

      {activeTab === "profile" && (
        <Card padding="lg">
          <SectionHeader title="Health Profile" />
          <div style={{display: 'flex', flexDirection: 'column', gap: '10px'}}>
             <p><strong>Sex:</strong> {profile?.sex || 'Not specified'}</p>
             <p><strong>Blood Type:</strong> {profile?.blood_type || 'Not specified'}</p>
             <p><strong>Height:</strong> {profile?.height ? `${profile.height} ${profile.height_unit}` : 'Not specified'}</p>
             <p><strong>Weight:</strong> {profile?.weight ? `${profile.weight} ${profile.weight_unit}` : 'Not specified'}</p>
             <p><em>(You can update this in Settings)</em></p>
          </div>
        </Card>
      )}

      {activeTab === "conditions" && (
        <Card padding="lg">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
            <SectionHeader title="Health Conditions" />
            <Button variant="primary" onClick={() => setShowAddCondition(true)}>Add Condition</Button>
          </div>
          
          {showAddCondition && (
            <div style={{ marginBottom: '20px', padding: '15px', background: 'var(--surface-50)', borderRadius: '8px' }}>
              <input 
                type="text" 
                placeholder="Condition Name (e.g., Hypertension)" 
                value={newCondition.name}
                onChange={e => setNewCondition({...newCondition, name: e.target.value})}
                style={{marginRight: '10px', padding: '8px'}}
              />
              <Button onClick={handleAddCondition}>Save</Button>
              <Button variant="ghost" onClick={() => setShowAddCondition(false)}>Cancel</Button>
            </div>
          )}

          {conditions.length === 0 ? (
            <EmptyState icon={<Activity size={24} />} title="No conditions recorded" description="Add your health conditions to improve AI relevance." />
          ) : (
            <ul style={{ listStyle: 'none', padding: 0 }}>
              {conditions.map(c => (
                <li key={c.id} style={{ display: 'flex', justifyContent: 'space-between', padding: '10px', borderBottom: '1px solid var(--border)' }}>
                  <div>
                    <strong>{c.name}</strong> - <span>{c.status}</span>
                  </div>
                  <Button variant="ghost" size="sm" onClick={() => handleDeleteCondition(c.id)}><Trash2 size={16}/></Button>
                </li>
              ))}
            </ul>
          )}
        </Card>
      )}

      {activeTab === "allergies" && (
        <Card padding="lg">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
            <SectionHeader title="Allergies" />
            <Button variant="primary" onClick={() => setShowAddAllergy(true)}>Add Allergy</Button>
          </div>

          {showAddAllergy && (
            <div style={{ marginBottom: '20px', padding: '15px', background: 'var(--surface-50)', borderRadius: '8px' }}>
              <input 
                type="text" 
                placeholder="Substance (e.g., Peanuts)" 
                value={newAllergy.substance}
                onChange={e => setNewAllergy({...newAllergy, substance: e.target.value})}
                style={{marginRight: '10px', padding: '8px'}}
              />
              <Button onClick={handleAddAllergy}>Save</Button>
              <Button variant="ghost" onClick={() => setShowAddAllergy(false)}>Cancel</Button>
            </div>
          )}

          {allergies.length === 0 ? (
            <EmptyState icon={<Activity size={24} />} title="No allergies recorded" description="Add your allergies to keep them in context." />
          ) : (
            <ul style={{ listStyle: 'none', padding: 0 }}>
              {allergies.map(a => (
                <li key={a.id} style={{ display: 'flex', justifyContent: 'space-between', padding: '10px', borderBottom: '1px solid var(--border)' }}>
                  <div>
                    <strong>{a.substance}</strong> - <span>Severity: {a.severity}</span>
                  </div>
                  <Button variant="ghost" size="sm" onClick={() => handleDeleteAllergy(a.id)}><Trash2 size={16}/></Button>
                </li>
              ))}
            </ul>
          )}
        </Card>
      )}

      {activeTab === "medications" && (
        <Card padding="lg">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
            <SectionHeader title="Medications" />
            <Button variant="primary" onClick={() => setShowAddMedication(true)}>Add Medication</Button>
          </div>

          {showAddMedication && (
            <div style={{ marginBottom: '20px', padding: '15px', background: 'var(--surface-50)', borderRadius: '8px' }}>
              <input 
                type="text" 
                placeholder="Medication Name" 
                value={newMedication.name}
                onChange={e => setNewMedication({...newMedication, name: e.target.value})}
                style={{marginRight: '10px', padding: '8px'}}
              />
              <input 
                type="text" 
                placeholder="Dose (e.g. 50mg)" 
                value={newMedication.dose}
                onChange={e => setNewMedication({...newMedication, dose: e.target.value})}
                style={{marginRight: '10px', padding: '8px'}}
              />
              <Button onClick={handleAddMedication}>Save</Button>
              <Button variant="ghost" onClick={() => setShowAddMedication(false)}>Cancel</Button>
            </div>
          )}

          {medications.length === 0 ? (
            <EmptyState icon={<Pill size={24} />} title="No medications tracked" description="Add your medications to keep a complete picture of your health." />
          ) : (
            <ul style={{ listStyle: 'none', padding: 0 }}>
              {medications.map(m => (
                <li key={m.id} style={{ display: 'flex', justifyContent: 'space-between', padding: '10px', borderBottom: '1px solid var(--border)' }}>
                  <div>
                    <strong>{m.name}</strong> - <span>{m.dose}</span> ({m.status})
                  </div>
                  <Button variant="ghost" size="sm" onClick={() => handleDeleteMedication(m.id)}><Trash2 size={16}/></Button>
                </li>
              ))}
            </ul>
          )}
        </Card>
      )}

      {activeTab === "goals" && (
        <Card padding="lg">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
            <SectionHeader title="Health Goals" />
            <Button variant="primary" onClick={() => setShowAddGoal(true)}>Add Goal</Button>
          </div>

          {showAddGoal && (
            <div style={{ marginBottom: '20px', padding: '15px', background: 'var(--surface-50)', borderRadius: '8px' }}>
              <input 
                type="text" 
                placeholder="Goal Title" 
                value={newGoal.title}
                onChange={e => setNewGoal({...newGoal, title: e.target.value})}
                style={{marginRight: '10px', padding: '8px'}}
              />
              <Button onClick={handleAddGoal}>Save</Button>
              <Button variant="ghost" onClick={() => setShowAddGoal(false)}>Cancel</Button>
            </div>
          )}

          {goals.length === 0 ? (
            <EmptyState icon={<Activity size={24} />} title="No goals set" description="Set health goals to track your progress." />
          ) : (
            <ul style={{ listStyle: 'none', padding: 0 }}>
              {goals.map(g => (
                <li key={g.id} style={{ display: 'flex', justifyContent: 'space-between', padding: '10px', borderBottom: '1px solid var(--border)' }}>
                  <div>
                    <strong>{g.title}</strong> - <span>{g.status}</span>
                  </div>
                  <Button variant="ghost" size="sm" onClick={() => handleDeleteGoal(g.id)}><Trash2 size={16}/></Button>
                </li>
              ))}
            </ul>
          )}
        </Card>
      )}
      
      {activeTab === "measurements" && (
         <Card padding="lg">
           <SectionHeader title="Measurements" />
           {measurements.length === 0 ? (
            <EmptyState icon={<Activity size={24} />} title="No measurements" description="No measurements recorded yet." />
           ) : (
             <ul style={{ listStyle: 'none', padding: 0 }}>
              {measurements.map(m => (
                <li key={m.id} style={{ padding: '10px', borderBottom: '1px solid var(--border)' }}>
                  <strong>{m.type}</strong>: {m.value} {m.secondary_value && `/ ${m.secondary_value}`} {m.unit}
                </li>
              ))}
            </ul>
           )}
         </Card>
      )}

    </div>
  );
}

export default MyHealth;