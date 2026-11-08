import { test, expect } from './fixtures'

// Every request here must be refused by the proxy itself. If a check breaks, the request reaches
// the backend as a logout without a session, which changes nothing.
const logout = '/api/v0/users/logout/'
const crossSite = { error: 'Cross-site request' }

test.beforeEach(() => {
  test.skip(test.info().project.name !== 'chromium', 'The proxy answers the same to every browser')
})

test('proxy refuses a write without the header pages on other sites cannot send', async ({ request }) => {
  const response = await request.post(logout, { headers: { 'sec-fetch-site': 'same-origin' } })
  expect(response.status()).toBe(403)
  expect(await response.json()).toEqual(crossSite)
})

test('proxy refuses a write from another site', async ({ request }) => {
  const response = await request.post(logout, { headers: { 'x-requested-with': 'fetch', 'sec-fetch-site': 'cross-site' } })
  expect(response.status()).toBe(403)
  expect(await response.json()).toEqual(crossSite)
})

test('proxy refuses a write from a subdomain', async ({ request }) => {
  const response = await request.post(logout, { headers: { 'x-requested-with': 'fetch', 'sec-fetch-site': 'same-site' } })
  expect(response.status()).toBe(403)
  expect(await response.json()).toEqual(crossSite)
})

test('proxy refuses logout with GET, which a link or an image could trigger', async ({ request }) => {
  const response = await request.get(logout)
  expect(response.status()).toBe(405)
  expect(await response.json()).toEqual({ error: 'Method not allowed' })
})

test('proxy refuses paths that would leave the API', async ({ request }) => {
  for (const path of ['/api/v0/..%2F..%2Fmetrics/', '/api/v0/products/..%5C..%5Cmetrics/']) {
    const response = await request.get(path)
    expect(response.status(), path).toBe(400)
    expect(await response.json(), path).toEqual({ error: 'Invalid path' })
  }
})
