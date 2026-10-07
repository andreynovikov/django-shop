import { test, expect } from '@playwright/test'

test('home page has products', async ({ page }) => {
  await page.goto('/')
  // page loaded
  await expect(page).toHaveTitle("Швейный Мир")
  // catalog button is visible
  await expect(page.getByRole('button', { name: 'Каталог' })).toBeVisible()
  // products loaded in at least one section
  await expect(
    page.locator('#sw-recomended > div.row > *').or(page.locator('#sw-new > div.row > *'))
  ).not.toHaveCount(0)
  // at least one product can be put in cart
  await expect.poll(() => page.locator('button.btn-success > .ci-cart').count()).toBeGreaterThan(0)
})