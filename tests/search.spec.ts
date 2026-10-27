import { Page } from '@playwright/test'

import { test, expect, openFilters } from './fixtures'

import { findSewingMachines } from './api'

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

test.describe('search input', () => {
  let product: { name: string, code: string }
  let suggestionRequests: string[]

  test.beforeEach(async ({ page, request }) => {
    const [found] = await findSewingMachines(request)
    product = { name: found.title, code: found.code }
    suggestionRequests = []
    // suggestions come straight from Diginetica, fixed ones keep the tests stable
    await page.route('https://autocomplete.diginetica.net/autocomplete**', route => {
      const text = new URL(route.request().url()).searchParams.get('st') ?? ''
      suggestionRequests.push(text)
      if (text === 'zzz')
        return route.fulfill({ json: { query: text, sts: [], taps: [], products: [], categories: [], brands: [], contents: [] } })
      return route.fulfill({
        json: {
          query: text,
          sts: [{ st: 'janome 1143', amount: '10' }, { st: 'janome juno', amount: '5' }],
          taps: [],
          products: [{
            id: '1',
            available: true,
            name: `Janome ${product.name}`,
            brand: 'Janome',
            price: '25000',
            score: 1,
            categories: [],
            attributes: {},
            link_url: `/products/${product.code}.html`,
            image_url: '',
            image_urls: []
          }],
          categories: [],
          brands: [],
          contents: []
        }
      })
    })
    await page.goto('/cart/')
  })

  // there are separate desktop and mobile inputs
  const searchInput = (page: Page) => page.getByPlaceholder('Поиск товаров').filter({ visible: true })

  async function search(page: Page, text: string) {
    const input = searchInput(page)
    // the input is server rendered, retry until hydrated and suggestions are requested
    await expect(async () => {
      await input.fill('')
      await input.fill(text)
      await expect.poll(() => suggestionRequests.includes(text), { timeout: 1500 }).toBe(true)
    }).toPass()
    return page.getByRole('listbox')
  }

  test('shows grouped suggestions with highlighted text', async ({ page }) => {
    const suggestions = await search(page, 'jan')
    await expect(suggestions).toContainText('Часто ищут')
    await expect(suggestions).toContainText('Популярные товары')
    await expect(suggestions.getByRole('option')).toHaveCount(3)
    const productOption = suggestions.getByRole('option', { name: product.name })
    await expect(productOption).toContainText('25 000')
    // the typed text is highlighted in suggestions
    await expect(suggestions.getByRole('option', { name: 'janome 1143' }).getByText('jan', { exact: true })).toBeVisible()
  })

  test('does not suggest for short text', async ({ page }) => {
    const input = searchInput(page)
    await input.fill('ja')
    await page.waitForTimeout(1000)
    await expect(page.getByRole('option')).toHaveCount(0)
    expect(suggestionRequests).toHaveLength(0)
  })

  test('shows when nothing is found', async ({ page }) => {
    await search(page, 'zzz')
    await expect(page.getByText('Ничего не найдено')).toBeVisible()
    await expect(page.getByRole('option')).toHaveCount(0)
  })

  test('Enter submits the search form', async ({ page }) => {
    await search(page, 'jan')
    await page.keyboard.press('Enter')
    await expect(page).toHaveURL(/\/search\/\?text=jan$/)
  })

  test('choosing a product opens its page', async ({ page }) => {
    const suggestions = await search(page, 'jan')
    await suggestions.getByRole('option', { name: product.name }).click()
    await expect(page).toHaveURL(`/products/${product.code}/`)
  })

  test('choosing a frequent search opens its results', async ({ page }) => {
    const suggestions = await search(page, 'jan')
    await suggestions.getByRole('option', { name: 'janome juno' }).click()
    await expect(page).toHaveURL('/search/?text=janome+juno')
  })

  test('choosing a frequent search with keyboard opens its results', async ({ page }) => {
    await search(page, 'jan')
    // the first option is janome 1143
    await page.keyboard.press('ArrowDown')
    await page.keyboard.press('Enter')
    await expect(page).toHaveURL('/search/?text=janome+1143')
  })

  test('Escape closes suggestions', async ({ page }) => {
    const suggestions = await search(page, 'jan')
    await page.keyboard.press('Escape')
    await expect(suggestions).toBeHidden()
    await expect(searchInput(page)).toHaveValue('jan')
  })
})
