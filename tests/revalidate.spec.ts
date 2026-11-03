import { findSewingMachines } from './api'
import { test, expect } from './fixtures'

// Revalidation marks pages in this server's cache, nothing is sent to the backend
const secret = process.env.REVALIDATION_TOKEN

test('revalidation rejects a wrong token', async ({ request }) => {
  const response = await request.post('/api/revalidate/', { data: { secret: 'wrong', model: 'product', pk: 1, code: 'x' } })
  expect(response.status()).toBe(401)
  expect(await response.json()).toEqual({ revalidated: false, message: 'Invalid token' })
})

test('revalidated page is rendered again on the next visit', async ({ request }) => {
  test.skip(!secret, 'REVALIDATION_TOKEN is not set')
  test.skip(!process.env.CI, 'Only the production server caches pages')
  test.skip(test.info().project.name !== 'chromium', 'The projects share the server cache')
  const [product] = await findSewingMachines(request)
  const path = `/products/${product.code}/`
  await request.get(path)
  expect((await request.get(path)).headers()['x-nextjs-cache']).toBe('HIT')

  // the backend posts to the path without the trailing slash and follows the redirect
  const response = await request.post('/api/revalidate', { data: { secret, model: 'product', pk: product.id, code: product.code } })
  expect(await response.json()).toEqual({ revalidated: true })
  expect((await request.get(path)).headers()['x-nextjs-cache']).toBe('MISS')
})
