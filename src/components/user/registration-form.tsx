'use client'

import { useState, Fragment, ChangeEvent, SubmitEvent } from 'react'
import Link from 'next/link'
import { useRouter } from 'next/navigation'

import { IconUser } from '@tabler/icons-react'

import { ButtonLoading } from '@/components/loading'
import { buttonClass } from '@/components/ui/button'
import { checkClass, checkInputClass, checkLabelClass, feedbackClass, formTextClass, inputClass } from '@/components/ui/form'
import { getCallbackUrl, validatePermanentPasswords } from '@/components/user/login-form'
import PhoneCodeInput from '@/components/user/phone-code-input'

import { formatPhone } from '@/lib/format'
import { usePhoneInput, isValidPhone } from '@/lib/phone-input'
import { useSession } from '@/lib/session'
import { normalizePhone, HttpError, RegistrationData } from '@/lib/queries'

type FieldErrors = Record<string, string[]>

// Fields of the first step, the backend checks them before it sends a code
const DATA_FIELDS = ['phone', 'email', 'name', 'username']

interface RegistrationFormProps {
  embedded?: string
  onComplete?: () => void
}

async function getErrors(error: unknown): Promise<FieldErrors> {
  if (error instanceof HttpError) {
    if (error.status === 429)
      return { 'non_field_errors': ["Слишком много запросов, попробуйте позже"] }
    if (error.response.headers.get('content-type')?.toLowerCase().includes('application/json')) {
      const errors: FieldErrors = await error.response.json()
      if ('password' in errors) // the backend's name for it
        errors.permanent_password = errors.password
      return errors
    }
    return { 'non_field_errors': [error.statusText] }
  }
  return { 'non_field_errors': [error instanceof Error ? error.message : 'Неизвестная ошибка регистрации'] }
}

