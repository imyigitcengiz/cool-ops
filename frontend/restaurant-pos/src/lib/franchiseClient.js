const API_BASE = (import.meta.env.VITE_API_URL || '') + '/restoran/api';

export function getFranchiseToken() {
  return localStorage.getItem('franchise_token') || '';
}

export async function franchiseFetch(path, options = {}) {
  const token = getFranchiseToken();
  const url = `${API_BASE}/franchise${path.startsWith('/') ? path : `/${path}`}`;
  const headers = {
    'Content-Type': 'application/json',
    'Franchise-Token': token,
    ...(options.headers || {}),
  };
  const res = await fetch(url, { ...options, headers });
  if (res.status === 401 || res.status === 403) {
    window.dispatchEvent(new CustomEvent('franchise-session-expired'));
  }
  return res;
}
