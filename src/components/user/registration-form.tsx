'use client'

import { useState, Fragment, ChangeEvent, SubmitEvent } from 'react'
import Link from 'next/link'

import { stringify as stringifyQuery } from 'querystring'

import { ButtonLoading } from '@/components/loading'

import { usePhoneInput, isValidPhone } from '@/lib/phone-input'
import { useSession } from '@/lib/session'
import { useNavigation } from '@/lib/navigation'
import { normalizePhone, HttpError } from '@/lib/queries'

type FieldErrors = Record<string, string[]>

interface RegistrationFormProps {
  embedded?: string
  onComplete?: (phone: string) => void
}

async function getErrors(error: unknown): Promise<FieldErrors> {
  if (error instanceof HttpError) {
    if (error.response.headers.get('content-type')?.toLowerCase().includes('application/json'))
      return await error.response.json()
    return { 'non_field_errors': [error.statusText] }
  }
  return { 'non_field_errors': [error instanceof Error ? error.message : 'Неизвестная ошибка регистрации'] }
}

export default function RegistrationForm({ embedded = '', onComplete }: RegistrationFormProps) {
  const [consent, setConsent] = useState(false)
  const [isRegisterPending, setRegisterPending] = useState(false)
  const [error, setError] = useState<FieldErrors>({})

  const { query, navigate } = useNavigation()

  const { register } = useSession()

  const phoneRef = usePhoneInput()

  const handleChange = (e: ChangeEvent<HTMLInputElement>) => {
    const field = e.currentTarget.name
    if (field in error)
      setError(Object.fromEntries(Object.entries(error).filter(([key]) => key !== field)))
    if (field === 'consent')
      setConsent(e.currentTarget.checked)
  }

  const handleSubmit = async (e: SubmitEvent<HTMLFormElement>) => {
    e.preventDefault()
    setError({})
    const formData = new FormData(e.currentTarget)
    const phone = formData.get('phone') as string
    if (!isValidPhone(phone)) {
      setError({ 'phone': ["Введите корректный номер"] })
      return
    }
    if (!consent) {
      setError({ 'consent': ["Регистрация возможна только после предоставления согласия"] })
      return
    }
    const normalizedPhone = normalizePhone(phone)
    formData.set('phone', normalizedPhone)
    setRegisterPending(true)
    const result = await register(formData)
    if ('error' in result) {
      setError(await getErrors(result.error))
    } else if (!result.ok) {
      setError({ 'non_field_errors': ['Неизвестная ошибка регистрации'] })
    } else if (embedded) {
      if (onComplete)
        onComplete(normalizedPhone)
    } else {
      const params = stringifyQuery({
        ...query,
        phone: normalizedPhone,
        ctx: 'reg'
      })
      navigate(`/login?${params}`)
    }
    setRegisterPending(false)
  }

  return (
    <form onSubmit={handleSubmit} noValidate>
      {error['non_field_errors']?.map((err, index) => (
        <Fragment key={index}>
          <div className="is-invalid text-danger">Ошибка: </div>
          <div className="invalid-feedback mt-0 mb-3">{err}</div>
        </Fragment>
      ))}
      <div className="mb-3">
        <label htmlFor={`${embedded}reg-phone-input`}>Укажите номер мобильного телефона:</label>
        <input
          type="tel"
          name="phone"
          className={"form-control" + (error['phone'] ? " is-invalid" : "")}
          ref={phoneRef}
          id={`${embedded}reg-phone-input`}
          placeholder="+7 (999) 111-22-33"
          onChange={handleChange}
          autoComplete="phone"
          required />
        {error['phone']?.map((err, index) => (
          <div className="invalid-feedback" key={index}>{err}</div>
        ))}
      </div>
      <div className="mb-3">
        <label htmlFor={`${embedded}reg-email-input`}>Адрес электронной почты:</label>
        <input
          type="email"
          className={"form-control" + (error['email'] ? " is-invalid" : "")}
          name="email"
          id={`${embedded}reg-email-input`}
          onChange={handleChange}
          autoComplete="email" />
        {error['email']?.map((err, index) => (
          <div className="invalid-feedback" key={index}>{err}</div>
        ))}
        <small className="form-text text-muted">опционально</small>
      </div>
      <div className="mb-3">
        <label htmlFor={`${embedded}reg-name-input`}>Фамилия Имя Отчество:</label>
        <input
          type="text"
          className={"form-control" + (error['name'] ? " is-invalid" : "")}
          name="name"
          id={`${embedded}reg-name-input`}
          onChange={handleChange}
          autoComplete="name" />
        {error['name']?.map((err, index) => (
          <div className="invalid-feedback" key={index}>{err}</div>
        ))}
        <small className="form-text text-muted">если Вы планируете оформлять заказы</small>
      </div>
      <div className="mb-3">
        <label htmlFor={`${embedded}reg-username-input`}>Псевдоним для отзывов:</label>
        <input
          type="text"
          className={"form-control" + (error['username'] ? " is-invalid" : "")}
          name="username"
          id={`${embedded}reg-username-input`}
          onChange={handleChange} />
        {error['username']?.map((err, index) => (
          <div className="invalid-feedback" key={index}>{err}</div>
        ))}
        <small className="form-text text-muted">если Вы не хотите, чтобы Ваше настоящее имя отображалось в отзывах</small>
      </div>
      <div className="form-check mb-3">
        <input
          type="checkbox"
          className={"form-check-input" + (error['consent'] ? " is-invalid" : "")}
          name="consent"
          id="sw-consent-check"
          checked={consent}
          onChange={handleChange} />
        {" "}
        <label className="form-check-label" htmlFor="sw-consent-check">
          Я даю{" "}
          <Link href="/pages/personaldata/">
            согласие на обработку персональных данных
          </Link>
        </label>
        {error['consent']?.map((err, index) => (
          <div className="invalid-feedback" key={index}>{err}</div>
        ))}
      </div>
      <div className="text-end">
        <button className={"btn btn-primary ms-4" + (embedded ? " btn-shadow" : "")} type="submit" disabled={isRegisterPending}>
          {!embedded && <i className="ci-user me-2 ms-n1" />}
          Зарегистрироваться
          {isRegisterPending && <ButtonLoading />}
        </button>
      </div>
    </form>
  )
}
