'use client'

import { useState, SubmitEvent } from 'react'

import { buttonClass } from '@/components/ui/button'
import { feedbackClass, formTextClass, inputClass } from '@/components/ui/form'

import { getWarrantyCard, HttpError } from '@/lib/queries'

type FieldErrors = Record<string, string[]>

// Opens the printable warranty card of the serial number in a new window
export default function WarrantyCardForm() {
  const [error, setError] = useState<FieldErrors>({})

  const handleSubmit = async (e: SubmitEvent<HTMLFormElement>) => {
    e.preventDefault()
    setError({})
    const code = (e.currentTarget.elements.namedItem('code') as HTMLInputElement).value
    if (code === '') {
      setError({ 'code': ["Укажите серийный номер изделия"] })
      return
    }
    try {
      const { html } = await getWarrantyCard(code)
      const newWindow = window.open()
      if (newWindow !== null) {
        newWindow.document.write(html)
        newWindow.document.title = `Гарантийный талон №${code}`
      }
    } catch (error) {
      if (error instanceof HttpError && error.response.headers.get('content-type')?.toLowerCase() === 'application/json')
        setError(await error.response.json())
      else
        setError({ 'non_field_errors': [error instanceof HttpError ? error.statusText : String(error)] })
    }
  }

  return (
    <form onSubmit={handleSubmit} noValidate>
      {error['non_field_errors']?.map((err, index) => (
        <div key={index}>
          <div className="text-danger">Ошибка: </div>
          <div className="mb-4 text-xs text-danger">{err}</div>
        </div>
      ))}
      <div className="mb-4">
        <label htmlFor="id_code">Серийный номер:</label>
        <input
          type="text"
          name="code"
          className={inputClass({ invalid: 'code' in error })}
          maxLength={100}
          required
          id="id_code" />
        {error['code']?.map((err, index) => (
          <div className={feedbackClass} key={index}>{err}</div>
        ))}
        <small className={formTextClass}>Серийный номер можно найти на корпусе изделия или в гарантийном талоне</small>
      </div>
      <input type="submit" className={buttonClass()} value="Распечатать" />
    </form>
  )
}
