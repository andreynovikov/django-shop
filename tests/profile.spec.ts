import { test, expect } from './fixtures'

test('user edits the profile', async ({ page, backend }) => {
  const user = backend.signIn({ name: 'Анна' })
  await page.goto('/user/profile/')

  // the form is shown once the user and the form fields are loaded
  const name = page.getByLabel('Имя:', { exact: true })
  await expect(name).toHaveValue('Анна')
  await name.fill('Анна Иванова')
  await page.getByLabel('Эл.почта:', { exact: true }).fill('anna@example.com')
  await page.getByLabel('Адрес:', { exact: true }).fill('Москва, Тверская, 1')
  await page.getByRole('button', { name: 'Сохранить' }).click()

  await expect(page.locator('.alert-success')).toHaveText('Изменения успешно сохранены.')
  const changes = { name: 'Анна Иванова', email: 'anna@example.com', address: 'Москва, Тверская, 1' }
  expect(backend.requestsTo('PUT', `users/${user.id}/`).map(({ body }) => body)).toEqual([expect.objectContaining(changes)])
  expect(backend.user).toMatchObject(changes)
  // the account menu shows the new name
  await expect(page.locator('aside h3')).toHaveText('Анна Иванова')
})
