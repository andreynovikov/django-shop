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

// The cart notice is in the topbar from the lg breakpoint, below it is in the handheld toolbar; only one of them is shown
const cartCount = (page: Page) => page.getByRole('link', { name: 'Корзина', exact: true })
  .getByTitle('Товаров в корзине')

const cartItem = (page: Page, product: ProductInfo) => page.locator('section > div')
  .filter({ has: page.getByRole('heading', { name: product.title, exact: true }) })

const orderedItems = (order: { items: { product: { id: number }, quantity: number }[] } | undefined) =>
  order?.items.map(({ product, quantity }) => ({ product: product.id, quantity }))

// checkout goes through product pages, the cart and the order confirmation
test.slow()

test('anonymous buyer orders with a new phone', async ({ page, request, backend }) => {
  const [first, second] = await findSewingMachines(request, { instock: '1' })
  backend.addProducts(first, second)

  await buy(page, first)
  await buy(page, second)
  await expect(cartCount(page)).toHaveText('2')

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
  // the address typed for the order becomes the buyer's, and order mail waits until it is confirmed
  expect(backend.user).toMatchObject({ email: 'anna@example.com', email_verified: false, phone_verified: false })
  expect(backend.lastEmailLink('anna@example.com')).toBeDefined()
  await expect(page.getByText('Мы отправили на anna@example.com письмо со ссылкой для подтверждения адреса.')).toBeVisible()
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

for (const wholesale of [false, true]) {
  test(`${wholesale ? 'wholesale site orders products sold in packs in whole packs' : 'retail site ignores packs'}`, async ({ page, request, backend }) => {
    const [product] = await findSewingMachines(request, { instock: '1' })
    backend.addProducts({ ...product, ws_pack_only: true, pack_factor: 6 })
    // the backend tells the storefront whether its site is wholesale
    await page.route('**/api/v0/sites/current/', async route => {
      const response = await route.fetch()
      await route.fulfill({ response, json: { ...await response.json(), wholesale } })
    })

    await buy(page, product)
    // the fake backend answers the basket at once, the site comes later from the real one: type once the cart
    // knows the packs (the next test types before it)
    const siteLoaded = page.waitForResponse('**/api/v0/sites/current/')
    await page.goto('/cart/')
    await siteLoaded
    const quantity = cartItem(page, product).getByRole('spinbutton')
    await expect(quantity).toHaveAttribute('step', wholesale ? '6' : '1')
    await quantity.fill('7')
    await quantity.press('Enter')

    await expect(quantity).toHaveValue(wholesale ? '12' : '7')
    await expect(cartItem(page, product).getByText('кратно 6')).toHaveCount(wholesale ? 1 : 0)
    await expect.poll(() => backend.basketItems).toEqual([{ product: product.id, quantity: wholesale ? 12 : 7 }])
  })
}

test('wholesale site rounds a quantity typed before it loaded up to whole packs', async ({ page, request, backend }) => {
  const [product] = await findSewingMachines(request, { instock: '1' })
  backend.addProducts({ ...product, ws_pack_only: true, pack_factor: 6 })
  // on the cart page the site answers once the quantity is typed
  const typed = Promise.withResolvers<void>()
  let holdSite = false
  await page.route('**/api/v0/sites/current/', async route => {
    const response = await route.fetch()
    const json = { ...await response.json(), wholesale: true }
    if (holdSite)
      await typed.promise
    await route.fulfill({ response, json })
  })

  await buy(page, product)
  holdSite = true
  await page.goto('/cart/')
  const quantity = cartItem(page, product).getByRole('spinbutton')
  await quantity.fill('7')
  await quantity.press('Enter')
  // without the site the cart knows no packs
  await expect.poll(() => backend.basketItems).toEqual([{ product: product.id, quantity: 7 }])
  typed.resolve()

  await expect(cartItem(page, product).getByText('кратно 6')).toBeVisible()
  await expect(quantity).toHaveValue('12')
  await expect.poll(() => backend.basketItems).toEqual([{ product: product.id, quantity: 12 }])
})
