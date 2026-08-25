const BASE_URL = (import.meta.env.VITE_API_BASE_URL || '').replace(/\/$/, '');

export const ACCESS_KEY = 'erean_access';
export const REFRESH_KEY = 'erean_refresh';

export function getAccess() {
  return localStorage.getItem(ACCESS_KEY);
}

export function getRefresh() {
  return localStorage.getItem(REFRESH_KEY);
}

export function setTokens(access, refresh) {
  if (access) localStorage.setItem(ACCESS_KEY, access);
  if (refresh) localStorage.setItem(REFRESH_KEY, refresh);
}

export function clearTokens() {
  localStorage.removeItem(ACCESS_KEY);
  localStorage.removeItem(REFRESH_KEY);
}

function logout() {
  clearTokens();
  window.dispatchEvent(new CustomEvent('erean:logout'));
}

let refreshPromise = null;

async function refreshAccessToken() {
  const refresh = getRefresh();
  if (!refresh) return null;

  if (!refreshPromise) {
    refreshPromise = fetch(`${BASE_URL}/api/auth/token/refresh/`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ refresh }),
    })
      .then((res) => (res.ok ? res.json() : null))
      .then((data) => {
        if (data?.access) {
          setTokens(data.access, null);
          return data.access;
        }
        return null;
      })
      .catch(() => null)
      .finally(() => {
        refreshPromise = null;
      });
  }
  return refreshPromise;
}

export async function apiFetch(path, options = {}) {
  const { isForm = false, ...rest } = options;

  const send = async (token) => {
    const headers = { ...(rest.headers || {}) };
    if (token) headers.Authorization = `Bearer ${token}`;

    if (!isForm && rest.body && !headers['Content-Type']) {
      headers['Content-Type'] = 'application/json';
    }
    return fetch(`${BASE_URL}${path}`, { ...rest, headers });
  };

  let response;
  try {
    response = await send(getAccess());
  } catch {
    return { ok: false, status: 0, error: { detail: 'Cannot reach the server.' } };
  }

  if (response.status === 401 && getRefresh()) {
    const fresh = await refreshAccessToken();
    if (!fresh) {
      logout();
      return { ok: false, status: 401, error: { detail: 'Your session has expired.' } };
    }
    response = await send(fresh);
    if (response.status === 401) {
      logout();
      return { ok: false, status: 401, error: { detail: 'Your session has expired.' } };
    }
  }

  if (response.status === 204) return { ok: true, data: null };

  const contentType = response.headers.get('content-type') || '';
  let body = null;
  if (contentType.includes('application/json')) {
    body = await response.json().catch(() => null);
  }

  if (!response.ok) {
    return { ok: false, status: response.status, error: body || {} };
  }
  return { ok: true, data: body };
}

export async function downloadFile(path, fallbackName = 'download') {
  const response = await fetch(`${BASE_URL}${path}`, {
    headers: { Authorization: `Bearer ${getAccess()}` },
  });
  if (!response.ok) {
    return { ok: false, status: response.status, error: {} };
  }

  const contentType = response.headers.get('content-type') || '';

  if (contentType.includes('application/json')) {
    const data = await response.json();
    if (data.link_url) {
      window.open(data.link_url, '_blank', 'noopener');
      return { ok: true, data };
    }
    return { ok: false, status: response.status, error: data };
  }

  const disposition = response.headers.get('content-disposition') || '';
  const match = disposition.match(/filename="?([^";]+)"?/);
  const blob = await response.blob();
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = match ? match[1] : fallbackName;
  document.body.appendChild(link);
  link.click();
  link.remove();
  URL.revokeObjectURL(url);
  return { ok: true, data: null };
}

export const get = (path) => apiFetch(path);
export const post = (path, body) =>
  apiFetch(path, { method: 'POST', body: JSON.stringify(body) });
export const patch = (path, body) =>
  apiFetch(path, { method: 'PATCH', body: JSON.stringify(body) });
export const del = (path) => apiFetch(path, { method: 'DELETE' });
export const postForm = (path, formData) =>
  apiFetch(path, { method: 'POST', body: formData, isForm: true });
