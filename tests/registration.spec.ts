import { Page } from '@playwright/test'

import { test, expect, accountLink } from './fixtures'
import { focusPhone, typePhone } from './phone'

async function register(page: Page) {
  const phone = page.getByRole('textbox', { name: 'Укажите номер мобильного телефона:' })
  await focusPhone(phone)
  await typePhone(phone, '9161234567')
  await page.getByRole('textbox', { name: 'Адрес электронной почты:' }).fill('anna@example.com')
  await page.getByRole('textbox', { name: 'Фамилия Имя Отчество:' }).fill('Анна Иванова')
  await page.getByRole('checkbox').check()
  await page.getByRole('button', { name: 'Зарегистрироваться' }).click()
}

test('user registers and logs in with a code from SMS', async ({ page, backend }) => {
  await page.goto('/register/')
  await register(page)

  // the login form gets the new phone and asks for the code it sent
  await expect(page).toHaveURL(url => url.pathname === '/login/' &&
    url.searchParams.get('phone') === '+79161234567' && url.searchParams.get('ctx') === 'reg')
  expect(backend.requestsTo('POST', 'users/').map(({ body }) => body)).toEqual([
    expect.objectContaining({ phone: '+79161234567', email: 'anna@example.com', name: 'Анна Иванова' })
  ])
  const code = page.getByPlaceholder('Код из смс')
  await expect(code).toBeVisible()
  await expect(page.getByLabel('Постоянный пароль:')).toBeVisible()

  await code.fill(backend.lastSmsCode('+79161234567')!)
  await page.getByRole('button', { name: 'Продолжить' }).click()
  await expect(page).toHaveURL('/')
  await expect(accountLink(page)).toBeVisible()
  expect(backend.user).toMatchObject({ phone: '+79161234567', name: 'Анна Иванова' })
})

test('registered phone is not registered again', async ({ page, backend }) => {
  backend.addUser({ name: 'Другой покупатель' })
  await page.goto('/register/')
  await register(page)

  await expect(page.getByText('Пользователь с указанным номером уже зарегестрирован')).toBeVisible()
  await expect(page).toHaveURL('/register/')
  expect(backend.findUser('+79161234567')?.name).toBe('Другой покупатель')
  expect(backend.smsLog).toEqual([])
})
