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
