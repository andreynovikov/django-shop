import { Page } from '@playwright/test'

import { test, expect, loginWithCode } from './fixtures'
import { focusPhone, typePhone } from './phone'

// The dev server compiles the login page and user pages on their first visit
test.slow()

const expectLoginFor = (page: Page, path: string) =>
  expect(page).toHaveURL(url => url.pathname === '/login/' && url.searchParams.get('callbackUrl') === path, { timeout: 30_000 })

for (const path of ['/user/orders/', '/user/favorites/', '/user/profile/']) {
  test(`${path} asks to log in and comes back`, async ({ page, backend }) => {
    const user = backend.addUser()
    await page.goto(path)
    await expectLoginFor(page, path)

    await loginWithCode(page, backend, user.phone)
    await expect(page).toHaveURL(path)
    await expect(page.locator('aside h3')).toHaveText(user.name)
  })
}

test('order page asks to log in and comes back', async ({ page, backend }) => {
  const user = backend.addUser()
  const order = backend.addOrder({}, user)
  await page.goto(`/user/orders/${order.id}/`)
  await expectLoginFor(page, `/user/orders/${order.id}/`)

  await loginWithCode(page, backend, user.phone)
  await expect(page).toHaveURL(`/user/orders/${order.id}/`)
  await expect(page.getByRole('heading', { name: `Заказ №${order.id}` })).toBeVisible()
})

test('order tracking asks to log in and shows the last order', async ({ page, backend }) => {
  const user = backend.addUser()
  backend.addOrder({}, user)
  const last = backend.addOrder({}, user)
  await page.goto('/user/orders/?track')
  await expectLoginFor(page, '/user/orders/?track')

  await loginWithCode(page, backend, user.phone)
  await expect(page).toHaveURL(`/user/orders/${last.id}/`)
})

test('order confirmation sends anonymous user to the cart', async ({ page, backend }) => {
  await page.goto('/confirmation/')
  await expect(page).toHaveURL('/cart/')
  expect(backend.user).toBeUndefined()
})

test('callback survives registration', async ({ page, backend }) => {
  await page.goto('/user/profile/')
  await expectLoginFor(page, '/user/profile/')

  const registerLink = page.getByRole('link', { name: 'зарегистрироваться' })
  // the link gets the query once the page is hydrated
  await expect(registerLink).toHaveAttribute('href', /callbackUrl=/)
  await registerLink.click()
  await expect(page).toHaveURL(url => url.pathname === '/register/' && url.searchParams.get('callbackUrl') === '/user/profile/')

  const phone = page.getByRole('textbox', { name: 'Укажите номер мобильного телефона:' })
  await focusPhone(phone)
  await typePhone(phone, '9161234567')
  await page.getByRole('checkbox').check()
  await page.getByRole('button', { name: 'Зарегистрироваться' }).click()

  const code = page.getByPlaceholder('Код из смс')
  await expect(code).toBeVisible()
  await code.fill(backend.lastSmsCode('+79161234567')!)
  await page.getByRole('button', { name: 'Продолжить' }).click()
  await expect(page).toHaveURL('/user/profile/')
})

for (const callbackUrl of ['https://example.com/', '//example.com/']) {
  test(`login does not follow off-site callback ${callbackUrl}`, async ({ page, backend }) => {
    await page.route(/^https?:\/\/example\.com\//, route => route.fulfill({ body: 'Another site' }))
    const user = backend.addUser()
    await page.goto(`/login/?callbackUrl=${encodeURIComponent(callbackUrl)}`)

    await loginWithCode(page, backend, user.phone)
    await expect(page).toHaveURL('/')
  })
}