// Registration: the data, then the code that the backend sends to the phone. The account is created,
// and the user signed in, only when the code comes back.
export default function RegistrationForm({ embedded = '', onComplete }: RegistrationFormProps) {
  const [consent, setConsent] = useState(false)
  const [isRegisterPending, setRegisterPending] = useState(false)
  const [error, setError] = useState<FieldErrors>({})

  // The data a code was sent for, it is sent again with the code
  const [data, setData] = useState<RegistrationData>()
  const [codeStep, setCodeStep] = useState(false)
  const [delay, setDelay] = useState(-1)
  const [attemptsLeft, setAttemptsLeft] = useState(0)

  const router = useRouter()

  const { register } = useSession()

  const phoneRef = usePhoneInput()

  const handleChange = (e: ChangeEvent<HTMLInputElement>) => {
    const field = e.currentTarget.name
    if (field in error)
      setError(Object.fromEntries(Object.entries(error).filter(([key]) => key !== field)))
    if (field === 'consent')
      setConsent(e.currentTarget.checked)
  }

  const requestCode = async (body: RegistrationData) => {
    setRegisterPending(true)
    const result = await register(body)
    setRegisterPending(false)
    if ('codeSent' in result) {
      setData(body)
      setCodeStep(true)
      setDelay(result.codeSent.retry_after)
      setAttemptsLeft(result.codeSent.attempts_left)
    } else if ('error' in result) {
      const errors = await getErrors(result.error)
      if (DATA_FIELDS.some(field => field in errors))
        setCodeStep(false)
      setError(errors)
    }
  }

  const handleDataSubmit = async (e: SubmitEvent<HTMLFormElement>) => {
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
    const body: RegistrationData = Object.fromEntries(DATA_FIELDS.map(field => [field, String(formData.get(field) ?? '')]))
    body.phone = normalizePhone(phone)
    await requestCode(body)
  }

  const handleCodeSubmit = async (e: SubmitEvent<HTMLFormElement>) => {
    e.preventDefault()
    if (data === undefined)
      return
    setError({})
    const formData = new FormData(e.currentTarget)
    const code = String(formData.get('code') ?? '')
    const password = String(formData.get('permanent_password') ?? '')
    const err: Record<string, string> = validatePermanentPasswords(password, String(formData.get('permanent_password2') ?? ''))
    if (!/^\d{6}$/.test(code))
      err.code = "Указан неверный код"
    if (Object.keys(err).length > 0) {
      setError(Object.fromEntries(Object.entries(err).map(([field, message]) => [field, [message]])))
      return
    }
    setRegisterPending(true)
    const result = await register({ ...data, code, ...(password ? { password } : {}) })
    if ('user' in result) { // signed in, stays pending while the page changes
      if (embedded) {
        if (onComplete)
          onComplete()
      } else {
        router.push(getCallbackUrl(new URLSearchParams(window.location.search).get('callbackUrl')))
      }
      return
    }
    setRegisterPending(false)
    if ('error' in result) {
      const errors = await getErrors(result.error)
      if ('code' in errors)
        setAttemptsLeft(attempts => attempts - 1)
      if (DATA_FIELDS.some(field => field in errors)) // taken meanwhile
        setCodeStep(false)
      setError(errors)
    }
  }

  const resendCode = () => {
    if (data === undefined)
      return
    setDelay(-1)
    setError({})
    requestCode(data)
  }

  const changeData = () => {
    setCodeStep(false)
    setDelay(-1)
    setError({})
  }

  const errorMessages = error['non_field_errors']?.map((err, index) => (
    <Fragment key={index}>
      <div className="text-danger">Ошибка: </div>
      <div className="mb-4 w-full text-xs text-danger">{err}</div>
    </Fragment>
  ))

  if (codeStep && data !== undefined)
    return (
      <form onSubmit={handleCodeSubmit} noValidate>
        {errorMessages}
        <div className="mb-2 text-xl font-light">{formatPhone(data.phone)}</div>
        <div className="-mt-2 mb-4 text-xs text-muted">
          <a className="text-primary hover:text-link-hover" onClick={changeData}>Изменить данные</a>
        </div>
        <div className="mb-4">
          <PhoneCodeInput
            id={`${embedded}reg-code-input`}
            delay={delay}
            attemptsLeft={attemptsLeft}
            error={error['code']?.[0]}
            className={embedded ? '' : 'max-w-80'}
            onChange={handleChange}
            onResend={resendCode} />
        </div>
        <div className="grid gap-x-7.5 md:grid-cols-2">
          <div className="mb-4">
            <label className="inline-block" htmlFor={`${embedded}reg-password-input`}>Постоянный пароль:</label>
            <input
              type="password"
              className={inputClass({ size: 'sm', invalid: !!error['permanent_password'] })}
              name="permanent_password"
              id={`${embedded}reg-password-input`}
              onChange={handleChange}
              autoComplete="new-password" />
            {error['permanent_password']?.map((err, index) => (
              <div className={feedbackClass} key={index}>{err}</div>
            ))}
            <span className={formTextClass}>Если Вы не укажете постоянный пароль, вход будет осуществляться с помощью смс</span>
          </div>
          <div className="mb-4">
            <label className="inline-block" htmlFor={`${embedded}reg-password-input2`}>ещё раз:</label>
            <input
              type="password"
              className={inputClass({ size: 'sm', invalid: !!error['permanent_password2'] })}
              name="permanent_password2"
              id={`${embedded}reg-password-input2`}
              onChange={handleChange}
              autoComplete="new-password" />
            {error['permanent_password2']?.map((err, index) => (
              <div className={feedbackClass} key={index}>{err}</div>
            ))}
          </div>
        </div>
        <div className="text-end">
          <button className={`${buttonClass({ shadow: !!embedded })} ms-6`} type="submit" disabled={isRegisterPending}>
            {!embedded && <IconUser size={16} stroke={1.5} className="-ms-1 me-2" />}
            Подтвердить
            {isRegisterPending && <ButtonLoading />}
          </button>
        </div>
      </form>
    )

  return (
    <form onSubmit={handleDataSubmit} noValidate>
      {errorMessages}
      <div className="mb-4">
        <label className="inline-block" htmlFor={`${embedded}reg-phone-input`}>Укажите номер мобильного телефона:</label>
        <input
          type="tel"
          name="phone"
          className={inputClass({ invalid: !!error['phone'] })}
          ref={phoneRef}
          id={`${embedded}reg-phone-input`}
          placeholder="+7 (999) 111-22-33"
          defaultValue={data?.phone}
          onChange={handleChange}
          autoComplete="tel"
          required />
        {error['phone']?.map((err, index) => (
          <div className={feedbackClass} key={index}>{err}</div>
        ))}
        <small className={formTextClass}>на него придёт код для подтверждения</small>
      </div>
      <div className="mb-4">
        <label className="inline-block" htmlFor={`${embedded}reg-email-input`}>Адрес электронной почты:</label>
        <input
          type="email"
          className={inputClass({ invalid: !!error['email'] })}
          name="email"
          id={`${embedded}reg-email-input`}
          defaultValue={data?.email}
          onChange={handleChange}
          autoComplete="email" />
        {error['email']?.map((err, index) => (
          <div className={feedbackClass} key={index}>{err}</div>
        ))}
        <small className={formTextClass}>опционально, на него придёт ссылка для подтверждения</small>
      </div>
      <div className="mb-4">
        <label className="inline-block" htmlFor={`${embedded}reg-name-input`}>Фамилия Имя Отчество:</label>
        <input
          type="text"
          className={inputClass({ invalid: !!error['name'] })}
          name="name"
          id={`${embedded}reg-name-input`}
          defaultValue={data?.name}
          onChange={handleChange}
          autoComplete="name" />
        {error['name']?.map((err, index) => (
          <div className={feedbackClass} key={index}>{err}</div>
        ))}
        <small className={formTextClass}>если Вы планируете оформлять заказы</small>
      </div>
      <div className="mb-4">
        <label className="inline-block" htmlFor={`${embedded}reg-username-input`}>Псевдоним для отзывов:</label>
        <input
          type="text"
          className={inputClass({ invalid: !!error['username'] })}
          name="username"
          id={`${embedded}reg-username-input`}
          defaultValue={data?.username}
          onChange={handleChange} />
        {error['username']?.map((err, index) => (
          <div className={feedbackClass} key={index}>{err}</div>
        ))}
        <small className={formTextClass}>если Вы не хотите, чтобы Ваше настоящее имя отображалось в отзывах</small>
      </div>
      <div className={`${checkClass()} mb-4`}>
        <input
          type="checkbox"
          className={checkInputClass({ invalid: !!error['consent'] })}
          name="consent"
          id={`${embedded}sw-consent-check`}
          checked={consent}
          onChange={handleChange} />
        {" "}
        <label className={checkLabelClass} htmlFor={`${embedded}sw-consent-check`}>
          Я даю{" "}
          <Link href="/pages/personaldata/">
            согласие на обработку персональных данных
          </Link>
        </label>
        {error['consent']?.map((err, index) => (
          <div className={feedbackClass} key={index}>{err}</div>
        ))}
      </div>
      <div className="text-end">
        <button className={`${buttonClass({ shadow: !!embedded })} ms-6`} type="submit" disabled={isRegisterPending}>
          {!embedded && <IconUser size={16} stroke={1.5} className="-ms-1 me-2" />}
          Зарегистрироваться
          {isRegisterPending && <ButtonLoading />}
        </button>
      </div>
    </form>
  )
}
