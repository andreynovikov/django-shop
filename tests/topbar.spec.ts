import { test, expect } from './fixtures'

// Phones menu is shown only below the lg breakpoint
test.use({ viewport: { width: 390, height: 844 } })

test('phones menu opens', async ({ page }) => {
  await page.goto('/stores/')
  await page.getByRole('button', { name: 'Телефоны' }).click()

  const menu = page.getByRole('menu')
  await expect(menu).toBeVisible()
  await expect(menu.locator('a[href="tel:+74957440087"]')).toBeVisible()
  await expect(menu).toContainText('розничные магазины')

  await page.keyboard.press('Escape')
  await expect(menu).toBeHidden()
})

test('top menu is toggled from the handheld toolbar', async ({ page }) => {
  await page.goto('/cart/')
  const menu = page.getByRole('navigation', { name: 'Разделы сайта' })
  const menuLink = menu.getByRole('link', { name: 'Сервисные центры' })
  const toggle = page.getByRole('button', { name: 'Меню', exact: true })

  // collapsed menu stays in the page so crawlers can follow the links
  await expect(menuLink).toBeHidden()
  await expect(menu.getByRole('link', { name: 'Сервисные центры', includeHidden: true })).toHaveCount(1)

  // the toolbar is server rendered, retry until hydrated
  await expect(async () => {
    await toggle.click()
    await expect(menuLink).toBeVisible({ timeout: 1000 })
  }).toPass()
  await toggle.click()
  await expect(menuLink).toBeHidden()
})

test.describe('on desktop', () => {
  test.use({ viewport: { width: 1280, height: 800 } })

  test('top menu is always shown', async ({ page }) => {
    await page.goto('/cart/')
    await expect(page.getByRole('navigation', { name: 'Разделы сайта' }).getByRole('link', { name: 'Сервисные центры' })).toBeVisible()
  })

  test('favorites tool shows tooltip', async ({ page, backend, isMobile }) => {
    test.skip(isMobile, 'Tooltips open on hover')
    backend.signIn()
    await page.goto('/cart/')
    const tooltip = page.getByRole('tooltip')

    // the tool is rendered only for signed in users, so the page is hydrated when it appears
    await page.getByRole('link', { name: 'Избранное', exact: true }).hover()
    await expect(tooltip).toHaveText('Избранное')
    await expect(tooltip).toHaveAttribute('data-side', 'top')
  })

  test('stuck menu toggler shows tooltip', async ({ page, isMobile }) => {
    test.skip(isMobile, 'Tooltips open on hover')
    await page.goto('/catalog/sewing_machines/')
    const toggler = page.getByRole('button', { name: 'Раскрыть меню' })
    const tooltip = page.getByRole('tooltip')

    // the toggler appears when the navbar sticks after scrolling, the page is hydrated once it does
    await expect(async () => {
      await page.mouse.wheel(0, 600)
      await expect(toggler).toBeVisible({ timeout: 1000 })
    }).toPass()
    await toggler.hover()
    await expect(tooltip).toHaveText('Раскрыть меню')
  })
})
