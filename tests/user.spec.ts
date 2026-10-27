import { test, expect, signIn } from './fixtures'

import { PAYMENT_CARD, STATUS_COLLECTED } from '@/components/order/status-badge'

// collected and not paid yet, so the orders list shows the icon payment button
const order = {
  id: 12345,
  created: '2026-10-20T14:30:00+03:00',
  status: STATUS_COLLECTED,
  status_text: 'Собран',
  total: 25000,
  paid: false,
  payment: PAYMENT_CARD,
  payment_text: 'Картой',
  items: [],
  delivery: 1,
  delivery_info: '',
  delivery_price: 0,
  delivery_tracking_number: '',
  delivery_dispatch_date: null,
  delivery_handing_date: null,
  delivery_time_from: null,
  delivery_time_till: null,
  address: '',
  name: 'Тестовый покупатель',
  phone: '+79161234567',
  is_firm: false,
  firm_name: '',
  firm_address: '',
  firm_details: '',
  store: null,
}

test.beforeEach(async ({ page }) => {
  await signIn(page)
  await page.route('**/api/v0/orders/**', route => {
    const url = route.request().url()
    if (url.includes('/orders/last/'))
      return route.fulfill({ json: { id: null } })
    if (url.includes(`/orders/${order.id}/`))
      return route.fulfill({ json: order })
    return route.fulfill({ json: { count: 1, next: null, previous: null, results: [order] } })
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

test('orders list shows tooltips', async ({ page, isMobile }) => {
  test.skip(isMobile, 'Tooltips open on hover')
  await page.goto('/user/orders/')
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
  const tooltip = page.locator('.tooltip')

  await page.locator('.sw-order-created span').hover()
  await expect(tooltip).toContainText('октября 2026')
  await expect(tooltip).toHaveClass(/bs-tooltip-bottom/)
})
