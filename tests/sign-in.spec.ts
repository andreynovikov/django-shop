import { Page } from '@playwright/test'

import { test, expect } from './fixtures'

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

test('registration in sign-in modal continues to login with the phone', async ({ page }) => {
  // do not create a real user, and do not let the login form request a code for the phone
  await page.route('**/api/v0/users/', route => route.fulfill({ status: 201, json: { id: 5 } }))
  let checkedUrl
  await page.route('**/api/v0/users/*/check/', route => {
    checkedUrl = route.request().url()
    return route.fulfill({ json: { phone: '+79161234567', permanent_password: false } })
  })

  const dialog = await openSignIn(page)
  await dialog.getByRole('tab', { name: 'Регистрация' }).click()
  await dialog.getByRole('textbox', { name: 'Укажите номер мобильного телефона:' }).fill('9161234567')
  await dialog.getByRole('checkbox').check()
  await dialog.getByRole('button', { name: 'Зарегистрироваться' }).click()

  // login form gets the registered phone and asks for the code
  await expect(dialog.getByRole('tab', { name: 'Вход' })).toHaveAttribute('aria-selected', 'true')
  await expect(dialog.getByPlaceholder('Код из смс')).toBeVisible()
  await expect(dialog.locator('.lead')).toContainText(/916.*123.*45.*67/)
  expect(checkedUrl).toContain('/users/+79161234567/check/')
})
