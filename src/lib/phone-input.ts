import type { MaskitoOptions, MaskitoPreprocessor } from '@maskito/core'
import {
  maskitoAddOnFocusPlugin,
  maskitoCaretGuard,
  maskitoPrefixPostprocessorGenerator,
  maskitoRemoveOnBlurPlugin,
} from '@maskito/kit'
import { useMaskito } from '@maskito/react'
import parsePhoneNumber from 'libphonenumber-js'

const phoneInputOptions = {
  mask: [
    '+', '7', ' ', '(', /\d/, /\d/, /\d/, ')', ' ', /\d/, /\d/, /\d/, '-', /\d/, /\d/, '-', /\d/, /\d/,
  ],
  postprocessors: [
    // Non-removable country prefix
    maskitoPrefixPostprocessorGenerator('+7 '),
  ],
  preprocessors: [createCompletePhoneInsertionPreprocessor()],
  plugins: [
    maskitoAddOnFocusPlugin('+7 '),
    maskitoRemoveOnBlurPlugin('+7 '),
    // Forbids putting caret before non-removable country prefix, but allows selection of full value
    maskitoCaretGuard((value, [from, to]) => [
      from === to ? '+7 '.length : 0,
      value.length,
    ]),
  ],
} satisfies MaskitoOptions

// Paste "89123456789" => "+7 (912) 345-67-89"
function createCompletePhoneInsertionPreprocessor(): MaskitoPreprocessor {
  const trimPrefix = (value: string): string => value.replace(/^(\+?7|8)\s?/, '')
  const countDigits = (value: string): number => value.replaceAll(/\D/g, '').length

  return ({ elementState, data }) => {
    const { value, selection } = elementState

    return {
      elementState: {
        selection,
        value: countDigits(value) > 11 ? trimPrefix(value) : value,
      },
      data: countDigits(data) >= 11 ? trimPrefix(data) : data,
    }
  }
}

export function usePhoneInput() {
  return useMaskito({ options: phoneInputOptions })
}

export function isValidPhone(value: string) {
  const phoneNumber = parsePhoneNumber(value, 'RU')
  return phoneNumber && phoneNumber.isValid()
}