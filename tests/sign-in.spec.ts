import { Page } from '@playwright/test'

import { test, expect, accountLink } from './fixtures'

async function openSignIn(page: Page) {
  await page.goto('/cart/')
  const profileLink = page.locator('a.navbar-tool-icon-box', { has: page.locator('.ci-user') }).filter({ visible: true })
  const dialog = page.getByRole('dialog')
  // the topbar is server rendered, retry until hydrated
  await expect(async () => {
    await profileLink.click()
    await expect(dialog).toBeVisible({ timeout: 1000 })
  }).toPass()
  return dialog
}

test('sign-in modal switches between login and registration', async ({ page }) => {
  const dialog = await openSignIn(page)
  const signInTab = dialog.getByRole('tab', { name: 'Вход' })
  const signUpTab = dialog.getByRole('tab', { name: 'Регистрация' })
  await expect(signInTab).toHaveAttribute('aria-selected', 'true')
  await expect(dialog.getByRole('button', { name: 'Войти' })).toBeVisible()

  await signUpTab.click()
  await expect(signUpTab).toHaveAttribute('aria-selected', 'true')
  const registrationPhone = dialog.getByRole('textbox', { name: 'Укажите номер мобильного телефона:' })
  await registrationPhone.fill('9161234567')

  // both forms stay mounted, so switching tabs keeps what was typed
  await signInTab.click()
  await expect(dialog.getByRole('button', { name: 'Войти' })).toBeVisible()
  await signUpTab.click()
  await expect(registrationPhone).toHaveValue(/916.*123.*45.*67/)

  await dialog.getByRole('button', { name: 'Закрыть' }).click()
  await expect(dialog).toBeHidden()
})

test('sign-in modal closes on Escape and outside click', async ({ page }) => {
  const dialog = await openSignIn(page)
  await page.keyboard.press('Escape')
  await expect(dialog).toBeHidden()

  await page.locator('a.navbar-tool-icon-box', { has: page.locator('.ci-user') }).filter({ visible: true }).click()
  await expect(dialog).toBeVisible()
  await page.mouse.click(5, 5)
  await expect(dialog).toBeHidden()
})

test('registration in sign-in modal continues to login with the phone', async ({ page, backend }) => {
  const dialog = await openSignIn(page)
  await dialog.getByRole('tab', { name: 'Регистрация' }).click()
  await dialog.getByRole('textbox', { name: 'Укажите номер мобильного телефона:' }).fill('9161234567')
  await dialog.getByRole('checkbox').check()
  await dialog.getByRole('button', { name: 'Зарегистрироваться' }).click()

  // login form gets the registered phone and asks for the code
  await expect(dialog.getByRole('tab', { name: 'Вход' })).toHaveAttribute('aria-selected', 'true')
  await expect(dialog.getByPlaceholder('Код из смс')).toBeVisible()
  await expect(dialog.locator('.lead')).toContainText(/916.*123.*45.*67/)
  expect(backend.findUser('+79161234567')).toBeDefined()
  // the form checks the phone in an effect, which React runs twice in development
  expect(new Set(backend.requestsTo('POST', /\/check\/$/).map(({ path }) => path))).toEqual(new Set(['users/+79161234567/check/']))
})

test('login in sign-in modal stays on the page', async ({ page, backend }) => {
  const user = backend.addUser()
  const dialog = await openSignIn(page)
  await dialog.getByRole('textbox', { name: 'Укажите номер мобильного телефона:' }).fill('9161234567')
  await dialog.getByRole('button', { name: 'Войти' }).click()

  const code = dialog.getByPlaceholder('Код из смс')
  await expect(code).toBeVisible()
  await code.fill(backend.lastSmsCode(user.phone)!)
  await dialog.getByRole('button', { name: 'Продолжить' }).click()

  await expect(dialog).toBeHidden()
  await expect(page).toHaveURL('/cart/')
  await expect(accountLink(page)).toBeVisible()
})
