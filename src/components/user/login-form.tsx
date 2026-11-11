'use client'

import { useState, ChangeEvent, SubmitEvent, Suspense } from 'react'
import Link from 'next/link'
import { useRouter, useSearchParams } from 'next/navigation'
import { useMutation } from '@tanstack/react-query'

import { IconBasket, IconLockOpen, IconLogin2 } from '@tabler/icons-react'

import Countdown from '@/components/countdown'
import { ButtonLoading } from '@/components/loading'
import { buttonClass } from '@/components/ui/button'
import { checkClass, checkInputClass, checkLabelClass, feedbackClass, formTextClass, inputClass } from '@/components/ui/form'

import { formatPhone } from '@/lib/format'
import { usePhoneInput, isValidPhone } from '@/lib/phone-input'
import { useSession } from '@/lib/session'
import { checkUser, normalizePhone, HttpError, LoginCredentials } from '@/lib/queries'

type FieldErrors = Record<string, string>

interface LoginFormProps {
  ctx: string
  hideModal?: () => void
  embedded?: string
}

// For new passwords only: older, shorter ones still log in
export const PERMANENT_PASSWORD_LENGTH = 8

export function validatePermanentPasswords(value1: string, value2: string) {
  const err: FieldErrors = {}
  if (value1 != value2)
    err['permanent_password2'] = "Пароли не совпадают"
  if (value1.length > 0 && value1.length < PERMANENT_PASSWORD_LENGTH)
    err['permanent_password'] = `Постоянный пароль должен быть не менее ${PERMANENT_PASSWORD_LENGTH} символов`
  return err
}

