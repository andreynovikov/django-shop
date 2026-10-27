import { test as base, Page } from '@playwright/test'

import type { User } from '@/lib/types'

export { expect } from '@playwright/test'

export const testUser: User = {
  id: 1,
  is_anonymous: false,
  phone: '+79161234567',
  name: 'Тестовый покупатель',
  full_name: 'Тестовый покупатель',
  gravatar: '',
  username: 'test',
  email: '',
  postcode: '',
  city: '',
  address: '',
  discount: 0,
  bonuses: 0,
  expiring_bonuses: 0,
  expiration_date: null,
  permanent_password: true,
  last_login: '',
  date_joined: '',
}

export const test = base.extend<{ skipHeavyResources: void }>({
  // Remote product images go through the image optimizer and embedded videos load third-party players,
  // both can delay the load event for a long time and are not needed in tests
  skipHeavyResources: [async ({ page }, use) => {
    await page.route('**/_next/image?**', route => route.abort())
    await page.route('**/*', route => {
      const request = route.request()
      if (request.isNavigationRequest() && request.frame().parentFrame() !== null)
        return route.abort()
      return route.fallback()
    })
    await use()
  }, { auto: true }],
})

// Pretend to be signed in, browser requests go through the API proxy so they can be mocked
export async function signIn(page: Page, user: Partial<User> = {}) {
  await page.route('**/api/v0/users/current/', route => route.fulfill({ json: { ...testUser, ...user } }))
  await page.route('**/api/v0/favorites/', route => route.fulfill({ json: [] }))
}

// Filters are in the sidebar from the lg breakpoint, below it they are in an offcanvas
export async function openFilters(page: Page, isMobile: boolean) {
  if (isMobile)
    await page.locator('.handheld-toolbar-label', { hasText: 'Фильтры' }).click()
}
