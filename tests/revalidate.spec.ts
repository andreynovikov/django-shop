import { APIRequestContext } from '@playwright/test'

import { findSewingMachines } from './api'
import { test, expect } from './fixtures'

// Revalidation marks pages in this server's cache, nothing is sent to the backend
const secret = process.env.REVALIDATION_TOKEN

const cacheState = async (request: APIRequestContext, path: string) =>
  (await request.get(path)).headers()['x-nextjs-cache']

// the backend posts to the path without the trailing slash and follows the redirect
const revalidate = async (request: APIRequestContext, data: object) =>
  await (await request.post('/api/revalidate', { data: { secret, ...data } })).json()

test('revalidation rejects a wrong token', async ({ request }) => {
  const response = await request.post('/api/revalidate/', { data: { secret: 'wrong', tags: ['catalog'] } })
  expect(response.status()).toBe(401)
  expect(await response.json()).toEqual({ revalidated: false, message: 'Invalid token' })
})

test('revalidation takes tags only', async ({ request }) => {
  test.skip(!secret, 'REVALIDATION_TOKEN is not set')
  // the paths of a model item, which the backend posted before tags
  const response = await request.post('/api/revalidate/', { data: { secret, model: 'product', pk: 1, code: 'x' } })
  expect(response.status()).toBe(400)
  expect(await response.json()).toEqual({ revalidated: false, message: 'Parameters missing' })
})

test.describe('cached pages', () => {
  test.skip(!secret, 'REVALIDATION_TOKEN is not set')
  test.skip(!process.env.CI, 'Only the production server caches pages')
  test.describe.configure({ mode: 'serial' })

  let path: string
  let code: string

  test.beforeEach(async ({ request }, testInfo) => {
    test.skip(testInfo.project.name !== 'chromium', 'The projects share the server cache')
    if (!path) {
      const [product] = await findSewingMachines(request)
      code = product.code
      path = `/products/${code}/`
    }
    await request.get(path)
    expect(await cacheState(request, path)).toBe('HIT')
  })

  test('page is rendered again on the next visit when its data changes', async ({ request }) => {
    expect(await revalidate(request, { tags: ['product:another'] })).toEqual({ revalidated: true })
    expect(await cacheState(request, path)).toBe('HIT')

    expect(await revalidate(request, { tags: ['catalog', `product:${code}`] })).toEqual({ revalidated: true })
    expect(await cacheState(request, path)).toBe('MISS')
  })

  test('page revalidated in the background is shown as it was once', async ({ request }) => {
    expect(await revalidate(request, { tags: [`product:${code}`], background: true })).toEqual({ revalidated: true })
    expect(await cacheState(request, path)).toBe('STALE')
    await expect.poll(() => cacheState(request, path)).toBe('HIT')
  })
})

test('only staff may revalidate a page', async ({ request }) => {
  // the route asks the backend who the session is, which the fake backend doesn't answer for the server
  const anonymous = await request.get('/api/revalidate/?path=/catalog/', { maxRedirects: 0 })
  expect(anonymous.status()).toBe(403)
  expect(await anonymous.json()).toEqual({ revalidated: false, message: 'Staff only' })

  const elsewhere = await request.get('/api/revalidate/?path=//example.com/', { maxRedirects: 0 })
  expect(elsewhere.status()).toBe(400)
})
