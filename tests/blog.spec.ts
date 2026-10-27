import { test, expect } from '@playwright/test'

test('blog redirects to entries', async ({ page }) => {
  await page.goto('/blog/')
  await expect(page).toHaveURL('/blog/entries/')
})

test('blog has entries', async ({ page }) => {
  await page.goto('/blog/entries/')
  await expect(page.locator('article.blog-list')).not.toHaveCount(0)
})

test('blog entries pagination works', async ({ page }) => {
  await page.goto('/blog/entries/')
  const pagination = page.locator('nav > ul.pagination')
  // test only if pagination exists
  if (await pagination.count() > 0) {
    const pageLink = pagination.locator('li.page-item > a.page-link').last()
    const href = await pageLink.getAttribute('href')
    expect(href).not.toBeNull()
    await pageLink.click()
    await expect(page).toHaveURL(href as string) // we've checked for null
    // a failed client navigation falls back to a full page load, so the URL changes even when the page is broken
    const pageNumber = (href as string).match(/\/(\d+)\/$/)?.[1]
    await expect(pagination.locator('li[aria-current="page"]')).toHaveText(new RegExp(`^${pageNumber}`))
    await expect(page.locator('article.blog-list')).not.toHaveCount(0)
  }
})

test('blog entry opens', async ({ page }) => {
  await page.goto('/blog/entries/')
  const firstEntryLink = page.locator('article.blog-list').first().locator('.blog-entry-title > a')
  const title = await firstEntryLink.innerText()
  await firstEntryLink.click()
  await expect(page).toHaveTitle(new RegExp(`^${title}`))
})

test('blog category opens', async ({ page }) => {
  await page.goto('/blog/entries/')
  const firstEntryLink = page.locator('article.blog-list > .blog-end-column .text-muted a.blog-entry-meta-link').first()
  const title = await firstEntryLink.innerText()
  await firstEntryLink.click()
  await expect(page).toHaveTitle(new RegExp(`^Архив категории ${title}`))
})

test('blog tag opens', async ({ page }) => {
  await page.goto('/blog/entries/')
  const firstEntryLink = page.locator('article.blog-list a.btn-tag').first()
  const title = await firstEntryLink.innerText()
  await firstEntryLink.click()
  await expect(page).toHaveTitle(new RegExp(`^Архив по тэгу '${title.slice(1)}'`))
})

test('blog entry navigation shows neighbour entries in popovers', async ({ page, isMobile }) => {
  test.skip(isMobile, 'Popovers open on hover')
  await page.goto('/blog/entries/')
  // the second entry has both previous and next entries
  await page.locator('article.blog-list').nth(1).locator('.blog-entry-title > a').click()
  await page.waitForURL(/\/blog\/(?!entries\/)/)

  const popover = page.locator('.popover')
  for (const icon of ['.ci-arrow-left', '.ci-arrow-right']) {
    const link = page.locator('.entry-navigation a.entry-navigation-link', { has: page.locator(icon) })
    // the page is server rendered, retry until hydrated
    await expect(async () => {
      await page.mouse.move(0, 0)
      await link.hover()
      await expect(popover).toBeVisible({ timeout: 1500 })
    }).toPass()
    await expect(popover.locator('h6')).not.toBeEmpty()

    await page.mouse.move(0, 0)
    await expect(popover).toBeHidden()
  }
})
