'use client'

import { useState, useEffect, ChangeEvent, SubmitEvent } from 'react'
import Link from 'next/link'
import { useMutation } from '@tanstack/react-query'
import { stringify as stringifyQuery } from 'querystring'

import Countdown from '@/components/countdown'
import { ButtonLoading } from '@/components/loading'

import { formatPhone } from '@/lib/format'
import { usePhoneInput, isValidPhone } from '@/lib/phone-input'
import { useSession } from '@/lib/session'
import { useNavigation } from '@/lib/navigation'
import { checkUser, normalizePhone, HttpError, LoginCredentials } from '@/lib/queries'

const CODE_RESEND_DELAY = 240

type FieldErrors = Record<string, string>

interface LoginFormProps {
  ctx: string
  phone?: string
  hideModal?: () => void
  embedded?: string
}

// signIn returns error response body as text
function getError(field: string, error: unknown): FieldErrors {
  let data = error
  if (typeof error === 'string') {
    try {
      data = JSON.parse(error)
    } catch {
      // not a JSON response
    }
  }
  if (data !== null && typeof data === 'object' && !(data instanceof Error)) {
    const errors = data as Record<string, unknown>
    if (Array.isArray(errors[field]))
      return { [field]: errors[field][0] }
    else if (Array.isArray(errors.non_field_errors))
      return { [field]: errors.non_field_errors[0] }
    else if (typeof errors.detail === 'string')
      return { [field]: errors.detail }
  }
  if (data)
    return { [field]: String(data) }
  return { [field]: "Неизвестная ошибка входа" }
}

// Only paths on this site, so a link to the login page can't send the user to another site
function getCallbackUrl(callbackUrl: unknown) {
  if (typeof callbackUrl === 'string' && callbackUrl.startsWith('/') && !/^\/[/\\]/.test(callbackUrl))
    return callbackUrl
  return '/'
}

