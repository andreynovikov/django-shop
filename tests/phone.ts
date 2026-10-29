import { expect, Locator, Page } from '@playwright/test'

// Phone inputs are masked with Maskito, these helpers enter a number the ways a user can

// The mask is attached on hydration, it puts the country code into an empty input on focus
export async function focusPhone(input: Locator) {
  await expect(async () => {
    await input.click()
    await expect(input).toHaveValue('+7 ', { timeout: 1000 })
  }).toPass()
}

export async function typePhone(input: Locator, digits: string) {
  await input.click()
  await input.pressSequentially(digits)
}

// Copies the text with the keyboard, so the input gets a real paste from the clipboard
export async function pastePhone(page: Page, input: Locator, text: string) {
  await page.evaluate((text) => {
    const source = document.createElement('textarea')
    source.id = 'sw-test-clipboard'
    source.value = text
    document.body.append(source)
    source.focus()
    source.select()
  }, text)
  await page.keyboard.press('ControlOrMeta+C')
  await page.evaluate(() => document.getElementById('sw-test-clipboard')?.remove())
  await input.click()
  await page.keyboard.press('ControlOrMeta+V')
}

// Chrome autofill sets the value without a beforeinput event and fires an input event without inputType
export async function autofillPhone(input: Locator, value: string) {
  await input.focus()
  await input.evaluate((element: HTMLInputElement, value) => {
    Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, 'value')!.set!.call(element, value)
    element.dispatchEvent(new Event('input', { bubbles: true }))
  }, value)
}
