import { test, expect, accountLink } from './fixtures'

test('user logs out from the topbar menu', async ({ page, backend, isMobile }) => {
  test.skip(isMobile, 'The menu opens on hover from the lg breakpoint')
  backend.signIn()
  await page.goto('/cart/')

  await accountLink(page).hover()
  await page.getByRole('banner').getByRole('button', { name: 'Выйти' }).click()

  await expect(page.getByRole('button', { name: 'Вход в личный кабинет', exact: true })).toBeVisible()
  await expect(accountLink(page)).toHaveCount(0)
  await expect(page.getByRole('link', { name: 'Избранное', exact: true })).toHaveCount(0)
  expect(backend.user).toBeUndefined()
})

test('user logs out from the account menu', async ({ page, backend, isMobile }) => {
  // goes through the profile, the home page, the orders and the login page
  test.slow()
  backend.signIn()
  await page.goto('/user/profile/')

  // the menu is collapsed below the lg breakpoint
  const menu = page.locator('aside')
  if (isMobile)
    await menu.getByRole('button', { name: 'Личный кабинет' }).click()
  await menu.getByText('Выйти').click()

  // the home page is rendered from the backend
  await expect(page).toHaveURL('/', { timeout: 30_000 })
  expect(backend.user).toBeUndefined()

  // user pages ask to log in again
  await page.goto('/user/orders/')
  await expect(page).toHaveURL(url => url.pathname === '/login/' && url.searchParams.get('callbackUrl') === '/user/orders/')
})

test('failed logout keeps the user signed in and says so', async ({ page, backend, isMobile }) => {
  backend.signIn()
  await page.goto('/user/profile/')
  // answered before the fake backend, which would sign the user out
  await page.route('**/api/v0/users/logout/', route => route.fulfill({ status: 500, body: 'Server Error' }))

  const menu = page.locator('aside')
  if (isMobile)
    await menu.getByRole('button', { name: 'Личный кабинет' }).click()
  await menu.getByRole('button', { name: 'Выйти' }).click()

  await expect(menu.getByRole('alert')).toHaveText('Не удалось выйти, попробуйте ещё раз')
  await expect(page).toHaveURL('/user/profile/')
  expect(backend.user).toBeDefined()

  // the next try goes through
  await page.unroute('**/api/v0/users/logout/')
  await menu.getByRole('button', { name: 'Выйти' }).click()
  await expect(page).toHaveURL('/', { timeout: 30_000 })
  expect(backend.user).toBeUndefined()
})

test('failed logout from the topbar menu is told in a toast', async ({ page, backend, isMobile }) => {
  test.skip(isMobile, 'The menu opens on hover from the lg breakpoint')
  backend.signIn()
  await page.goto('/cart/')
  await page.route('**/api/v0/users/logout/', route => route.abort())

  await accountLink(page).hover()
  await page.getByRole('banner').getByRole('button', { name: 'Выйти' }).click()

  await expect(page.getByText('Не удалось выйти, попробуйте ещё раз')).toBeVisible()
  await expect(accountLink(page)).toBeVisible()
})
