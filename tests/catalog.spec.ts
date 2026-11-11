import { Page } from '@playwright/test'

import { test, expect, gotoHydrated, openFilters } from './fixtures'

// A category with several pages of products
const largeCategory = '/catalog/accessories/threads/GutermannSewAll/'
const nextPageRequest = /\/api\/v0\/products\/\?.*\bpage=2\b/

const productTitles = (page: Page) => page.getByRole('main').getByRole('heading', { level: 3 })
const pageLinks = (page: Page) => page.getByRole('navigation', { name: 'Переключение страниц' })

// The link to the next page loads it in place, once the user scrolls to it
async function loadNextPage(page: Page) {
  const titles = productTitles(page)
  const count = await titles.count()
  await page.getByRole('link', { name: 'Показать ещё' }).scrollIntoViewIfNeeded()
  await expect.poll(() => titles.count()).toBeGreaterThan(count)
  return count
}


test('price range filter updates query', async ({ page, isMobile }) => {
  await page.goto('/catalog/sewing_machines/')
  await openFilters(page, isMobile)
  const widget = page.getByRole('heading', { name: 'Цена' }).locator('..')
  const thumbs = widget.getByRole('slider')
  await expect(thumbs).toHaveCount(2)

  // moving the minimum thumb with keyboard, thumbs are server rendered so retry until hydrated
  const minInput = widget.locator('input[name="price_min"]')
  const initialMin = Number(await minInput.inputValue())
  // the scale starts at the lowest price, where the minimum thumb rests
  await expect(thumbs.first()).toHaveAttribute('min', String(initialMin))
  await expect(async () => {
    await thumbs.first().focus()
    await page.keyboard.press('PageUp')
    await expect(page).toHaveURL(/[?&]price=\d+-\d+/, { timeout: 1000 })
  }).toPass()
  await expect.poll(async () => Number(await minInput.inputValue())).toBeGreaterThan(initialMin)

  // typing the maximum moves the slider thumb
  const maxInput = widget.locator('input[name="price_max"]')
  await maxInput.fill('50000')
  await expect(thumbs.last()).toHaveAttribute('aria-valuenow', '50000')
  await expect(page).toHaveURL(/[?&]price=\d+-50000/)

  // the backend refuses a negative bound, so typing one changes nothing
  await maxInput.fill('-5')
  await expect(maxInput).toHaveValue('50000')
  await expect(page).toHaveURL(/[?&]price=\d+-50000/)
})

test('slider filter updates query', async ({ page, isMobile }) => {
  await page.goto('/catalog/sewing_machines/')
  await openFilters(page, isMobile)
  const widget = page.getByRole('heading', { name: 'Потребляемая мощность больше' }).locator('..')
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
  const tooltip = page.getByRole('tooltip')

  // the icon is rendered only for signed in users, so the page is hydrated when it appears
  await page.getByRole('button', { name: 'Отложить' }).first().hover()
  await expect(tooltip).toHaveText('Отложить')
  await expect(tooltip).toHaveAttribute('data-side', 'left')
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

test('category loads the next page as the user scrolls', async ({ page }) => {
  await gotoHydrated(page, largeCategory)
  const more = page.getByRole('link', { name: 'Показать ещё' })
  await expect(more).toHaveAttribute('href', `${largeCategory}2/`)
  await expect(pageLinks(page).getByRole('link', { name: /^След/ })).toHaveAttribute('href', `${largeCategory}2/`)

  await loadNextPage(page)
  // both pages are shown, so the links go on from the third
  await expect(more).toHaveAttribute('href', `${largeCategory}3/`)
  await expect(pageLinks(page).getByRole('link', { name: /^След/ })).toHaveAttribute('href', `${largeCategory}3/`)
})

test('category loads no page for robots, they follow the links', async ({ page, isMobile }) => {
  test.skip(isMobile, 'The window is resized to a desktop one')
  // robots render the page in a tall window and don't scroll
  await page.setViewportSize({ width: 1280, height: 20000 })
  const nextPages: string[] = []
  page.on('request', (request) => {
    if (nextPageRequest.test(request.url()))
      nextPages.push(request.url())
  })
  await gotoHydrated(page, largeCategory)
  await expect(page.getByRole('link', { name: 'Показать ещё' })).toBeInViewport()
  // the link would be loaded at once, the network doesn't go idle in the PLAYWRIGHT_TEST build
  await page.waitForTimeout(1000)
  expect(nextPages).toEqual([])

  // the whole page fits in the window, a user's window scrolls to the link
  await page.setViewportSize({ width: 1280, height: 720 })
  const nextPage = page.waitForRequest(nextPageRequest)
  await page.getByRole('link', { name: 'Показать ещё' }).scrollIntoViewIfNeeded()
  await nextPage
})

test('following category page links to the others', async ({ page }) => {
  await page.goto(`${largeCategory}2/`)
  await expect(page).toHaveTitle(/, страница 2 /)
  await expect(pageLinks(page).getByRole('link', { name: /^Пред/ })).toHaveAttribute('href', largeCategory)
  await expect(pageLinks(page).getByRole('link', { name: /^След/ })).toHaveAttribute('href', `${largeCategory}3/`)
})

test('back button returns to the category pages loaded on scroll', async ({ page }) => {
  await gotoHydrated(page, largeCategory)
  const firstPageCount = await loadNextPage(page)

  // the first product of the second page
  const title = productTitles(page).nth(firstPageCount)
  const name = (await title.textContent())!
  await title.getByRole('link').click()
  await expect(page).not.toHaveURL(new RegExp(`${largeCategory}$`))

  await page.goBack()
  await expect(productTitles(page).filter({ hasText: name })).toBeInViewport()
})
