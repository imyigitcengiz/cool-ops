const API_BASE = (import.meta.env.VITE_API_URL || '') + '/restoran/api';

const BRANCH_EXEMPT_PREFIXES = [
  '/auth/',
  '/branches',
  '/restaurant-profile',
  '/payments/',
];

export function getSelectedBranchId() {
  return localStorage.getItem('selected_branch_id') || '';
}

export function setSelectedBranchId(id) {
  if (id) {
    localStorage.setItem('selected_branch_id', String(id));
  } else {
    localStorage.removeItem('selected_branch_id');
  }
  window.dispatchEvent(new CustomEvent('branch-changed', { detail: { branchId: id || null } }));
}

function shouldAttachBranch(path) {
  const raw = path.split('?')[0];
  const rel = raw.startsWith(API_BASE)
    ? raw.slice(API_BASE.length)
    : (raw.startsWith('/') ? raw : `/${raw}`);
  return !BRANCH_EXEMPT_PREFIXES.some((prefix) => rel.startsWith(prefix));
}

function withBranchQuery(path) {
  const branchId = getSelectedBranchId();
  if (!branchId || !shouldAttachBranch(path)) return path;
  if (path.includes('branch_id=')) return path;
  const sep = path.includes('?') ? '&' : '?';
  return `${path}${sep}branch_id=${encodeURIComponent(branchId)}`;
}

export function getAuthToken() {
  return localStorage.getItem('auth_token') || '';
}

export function authHeaders(extra = {}) {
  const token = getAuthToken();
  const headers = { ...extra };
  if (token) {
    headers.Authorization = `Token ${token}`;
  }
  return headers;
}

export function dispatchPlanExpired(detail) {
  window.dispatchEvent(new CustomEvent('plan-expired', { detail }));
}

export function dispatchUnauthorized() {
  window.dispatchEvent(new CustomEvent('auth-unauthorized'));
}

export async function apiFetch(path, options = {}) {
  const scopedPath = withBranchQuery(path);
  let url;
  if (scopedPath.startsWith('http')) {
    url = scopedPath;
  } else {
    const rel = scopedPath.startsWith('/') ? scopedPath : `/${scopedPath}`;
    url = rel === API_BASE || rel.startsWith(`${API_BASE}/`) ? rel : `${API_BASE}${rel}`;
  }
  const headers = authHeaders(options.headers || {});

  if (options.body && !(options.body instanceof FormData) && !headers['Content-Type']) {
    headers['Content-Type'] = 'application/json';
  }

  const res = await fetch(url, { ...options, headers });

  if (res.status === 401) {
    dispatchUnauthorized();
  }
  if (res.status === 402) {
    try {
      const data = await res.clone().json();
      dispatchPlanExpired(data);
    } catch {
      dispatchPlanExpired({});
    }
  }

  return res;
}

export async function apiJson(path, options = {}) {
  const res = await apiFetch(path, options);
  const data = await res.json().catch(() => ({}));
  return { res, data };
}

export { API_BASE };