// signIn returns error response body as text
export function getError(field: string, error: unknown): FieldErrors {
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

// Only paths on this site, so a link to the login page can't send the user to another site.
// The origin is compared after parsing, because browsers drop tabs and newlines: '/\t/example.com' is //example.com
export function getCallbackUrl(callbackUrl: unknown) {
  if (typeof callbackUrl === 'string') {
    try {
      const url = new URL(callbackUrl, window.location.origin)
      if (url.origin === window.location.origin)
        return url.pathname + url.search + url.hash
    } catch {
      // not a URL
    }
  }
  return '/'
}

// Passes the query on, the callback URL in it. The static page has the link without it until hydration
function RegisterLink() {
  const query = useSearchParams().toString()
  return <Link href={`/register/${query ? `?${query}` : ''}`}>зарегистрироваться</Link>
}

export default function LoginForm({ ctx, hideModal, embedded = '' }: LoginFormProps) {
  const [pdConsent, setPdConsent] = useState(false)
  const [ofConsent, setOfConsent] = useState(false)
  const [isSignInPending, setSignInPending] = useState(false)
  const [error, setError] = useState<FieldErrors>({})

  const [delay, setDelay] = useState(-1)
  const [codeAttemptsLeft, setCodeAttemptsLeft] = useState(0)

  const [showPermanentPassword, setShowPermanentPassword] = useState(false)

  const router = useRouter()
  const { signIn } = useSession()

  const {
    mutate: performUserCheck,
    reset: resetUserCheck,
    data: shopUser,
    isPending: isUserCheckPending
  } = useMutation({
    mutationFn: ({ phone, reset }: { phone: string, reset: boolean }) => checkUser(phone, reset),
    onSuccess: (data) => {
      setDelay(data.retry_after)
      setCodeAttemptsLeft(data.attempts_left)
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
      } else if (error instanceof HttpError && error.status === 429) {
        setError({ phone: "Слишком много запросов, попробуйте позже" })
      } else if (error instanceof HttpError && error.status === 400) {
        // an old account with a phone of another country
        setError({ phone: "Мы отправляем коды только на российские мобильные номера" })
      }
    }
  })

  const phoneRef = usePhoneInput()

  const validatePhone = (value: string): FieldErrors => {
    return isValidPhone(value) ?
      {} : { phone: "Введите корректный номер" }
  }

  const validatePassword = (value: string): FieldErrors => {
    if (!(shopUser?.permanent_password ? /^.{5,}$/ : /^\d{6}$/).test(value))
      return { password: "Указан неверный " + (shopUser?.permanent_password ? "пароль" : "код") }
    else
      return {}
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
        if (result.ok) { // signed in, stays pending while the page changes
          if (embedded) {
            if (hideModal)
              hideModal()
          } else {
            router.push(getCallbackUrl(new URLSearchParams(window.location.search).get('callbackUrl')))
          }
          return
        }
        setSignInPending(false)
        if ('status' in result && result.status === 400) {
          setError(getError('permanent_password', result.error)) // too short, the code is not used up
        } else if ('status' in result && [401, 403].includes(result.status)) {
          if (shopUser.permanent_password) {
            setError({ password: "Вы ввели неправильный пароль" })
          } else {
            setError({ password: "Неверный или устаревший код" })
            setCodeAttemptsLeft(attempts => attempts - 1)
          }
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
  const buttonIcon = { size: 18, stroke: 1.5, className: 'me-2' }

  return (
    <form onSubmit={handleSubmit} noValidate>
      {shopUser !== undefined ? (
        <>
          { /* Пользователь с таким телефоном уже есть, требуем подтверждение пароля */}
          <div className="mb-2 text-xl font-light">{formatPhone(shopUser.phone)}</div>
          {ctx === 'order' && (
            <div className="-mt-2 mb-4 text-xs text-muted">
              <a className="text-primary hover:text-link-hover" onClick={resetPhone}>Указать другой телефон</a>
            </div>
          )}
          <div className="mb-4">
            <input
              type={shopUser.permanent_password ? "password" : "text"}
              name="password"
              className={`${inputClass({ invalid: 'password' in error })} ${embedded ? '' : 'max-w-80'}`}
              id={`${embedded}${ctx}-password-input`}
              placeholder={shopUser.permanent_password ? "Пароль" : "Код из смс"}
              onChange={handleChange}
              autoComplete={shopUser.permanent_password ? "current-password" : "one-time-code"}
              inputMode={shopUser.permanent_password ? undefined : "numeric"}
              maxLength={shopUser.permanent_password ? undefined : 6}
              required
              autoFocus />
            {'password' in error && <div className={feedbackClass}>{error.password}</div>}
            <div className={formTextClass}>
              <Countdown delay={codeAttemptsLeft > 0 ? delay : 0} permanentPassword={shopUser.permanent_password} reset={resetPassword} />
            </div>
          </div>
          {!['order', 'preorder', 'warranty'].includes(ctx) && !shopUser.permanent_password && (
            showPermanentPassword ? (
              <div className="grid gap-x-7.5 md:grid-cols-2">
                <div className="mb-4">
                  <label className="inline-block" htmlFor="permanent-password-input">Постоянный пароль:</label>
                  <input
                    type="password"
                    className={inputClass({ size: 'sm', invalid: 'permanent_password' in error })}
                    name="permanent_password"
                    id="permanent-password-input" />
                  {'permanent_password' in error && <div className={feedbackClass}>{error.permanent_password}</div>}
                </div>
                <div className="mb-4">
                  <label className="inline-block" htmlFor="permanent-password-input2">ещё раз:</label>
                  <input
                    type="password"
                    className={inputClass({ size: 'sm', invalid: 'permanent_password2' in error })}
                    name="permanent_password2"
                    id="permanent-password-input2" />
                  {'permanent_password2' in error && <div className={feedbackClass}>{error.permanent_password2}</div>}
                </div>
              </div>
            ) : (
              <div className="mb-4 text-md">
                Вы можете <a onClick={() => setShowPermanentPassword(true)}>указать постоянный пароль</a>, чтобы не получать каждый раз смс
              </div>
            )
          )}
        </>
      ) : (
        <>
          { /* Анонимный пользователь */}
          <div className="mb-4">
            <label className="inline-block text-xl font-light" htmlFor={`${embedded}${ctx}-phone-input`}>
              {ctx === 'order' ? "Для продолжения у" : "У"}
              кажите номер мобильного телефона:
            </label>
            <input
              type="tel"
              name="phone"
              className={inputClass({ invalid: 'phone' in error })}
              ref={phoneRef}
              id={`${embedded}${ctx}-phone-input`}
              placeholder="+7 (999) 111-22-33"
              onChange={handleChange}
              autoComplete="tel"
              required />
            {'phone' in error && <div className={feedbackClass}>{error.phone}</div>}
          </div>
        </>
      )}

      {['order', 'preorder', 'warranty'].includes(ctx) && (
        <>
          <div className={`${checkClass()} mb-4`}>
            <input
              type="checkbox"
              className={checkInputClass({ invalid: 'pd-consent' in error })}
              name="pd-consent"
              id="sw-pd-consent-check"
              checked={pdConsent}
              onChange={handleChange} />
            {" "}
            <label className={checkLabelClass} htmlFor="sw-pd-consent-check">
              Я даю{" "}
              <Link href="/pages/personaldata/">
                согласие на обработку персональных данных
              </Link>
            </label>
            {'pd-consent' in error && <div className={feedbackClass}>{error['pd-consent']}</div>}
          </div>
          {ctx === 'order' && (
            <div className={`${checkClass()} mb-4`}>
              <input
                type="checkbox"
                className={checkInputClass({ invalid: 'of-consent' in error })}
                name="of-consent"
                id="sw-of-consent-check"
                checked={ofConsent}
                onChange={handleChange} />
              {" "}
              <label className={checkLabelClass} htmlFor="sw-of-consent-check">
                Я подтверждаю согласие с{" "}
                <Link href="/pages/oferta/">
                  условиями публичной оферты
                </Link>
              </label>
              {'of-consent' in error && <div className={feedbackClass}>{error['of-consent']}</div>}
            </div>
          )}
        </>
      )}
      {ctx === 'order' ? (
        <button className={`${buttonClass({ block: true, shadow: true })} mt-6`} disabled={isPending}>
          {shopUser ? <IconLogin2 {...buttonIcon} /> : <IconBasket {...buttonIcon} />}Оформить заказ
          {isPending && <ButtonLoading />}
        </button>
      ) : ctx === 'preorder' ? (
        <button className={`${buttonClass({ block: true, shadow: true })} mt-6`} disabled={isPending}>
          {shopUser ? <IconLogin2 {...buttonIcon} /> : <IconBasket {...buttonIcon} />}Оформить запрос о поступлении
          {isPending && <ButtonLoading />}
        </button>
      ) : ctx === 'warranty' ? (
        <button className={`${buttonClass({ shadow: true })} mt-6`} disabled={isPending}>
          {shopUser ? <IconLogin2 {...buttonIcon} /> : <IconLockOpen {...buttonIcon} />}Продолжить
          {isPending && <ButtonLoading />}
        </button>
      ) : (
        <div className="text-end">
          <button className={`${buttonClass({ shadow: !!embedded })} ms-6`} type="submit" disabled={isPending}>
            {!embedded && (shopUser ? <IconLogin2 size={16} stroke={1.5} className="-ms-1 me-2" /> : <IconLockOpen size={16} stroke={1.5} className="-ms-1 me-2" />)}
            {!!shopUser ? "Продолжить" : "Войти"}
            {isPending && <ButtonLoading />}
          </button>
        </div>
      )}
      {!shopUser && !embedded && (
        <div className="mt-6 text-md">
          Если Вы не совершали покупок в магазине, Вы можете{" "}
          <Suspense fallback={<Link href="/register/">зарегистрироваться</Link>}>
            <RegisterLink />
          </Suspense>
        </div>
      )}
    </form>
  )
}