import { Page } from '@playwright/test'

import type { ProductInfo } from '@/lib/types'

import { findSewingMachines } from './api'
import { test, expect, gotoHydrated, rubles } from './fixtures'
import { focusPhone, typePhone } from './phone'

async function buy(page: Page, product: ProductInfo) {
  await gotoHydrated(page, `/products/${product.code}/`)
  await page.getByRole('button', { name: 'Купить' }).click()
  // the product page offers to check out once the product is in the basket
  await expect(page.getByRole('link', { name: 'Оформить заказ' })).toBeVisible()
}

// The cart notice is in the topbar from the lg breakpoint, below it is in the handheld toolbar
const cartCount = (page: Page, isMobile: boolean) => isMobile
  ? page.locator('a.handheld-toolbar-item[href^="/cart"] .badge')
  : page.locator('a.navbar-tool-icon-box[href^="/cart"] .navbar-tool-label')

const cartItem = (page: Page, product: ProductInfo) => page.locator('section > div')
  .filter({ has: page.locator('.product-title').getByText(product.title, { exact: true }) })

const orderedItems = (order: { items: { product: { id: number }, quantity: number }[] } | undefined) =>
  order?.items.map(({ product, quantity }) => ({ product: product.id, quantity }))

// checkout goes through product pages, the cart and the order confirmation
test.slow()

test('anonymous buyer orders with a new phone', async ({ page, request, backend, isMobile }) => {
  const [first, second] = await findSewingMachines(request, { instock: '1' })
  backend.addProducts(first, second)

  await buy(page, first)
  await buy(page, second)
  await expect(cartCount(page, isMobile)).toHaveText('2')

  await page.goto('/cart/')
  const total = page.locator('aside h3')
  const quantity = cartItem(page, first).getByRole('spinbutton')
  await quantity.fill('3')
  await quantity.press('Enter')
  await expect(total).toHaveText(rubles(first.cost * 3 + second.cost))

  await cartItem(page, second).getByRole('button', { name: 'Удалить' }).click()
  await expect(cartItem(page, second)).toHaveCount(0)
  await expect(total).toHaveText(rubles(first.cost * 3))
  expect(backend.basketItems).toEqual([{ product: first.id, quantity: 3 }])

  const phone = page.getByRole('textbox', { name: 'Для продолжения укажите номер мобильного телефона:' })
  await focusPhone(phone)
  await typePhone(phone, '9161234567')
  await page.getByRole('checkbox', { name: /согласие на обработку персональных данных/ }).check()
  await page.getByRole('checkbox', { name: /условиями публичной оферты/ }).check()
  await page.locator('aside').getByRole('button', { name: 'Оформить заказ' }).click()

  await expect(page).toHaveURL(/\/confirmation\/$/)
  const form = page.locator('section form')
  await form.getByLabel('Фамилия Имя Отчество:').fill('Анна Иванова')
  await form.getByLabel('E-mail для уведомлений:').fill('anna@example.com')
  await form.getByLabel('Адрес доставки:').fill('Москва, Тверская, 1')
  await form.getByRole('button', { name: 'Оформить заказ' }).click()
  await expect(page.getByText('Спасибо за заказ!')).toBeVisible()

  const order = backend.lastOrder()
  expect(orderedItems(order)).toEqual([{ product: first.id, quantity: 3 }])
  expect(order).toMatchObject({ phone: '+79161234567', name: 'Анна Иванова', email: 'anna@example.com', address: 'Москва, Тверская, 1' })
  // a new buyer is registered silently, without a code by SMS
  expect(backend.requestsTo('POST', 'users/login/').map(({ body }) => body)).toEqual([{ phone: '+79161234567', ctx: 'order' }])
  expect(backend.smsLog).toEqual([])
  expect(backend.basketItems).toEqual([])
})

test('signed in buyer orders right away', async ({ page, request, backend }) => {
  const [product] = await findSewingMachines(request, { instock: '1' })
  backend.addProducts(product)
  const user = backend.signIn({ name: 'Анна Иванова', email: 'anna@example.com', address: 'Москва, Тверская, 1' })

  await buy(page, product)
  await page.goto('/cart/')
  await expect(page.getByText(`Добро пожаловать, ${user.name}!`)).toBeVisible()
  await page.locator('aside').getByRole('button', { name: 'Оформить заказ' }).click()

  await expect(page).toHaveURL(/\/confirmation\/$/)
  const form = page.locator('section form')
  // the order is filled in from the profile
  await expect(form.getByLabel('Фамилия Имя Отчество:')).toHaveValue(user.name)
  await expect(form.getByLabel('E-mail для уведомлений:')).toHaveValue(user.email)
  await expect(form.getByLabel('Адрес доставки:')).toHaveValue(user.address)
  await form.getByRole('button', { name: 'Оформить заказ' }).click()
  await expect(page.getByText('Спасибо за заказ!')).toBeVisible()

  expect(orderedItems(backend.lastOrder())).toEqual([{ product: product.id, quantity: 1 }])
  expect(backend.requestsTo('POST', /\/check\/$/)).toEqual([])
  expect(backend.smsLog).toEqual([])
})
