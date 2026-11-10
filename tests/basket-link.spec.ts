import { Page } from '@playwright/test'

import type { ProductInfo } from '@/lib/types'

import { findSewingMachines } from './api'
import { test, expect } from './fixtures'

// The links in the backend's abandoned basket email, see BasketViewSet.restore and clear in django-shop
const query = '?utm_source=email&utm_content=abandoned_basket'

const cartItem = (page: Page, product: ProductInfo) => page.locator('section > div')
  .filter({ has: page.getByRole('heading', { name: product.title, exact: true }) })

test('restore link fills the basket and opens the cart', async ({ page, request, backend }) => {
  const [first, second] = await findSewingMachines(request)
  await page.goto(`/shop/basket/restore/${first.id}*2,${second.id}*1/${query}`)

  await expect(page).toHaveURL(`/cart/${query}`)
  await expect(cartItem(page, first).getByRole('spinbutton')).toHaveValue('2')
  await expect(cartItem(page, second).getByRole('spinbutton')).toHaveValue('1')
  expect(backend.basketItems).toEqual([{ product: first.id, quantity: 2 }, { product: second.id, quantity: 1 }])
  expect(backend.basketUtmSource).toBe('email')
})

test('restore link leaves the basket the visitor has', async ({ page, request, backend }) => {
  const [first, second] = await findSewingMachines(request)
  backend.addBasket({ product: first })
  await page.goto(`/shop/basket/restore/${second.id}*1/${query}`)

  await expect(page).toHaveURL(`/cart/${query}`)
  await expect(cartItem(page, first)).toBeVisible()
  await expect(cartItem(page, second)).toHaveCount(0)
  expect(backend.basketItems).toEqual([{ product: first.id, quantity: 1 }])
})

test('clear link empties the basket it was sent for', async ({ page, request, backend }) => {
  const [first] = await findSewingMachines(request)
  const sign = backend.basketClearSign(backend.addBasket({ product: first }))
  await page.goto(`/shop/basket/clear/${sign}/${query}`)

  await expect(page).toHaveURL(`/cart/${query}`)
  await expect(cartItem(page, first)).toHaveCount(0)
  expect(backend.basketItems).toEqual([])
})

test('clear link with a bad signature is refused', async ({ page, request, backend }) => {
  const [first] = await findSewingMachines(request)
  backend.addBasket({ product: first })
  await page.goto(`/shop/basket/clear/1:forged/${query}`)

  await expect(page.getByRole('main').getByRole('alert')).toContainText('Ссылка недействительна.')
  await expect(page).toHaveURL(`/shop/basket/clear/1:forged/${query}`)
  expect(backend.basketItems).toEqual([{ product: first.id, quantity: 1 }])
})
