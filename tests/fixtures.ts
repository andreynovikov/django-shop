import { test as base, expect, Page } from '@playwright/test'

import { FakeBackend, normalizePhone } from './fake-backend'
import { focusPhone } from './phone'

export { expect }

export const test = base.extend<{ blockApiWrites: void, skipHeavyResources: void, backend: FakeBackend }>({
  // Tests run against the production backend, so writes must be mocked or faked by the test.
  // Anything else is aborted and fails the test.
  blockApiWrites: [async ({ page }, use) => {
    const blocked: string[] = []
    await page.route('**/api/v0/**', route => {
      const request = route.request()
      if (request.method() === 'GET')
        return route.fallback()
      blocked.push(`${request.method()} ${request.url()}`)
      return route.abort('blockedbyclient')
    })
    // analytics would count test orders as real purchases
    await page.route(/^https:\/\/(mc\.yandex\.ru|code\.jivo\.ru)\//, route => route.abort('blockedbyclient'))
    await use()
    expect(blocked, 'API requests without a mock were blocked').toEqual([])
  }, { auto: true }],
  // Remote images, directly or through the image optimizer, and the third-party players of embedded videos
  // can delay the load event for a long time and are not needed in tests
  skipHeavyResources: [async ({ page }, use) => {
    await page.route('**/_next/image?**', route => route.abort())
    await page.route(/^https:\/\/(www|api)\.sewing-world\.ru\/media\//, route => route.abort())
    await page.route('**/*', route => {
      const request = route.request()
      if (request.isNavigationRequest() && request.frame().parentFrame() !== null)
        return route.abort()
      return route.fallback()
    })
    await use()
  }, { auto: true }],
  // Its route is added after the guard, so the fake answers first and the guard sees only what it passes on
  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  backend: async ({ page, request, blockApiWrites }, use) => {
    const backend = new FakeBackend(request)
    await backend.install(page)
    await use(backend)
  },
})

// Filters are in the sidebar from the lg breakpoint, below it they are in an offcanvas
export async function openFilters(page: Page, isMobile: boolean) {
  if (isMobile)
    await page.locator('.handheld-toolbar-label', { hasText: 'Фильтры' }).click()
}

// The session is requested only after hydration, so the page handles clicks once it is.
// The load event is not awaited, remote images can hold it for long.
export async function gotoHydrated(page: Page, url: string) {
  const hydrated = page.waitForRequest(request => request.method() === 'GET' && request.url().endsWith('/api/v0/users/current/'))
  await page.goto(url, { waitUntil: 'commit' })
  await hydrated
}

// The topbar account icon links to the orders only for a signed in user
export const accountLink = (page: Page) => page.locator('a.navbar-tool-icon-box[href^="/user/orders"]')

// Prices are formatted for the ru locale, with no-break spaces between thousands
export const rubles = (value: number) => new RegExp(value.toLocaleString('ru').replaceAll(/\s/g, '\\s') + '\\sруб')

// Logs in on the login form with the code the fake backend sent by SMS
export async function loginWithCode(page: Page, backend: FakeBackend, phone: string) {
  const input = page.getByRole('textbox', { name: 'Укажите номер мобильного телефона:' })
  await focusPhone(input)
  await input.pressSequentially(normalizePhone(phone).slice(2))
  await page.getByRole('button', { name: 'Войти' }).click()
  const code = page.getByPlaceholder('Код из смс')
  await expect(code).toBeVisible()
  await code.fill(backend.lastSmsCode(phone)!)
  await page.getByRole('button', { name: 'Продолжить' }).click()
}
