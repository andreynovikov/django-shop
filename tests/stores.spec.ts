import { test, expect } from './fixtures'

test('store list expands one city at a time', async ({ page }) => {
  await page.goto('/stores/')
  // the big cities are listed twice, first as bold shortcuts
  const moscow = page.getByRole('button', { name: 'Москва', exact: true }).first()
  const spb = page.getByRole('button', { name: 'Санкт-Петербург', exact: true }).first()
  const moscowStores = moscow.locator('xpath=following-sibling::div[1]')
  const spbStores = spb.locator('xpath=following-sibling::div[1]')

  // collapsed stores stay in the page so crawlers can follow the links
  await expect(moscowStores).toBeHidden()
  await expect(moscowStores.locator('a[href^="/stores/"]')).not.toHaveCount(0)

  // the list is server rendered, retry until hydrated
  await expect(async () => {
    await moscow.click()
    await expect(moscowStores).toBeVisible({ timeout: 1000 })
  }).toPass()
  await expect(moscow).toHaveAttribute('aria-expanded', 'true')

  // clicking the open city keeps it open
  await moscow.click()
  await expect(moscowStores).toBeVisible()

  await spb.click()
  await expect(spbStores).toBeVisible()
  await expect(moscowStores).toBeHidden()
  await expect(moscow).toHaveAttribute('aria-expanded', 'false')
})
