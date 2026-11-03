import { test, expect, gotoHydrated } from './fixtures'
import { focusPhone, typePhone } from './phone'

const registered = 'Серийный номер SN123456 зарегистрирован. После проверки информация о нём будет доступна в личном кабинете.'

test('anonymous owner extends the warranty with a new phone', async ({ page, backend }) => {
  await gotoHydrated(page, '/warranty/extend/')
  await expect(page).toHaveTitle('Расширение гарантии - Швейный Мир')
  await expect(page.getByRole('heading', { level: 1 })).toHaveText('Расширение гарантии')
  await page.getByPlaceholder('Серийный номер').fill('SN123456')
  await page.getByRole('button', { name: 'Продлить' }).click()

  const phone = page.getByRole('textbox', { name: 'Укажите номер мобильного телефона:' })
  await focusPhone(phone)
  await typePhone(phone, '9161234567')
  await page.getByRole('checkbox', { name: /согласие на обработку персональных данных/ }).check()
  await page.getByRole('button', { name: 'Продолжить' }).click()

  await expect(page.getByText(registered)).toBeVisible()
  // a new owner is registered silently, like a new buyer
  expect(backend.requestsTo('POST', 'users/login/').map(({ body }) => body)).toEqual([{ phone: '+79161234567', ctx: 'warranty' }])
  expect(backend.smsLog).toEqual([])
  expect(backend.requestsTo('POST', 'serials/').map(({ body }) => body)).toEqual([{ number: 'SN123456' }])
})

test('signed in owner extends the warranty right away', async ({ page, backend }) => {
  backend.signIn()
  await gotoHydrated(page, '/warranty/extend/')
  await page.getByPlaceholder('Серийный номер').fill('SN123456')
  await page.getByRole('button', { name: 'Продлить' }).click()

  await expect(page.getByText(registered)).toBeVisible()
  expect(backend.requestsTo('POST', 'serials/').map(({ body }) => body)).toEqual([{ number: 'SN123456' }])
})
