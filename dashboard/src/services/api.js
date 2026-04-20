const API_BASE_URL = import.meta.env.VITE_PHISHGUARD_API_URL || "http://localhost:8000/api";
const TOKEN_KEY = "phishguardAdminToken";

export function getToken() {
  return localStorage.getItem(TOKEN_KEY);
}

export function setToken(token) {
  localStorage.setItem(TOKEN_KEY, token);
}

export function clearToken() {
  localStorage.removeItem(TOKEN_KEY);
}

async function request(path, options = {}) {
  const token = getToken();
  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...(options.headers || {})
    }
  });
  if (!response.ok) {
    const body = await response.json().catch(() => ({}));
    throw new Error(body.detail || `Request failed with status ${response.status}`);
  }
  return response.json();
}

export async function login(username, password) {
  const result = await request("/admin/login", {
    method: "POST",
    body: JSON.stringify({ username, password })
  });
  setToken(result.access_token);
  return result;
}

export function fetchSummary() {
  return request("/admin/summary");
}

export function fetchRecent() {
  return request("/admin/recent?limit=20");
}

export function fetchTrends() {
  return request("/admin/trends?days=14");
}

export function fetchBrands() {
  return request("/admin/brands?limit=8");
}

export function fetchFeedback() {
  return request("/admin/feedback?limit=20");
}

export function fetchSiemExport() {
  return request("/siem/export?limit=100");
}
