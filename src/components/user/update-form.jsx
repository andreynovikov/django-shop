import { useState, useEffect, useReducer, forwardRef, useImperativeHandle, useRef } from 'react'
import Script from 'next/script'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'

import { Loading } from '@/components/loading'

import { useSession } from '@/lib/session'
import { userKeys, getUserForm, updateUser } from '@/lib/queries'

export default forwardRef(function UpdateForm({ embedded, onReady, onUpdated }, ref) {
  const [ready, setReady] = useState(false)
  const [updated, setUpdated] = useState(false)
  const [error, setError] = useState(false)
  const queryClient = useQueryClient()

  const { user, status } = useSession()

  const [formData, setFormData] = useReducer((state, update) => {
    return { ...state, ...update }
  }, {})

  const { data: form, isSuccess } = useQuery({
    queryKey: userKeys.form(),
    queryFn: () => getUserForm(),
  })

  useEffect(() => {
    if (status === 'authenticated' && isSuccess) {
      const formDefaults = form.reduce((data, field) => {
        data[field.name] = ''
        return data
      }, {})
      setFormData({ ...formDefaults, ...user, ...formData }) // otherwise form is reset on each window focus
    }
    /* eslint-disable react-hooks/exhaustive-deps */
  }, [user, status, form, isSuccess])

  useEffect(() => {
    if (isSuccess && status === 'authenticated' && Object.keys(formData).length > 0) {
      setReady(true)
      onReady()
    }
    /* eslint-disable react-hooks/exhaustive-deps */
  }, [isSuccess, status, formData])

  useEffect(() => {
    if (updated) {
      const timer = setTimeout(() => setUpdated(false), 5 * 1000)
      return () => {
        clearTimeout(timer)
      }
    }
  }, [updated])

  const updateUserMutation = useMutation({
    mutationFn: () => updateUser(user.id, formData),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: userKeys.details() })
    }
  })

  const formRef = useRef()
  const phoneRef = useRef()

  const validatePhone = () => {
    return phoneRef.current && phoneRef.current.inputmask.isComplete()
  }

  const handleChange = (e) => {
    setFormData({ [e.target.name]: e.target.value })
  }

  const handleSubmit = async (e) => {
    if (e)
      e.preventDefault()
    if (!validatePhone(formRef.current.elements.phone.value)) {
      console.error("error")
      setError({ phone: ["Введите корректный номер"] })
    } else {
      updateUserMutation.mutate(undefined, {
        onSuccess: () => {
          if (onUpdated !== undefined)
            onUpdated()
          else
            setUpdated(true)
        },
        onError: (error) => {
          console.error(error)
          if (error.response && error.response.data)
            setError(error.response.data)
        }
      })
    }
  }

  useImperativeHandle(ref, () => ({
    submit: handleSubmit
  }))

  const setupInputMask = () => {
    if (window && window.Inputmask && phoneRef.current && !!!phoneRef.current.inputmask) {
      window.Inputmask({
        mask: ["(999) 999-99-99", "* (999) 999-99-99"],
        definitions: {
          "*": { validator: "[78]" }
        },
        onBeforePaste: function (pastedValue) {
          return pastedValue.replace("+7", "")
        },
        onBeforeMask: function (value) {
          return value.replace("+7", "")
        },
        oncomplete: function () {
          var value = this.inputmask.unmaskedvalue()
          if (value.length > 10) {
            value = value.substr(1)
            this.inputmask.setValue(value)
          }
        },
        keepStatic: true
      }).mask(phoneRef.current)
    }
  }

  if (!ready)
    return <Loading className="text-center" />

  return (
    <form ref={formRef} noValidate>
      {updated && (
        <div className="alert alert-success d-flex" role="alert">
          <div className="alert-icon"><i className="ci-check-circle" /></div>
          <div>Изменения успешно сохранены.</div>
        </div>
      )}

      <div className="row gx-4 gy-3">
        {form.map((field) => (
          <div className={`col-${embedded ? "12" : "md-6"}`} key={field.id}>
            <label className="form-label" htmlFor={field.id}>{field.label}:</label>
            {field.name === "phone" ? (
              <div className="input-group">
                <span className="input-group-text bg-secondary">+7</span>
                <input
                  ref={phoneRef}
                  className={"form-control" + ((error && field.name in error) ? " is-invalid" : "")}
                  id={field.id}
                  name={field.name}
                  value={formData[field.name]}
                  onChange={handleChange}
                  type="tel"
                  placeholder="(999) 111-22-33"
                  autoComplete="phone"
                  required={field.required} />
                {error && field.name in error && error[field.name].map((err, index) => (
                  <div className="invalid-feedback" key={index}>{err}</div>
                ))}
              </div>
            ) : (
              <>
                <input
                  className={"form-control" + ((error && field.name in error) ? " is-invalid" : "")}
                  id={field.id}
                  name={field.name}
                  value={formData[field.name]}
                  onChange={handleChange}
                  required={field.required} />
                {error && field.name in error && error[field.name].map((err, index) => (
                  <div className="invalid-feedback" key={index}>{err}</div>
                ))}
              </>
            )}
            {field.text && <small className="form-text text-muted">{field.help}</small>}
          </div>
        ))}
      </div>
      <Script
        id="inputmask"
        src="/js/inputmask.js"
        onReady={setupInputMask}
        onLoad={setupInputMask} />
    </form>
  )
})
