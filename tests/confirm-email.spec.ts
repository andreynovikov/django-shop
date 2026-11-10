import { test, expect } from './fixtures'

test('link from the email confirms the address', async ({ page, backend }) => {
  // the account is not signed in on this device: the link works without a session
  backend.addUser({ email: 'anna@example.com', email_verified: false })
  backend.emailLog.push({ user: backend.findUser('+79161234567')!.id, email: 'anna@example.com', token: 'good-token' })
  await page.goto('/confirm-email/?token=good-token')

  await expect(page.getByRole('alert').filter({ hasText: 'Адрес anna@example.com подтверждён' })).toBeVisible()
  expect(backend.findUser('+79161234567')?.email_verified).toBe(true)
  // React runs effects twice in development, the token is still sent once
  expect(backend.requestsTo('POST', 'users/confirm-email/').map(({ body }) => body)).toEqual([{ token: 'good-token' }])
})

test('signed in user sees the address confirmed in the profile', async ({ page, backend }) => {
  backend.signIn({ email: 'anna@example.com', email_verified: false })
  await page.goto('/user/profile/')
  await page.getByText('Отправить письмо ещё раз').click()
  await expect(page.getByText('Письмо отправлено.')).toBeVisible()

  await page.goto(backend.lastEmailLink('anna@example.com')!)
  await expect(page.getByRole('alert').filter({ hasText: 'подтверждён' })).toBeVisible()
  await page.getByRole('link', { name: 'профиль' }).click()
  await expect(page.getByLabel('Эл.почта:', { exact: true })).toHaveValue('anna@example.com')
  await expect(page.getByText('Адрес не подтверждён')).toBeHidden()
})

for (const url of ['/confirm-email/?token=bad-token', '/confirm-email/']) {
  test(`bad link is refused: ${url}`, async ({ page, backend }) => {
    backend.addUser({ email: 'anna@example.com', email_verified: false })
    await page.goto(url)
    await expect(page.getByRole('alert').filter({ hasText: 'Ссылка недействительна или устарела.' })).toBeVisible()
    expect(backend.findUser('+79161234567')?.email_verified).toBe(false)
  })
}
