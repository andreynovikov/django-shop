import { test as base, Page } from '@playwright/test'

export { expect } from '@playwright/test'

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

// Filters are in the sidebar from the lg breakpoint, below it they are in an offcanvas
export async function openFilters(page: Page, isMobile: boolean) {
  if (isMobile)
    await page.locator('.handheld-toolbar-label', { hasText: 'Фильтры' }).click()
}
