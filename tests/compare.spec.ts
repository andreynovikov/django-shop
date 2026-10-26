import { test, expect } from './fixtures'

import { findSewingMachines } from './api'

test('field help popover shows help page', async ({ page, request }) => {
  const products = await findSewingMachines(request, { instock: '1' })
  expect(products.length).toBeGreaterThan(1)

  await page.goto(`/compare/?product=${products[0].id}&product=${products[1].id}`)
  const row = page.locator('tr', { has: page.locator('th', { hasText: 'Тип челнока' }) })
  // help button appears after help page list is loaded
  await row.getByRole('button').click()

  const popup = page.getByRole('dialog')
  await expect(popup).toBeVisible()
  await expect(popup.locator('.spinner-border')).toHaveCount(0)
  await expect(popup.locator('.fs-sm')).not.toBeEmpty()

  await page.keyboard.press('Escape')
  await expect(popup).toBeHidden()
})
