import { Page } from '@playwright/test'

import type { Order, StoreInfo } from '@/lib/types'
import { DELIVERY_SELF, PAYMENT_CARD, STATUS_COLLECTED } from '@/components/order/status-badge'

import { findSewingMachines } from './api'
import { test, expect } from './fixtures'

let order: Order

// The topbar offers to pay the order once it is loaded, which can move the page under the mouse
async function waitForPayment(page: Page) {
  await expect(page.locator('.topbar').getByRole('button', { name: 'Оплатить заказ' })).toBeVisible()
}

test.beforeEach(({ backend }) => {
  backend.signIn()
  // collected and not paid yet, so the orders list shows the icon payment button
  order = backend.addOrder({
    created: '2026-10-20T14:30:00+03:00',
    status: STATUS_COLLECTED,
    status_text: 'Собран',
    payment: PAYMENT_CARD,
    payment_text: 'Картой',
    total: 25000,
  })
})

test('user menu is always shown on desktop', async ({ page, isMobile }) => {
  test.skip(isMobile, 'The menu is collapsed below the lg breakpoint')
  await page.goto('/user/orders/')
  const menu = page.locator('aside')
  await expect(menu.getByRole('link', { name: /Заказы/ })).toBeVisible()
  await expect(menu.getByRole('button', { name: 'Личный кабинет' })).toBeHidden()
})

test('user menu collapses on mobile', async ({ page, isMobile }) => {
  test.skip(!isMobile, 'The menu is collapsed below the lg breakpoint')
  await page.goto('/user/orders/')
  const menu = page.locator('aside')
  const toggle = menu.getByRole('button', { name: 'Личный кабинет' })
  const ordersLink = menu.getByRole('link', { name: /Заказы/ })

  await expect(ordersLink).toBeHidden()
  await toggle.click()
  await expect(ordersLink).toBeVisible()
  await toggle.click()
  await expect(ordersLink).toBeHidden()
})

// The menu and the header frame are in the account layout, the title comes from the @header slot
test('user menu switches account pages', async ({ page, isMobile }) => {
  await page.goto('/user/orders/')
  const menu = page.locator('aside')
  const toggle = menu.getByRole('button', { name: 'Личный кабинет' })
  const heading = page.getByRole('heading', { level: 1 })
  await expect(heading).toHaveText('Список заказов')

  const pages = [
    { link: /Избранное/, title: 'Избранное', path: '/user/favorites/' },
    { link: /Профиль/, title: 'Профиль', path: '/user/profile/' },
    { link: /Заказы/, title: 'Список заказов', path: '/user/orders/' },
  ]
  for (const { link, title, path } of pages) {
    if (isMobile)
      await toggle.click()
    await menu.getByRole('link', { name: link }).click()

    await expect(page).toHaveURL(path)
    await expect(heading).toHaveText(title)
    await expect(page).toHaveTitle(`${title} - Швейный Мир`)
    if (isMobile)
      await expect(menu.getByRole('link', { name: link })).toBeHidden()
  }
})

test('orders list shows tooltips', async ({ page, isMobile }) => {
  test.skip(isMobile, 'Tooltips open on hover')
  await page.goto('/user/orders/')
  await waitForPayment(page)
  const row = page.locator('tbody tr', { hasText: order.id.toString() })
  const tooltip = page.locator('.tooltip')

  await row.locator('td').nth(1).locator('span').hover()
  await expect(tooltip).toContainText('октября 2026')
  await expect(tooltip).toHaveClass(/bs-tooltip-top/)

  await page.mouse.move(0, 0)
  await expect(tooltip).toBeHidden()

  await row.locator('.btn-outline-success').hover()
  await expect(tooltip).toHaveText('Оплатить заказ')
})

test('order page shows creation date in tooltip', async ({ page, isMobile }) => {
  test.skip(isMobile, 'Tooltips open on hover')
  await page.goto(`/user/orders/${order.id}/`)
  await waitForPayment(page)
  const tooltip = page.locator('.tooltip')

  await page.locator('.sw-order-created span').hover()
  await expect(tooltip).toContainText('октября 2026')
  await expect(tooltip).toHaveClass(/bs-tooltip-bottom/)
})

test('orders list opens order details', async ({ page, request, backend, isMobile }) => {
  const [first, second] = await findSewingMachines(request)
  const storesResponse = await request.get('/api/v0/stores/')
  expect(storesResponse.ok()).toBeTruthy()
  const [store] = await storesResponse.json() as StoreInfo[]
  const pickup = backend.addOrder({ delivery: DELIVERY_SELF, store, items: [{ product: first, quantity: 2 }, { product: second }] })

  await page.goto('/user/orders/')
  const rows = page.locator('tbody tr')
  await expect(rows).toHaveCount(2)
  if (!isMobile)
    await expect(page.locator('aside').getByRole('link', { name: /Заказы/ })).toContainText('2')
  await rows.filter({ hasText: pickup.id.toString() }).click()

  await expect(page).toHaveURL(`/user/orders/${pickup.id}/`)
  await expect(page.getByRole('heading', { level: 1 })).toHaveText(`Заказ №${pickup.id}`)
  await expect(page.locator('.breadcrumb').getByRole('link', { name: 'Заказы' })).toHaveAttribute('href', '/user/orders/')
  const titles = page.locator('.product-title')
  await expect(titles.getByText(first.title, { exact: true })).toBeVisible()
  await expect(titles.getByText(second.title, { exact: true })).toBeVisible()
  await expect(page.getByRole('link', { name: `${store.city.name}, ${store.address}` })).toHaveAttribute('href', `/stores/${store.id}/`)
})
