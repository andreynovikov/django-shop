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

test('product can be put in cart', async ({ page }) => {
  await page.goto('/')
  // add product to cart
  const addButton = page.locator('button.btn-success:has(.ci-cart)').last()
  await addButton.click()
  // get product price
  const price = await addButton.locator('..').locator('//preceding-sibling::div[contains(@class, "product-price")]').innerText()
  // check cart
  const cartNavbarTool = page.locator('a.navbar-tool-icon-box[href="/cart/"]').locator('..')
  // cart has item
  await expect(cartNavbarTool.locator('.navbar-tool-icon-box > .navbar-tool-label')).toHaveText('1')
  // cart total equals product cost
  await expect(cartNavbarTool.locator('.navbar-tool-text')).toHaveText(`Корзина${price}`)
})
