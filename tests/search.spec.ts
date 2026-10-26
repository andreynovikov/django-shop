import { test, expect, openFilters } from './fixtures'

test('search price filter updates query', async ({ page, isMobile }) => {
  await page.goto('/search/?text=janome')
  await openFilters(page, isMobile)
  const widget = page.locator('.widget', { has: page.getByRole('heading', { name: 'Цена' }) })
  const thumbs = widget.getByRole('slider')
  await expect(thumbs).toHaveCount(2)

  await thumbs.last().focus()
  await page.keyboard.press('PageDown')
  await expect(page).toHaveURL(/[?&]price=\d+-\d+/)
})
