import { JSONValue } from '@/lib/types'

export class HttpError extends Error {
  status: number
  statusText: string
  response: Response

  constructor(response: Response, message?: string) {
    super(message || `HTTP Error: ${response.status} ${response.statusText}`)
    this.name = 'HttpError'
    this.status = response.status
    this.statusText = response.statusText
    this.response = response
  }
}

export interface FormDataJson {
    [k: string]: FormDataEntryValue
}

export type ApiRequestInit<TData = JSONValue> = Omit<RequestInit, 'body'> & {
  body?: TData | FormData
}

export async function apiFetch<TReturn, TData = JSONValue>(endpoint: string, options: ApiRequestInit<TData> = {}): Promise<TReturn> {
  const { body, ...customOptions } = options

  const headers = {
    ...(body === undefined || body instanceof FormData ? {} : { 'content-type': 'application/json' }),
    ...customOptions.headers,
  }

  const config: RequestInit = {
    method: body ? 'POST' : 'GET',
    ...customOptions,
    headers,
    body: body !== undefined ? body instanceof FormData ? body : JSON.stringify(body) : null,
    credentials: 'include',
  }

  // Route POST requests through API proxy to correctly set CSRF header
  const baseURL = (body ? '' : (process.env.API_SERVER ?? '')) + '/api/v0/'
  const response = await fetch(baseURL + endpoint, config)

  if (!response.ok) {
    throw new HttpError(response)
  }

  if (response.status === 204)
    return undefined as TReturn

  return response.json() as Promise<TReturn>
}