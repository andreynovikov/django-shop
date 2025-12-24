import { useEffect, useState, useRef } from 'react'
import { useRouter } from 'next/router'
import Link from 'next/link'

import { register } from '@/lib/session'
import { normalizePhone } from '@/lib/queries'
import phoneInputMask from '@/lib/phone-input-mask'

export default function RegistrationForm({ embedded = '', onComplete }) {
  const [consent, setConsent] = useState(false)
  const [error, setError] = useState({})

  const router = useRouter()

  const phoneRef = useRef(null)

  useEffect(() => {
    if (phoneRef.current && !!!phoneRef.current.inputmask)
      phoneInputMask.mask(phoneRef.current)
  }, [phoneRef])

  const validatePhone = () => {
    return phoneRef.current && phoneRef.current.inputmask.isComplete()
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
    if (field === 'consent')
      setConsent(e.target.checked)
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError(false)
    if (!validatePhone()) {
      setError({ 'phone': ["Введите корректный номер"] })
      return
    }
    if (!consent) {
      setError({ 'consent': ["Регистрация возможна только после предоставления согласия"] })
      return
    }
    const formData = new FormData(e.currentTarget)
    formData.set('phone', normalizePhone(formData.get('phone')))
    const result = await register(formData)
    if (result.ok) {
      if (embedded) {
        if (onComplete)
          onComplete(formData.get('phone'))
      } else {
        router.push({
          pathname: '/login',
          query: {
            ...router.query,
            phone: formData.get('phone'),
            ctx: 'reg'
          }
        })
      }
    } else {
      if (result.error?.response?.data && result.error.response.headers['content-type'].toLowerCase() === 'application/json')
        setError(result.error.response.data)
      else
        setError({ 'non_field_errors': [result.error.response?.statusText || result.error.message] })
    }
  }

  return (
    <form onSubmit={handleSubmit} noValidate>
      {error && 'non_field_errors' in error && error['non_field_errors'].map((err, index) => (
        <>
          <div className="is-invalid text-danger">Ошибка: </div>
          <div className="invalid-feedback mt-0 mb-3" key={index}>{err}</div>
        </>
      ))}
      <div className="mb-3">
        <label htmlFor="reg-phone-input">Укажите номер мобильного телефона:</label>
        <div className="input-group">
          <span className="input-group-text bg-secondary">+7</span>
          <input
            type="tel"
            name="phone"
            className={"form-control" + ((error && 'phone' in error) ? " is-invalid" : "")}
            ref={phoneRef}
            id={`${embedded}reg-phone-input`}
            placeholder="(999) 111-22-33"
            onChange={handleChange}
            autoComplete="phone"
            required />
          {error && 'phone' in error && error['phone'].map((err, index) => (
            <div className="invalid-feedback" key={index}>{err}</div>
          ))}
        </div>
      </div>
      <div className="mb-3">
        <label htmlFor={`${embedded}reg-email-input`}>Адрес электронной почты:</label>
        <input
          type="email"
          className={"form-control" + ((error && 'email' in error) ? " is-invalid" : "")}
          name="email"
          id={`${embedded}reg-email-input`}
          onChange={handleChange}
          autoComplete="email" />
        {error && 'email' in error && error['email'].map((err, index) => (
          <div className="invalid-feedback" key={index}>{err}</div>
        ))}
        <small className="form-text text-muted">опционально</small>
      </div>
      <div className="mb-3">
        <label htmlFor={`${embedded}reg-name-input`}>Фамилия Имя Отчество:</label>
        <input
          type="text"
          className={"form-control" + ((error && 'name' in error) ? " is-invalid" : "")}
          name="name"
          id={`${embedded}reg-name-input`}
          onChange={handleChange}
          autoComplete="name" />
        {error && 'name' in error && error['name'].map((err, index) => (
          <div className="invalid-feedback" key={index}>{err}</div>
        ))}
        <small className="form-text text-muted">если Вы планируете оформлять заказы</small>
      </div>
      <div className="mb-3">
        <label htmlFor={`${embedded}reg-username-input`}>Псевдоним для отзывов:</label>
        <input
          type="text"
          className={"form-control" + ((error && 'username' in error) ? " is-invalid" : "")}
          name="username"
          id={`${embedded}reg-username-input`}
          onChange={handleChange} />
        {error && 'username' in error && error['username'].map((err, index) => (
          <div className="invalid-feedback" key={index}>{err}</div>
        ))}
        <small className="form-text text-muted">если Вы не хотите, чтобы Ваше настоящее имя отображалось в отзывах</small>
      </div>
      <div className="form-check mb-3">
        <input
          type="checkbox"
          className={"form-check-input" + ((error && 'consent' in error) ? " is-invalid" : "")}
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
        {error && 'consent' in error && error['consent'].map((err, index) => (
          <div className="invalid-feedback" key={index}>{err}</div>
        ))}
      </div>
      <div className="text-end">
        <button className={"btn btn-primary ms-4" + (embedded && " btn-shadow")} type="submit">
          {!embedded && <i className="ci-user me-2 ms-n1" />}
          Зарегистрироваться
        </button>
      </div>
    </form>
  )
}
