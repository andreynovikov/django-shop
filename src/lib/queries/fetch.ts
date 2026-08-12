export class HttpError extends Error {
  status: number;
  statusText: string;
  response: Response;

  constructor(response: Response, message?: string) {
    super(message || `HTTP Error: ${response.status} ${response.statusText}`);
    this.name = 'HttpError';
    this.status = response.status;
    this.statusText = response.statusText;
    this.response = response;
  }
}

export async function apiFetch<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
  const { body, ...customOptions } = options

  const headers = {
    ...(body ? { 'content-type': 'application/json' } : {}),
    ...customOptions.headers,
  }

  const config: RequestInit = {
    method: body ? 'POST' : 'GET',
    ...customOptions,
    headers,
    body: body ? JSON.stringify(body) : null,
    credentials: 'include',
  }

  const baseURL = (process.env.API_SERVER ?? '') + '/api/v0/'
  const response = await fetch(baseURL + endpoint, config)

  if (!response.ok) {
    throw new HttpError(response)
  }

  return response.json() as Promise<T>
}