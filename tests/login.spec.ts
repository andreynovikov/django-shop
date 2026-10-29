import { Page } from '@playwright/test'

import type { FakeBackend } from './fake-backend'
import { test, expect, accountLink } from './fixtures'
import { autofillPhone, focusPhone, pastePhone, typePhone } from './phone'

const phoneInput = (page: Page) => page.getByRole('textbox', { name: 'Укажите номер мобильного телефона:' })

test.beforeEach(async ({ page }) => {
  await page.goto('/login/')
  await focusPhone(phoneInput(page))
})

test('user logs in with a code from SMS', async ({ page, backend }) => {
  const user = backend.addUser()
  await typePhone(phoneInput(page), '9161234567')
  await page.getByRole('button', { name: 'Войти' }).click()

  const code = page.getByPlaceholder('Код из смс')
  await expect(code).toBeVisible()
  await code.fill(backend.lastSmsCode(user.phone)!)
  await page.getByRole('button', { name: 'Продолжить' }).click()

  await expect(page).toHaveURL('/')
  await expect(accountLink(page)).toBeVisible()
  expect(backend.user?.id).toBe(user.id)
})

test('unknown phone is not logged in', async ({ page, backend }) => {
  await typePhone(phoneInput(page), '9161234567')
  await page.getByRole('button', { name: 'Войти' }).click()

  await expect(page.getByText('Пользователь с таким телефоном не зарегистрирован')).toBeVisible()
  expect(backend.smsLog).toEqual([])
})

test('wrong code is not accepted', async ({ page, backend }) => {
  backend.addUser()
  await typePhone(phoneInput(page), '9161234567')
  await page.getByRole('button', { name: 'Войти' }).click()

  const code = page.getByPlaceholder('Код из смс')
  await expect(code).toBeVisible()
  // codes are four digits from 1000
  await code.fill('0000')
  await page.getByRole('button', { name: 'Продолжить' }).click()

  await expect(page.getByText('Вы ввели неправильный код')).toBeVisible()
  await expect(accountLink(page)).toHaveCount(0)
  expect(backend.user).toBeUndefined()
})

test.describe('phone input', () => {
  test.beforeEach(({ backend }) => {
    backend.addUser()
  })

  async function expectPhoneChecked(page: Page, backend: FakeBackend) {
    await expect(phoneInput(page)).toHaveValue('+7 (916) 123-45-67')
    await page.getByRole('button', { name: 'Войти' }).click()
    await expect(page.getByPlaceholder('Код из смс')).toBeVisible()
    expect(backend.requestsTo('POST', /\/check\/$/).map(({ path }) => path)).toEqual(['users/+79161234567/check/'])
  }

  // the country code is already in the input, so only the rest of the number is typed
  test('takes typed digits', async ({ page, backend }) => {
    await typePhone(phoneInput(page), '9161234567')
    await expectPhoneChecked(page, backend)
  })

  for (const value of ['+79161234567', '+7 (916) 123-45-67', '89161234567', '8 916 123-45-67', '9161234567']) {
    test(`takes pasted ${value}`, async ({ page, backend }) => {
      await pastePhone(page, phoneInput(page), value)
      await expectPhoneChecked(page, backend)
    })

    test(`takes autofilled ${value}`, async ({ page, backend }) => {
      await autofillPhone(phoneInput(page), value)
      await expectPhoneChecked(page, backend)
    })
  }
})
