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
  await expect(code).toHaveAttribute('type', 'text')
  await expect(code).toHaveAttribute('autocomplete', 'one-time-code')
  await code.fill(backend.lastSmsCode(user.phone)!)
  await page.getByRole('button', { name: 'Продолжить' }).click()

  await expect(page).toHaveURL('/')
  await expect(accountLink(page)).toBeVisible()
  expect(backend.user?.id).toBe(user.id)
})

test('user logs in with a permanent password', async ({ page, backend }) => {
  const secret = 'a permanent password of any length over five'
  const user = backend.addUser({ permanent_password: true, password: secret })
  await typePhone(phoneInput(page), '9161234567')
  await page.getByRole('button', { name: 'Войти' }).click()

  const password = page.getByPlaceholder('Пароль')
  await expect(password).toBeVisible()
  await expect(password).toHaveAttribute('type', 'password')
  await expect(password).toHaveAttribute('autocomplete', 'current-password')
  await password.fill(secret)
  await page.getByRole('button', { name: 'Продолжить' }).click()

  await expect(page).toHaveURL('/')
  expect(backend.user?.id).toBe(user.id)
  expect(backend.smsLog).toEqual([])
})

test('forgotten password is replaced by a code only when the code is used', async ({ page, backend }) => {
  const user = backend.addUser({ permanent_password: true, password: 'permanent' })
  await typePhone(phoneInput(page), '9161234567')
  await page.getByRole('button', { name: 'Войти' }).click()
  await page.getByText('Сбросить забытый пароль').click()

  const code = page.getByPlaceholder('Код из смс')
  await expect(code).toBeVisible()
  expect(user.permanent_password).toBe(true)
  await code.fill(backend.lastSmsCode(user.phone)!)
  await page.getByRole('button', { name: 'Продолжить' }).click()

  await expect(page).toHaveURL('/')
  expect(user.permanent_password).toBe(false)
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
  // the fake's codes start from 100000
  await code.fill('000000')
  await page.getByRole('button', { name: 'Продолжить' }).click()

  await expect(page.getByText('Неверный или устаревший код')).toBeVisible()
  await expect(accountLink(page)).toHaveCount(0)
  expect(backend.user).toBeUndefined()
})

test('code of a wrong length does not use up an attempt', async ({ page, backend }) => {
  backend.addUser()
  await typePhone(phoneInput(page), '9161234567')
  await page.getByRole('button', { name: 'Войти' }).click()

  const code = page.getByPlaceholder('Код из смс')
  await expect(code).toBeVisible()
  await code.fill('1234')
  await page.getByRole('button', { name: 'Продолжить' }).click()

  await expect(page.getByText('Указан неверный код')).toBeVisible()
  expect(backend.requestsTo('POST', 'users/login/')).toEqual([])
})

test('new code can be requested at once when attempts run out', async ({ page, backend }) => {
  const user = backend.addUser()
  await typePhone(phoneInput(page), '9161234567')
  await page.getByRole('button', { name: 'Войти' }).click()

  const code = page.getByPlaceholder('Код из смс')
  const resend = page.getByText('Прислать код повторно')
  await expect(code).toBeVisible()
  await code.fill('000000')
  for (let attempt = 1; attempt <= 5; attempt++) {
    await expect(resend).toHaveCount(0)
    await page.getByRole('button', { name: 'Продолжить' }).click()
    await expect.poll(() => backend.requestsTo('POST', 'users/login/').length).toBe(attempt)
    await expect(page.getByText('Неверный или устаревший код')).toBeVisible()
  }

  await resend.click()
  await expect.poll(() => backend.smsLog.length).toBe(2)
  await expect(resend).toHaveCount(0)
  await code.fill(backend.lastSmsCode(user.phone)!)
  await page.getByRole('button', { name: 'Продолжить' }).click()

  await expect(page).toHaveURL('/')
  expect(backend.user?.id).toBe(user.id)
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
