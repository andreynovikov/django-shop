import { test, expect } from './fixtures'

test('home page has products', async ({ page }) => {
  await page.goto('/')
  // page loaded
  await expect(page).toHaveTitle("Швейный Мир")
  // catalog button is visible
  await expect(page.getByRole('button', { name: 'Каталог' })).toBeVisible()
  // products loaded in at least one section
  await expect(
    page.locator('#sw-recomended [itemtype="http://schema.org/Offer"]').or(page.locator('#sw-new [itemtype="http://schema.org/Offer"]'))
  ).not.toHaveCount(0)
  // at least one product can be put in cart
  await expect.poll(() => page.getByRole('button', { name: 'В корзину' }).count()).toBeGreaterThan(0)
})