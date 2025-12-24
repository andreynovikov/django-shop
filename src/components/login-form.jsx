import { useState, useEffect, useRef } from 'react'
import { useRouter } from 'next/router'
import Link from 'next/link'
import { useQuery } from '@tanstack/react-query'

import Countdown from '@/components/countdown'

import { formatPhone } from '@/lib/format'
import { signIn } from '@/lib/session'
import { userKeys, checkUser, normalizePhone } from '@/lib/queries'
import phoneInputMask from '@/lib/phone-input-mask'

const CODE_RESEND_DELAY = 240

export default function LoginForm({ ctx, phone, hideModal = undefined, embedded = '' }) {
  const [loginPhone, setLoginPhone] = useState(phone)
  const [pdConsent, setPdConsent] = useState(false)
  const [ofConsent, setOfConsent] = useState(false)
  const [reset, setReset] = useState(false)
  const [error, setError] = useState({})

  const [delay, setDelay] = useState(-1) // TODO: keep delay on page reload

  const [showPermanentPassword, setShowPermanentPassword] = useState(ctx === 'reg')

  const router = useRouter()

  const { data: shopUser, isSuccess, isFetching, error: queryError, refetch } = useQuery({
    queryKey: userKeys.check(loginPhone, reset),
    queryFn: () => checkUser(loginPhone, reset),
    enabled: !!loginPhone
  })

  useEffect(() => {
    if (isSuccess && !isFetching) {
      setReset(false)
      if (!shopUser.permanent_password) {
        setDelay(CODE_RESEND_DELAY)
      } else {
        setDelay(0)
      }
    }
  }, [shopUser, isSuccess, isFetching])

  useEffect(() => {
    if (reset) {
      refetch()
    }
  }, [refetch, reset])

  useEffect(() => {
    if (queryError?.response?.status === 404) {
      if (['order', 'preorder', 'warranty'].includes(ctx)) {
        // register user in background when making order or registering warranty
        signIn({ phone: loginPhone, ctx })
          .then(result => {
            if (result.ok) {
              if (embedded && hideModal)
                hideModal()
            } else {
              setError({ phone: result.error })
            }
          })
      } else {
        setError({ phone: "Пользователь с таким телефоном не зарегистрирован" })
      }
    }
  }, [queryError, loginPhone, ctx, embedded, hideModal])

  const phoneRef = useRef(null)
  const passwordRef = useRef(null)

  useEffect(() => {
    if (phoneRef.current && !!!phoneRef.current.inputmask)
      phoneInputMask.mask(phoneRef.current)
  }, [phoneRef])

  const validatePhone = () => {
    return phoneRef.current && phoneRef.current.inputmask.isComplete() ?
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
      err = { ...err, ...validatePhone() }
      if (Object.keys(err).length > 0) {
        setError(err)
      } else {
        setLoginPhone(normalizePhone(e.target.elements.phone.value))
      }
    } else if (e.target.elements.password) {
      err = { ...err, ...validatePassword(e.target.elements.password.value) }
      if (showPermanentPassword)
        err = { ...err, ...validatePermanentPasswords(e.target.elements.permanent_password.value, e.target.elements.permanent_password2.value) }
      if (Object.keys(err).length > 0) {
        setError(err)
      } else {
        const credentials = {
          phone: loginPhone,
          password: e.target.elements.password.value,
        }
        if (showPermanentPassword && e.target.elements.permanent_password.value.length > 0)
          credentials['permanent_password'] = e.target.elements.permanent_password.value
        const result = await signIn(credentials)
        if (result.ok) {
          if (embedded) {
            if (hideModal)
              hideModal()
          } else {
            router.push(router.query.callbackUrl || '/')
          }
        } else {
          try {
            if (result.error?.response?.data) {
              if (result.error.response.data.password)
                setError({ password: result.error.response.data.password[0] })
              else if (result.error.response.status === 401)
                setError({ password: "Вы ввели неправильный " + (shopUser?.permanent_password ? "пароль" : "код") })
              else if (result.error.response.data.non_field_errors)
                setError({ password: result.error.response.data.non_field_errors[0] })
              else
                setError({ password: "Неизвестная ошибка входа" })
            } else {
              setError({ password: "Неизвестная ошибка входа" })
            }
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
    setLoginPhone('')
    setError({})
  }

  const resetPassword = () => {
    setDelay(-1)
    setReset(true)
  }

  return (
    <form onSubmit={handleSubmit} noValidate>
      {!!shopUser ? (
        <>
          { /* Пользователь с таким телефоном уже есть, требуем подтверждение пароля */}
          <div className="lead mb-2">{formatPhone(loginPhone)}</div>
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
              placeholder={shopUser?.permanent_password ? "Пароль" : "Код из смс"}
              onChange={handleChange}
              required
              autoFocus />
            {'password' in error && <div className="invalid-feedback">{error.password}</div>}
            <div className="form-text">
              <Countdown delay={delay} permanentPassword={shopUser?.permanent_password} reset={isSuccess ? resetPassword : undefined} />
            </div>
          </div>
          {!['order', 'preorder', 'warranty'].includes(ctx) && isSuccess && !shopUser.permanent_password && (
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
            <div className="input-group">
              <span className="input-group-text bg-secondary">+7</span>
              <input
                type="tel"
                name="phone"
                className={"form-control" + ('phone' in error ? " is-invalid" : "")}
                ref={phoneRef}
                id={`${embedded}${ctx}-phone-input`}
                placeholder="(999) 111-22-33"
                onChange={handleChange}
                autoComplete="phone"
                required />
              {'phone' in error && <div className="invalid-feedback">{error.phone}</div>}
            </div>
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
        <button className="btn btn-primary btn-shadow d-block w-100 mt-4">
          <i className={"fs-lg me-2 " + (!!shopUser ? "ci-sign-in" : "ci-basket-alt")} />Оформить заказ
        </button>
      ) : ctx === 'preorder' ? (
        <button className="btn btn-primary btn-shadow d-block w-100 mt-4">
          <i className={"fs-lg me-2 " + (!!shopUser ? "ci-sign-in" : "ci-basket-alt")} />Оформить запрос о поступлении
        </button>
      ) : ctx === 'warranty' ? (
        <button className="btn btn-primary btn-shadow d-block mt-4">
          <i className={"fs-lg me-2 " + (!!shopUser ? "ci-sign-in" : "ci-unlocked")} />Продолжить
        </button>
      ) : (
        <div className="text-end">
          <button className={"btn btn-primary ms-4" + (embedded && " btn-shadow")} type="submit">
            {!embedded && <i className={"me-2 ms-n1" + (!!shopUser ? "ci-sign-in" : "ci-unlocked")} />}
            {!!shopUser ? "Продолжить" : "Войти"}
          </button>
        </div>
      )}
      {!!!shopUser && !embedded && (
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