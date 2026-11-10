import { test, expect } from './fixtures'

test.beforeEach(() => {
  test.skip(test.info().project.name !== 'chromium', 'The server sends the same headers to every browser')
})

test('pages can be framed by the site and by Metrika only', async ({ request }) => {
  for (const path of ['/', '/cart/']) {
    const headers = (await request.get(path)).headers()
    expect(headers['content-security-policy'], path).toMatch(/^frame-ancestors 'self' https:\/\/metrika\.yandex\.ru /)
    expect(headers['x-content-type-options'], path).toBe('nosniff')
    expect(headers['x-frame-options'], path).toBeUndefined()
  }
})

test('sign-in and account pages can be framed by nobody', async ({ request }) => {
  for (const path of ['/login/', '/register/', '/confirm-email/', '/user/orders/', '/user/orders/1/']) {
    const headers = (await request.get(path)).headers()
    expect(headers['content-security-policy'], path).toBe("frame-ancestors 'none'")
    expect(headers['x-frame-options'], path).toBe('DENY')
    expect(headers['x-content-type-options'], path).toBe('nosniff')
  }
})
