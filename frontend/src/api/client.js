const API_BASE_URL = "http://localhost:8000";

async function apiRequest(endpoint, options = {}) {
    const response = await fetch(`${API_BASE_URL}${endpoint}`, {
        ...options,
        headers: {
            "Content-Type": "application/json",
            ...(options.headers || {}),
        },
    });

    if (!response.ok) {
        throw new Error(`API error: ${response.status}`);
    }

    return await response.json();
}

export { apiRequest };