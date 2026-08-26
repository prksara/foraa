// --------------------------------------------------
// Foraa API Client
// All backend communication is centralized here.
// Components never call fetch() directly.
// --------------------------------------------------

import { supabase } from '../lib/supabase'

const BASE_URL = import.meta.env.VITE_API_URL ?? "http://localhost:8000";

async function getAuthHeader() {
    const { data: { session } } = await supabase.auth.getSession()
    return session?.access_token ? { Authorization: `Bearer ${session.access_token}` } : {}
}

/**
 * Low-level fetch wrapper.
 * Throws a structured error on non-2xx responses.
 */
async function request(path, options = {}) {
    const url = `${BASE_URL}${path}`;
    const authHeader = await getAuthHeader();

    const response = await fetch(url, {
        headers: {
            "Content-Type": "application/json",
            ...authHeader,
            ...options.headers,
        },
        ...options,
    });

    if (!response.ok) {
        let detail = `HTTP ${response.status}`;
        try {
            const errorBody = await response.json();
            detail = errorBody.detail ?? detail;
        } catch {
            // ignore JSON parse error — use the HTTP status
        }
        throw new Error(detail);
    }

    return response.json();
}

// --------------------------------------------------
// Health
// --------------------------------------------------

export async function checkHealth() {
    return request("/health");
}

// --------------------------------------------------
// Conversations
// --------------------------------------------------

export async function fetchConversations() {
    return request("/conversations");
}

export async function fetchConversation(id) {
    return request(`/conversations/${id}`);
}

export async function createConversation() {
    return request("/conversations", { method: "POST" });
}

export async function deleteConversation(id) {
    return request(`/conversations/${id}`, { method: "DELETE" });
}

// --------------------------------------------------
// Chat
// --------------------------------------------------

export async function sendChatMessage(message) {
    return request("/chat", {
        method: "POST",
        body: JSON.stringify({ message }),
    });
}

/**
 * Stream a chat response.
 * @param {string} message 
 * @param {string} conversation_id 
 * @param {string} active_report_id
 * @param {function} onMessage - called with content chunk or conversation id
 * @param {AbortSignal} signal - optional abort signal
 */
export async function streamChatMessage(message, conversation_id, active_report_id, onMessage, signal) {
    const url = `${BASE_URL}/chat/stream`;
    const authHeader = await getAuthHeader();
    
    const response = await fetch(url, {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
            ...authHeader,
        },
        body: JSON.stringify({ message, conversation_id, active_report_id }),
        signal
    });

    if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder("utf-8");
    let buffer = "";

    try {
        while (true) {
            const { done, value } = await reader.read();
            if (done) break;

            buffer += decoder.decode(value, { stream: true });
            const lines = buffer.split("\n");
            
            // Keep the last incomplete line in the buffer
            buffer = lines.pop();

            for (const line of lines) {
                if (line.startsWith("data: ")) {
                    const dataStr = line.slice(6);
                    if (dataStr.trim() === "[DONE]") {
                        return;
                    }
                    try {
                        const data = JSON.parse(dataStr);
                        onMessage(data);
                    } catch (e) {
                        console.error("Error parsing SSE data", e, dataStr);
                    }
                }
            }
        }
    } finally {
        reader.releaseLock();
    }
}

// --------------------------------------------------
// Health Intelligence
// --------------------------------------------------

export async function fetchHealthSummary() {
    return request("/health/summary");
}

export async function fetchHealthProfile() {
    return request("/health/profile");
}

export async function updateHealthProfile(data) {
    return request("/health/profile", { method: "PUT", body: JSON.stringify(data) });
}

// Conditions
export async function fetchConditions() { return request("/health/conditions"); }
export async function createCondition(data) { return request("/health/conditions", { method: "POST", body: JSON.stringify(data) }); }
export async function updateCondition(id, data) { return request(`/health/conditions/${id}`, { method: "PUT", body: JSON.stringify(data) }); }
export async function deleteCondition(id) { return request(`/health/conditions/${id}`, { method: "DELETE" }); }

// Allergies
export async function fetchAllergies() { return request("/health/allergies"); }
export async function createAllergy(data) { return request("/health/allergies", { method: "POST", body: JSON.stringify(data) }); }
export async function updateAllergy(id, data) { return request(`/health/allergies/${id}`, { method: "PUT", body: JSON.stringify(data) }); }
export async function deleteAllergy(id) { return request(`/health/allergies/${id}`, { method: "DELETE" }); }

// Medications
export async function fetchMedications() { return request("/health/medications"); }
export async function createMedication(data) { return request("/health/medications", { method: "POST", body: JSON.stringify(data) }); }
export async function updateMedication(id, data) { return request(`/health/medications/${id}`, { method: "PUT", body: JSON.stringify(data) }); }
export async function deleteMedication(id) { return request(`/health/medications/${id}`, { method: "DELETE" }); }

// Lifestyle
export async function fetchLifestyle() { return request("/health/lifestyle"); }
export async function createLifestyle(data) { return request("/health/lifestyle", { method: "POST", body: JSON.stringify(data) }); }
export async function updateLifestyle(id, data) { return request(`/health/lifestyle/${id}`, { method: "PUT", body: JSON.stringify(data) }); }
export async function deleteLifestyle(id) { return request(`/health/lifestyle/${id}`, { method: "DELETE" }); }

// Goals
export async function fetchGoals() { return request("/health/goals"); }
export async function createGoal(data) { return request("/health/goals", { method: "POST", body: JSON.stringify(data) }); }
export async function updateGoal(id, data) { return request(`/health/goals/${id}`, { method: "PUT", body: JSON.stringify(data) }); }
export async function deleteGoal(id) { return request(`/health/goals/${id}`, { method: "DELETE" }); }

// Measurements
export async function fetchMeasurements() { return request("/health/measurements"); }
export async function createMeasurement(data) { return request("/health/measurements", { method: "POST", body: JSON.stringify(data) }); }
export async function deleteMeasurement(id) { return request(`/health/measurements/${id}`, { method: "DELETE" }); }

// --------------------------------------------------
// Reports
// --------------------------------------------------

export async function uploadReport(files) {
    const formData = new FormData();
    // Assuming single file upload right now, backend accepts UploadFile
    formData.append("file", files[0]);
    
    const url = `${BASE_URL}/reports/upload`;
    const authHeader = await getAuthHeader();
    const response = await fetch(url, {
        method: 'POST',
        headers: {
            ...authHeader
        },
        body: formData
    });
    
    if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
    }
    return response.json();
}

export async function fetchReports() { return request("/reports"); }
export async function fetchReportDetails(id) { return request(`/reports/${id}`); }
export async function deleteReport(id) { return request(`/reports/${id}`, { method: "DELETE" }); }

export async function confirmExtraction(documentId, extractionId) {
    return request(`/reports/${documentId}/extractions/${extractionId}/confirm`, { method: "POST" });
}
export async function rejectExtraction(documentId, extractionId) {
    return request(`/reports/${documentId}/extractions/${extractionId}/reject`, { method: "POST" });
}

