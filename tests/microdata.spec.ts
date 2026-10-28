import { Page } from '@playwright/test'

import { test, expect } from './fixtures'
import { findSewingMachines } from './api'
import { extractMicrodata, isItem, typeName, validateMicrodata, MicrodataItem, MicrodataValue } from './microdata'

import type { Category } from '@/lib/types'

test.skip(({ browserName, isMobile }) => browserName !== 'chromium' || isMobile, 'Microdata does not depend on the browser')

// Microdata is server rendered, so it is checked in the HTML as crawlers get it.
// Not waiting for the load event also skips maps and other third-party scripts.
async function loadMicrodata(page: Page, path: string) {
  const response = await page.goto(path, { waitUntil: 'domcontentloaded' })
  // an error page has no microdata, which would read as missing items
  expect(response?.status()).toBe(200)
  // streamed Suspense content waits in hidden elements at the end of the body until React moves it into place
  await page.waitForFunction(() => document.querySelector('div[hidden][id^="S:"]') === null)
  return await extractMicrodata(page)
}

const ofType = (items: MicrodataValue[] | undefined, name: string) =>
  (items ?? []).filter((item): item is MicrodataItem => isItem(item) && typeName(item) === name)

const text = (item: MicrodataItem, property: string) => {
  const value = item.properties[property]?.[0]
  return value === undefined || isItem(value) ? undefined : value.value
}

test('product page has valid Product microdata', async ({ page, request }) => {
  const [product] = await findSewingMachines(request)
  const microdata = await loadMicrodata(page, `/products/${product.code}/`)
  expect.soft(validateMicrodata(microdata)).toEqual([])

  const products = ofType(microdata.items, 'Product')
  expect(products).toHaveLength(1)
  expect(text(products[0], 'name')).toContain(product.title)

  const offers = ofType(products[0].properties.offers, 'Offer')
  expect(offers).toHaveLength(1)
  expect(text(offers[0], 'price')).toBe(String(product.cost))
  expect(text(offers[0], 'url')).toMatch(new RegExp(`/products/${product.code}/$`))
})

test('category page has valid OfferCatalog microdata', async ({ page, request }) => {
  const response = await request.get('/api/v0/categories/sewing_machines/')
  expect(response.ok()).toBeTruthy()
  const category = await response.json() as Category

  const microdata = await loadMicrodata(page, '/catalog/sewing_machines/')
  expect.soft(validateMicrodata(microdata)).toEqual([])

  const catalogs = ofType(microdata.items, 'OfferCatalog')
  expect(catalogs).toHaveLength(1)
  expect(text(catalogs[0], 'name')).toBe(category.name)

  // every product card is a named offer of the catalog
  const offers = ofType(catalogs[0].properties.itemListElement, 'Offer')
  await expect(page.locator('.product-card')).toHaveCount(offers.length)
  expect(offers.filter((offer) => !text(offer, 'name'))).toEqual([])
})

test('stores page has valid Organization microdata', async ({ page }) => {
  const microdata = await loadMicrodata(page, '/stores/')
  expect.soft(validateMicrodata(microdata)).toEqual([])

  const stores = ofType(microdata.items, 'Organization')
  expect(stores.length).toBeGreaterThan(0)
  expect(stores).toHaveLength(microdata.items.length)
})

test('service page has valid Organization microdata', async ({ page }) => {
  const microdata = await loadMicrodata(page, '/service/')
  expect.soft(validateMicrodata(microdata)).toEqual([])

  const services = ofType(microdata.items, 'Organization')
  expect(services.length).toBeGreaterThan(0)
  expect(services).toHaveLength(microdata.items.length)
})

test('home page product cards have valid microdata', async ({ page }) => {
  const microdata = await loadMicrodata(page, '/')
  expect(validateMicrodata(microdata)).toEqual([])
})
