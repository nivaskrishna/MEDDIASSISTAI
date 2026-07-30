import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || (import.meta.env.PROD ? '/api' : 'http://localhost:8000/api');

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
    'Bypass-Tunnel-Reminder': 'true',
  },
});

// ──────────────────────────────────────────────────────────────────────────────
// Session ID — stored in localStorage, sent as X-Session-Id header
// Enables MongoDB history to link analyses to the same browser session.
// ──────────────────────────────────────────────────────────────────────────────

export function getSessionId() {
  let sid = localStorage.getItem('mediassist_session_id');
  if (!sid) {
    sid = crypto.randomUUID
      ? crypto.randomUUID()
      : Math.random().toString(36).slice(2) + Date.now().toString(36);
    localStorage.setItem('mediassist_session_id', sid);
  }
  return sid;
}

// ──────────────────────────────────────────────────────────────────────────────
// Core API calls
// ──────────────────────────────────────────────────────────────────────────────

export const analyzeSymptoms = async (query, image = null) => {
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), 45000);

  try {
    const response = await api.post('/analyze/analyze', { query, image }, {
      signal: controller.signal,
      timeout: 45000,
      headers: { 'X-Session-Id': getSessionId() }, // Enable MongoDB history saving
    });
    clearTimeout(timeoutId);
    return response.data;
  } catch (err) {
    clearTimeout(timeoutId);
    if (err.name === 'AbortError' || err.code === 'ECONNABORTED') {
      throw new Error('Analysis timed out. Please try again.');
    }
    throw err;
  }
};

export const searchHospitals = async (query, radius = 10, lat = null, lon = null) => {
  const params = { radius };
  if (lat !== null && lon !== null) {
    params.lat = lat;
    params.lon = lon;
  } else if (query && query.trim()) {
    params.query = query.trim();
  }
  const response = await api.get('/hospitals/search', { params });
  return response.data;
};

export const getMyLocation = async () => {
  const response = await api.get('/hospitals/geolocation');
  return response.data;
};

export const getConditions = async (search = '') => {
  const response = await api.get('/conditions', { params: { search } });
  return response.data;
};

export const getEmergencyContacts = async () => {
  const response = await api.get('/emergency-contacts');
  return response.data;
};

/**
 * Generate an image with Stable Diffusion XL via the backend.
 */
export const generateSDXLImage = async (prompt) => {
  const response = await api.post('/image-gen/generate', { prompt }, {
    timeout: 120000,
  });
  return response.data;
};

// ──────────────────────────────────────────────────────────────────────────────
// History API — MongoDB chat history & saved diagnoses (Phase 4)
// ──────────────────────────────────────────────────────────────────────────────

export const getHistory = async (limit = 20) => {
  try {
    const sid = getSessionId();
    const res = await api.get(`/history/${sid}`, { params: { limit } });
    return res.data; // { session_id, count, history: [...] }
  } catch {
    return { history: [] };
  }
};

export const clearHistory = async () => {
  try {
    const sid = getSessionId();
    const res = await api.delete(`/history/${sid}`);
    return res.data;
  } catch {
    return { deleted: 0 };
  }
};

export const saveDiagnosis = async ({ condition, severity, first_aid, doctor_type }) => {
  try {
    const res = await api.post('/history/save-diagnosis', {
      session_id: getSessionId(),
      condition, severity, first_aid, doctor_type,
    });
    return res.data;
  } catch {
    return { saved: false };
  }
};

export const getSavedDiagnoses = async () => {
  try {
    const sid = getSessionId();
    const res = await api.get(`/history/${sid}/saved`);
    return res.data;
  } catch {
    return { saved: [] };
  }
};

// ──────────────────────────────────────────────────────────────────────────────
// OpenFDA Drug Search (Phase 1)
// ──────────────────────────────────────────────────────────────────────────────

export const searchDrug = async (name, limit = 5) => {
  try {
    const res = await api.get('/fda/drug', { params: { name, limit } });
    return res.data; // { query, count, results: [...] }
  } catch (err) {
    console.warn('[api] Drug search failed:', err.message);
    return { results: [] };
  }
};

// ──────────────────────────────────────────────────────────────────────────────
// Country Info + Emergency Numbers (Phase 2)
// ──────────────────────────────────────────────────────────────────────────────

export const getCountryInfo = async (iso2) => {
  try {
    const res = await api.get(`/country/${iso2}`);
    return res.data;
  } catch {
    return null;
  }
};

export default api;
