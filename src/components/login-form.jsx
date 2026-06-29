import { useState, useEffect, useRef } from 'react'
import { useRouter } from 'next/router'
import Link from 'next/link'
import { useMutation } from '@tanstack/react-query'

import Countdown from '@/components/countdown'
import { ButtonLoading } from '@/components/loading'

import { formatPhone } from '@/lib/format'
import { usePhoneInput, isValidPhone } from '@/lib/phone-input'
import { signIn } from '@/lib/session'
import { checkUser, normalizePhone } from '@/lib/queries'

const CODE_RESEND_DELAY = 240

function getError(field, error) {
  if (error[field])
    return{ [field]: error[field][0] }
  else if (error.non_field_errors)
    return { [field]: error.non_field_errors[0] }
  else if (detail)
    return { [field]: error.detail }
  else if (error)
    return { [field]: error.toString() }
  else
    return { [field]: "Неизвестная ошибка входа" }
}

export default function LoginForm({ ctx, phone, hideModal = undefined, embedded = '' }) {
  const [pdConsent, setPdConsent] = useState(false)
  const [ofConsent, setOfConsent] = useState(false)
  const [isSignInPending, setSignInPending] = useState(false)
  const [error, setError] = useState({})

  const [delay, setDelay] = useState(-1) // TODO: keep delay on page reload

  const [showPermanentPassword, setShowPermanentPassword] = useState(ctx === 'reg')

  const router = useRouter()

  const {
    mutate: performUserCheck,
    reset: resetUserCheck,
    data: shopUser,
    isIdle,
    isPending: isUserCheckPending
  } = useMutation({
    mutationFn: ({ phone, reset }) => checkUser(phone, reset),
    onSuccess: (data) => {
      setDelay(data.permanent_password ? 0 : CODE_RESEND_DELAY)
    },
    onError: async (error, { phone }) => {
      console.log(error)
      if (error.response?.status === 404) {
        if (['order', 'preorder', 'warranty'].includes(ctx)) {
          setSignInPending(true)
          // register user in background when making order or registering warranty
          const result = await signIn({ phone, ctx })
          if (result.ok) {
            if (embedded && hideModal)
              hideModal()
          } else {
            setError(getError('phone', result.error))
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
  const passwordRef = useRef(null)

  const validatePhone = (value) => {
    return isValidPhone(value) ?
      {} : { phone: "Введите корректный номер" }
  }

  const validatePassword = (value) => {
    if (!!!(value.match(/^(:?\d{4}|.{5,30})$/)))
      return { password: "Указан неверный " + (shopUser?.permanent_password ? "пароль" : "код") }
    else
      return {}
  }

  const validatePermanentPasswords = (value1, value2) => {
    const err = {}
    if (value1 != value2)
      err['permanent_password2'] = "Пароли не совпадают"
    if (value1.length > 0 && value1.length < 5)
      err['permanent_password'] = "Постоянный пароль должен быть не менее 5 символов"
    return err
  }

  const handleChange = (e) => {
    const field = e.currentTarget.name
    if (error && field in error) {
      setError(Object.keys(error).reduce(function (filtered, key) {
        if (key !== field)
          filtered[key] = error[key]
        return filtered
      }, {}))
    }
    if (field === 'pd-consent')
      setPdConsent(e.target.checked)
    if (field === 'of-consent')
      setOfConsent(e.target.checked)
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError({})
    let err = {}

    if (['order', 'preorder', 'warranty'].includes(ctx)) {
      if (!pdConsent)
        err = { ...err, 'pd-consent': "Продолжение возможно только после предоставления согласия" }
      if (ctx === 'order' && !ofConsent)
        err = { ...err, 'of-consent': "Оформление заказа возможно только после подтверждения согласия" }
    }

    if (e.target.elements.phone) {
      err = { ...err, ...validatePhone(e.target.elements.phone.value) }
      if (Object.keys(err).length > 0) {
        setError(err)
      } else {
        performUserCheck({ phone: normalizePhone(e.target.elements.phone.value), reset: false })
      }
    } else if (e.target.elements.password) {
      err = { ...err, ...validatePassword(e.target.elements.password.value) }
      if (showPermanentPassword)
        err = { ...err, ...validatePermanentPasswords(e.target.elements.permanent_password.value, e.target.elements.permanent_password2.value) }
      if (Object.keys(err).length > 0) {
        setError(err)
      } else {
        const credentials = {
          phone: shopUser.phone,
          password: e.target.elements.password.value,
        }
        if (showPermanentPassword && e.target.elements.permanent_password.value.length > 0)
          credentials['permanent_password'] = e.target.elements.permanent_password.value
        setSignInPending(true)
        const result = await signIn(credentials)
        setSignInPending(false)
        if (result.ok) {
          if (embedded) {
            if (hideModal)
              hideModal()
          } else {
            router.push(router.query.callbackUrl || '/')
          }
        } else {
          try {
            if ([401, 403].includes(result.status))
              setError({ password: "Вы ввели неправильный " + (shopUser?.permanent_password ? "пароль" : "код") })
            else
              setError('password', result.error)
            // eslint-disable-next-line @typescript-eslint/no-unused-vars
          } catch (error) {
            setError({ password: result.error.response?.statusText || result.error.message })
          }
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
              ref={passwordRef}
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
              autoComplete="phone"
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
          <button className={"btn btn-primary ms-4" + (embedded && " btn-shadow")} type="submit" disabled={isPending}>
            {!embedded && <i className={"me-2 ms-n1 " + (shopUser ? "ci-sign-in" : "ci-unlocked")} />}
            {!!shopUser ? "Продолжить" : "Войти"}
            {isPending && <ButtonLoading />}
          </button>
        </div>
      )}
      {!shopUser && !embedded && (
        <div className="mt-4 fs-md">
          Если Вы не совершали покупок в магазине, Вы можете{" "}
          <Link href={{ pathname: '/register', query: router.query }}>
            зарегистрироваться
          </Link>
        </div>
      )}
    </form>
  )
}