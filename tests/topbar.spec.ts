import { test, expect } from './fixtures'

// Phones menu is shown only below the lg breakpoint
test.use({ viewport: { width: 390, height: 844 } })

// Topbar is rendered by both Pages Router and App Router layouts
for (const path of ['/cart/', '/stores/']) {
  test(`phones menu opens on ${path}`, async ({ page }) => {
    await page.goto(path)
    await page.getByRole('button', { name: 'Телефоны' }).click()

    const menu = page.getByRole('menu')
    await expect(menu).toBeVisible()
    await expect(menu.locator('a[href="tel:+74957440087"]')).toBeVisible()
    await expect(menu).toContainText('розничные магазины')

    await page.keyboard.press('Escape')
    await expect(menu).toBeHidden()
  })
}
