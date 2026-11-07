import { test, expect } from './fixtures'

test('blog redirects to entries', async ({ page }) => {
  await page.goto('/blog/')
  await expect(page).toHaveURL('/blog/entries/')
})

test('blog has entries', async ({ page }) => {
  await page.goto('/blog/entries/')
  await expect(page.getByRole('article')).not.toHaveCount(0)
})

test('blog entries pagination works', async ({ page }) => {
  await page.goto('/blog/entries/')
  const pagination = page.getByRole('navigation', { name: 'Переключение страниц' })
  // test only if pagination exists
  if (await pagination.count() > 0) {
    const pageLink = pagination.getByRole('link').last()
    const href = await pageLink.getAttribute('href')
    expect(href).not.toBeNull()
    await pageLink.click()
    await expect(page).toHaveURL(href as string) // we've checked for null
    // a failed client navigation falls back to a full page load, so the URL changes even when the page is broken
    const pageNumber = (href as string).match(/\/(\d+)\/$/)?.[1]
    await expect(pagination.locator('li[aria-current="page"]')).toHaveText(new RegExp(`^${pageNumber}`))
    await expect(page.getByRole('article')).not.toHaveCount(0)
  }
})

test('blog entry opens', async ({ page }) => {
  await page.goto('/blog/entries/')
  const firstEntryLink = page.getByRole('article').first().getByRole('heading').getByRole('link')
  const title = await firstEntryLink.innerText()
  await firstEntryLink.click()
  await expect(page).toHaveTitle(new RegExp(`^${title}`))
})

test('blog category opens', async ({ page }) => {
  await page.goto('/blog/entries/')
  const firstEntryLink = page.getByRole('article').locator('a[href^="/blog/categories/"]').first()
  const title = await firstEntryLink.innerText()
  await firstEntryLink.click()
  await expect(page).toHaveTitle(new RegExp(`^Архив категории ${title}`))
})

test('blog tag opens', async ({ page }) => {
  await page.goto('/blog/entries/')
  const firstEntryLink = page.getByRole('article').locator('a[href^="/blog/tags/"]').first()
  const title = await firstEntryLink.innerText()
  await firstEntryLink.click()
  await expect(page).toHaveTitle(new RegExp(`^Архив по тэгу '${title.slice(1)}'`))
})

test('blog entry navigation shows neighbour entries in popovers', async ({ page, isMobile }) => {
  test.skip(isMobile, 'Popovers open on hover')
  await page.goto('/blog/entries/')
  // the second entry has both previous and next entries
  await page.getByRole('article').nth(1).getByRole('heading').getByRole('link').click()
  await page.waitForURL(/\/blog\/(?!entries\/)/)

  const popover = page.getByRole('tooltip')
  const navigation = page.getByRole('navigation', { name: 'Навигация по записям' })
  for (const name of ['Предыдущая запись', 'Следующая запись']) {
    const link = navigation.getByRole('link', { name })
    // the page is server rendered, retry until hydrated
    await expect(async () => {
      await page.mouse.move(0, 0)
      await link.hover()
      await expect(popover).toBeVisible({ timeout: 1500 })
    }).toPass()
    await expect(popover.getByRole('heading')).not.toBeEmpty()

    await page.mouse.move(0, 0)
    await expect(popover).toBeHidden()
  }
})
