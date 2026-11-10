import { Page } from '@playwright/test'

import { test, expect, accountLink } from './fixtures'
import { focusPhone, typePhone } from './phone'

async function register(page: Page, { email = 'anna@example.com' } = {}) {
  const phone = page.getByRole('textbox', { name: 'Укажите номер мобильного телефона:' })
  await focusPhone(phone)
  await typePhone(phone, '9161234567')
  await page.getByRole('textbox', { name: 'Адрес электронной почты:' }).fill(email)
  await page.getByRole('textbox', { name: 'Фамилия Имя Отчество:' }).fill('Анна Иванова')
  await page.getByRole('checkbox').check()
  await page.getByRole('button', { name: 'Зарегистрироваться' }).click()
}

test('user registers with a code from SMS and is signed in', async ({ page, backend }) => {
  await page.goto('/register/')
  await register(page)

  // the data is checked and a code sent, but nothing is created until the code comes back
  const code = page.getByPlaceholder('Код из смс')
  await expect(code).toBeVisible()
  await expect(page.getByText(/916.*123.*45.*67/)).toBeVisible()
  expect(backend.findUser('+79161234567')).toBeUndefined()
  expect(backend.smsLog.map(({ phone }) => phone)).toEqual(['+79161234567'])

  await code.fill(backend.lastSmsCode('+79161234567')!)
  await page.getByRole('button', { name: 'Подтвердить' }).click()
  await expect(page).toHaveURL('/')
  await expect(accountLink(page)).toBeVisible()
  expect(backend.user).toMatchObject({ phone: '+79161234567', name: 'Анна Иванова', phone_verified: true, permanent_password: false })
  expect(backend.requestsTo('POST', 'users/').map(({ body }) => body)).toEqual([
    { phone: '+79161234567', email: 'anna@example.com', name: 'Анна Иванова', username: '' },
    { phone: '+79161234567', email: 'anna@example.com', name: 'Анна Иванова', username: '', code: backend.lastSmsCode('+79161234567') },
  ])
})

test('wrong code is refused and a new one can be requested', async ({ page, backend }) => {
  await page.goto('/register/')
  await register(page)

  const code = page.getByPlaceholder('Код из смс')
  const wrong = backend.lastSmsCode('+79161234567') === '000000' ? '111111' : '000000'
  for (let attempt = 0; attempt < 5; attempt++) {
    await code.fill(wrong)
    await page.getByRole('button', { name: 'Подтвердить' }).click()
    await expect(page.getByText('Неверный или устаревший код')).toBeVisible()
  }
  expect(backend.findUser('+79161234567')).toBeUndefined()

  // attempts ran out, so a new code is offered at once
  await page.getByText('Прислать код повторно').click()
  await expect.poll(() => backend.smsLog.length).toBe(2)
  await code.fill(backend.lastSmsCode('+79161234567')!)
  await page.getByRole('button', { name: 'Подтвердить' }).click()
  await expect(accountLink(page)).toBeVisible()
})

test('registered phone gets no code', async ({ page, backend }) => {
  backend.addUser({ name: 'Другой покупатель' })
  await page.goto('/register/')
  await register(page)

  await expect(page.getByText('Пользователь с указанным номером уже зарегестрирован')).toBeVisible()
  await expect(page).toHaveURL('/register/')
  expect(backend.findUser('+79161234567')?.name).toBe('Другой покупатель')
  expect(backend.smsLog).toEqual([])
})

test('taken email is told only with the code, which then registers the corrected one', async ({ page, backend }) => {
  backend.addUser({ phone: '+79167654321', email: 'anna@example.com' })
  await page.goto('/register/')
  await register(page)

  // the data step doesn't tell, so the form can't show whose address is a customer's
  const code = page.getByPlaceholder('Код из смс')
  await code.fill(backend.lastSmsCode('+79161234567')!)
  await page.getByRole('button', { name: 'Подтвердить' }).click()

  const email = page.getByRole('textbox', { name: 'Адрес электронной почты:' })
  await expect(page.getByText('Пользователь с указанным адресом уже зарегестрирован')).toBeVisible()
  await email.fill('anna.ivanova@example.com')
  await page.getByRole('button', { name: 'Зарегистрироваться' }).click()

  // the code wasn't used up, so no new one goes out
  await code.fill(backend.lastSmsCode('+79161234567')!)
  await page.getByRole('button', { name: 'Подтвердить' }).click()
  await expect(accountLink(page)).toBeVisible()
  expect(backend.user).toMatchObject({ phone: '+79161234567', email: 'anna.ivanova@example.com' })
  expect(backend.smsLog).toHaveLength(1)
})

test('data can be changed before the code', async ({ page, backend }) => {
  await page.goto('/register/')
  await register(page)
  await page.getByText('Изменить данные').click()

  const name = page.getByRole('textbox', { name: 'Фамилия Имя Отчество:' })
  await expect(name).toHaveValue('Анна Иванова')
  await name.fill('Анна Петрова')
  await page.getByRole('button', { name: 'Зарегистрироваться' }).click()

  // the code sent a moment ago is still valid, so no new one goes out
  await page.getByPlaceholder('Код из смс').fill(backend.lastSmsCode('+79161234567')!)
  await page.getByRole('button', { name: 'Подтвердить' }).click()
  await expect(accountLink(page)).toBeVisible()
  expect(backend.user?.name).toBe('Анна Петрова')
  expect(backend.smsLog).toHaveLength(1)
})

test('permanent password is set with the code', async ({ page, backend }) => {
  await page.goto('/register/')
  await register(page)
  await page.getByPlaceholder('Код из смс').fill(backend.lastSmsCode('+79161234567')!)

  const password = page.getByLabel('Постоянный пароль:')
  await password.fill('secret')
  await page.getByLabel('ещё раз:').fill('secret')
  await page.getByRole('button', { name: 'Подтвердить' }).click()
  await expect(page.getByText('Постоянный пароль должен быть не менее 8 символов')).toBeVisible()
  expect(backend.requestsTo('POST', 'users/')).toHaveLength(1)

  await password.fill('long-secret')
  await page.getByLabel('ещё раз:').fill('long-secret')
  await page.getByRole('button', { name: 'Подтвердить' }).click()
  await expect(accountLink(page)).toBeVisible()
  expect(backend.user).toMatchObject({ permanent_password: true, password: 'long-secret' })
})

test('email given at registration waits for confirmation', async ({ page, backend }) => {
  await page.goto('/register/')
  await register(page)
  expect(backend.emailLog).toEqual([]) // nothing to confirm before the account exists
  await page.getByPlaceholder('Код из смс').fill(backend.lastSmsCode('+79161234567')!)
  await page.getByRole('button', { name: 'Подтвердить' }).click()
  await expect(accountLink(page)).toBeVisible()

  expect(backend.user).toMatchObject({ email: 'anna@example.com', email_verified: false })
  expect(backend.lastEmailLink('anna@example.com')).toBeDefined()
})
