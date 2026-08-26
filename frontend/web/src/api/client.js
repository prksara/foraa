// --------------------------------------------------
// Foraa API Client
// All backend communication is centralized here.
// Components never call fetch() directly.
// --------------------------------------------------

const BASE_URL = import.meta.env.VITE_API_URL ?? "http://localhost:8000";

/**
 * Low-level fetch wrapper.
 * Throws a structured error on non-2xx responses.
 *
 * @param {string} path     - API path, e.g. "/chat"
 * @param {RequestInit} [options] - fetch options (method, body, headers)
 * @returns {Promise<any>}  - parsed JSON response
 */
async function request(path, options = {}) {
    const url = `${BASE_URL}${path}`;

    const response = await fetch(url, {
        headers: {
            "Content-Type": "application/json",
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

/**
 * Check that the Foraa backend is reachable.
 * @returns {Promise<{ status: string }>}
 */
export async function checkHealth() {
    return request("/health");
}

// --------------------------------------------------
// Chat
// --------------------------------------------------

/**
 * Send a chat message and receive a reply from Foraa.
 *
 * @param {string} message - the user's message
 * @returns {Promise<{ reply: string }>}
 */
export async function sendChatMessage(message) {
    return request("/chat", {
        method: "POST",
        body: JSON.stringify({ message }),
    });
}