export default function LoginForm({ ctx, phone, hideModal, embedded = '' }: LoginFormProps) {
  const [pdConsent, setPdConsent] = useState(false)
  const [ofConsent, setOfConsent] = useState(false)
  const [isSignInPending, setSignInPending] = useState(false)
  const [error, setError] = useState<FieldErrors>({})

  const [delay, setDelay] = useState(-1) // TODO: keep delay on page reload

  const [showPermanentPassword, setShowPermanentPassword] = useState(ctx === 'reg')

  const { query, navigate } = useNavigation()
  const { signIn } = useSession()

  const {
    mutate: performUserCheck,
    reset: resetUserCheck,
    data: shopUser,
    isIdle,
    isPending: isUserCheckPending
  } = useMutation({
    mutationFn: ({ phone, reset }: { phone: string, reset: boolean }) => checkUser(phone, reset),
    onSuccess: (data) => {
      setDelay(data.permanent_password ? 0 : CODE_RESEND_DELAY)
    },
    onError: async (error, { phone }) => {
      console.log(error)
      if (error instanceof HttpError && error.status === 404) {
        if (['order', 'preorder', 'warranty'].includes(ctx)) {
          setSignInPending(true)
          // register user in background when making order or registering warranty
          const result = await signIn({ phone, ctx })
          if (result.ok) {
            if (embedded && hideModal)
              hideModal()
          } else {
            setError(getError('phone', 'error' in result ? result.error : undefined))
          }
          setSignInPending(false)
        } else {
          setError({ phone: "Пользователь с таким телефоном не зарегистрирован" })
        }
      }
    }
  })

  useEffect(() => {
    if (phone && isIdle)
      performUserCheck({ phone, reset: false })
  }, [phone, performUserCheck, isIdle])

  const phoneRef = usePhoneInput()

  const validatePhone = (value: string): FieldErrors => {
    return isValidPhone(value) ?
      {} : { phone: "Введите корректный номер" }
  }

  const validatePassword = (value: string): FieldErrors => {
    if (!/^(:?\d{4}|.{5,30})$/.test(value))
      return { password: "Указан неверный " + (shopUser?.permanent_password ? "пароль" : "код") }
    else
      return {}
  }

  const validatePermanentPasswords = (value1: string, value2: string) => {
    const err: FieldErrors = {}
    if (value1 != value2)
      err['permanent_password2'] = "Пароли не совпадают"
    if (value1.length > 0 && value1.length < 5)
      err['permanent_password'] = "Постоянный пароль должен быть не менее 5 символов"
    return err
  }

  const handleChange = (e: ChangeEvent<HTMLInputElement>) => {
    const field = e.currentTarget.name
    if (field in error)
      setError(Object.fromEntries(Object.entries(error).filter(([key]) => key !== field)))
    if (field === 'pd-consent')
      setPdConsent(e.currentTarget.checked)
    if (field === 'of-consent')
      setOfConsent(e.currentTarget.checked)
  }

  const handleSubmit = async (e: SubmitEvent<HTMLFormElement>) => {
    e.preventDefault()
    setError({})
    let err: FieldErrors = {}
    const formData = new FormData(e.currentTarget)
    const phone = formData.get('phone') as string | null
    const password = formData.get('password') as string | null
    const permanentPassword = formData.get('permanent_password') as string ?? ''
    const permanentPassword2 = formData.get('permanent_password2') as string ?? ''

    if (['order', 'preorder', 'warranty'].includes(ctx)) {
      if (!pdConsent)
        err = { ...err, 'pd-consent': "Продолжение возможно только после предоставления согласия" }
      if (ctx === 'order' && !ofConsent)
        err = { ...err, 'of-consent': "Оформление заказа возможно только после подтверждения согласия" }
    }

    if (phone !== null) {
      err = { ...err, ...validatePhone(phone) }
      if (Object.keys(err).length > 0) {
        setError(err)
      } else {
        performUserCheck({ phone: normalizePhone(phone), reset: false })
      }
    } else if (password !== null && shopUser !== undefined) {
      err = { ...err, ...validatePassword(password) }
      if (showPermanentPassword)
        err = { ...err, ...validatePermanentPasswords(permanentPassword, permanentPassword2) }
      if (Object.keys(err).length > 0) {
        setError(err)
      } else {
        const credentials: LoginCredentials = {
          phone: shopUser.phone,
          password,
        }
        if (showPermanentPassword && permanentPassword.length > 0)
          credentials.permanent_password = permanentPassword
        setSignInPending(true)
        const result = await signIn(credentials)
        setSignInPending(false)
        if (result.ok) {
          if (embedded) {
            if (hideModal)
              hideModal()
          } else {
            navigate(getCallbackUrl(query.callbackUrl))
          }
        } else if ('status' in result && [401, 403].includes(result.status)) {
          setError({ password: "Вы ввели неправильный " + (shopUser.permanent_password ? "пароль" : "код") })
        } else {
          setError(getError('password', 'error' in result ? result.error : undefined))
        }
      }
    }
  }

  const resetPhone = () => {
    setDelay(-1)
    setError({})
    resetUserCheck()
  }

  const resetPassword = () => {
    if (shopUser === undefined)
      return
    setDelay(-1)
    performUserCheck({ phone: shopUser.phone, reset: true })
  }

  const isPending = isSignInPending || isUserCheckPending

  return (
    <form onSubmit={handleSubmit} noValidate>
      {shopUser !== undefined ? (
        <>
          { /* Пользователь с таким телефоном уже есть, требуем подтверждение пароля */}
          <div className="lead mb-2">{formatPhone(shopUser.phone)}</div>
          {ctx === 'order' && (
            <div className="form-text mt-n2 mb-3">
              <a className="link-primary" onClick={resetPhone} style={{ cursor: 'pointer' }}>Указать другой телефон</a>
            </div>
          )}
          <div className="mb-3 has-feedback">
            <input
              type="password"
              name="password"
              className={"form-control" + ('password' in error ? " is-invalid" : "")}
              style={embedded ? {} : { maxWidth: "20rem" }}
              id={`${embedded}${ctx}-password-input`}
              placeholder={shopUser.permanent_password ? "Пароль" : "Код из смс"}
              onChange={handleChange}
              required
              autoFocus />
            {'password' in error && <div className="invalid-feedback">{error.password}</div>}
            <div className="form-text">
              <Countdown delay={delay} permanentPassword={shopUser.permanent_password} reset={resetPassword} />
            </div>
          </div>
          {!['order', 'preorder', 'warranty'].includes(ctx) && !shopUser.permanent_password && (
            showPermanentPassword ? (
              <div className="row">
                <div className="mb-3 col-md">
                  <label htmlFor="permanent-password-input">Постоянный пароль:</label>
                  <input
                    type="password"
                    className={"form-control form-control-sm" + ('permanent_password' in error ? " is-invalid" : "")}
                    name="permanent_password"
                    id="permanent-password-input" />
                  {'permanent_password' in error && <div className="invalid-feedback">{error.permanent_password}</div>}
                  {ctx === 'reg' && (
                    <span className="form-text">Если Вы не укажете постоянный пароль, вход будет осуществляться с помощью смс</span>
                  )}
                </div>
                <div className="mb-3 col-md">
                  <label htmlFor="permanent-password-input2">ещё раз:</label>
                  <input
                    type="password"
                    className={"form-control form-control-sm" + ('permanent_password2' in error ? " is-invalid" : "")}
                    name="permanent_password2"
                    id="permanent-password-input2" />
                  {'permanent_password2' in error && <div className="invalid-feedback">{error.permanent_password2}</div>}
                </div>
              </div>
            ) : (
              <div className="mb-3 fs-md">
                Вы можете <a onClick={() => setShowPermanentPassword(true)}>указать постоянный пароль</a>, чтобы не получать каждый раз смс
              </div>
            )
          )}
        </>
      ) : (
        <>
          { /* Анонимный пользователь */}
          <div className="mb-3">
            <label className="lead" htmlFor={`${embedded}${ctx}-phone-input`}>
              {ctx === 'order' ? "Для продолжения у" : "У"}
              кажите номер мобильного телефона:
            </label>
            <input
              type="tel"
              name="phone"
              className={"form-control" + ('phone' in error ? " is-invalid" : "")}
              ref={phoneRef}
              id={`${embedded}${ctx}-phone-input`}
              placeholder="+7 (999) 111-22-33"
              onChange={handleChange}
              autoComplete="tel"
              required />
            {'phone' in error && <div className="invalid-feedback">{error.phone}</div>}
          </div>
        </>
      )}

      {['order', 'preorder', 'warranty'].includes(ctx) && (
        <>
          <div className="form-check mb-3">
            <input
              type="checkbox"
              className={"form-check-input" + ('pd-consent' in error ? " is-invalid" : "")}
              name="pd-consent"
              id="sw-pd-consent-check"
              checked={pdConsent}
              onChange={handleChange} />
            {" "}
            <label className="form-check-label" htmlFor="sw-pd-consent-check">
              Я даю{" "}
              <Link href="/pages/personaldata/">
                согласие на обработку персональных данных
              </Link>
            </label>
            {'pd-consent' in error && <div className="invalid-feedback">{error['pd-consent']}</div>}
          </div>
          {ctx === 'order' && (
            <div className="form-check mb-3">
              <input
                type="checkbox"
                className={"form-check-input" + ('of-consent' in error ? " is-invalid" : "")}
                name="of-consent"
                id="sw-of-consent-check"
                checked={ofConsent}
                onChange={handleChange} />
              {" "}
              <label className="form-check-label" htmlFor="sw-of-consent-check">
                Я подтверждаю согласие с{" "}
                <Link href="/pages/oferta/">
                  условиями публичной оферты
                </Link>
              </label>
              {'of-consent' in error && <div className="invalid-feedback">{error['of-consent']}</div>}
            </div>
          )}
        </>
      )}
      {ctx === 'order' ? (
        <button className="btn btn-primary btn-shadow d-block w-100 mt-4" disabled={isPending}>
          <i className={"fs-lg me-2 " + (shopUser ? "ci-sign-in" : "ci-basket-alt")} />Оформить заказ
          {isPending && <ButtonLoading />}
        </button>
      ) : ctx === 'preorder' ? (
        <button className="btn btn-primary btn-shadow d-block w-100 mt-4" disabled={isPending}>
          <i className={"fs-lg me-2 " + (shopUser ? "ci-sign-in" : "ci-basket-alt")} />Оформить запрос о поступлении
          {isPending && <ButtonLoading />}
        </button>
      ) : ctx === 'warranty' ? (
        <button className="btn btn-primary btn-shadow d-block mt-4" disabled={isPending}>
          <i className={"fs-lg me-2 " + (shopUser ? "ci-sign-in" : "ci-unlocked")} />Продолжить
          {isPending && <ButtonLoading />}
        </button>
      ) : (
        <div className="text-end">
          <button className={"btn btn-primary ms-4" + (embedded ? " btn-shadow" : "")} type="submit" disabled={isPending}>
            {!embedded && <i className={"me-2 ms-n1 " + (shopUser ? "ci-sign-in" : "ci-unlocked")} />}
            {!!shopUser ? "Продолжить" : "Войти"}
            {isPending && <ButtonLoading />}
          </button>
        </div>
      )}
      {!shopUser && !embedded && (
        <div className="mt-4 fs-md">
          Если Вы не совершали покупок в магазине, Вы можете{" "}
          <Link href={`/register?${stringifyQuery(query)}`}>
            зарегистрироваться
          </Link>
        </div>
      )}
    </form>
  )
}