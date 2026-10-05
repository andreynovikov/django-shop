import { test, expect } from '@playwright/test'

test('product page has canonical link', async ({ page }) => {
  await page.goto('/')
  await page.locator('.product-card > a').first().click()
  await page.waitForURL('/products/**')
  const path = new URL(page.url()).pathname
  await page.goto(path + '?test')
  await page.waitForURL('/products/**')
  const canonicalLink = page.locator('link[rel="canonical"]')
  await expect(canonicalLink).toHaveAttribute('href', new RegExp(`${path}$`))
})