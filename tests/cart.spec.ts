import { test, expect } from '@playwright/test'

test.describe.configure({ mode: 'serial' }) // force sequential execution


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
