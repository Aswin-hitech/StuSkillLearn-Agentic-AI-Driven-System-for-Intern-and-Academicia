const API_BASE = import.meta.env.VITE_API_BASE_URL ?? '/api/v1';

type ApiOptions = RequestInit & {
  token?: string | null;
  skipAuthRefresh?: boolean;
};

let refreshPromise: Promise<boolean> | null = null;

async function parseError(response: Response): Promise<Error> {
  let message = `Request failed (${response.status})`;
  try {
    const data = await response.json();
    if (typeof data?.detail === 'string') message = data.detail;
    else if (Array.isArray(data?.detail)) message = data.detail.map((item: any) => item?.msg ?? String(item)).join('; ');
  } catch {
    // Preserve the HTTP fallback when the response is not JSON.
  }
  return new Error(message);
}

async function refreshSession(): Promise<boolean> {
  if (!refreshPromise) {
    refreshPromise = fetch(`${API_BASE}/auth/refresh`, {
      method: 'POST',
      credentials: 'include',
      headers: { Accept: 'application/json' },
    })
      .then((response) => response.ok)
      .catch(() => false)
      .finally(() => { refreshPromise = null; });
  }
  return refreshPromise;
}

async function request<T>(path: string, options: ApiOptions, includeBearer: boolean): Promise<T> {
  const { token, skipAuthRefresh: _skip, ...requestOptions } = options;
  const headers = new Headers(requestOptions.headers ?? {});
  if (!headers.has('Accept')) headers.set('Accept', 'application/json');
  if (!headers.has('Content-Type') && requestOptions.body && !(requestOptions.body instanceof FormData)) headers.set('Content-Type', 'application/json');
  if (includeBearer && token) headers.set('Authorization', `Bearer ${token}`);

  const response = await fetch(`${API_BASE}${path}`, {
    ...requestOptions,
    headers,
    credentials: 'include',
  });

  if (!response.ok) throw Object.assign(await parseError(response), { status: response.status });
  if (response.status === 204) return undefined as T;
  return response.json() as Promise<T>;
}

export async function api<T>(path: string, options: ApiOptions = {}): Promise<T> {
  try {
    return await request<T>(path, options, true);
  } catch (error) {
    const status = (error as Error & { status?: number })?.status;
    const authEndpoint = path.startsWith('/auth/login') || path.startsWith('/auth/register') || path.startsWith('/auth/refresh');
    if (status !== 401 || options.skipAuthRefresh || authEndpoint) throw error;

    const refreshed = await refreshSession();
    if (!refreshed) throw error;
    // Ignore a stale in-memory Bearer token after refresh and rely on the newly rotated HttpOnly access cookie.
    return request<T>(path, options, false);
  }
}

export function jsonBody(value: unknown) {
  return JSON.stringify(value);
}
