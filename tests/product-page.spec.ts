import { test, expect, gotoHydrated } from './fixtures'

import { findSewingMachines, findProductInStores, findReviewableProduct } from './api'

test('product page has canonical link', async ({ page }) => {
  await page.goto('/')
  await page.locator('[itemtype="http://schema.org/Offer"]').first().getByRole('link').first().click()
  await page.waitForURL('/products/**')
  const path = new URL(page.url()).pathname
  await page.goto(path + '?test')
  await page.waitForURL('/products/**')
  const canonicalLink = page.locator('link[rel="canonical"]')
  await expect(canonicalLink).toHaveAttribute('href', new RegExp(`${path}$`))
})

test('store availability menu lists stores by city', async ({ page, request }) => {
  const found = await findProductInStores(request)
  test.skip(found === undefined, 'No product is available in retail stores')
  const { product, store } = found!

  await page.goto(`/products/${product.code}/`)
  await page.getByRole('button', { name: 'Наличие в магазинах' }).click()
  const menu = page.getByRole('menu')
  await expect(menu).toContainText('Товар есть в наличии в следующих магазинах:')

  // city collapsible is closed until clicked
  const storeLink = menu.getByRole('link', { name: store.address })
  await expect(storeLink).toBeHidden()
  await menu.getByRole('button', { name: store.city.name }).click()
  await expect(storeLink).toBeVisible()

  await page.keyboard.press('Escape')
  await expect(menu).toBeHidden()
})

test('store availability menu links to store page', async ({ page, request }) => {
  const found = await findProductInStores(request)
  test.skip(found === undefined, 'No product is available in retail stores')
  const { product, store } = found!

  await page.goto(`/products/${product.code}/`)
  await page.getByRole('button', { name: 'Наличие в магазинах' }).click()
  const menu = page.getByRole('menu')
  await menu.getByRole('button', { name: store.city.name }).click()
  await menu.getByRole('link', { name: store.address }).click()
  await expect(page).toHaveURL(`/stores/${store.id}/`)
  await expect(page.locator('h1')).toContainText(store.city.name)
})

test('field help popover shows help page', async ({ page, request }) => {
  const [product] = await findSewingMachines(request, { instock: '1' })

  await page.goto(`/products/${product.code}/`)
  const row = page.getByRole('term').filter({ hasText: 'Тип челнока' })
  // help button appears after help page list is loaded
  await row.getByRole('button').click()

  const popup = page.getByRole('dialog')
  await expect(popup).toBeVisible()
  // the help page replaces the loading spinner
  await expect(popup.getByRole('status')).toHaveCount(0)
  await expect(popup).not.toBeEmpty()

  await page.keyboard.press('Escape')
  await expect(popup).toBeHidden()
})

test('preorder shows toast notification', async ({ page, request, backend }) => {
  const [product] = await findSewingMachines(request, { instock: '0' })
  test.skip(product === undefined, 'No product is out of stock')

  // the fake backend does not take preorders, the request is checked here
  backend.signIn()
  let preorderBody
  await page.route('**/api/v0/orders/preorder/', route => {
    preorderBody = route.request().postDataJSON()
    return route.fulfill({ status: 201, json: {} })
  })

  // the button is server rendered, it opens the dialog once the page is hydrated
  await gotoHydrated(page, `/products/${product.code}/`)
  await page.getByText('Сообщить о поступлении').click()
  await page.getByRole('button', { name: 'Оформить запрос о поступлении' }).click()

  const notifications = page.getByRole('region', { name: 'Уведомления' })
  const toast = notifications.getByText('Запрос зарегистрирован')
  await expect(toast).toBeVisible()
  expect(preorderBody).toEqual({ product: product.id })

  // Base UI hides the close button from assistive technology, toasts are reachable with F6 instead
  await notifications.getByRole('button', { name: 'Закрыть', includeHidden: true }).click()
  await expect(toast).toBeHidden()
})

test('nickname modal closes only explicitly', async ({ page, request, backend }) => {
  const product = await findReviewableProduct(request)
  test.skip(product === undefined, 'No product allows reviews')

  // a user without a nickname is offered to set one above the review form
  backend.signIn({ username: '' })
  await page.route('**/api/v0/users/form/', route => route.fulfill({
    json: [{ id: 'id_username', name: 'username', label: 'Псевдоним', required: false }]
  }))
  await page.route('**/api/v0/reviews/shop.product/*/form/', route => route.fulfill({ json: [] }))

  await page.goto(`/products/${product!.code}/`)
  // reviews are loaded when scrolled into view
  await page.locator('#reviews').scrollIntoViewIfNeeded()
  await page.getByText('указать', { exact: true }).click()
  const dialog = page.getByRole('dialog')
  await expect(dialog).toBeVisible()

  // the backdrop is static
  await page.mouse.click(5, 5)
  await expect(dialog).toBeVisible()
  await page.keyboard.press('Escape')
  await expect(dialog).toBeHidden()

  await page.getByText('указать', { exact: true }).click()
  await dialog.getByRole('textbox', { name: 'Псевдоним' }).fill('nick')
  await dialog.getByRole('button', { name: 'Сохранить' }).click()
  await expect(dialog).toBeHidden()
  expect(backend.user?.username).toBe('nick')
})
