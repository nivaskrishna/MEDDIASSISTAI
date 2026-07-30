/**
 * diseaseApi.js
 * Calls our backend /api/disease/* which proxies disease.sh.
 * (We proxy through backend so we can cache and add error handling.)
 */

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000/api';

/**
 * Fetch worldwide COVID/disease statistics.
 * @returns {object} { cases, deaths, recovered, active, critical, todayCases, todayDeaths }
 */
export async function fetchGlobalStats() {
  try {
    const res = await fetch(`${API_BASE}/disease/stats`, {
      signal: AbortSignal.timeout(8000),
      headers: { 'Bypass-Tunnel-Reminder': 'true' },
    });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    return await res.json();
  } catch (err) {
    console.warn('[diseaseApi] Failed to fetch global stats:', err.message);
    return null;
  }
}

/**
 * Fetch disease stats for a specific country.
 * @param {string} countryCode - ISO2 or ISO3 country code
 */
export async function fetchCountryStats(countryCode) {
  try {
    const res = await fetch(`${API_BASE}/disease/country/${countryCode}`, {
      signal: AbortSignal.timeout(8000),
      headers: { 'Bypass-Tunnel-Reminder': 'true' },
    });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    return await res.json();
  } catch (err) {
    console.warn('[diseaseApi] Failed to fetch country stats:', err.message);
    return null;
  }
}
