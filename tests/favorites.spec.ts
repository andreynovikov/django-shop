import { findSewingMachines } from './api'
import { test, expect } from './fixtures'

test('signed in user keeps products in favorites', async ({ page, request, backend }) => {
  const [product] = await findSewingMachines(request)
  backend.signIn()

  // the button is rendered only for signed in users, so the page is hydrated when it appears
  await page.goto(`/products/${product.code}/`)
  await page.getByRole('button', { name: 'Отложить' }).click()
  await expect(page.getByRole('button', { name: 'В избранном' })).toBeVisible()
  expect(backend.favoriteIds).toEqual([product.id])

  // the favorites tool is in the topbar from the lg breakpoint, below it is in the handheld toolbar; only one is shown
  const favoritesLink = page.getByRole('link', { name: 'Избранное', exact: true })
  await expect(favoritesLink).toContainText('1')
  await favoritesLink.click()

  await expect(page).toHaveURL('/user/favorites/')
  await expect(page.getByRole('heading', { name: product.title, exact: true })).toBeVisible()
  await page.getByRole('button', { name: 'Удалить' }).click()
  await expect(page.getByText('Здесь появятся ваши отложенные товары')).toBeVisible()
  expect(backend.favoriteIds).toEqual([])
})

test('favorites page lists favorites on a direct visit', async ({ page, request, backend }) => {
  const [first, second] = await findSewingMachines(request)
  backend.signIn()
  backend.addFavorites([first, second])

  await page.goto('/user/favorites/')
  await expect(page.getByRole('heading', { name: first.title, exact: true })).toBeVisible()
  await expect(page.getByRole('heading', { name: second.title, exact: true })).toBeVisible()
})
