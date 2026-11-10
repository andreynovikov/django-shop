import { test, expect } from './fixtures'

test('user edits the profile', async ({ page, backend }) => {
  const user = backend.signIn({ name: 'Анна' })
  await page.goto('/user/profile/')

  // the form is shown once the user and the form fields are loaded
  const name = page.getByLabel('Имя:', { exact: true })
  await expect(name).toHaveValue('Анна')
  // the stored phone is formatted by the mask as soon as the form is shown
  await expect(page.getByLabel('Телефон:', { exact: true })).toHaveValue('+7 (916) 123-45-67')
  await name.fill('Анна Иванова')
  await page.getByLabel('Эл.почта:', { exact: true }).fill('anna@example.com')
  await page.getByLabel('Адрес:', { exact: true }).fill('Москва, Тверская, 1')
  await page.getByRole('button', { name: 'Сохранить' }).click()

  await expect(page.getByRole('alert').filter({ hasText: 'Изменения успешно сохранены.' })).toBeVisible()
  const changes = { name: 'Анна Иванова', email: 'anna@example.com', address: 'Москва, Тверская, 1' }
  expect(backend.requestsTo('PUT', `users/${user.id}/`).map(({ body }) => body)).toEqual([
    expect.objectContaining({ ...changes, phone: '+79161234567' }),
  ])
  expect(backend.user).toMatchObject(changes)
  // the account menu shows the new name
  await expect(page.locator('aside h3')).toHaveText('Анна Иванова')
  // the new address waits for the link sent to it
  expect(backend.user?.email_verified).toBe(false)
  expect(backend.lastEmailLink('anna@example.com')).toBeDefined()
  await expect(page.getByText('Адрес не подтверждён: перейдите по ссылке из письма.')).toBeVisible()
})

test('new phone is saved with a code sent to it', async ({ page, backend }) => {
  const user = backend.signIn({ name: 'Анна' })
  await page.goto('/user/profile/')

  const phone = page.getByLabel('Телефон:', { exact: true })
  await expect(phone).toHaveValue('+7 (916) 123-45-67')
  await phone.fill('+7 (916) 765-43-21')
  await page.getByLabel('Имя:', { exact: true }).fill('Анна Иванова')
  await page.getByRole('button', { name: 'Сохранить' }).click()

  // nothing is saved until the code comes back
  const code = page.getByLabel('Код из смс, отправленного на новый номер:')
  await expect(code).toBeVisible()
  expect(backend.smsLog.map(({ phone }) => phone)).toEqual(['+79167654321'])
  expect(backend.user).toMatchObject({ phone: '+79161234567', name: 'Анна' })

  await code.fill(backend.lastSmsCode('+79167654321') === '000000' ? '111111' : '000000')
  await page.getByRole('button', { name: 'Сохранить' }).click()
  await expect(page.getByText('Неверный или устаревший код')).toBeVisible()
  expect(backend.user?.phone).toBe('+79161234567')

  await code.fill(backend.lastSmsCode('+79167654321')!)
  await page.getByRole('button', { name: 'Сохранить' }).click()
  await expect(page.getByRole('alert').filter({ hasText: 'Изменения успешно сохранены.' })).toBeVisible()
  await expect(code).toBeHidden()
  expect(backend.user).toMatchObject({ phone: '+79167654321', name: 'Анна Иванова', phone_verified: true })
  expect(backend.requestsTo('PUT', `users/${user.id}/`).at(-1)?.body).toMatchObject({ phone: '+79167654321', code: backend.lastSmsCode('+79167654321') })
})

test('code is asked again for a phone typed after it', async ({ page, backend }) => {
  backend.signIn()
  await page.goto('/user/profile/')

  const phone = page.getByLabel('Телефон:', { exact: true })
  await phone.fill('+7 (916) 765-43-21')
  await page.getByRole('button', { name: 'Сохранить' }).click()
  const code = page.getByLabel('Код из смс, отправленного на новый номер:')
  await expect(code).toBeVisible()

  // the code was for the number typed before
  await phone.fill('+7 (916) 000-00-01')
  await expect(code).toBeHidden()
  await page.getByRole('button', { name: 'Сохранить' }).click()
  await expect(code).toBeVisible()
  expect(backend.smsLog.map(({ phone }) => phone)).toEqual(['+79167654321', '+79160000001'])
})

test('unconfirmed address gets the link again', async ({ page, backend }) => {
  const user = backend.signIn({ email: 'anna@example.com', email_verified: false })
  await page.goto('/user/profile/')

  await expect(page.getByText('Адрес не подтверждён: перейдите по ссылке из письма.')).toBeVisible()
  await page.getByText('Отправить письмо ещё раз').click()
  await expect(page.getByText('Письмо отправлено.')).toBeVisible()
  expect(backend.requestsTo('POST', `users/${user.id}/email-link/`)).toHaveLength(1)
  expect(backend.lastEmailLink('anna@example.com')).toBeDefined()
})

test('confirmed address shows no notice', async ({ page, backend }) => {
  backend.signIn({ email: 'anna@example.com' })
  await page.goto('/user/profile/')
  await expect(page.getByLabel('Эл.почта:', { exact: true })).toHaveValue('anna@example.com')
  await expect(page.getByText('Адрес не подтверждён')).toBeHidden()
})
