import { test, expect, openFilters } from './fixtures'

test('price range filter updates query', async ({ page, isMobile }) => {
  await page.goto('/catalog/sewing_machines/')
  await openFilters(page, isMobile)
  const widget = page.locator('.widget', { has: page.getByRole('heading', { name: 'Цена' }) })
  const thumbs = widget.getByRole('slider')
  await expect(thumbs).toHaveCount(2)

  // moving the minimum thumb with keyboard, thumbs are server rendered so retry until hydrated
  const minInput = widget.locator('input[name="price_min"]')
  const initialMin = Number(await minInput.inputValue())
  await expect(async () => {
    await thumbs.first().focus()
    await page.keyboard.press('PageUp')
    await expect(page).toHaveURL(/[?&]price=\d+-\d+/, { timeout: 1000 })
  }).toPass()
  await expect.poll(async () => Number(await minInput.inputValue())).toBeGreaterThan(initialMin)

  // typing the maximum moves the slider thumb
  await widget.locator('input[name="price_max"]').fill('50000')
  await expect(thumbs.last()).toHaveAttribute('aria-valuenow', '50000')
  await expect(page).toHaveURL(/[?&]price=\d+-50000/)
})

test('slider filter updates query', async ({ page, isMobile }) => {
  await page.goto('/catalog/sewing_machines/')
  await openFilters(page, isMobile)
  const widget = page.locator('.widget', { has: page.getByRole('heading', { name: 'Потребляемая мощность больше' }) })
  const thumb = widget.getByRole('slider')
  await expect(thumb).toHaveCount(1)
  const initialValue = await thumb.getAttribute('aria-valuenow')

  // thumb is server rendered so retry until hydrated
  await expect(async () => {
    await thumb.focus()
    await page.keyboard.press('ArrowRight')
    await expect(thumb).not.toHaveAttribute('aria-valuenow', initialValue!, { timeout: 1000 })
  }).toPass()
  const value = await thumb.getAttribute('aria-valuenow')
  await expect(page).toHaveURL(new RegExp(`[?&]sm_power=${value}`))
  await expect(widget).toContainText(`${value} Вт`)

  // returning to minimum removes the filter
  await page.keyboard.press('Home')
  await expect(thumb).toHaveAttribute('aria-valuenow', initialValue!)
  await expect(page).not.toHaveURL(/[?&]sm_power=/)
})

test('favorite icon shows tooltip', async ({ page, backend, isMobile }) => {
  test.skip(isMobile, 'Tooltips open on hover')
  backend.signIn()
  await page.goto('/catalog/sewing_machines/')
  const tooltip = page.locator('.tooltip')

  // the icon is rendered only for signed in users, so the page is hydrated when it appears
  await page.locator('.product-card .btn-wishlist').first().hover()
  await expect(tooltip).toHaveText('Отложить')
  await expect(tooltip).toHaveClass(/bs-tooltip-start/)
})

test('filters are in the sidebar on desktop', async ({ page, isMobile }) => {
  test.skip(isMobile, 'Filters are in an offcanvas below the lg breakpoint')
  await page.goto('/catalog/sewing_machines/')
  await expect(page.getByRole('heading', { name: 'Цена' })).toBeVisible()
  await expect(page.getByRole('dialog')).toHaveCount(0)
})

test('filters offcanvas closes on mobile', async ({ page, isMobile }) => {
  test.skip(!isMobile, 'Filters are in an offcanvas below the lg breakpoint')
  await page.goto('/catalog/sewing_machines/')
  const filters = page.getByRole('dialog')

  await openFilters(page, isMobile)
  await expect(filters).toBeVisible()
  await expect(filters.getByRole('heading', { name: 'Цена' })).toBeVisible()
  await expect(page.locator('.modal-backdrop')).toBeVisible()

  // the offcanvas leaves a strip of the backdrop on the right
  const viewport = page.viewportSize()!
  await page.mouse.click(viewport.width - 10, viewport.height / 2)
  await expect(filters).toBeHidden()

  await openFilters(page, isMobile)
  await expect(filters).toBeVisible()
  await page.keyboard.press('Escape')
  await expect(filters).toBeHidden()

  await openFilters(page, isMobile)
  await filters.getByRole('button', { name: 'Закрыть' }).click()
  await expect(filters).toBeHidden()
})
