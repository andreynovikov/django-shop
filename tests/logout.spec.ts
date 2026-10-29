import { test, expect, accountLink } from './fixtures'

test('user logs out from the topbar menu', async ({ page, backend, isMobile }) => {
  test.skip(isMobile, 'The menu opens on hover from the lg breakpoint')
  backend.signIn()
  await page.goto('/cart/')

  await accountLink(page).hover()
  await page.locator('.navbar-tool .dropdown-menu').getByText('Выйти').click()

  await expect(page.locator('.navbar-tool-text', { hasText: 'Вход в' })).toBeVisible()
  await expect(accountLink(page)).toHaveCount(0)
  await expect(page.locator('a.navbar-tool[href^="/user/favorites"]')).toHaveCount(0)
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

  // the home page is a full page load rendered from the backend
  await expect(page).toHaveURL('/', { timeout: 30_000 })
  expect(backend.user).toBeUndefined()

  // user pages ask to log in again
  await page.goto('/user/orders/')
  await expect(page).toHaveURL(url => url.pathname === '/login/' && url.searchParams.get('callbackUrl') === '/user/orders/')
})
