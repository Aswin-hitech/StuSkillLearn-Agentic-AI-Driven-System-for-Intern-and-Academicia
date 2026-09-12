const API_BASE = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000/api/v1';

export async function api<T>(path: string, options: RequestInit & { token?: string | null } = {}): Promise<T> {
  const { token, ...requestOptions } = options;
  const headers = new Headers(requestOptions.headers ?? {});
  if (!headers.has('Content-Type') && requestOptions.body && !(requestOptions.body instanceof FormData)) headers.set('Content-Type', 'application/json');
  if (token) headers.set('Authorization', `Bearer ${token}`);
  const response = await fetch(`${API_BASE}${path}`, { ...requestOptions, headers });
  if (!response.ok) {
    let message = `Request failed (${response.status})`;
    try {
      const data = await response.json();
      if (typeof data?.detail === 'string') message = data.detail;
    } catch {
      // Keep fallback.
    }
    throw new Error(message);
  }
  return response.json() as Promise<T>;
}

export function jsonBody(value: unknown) {
  return JSON.stringify(value);
}
