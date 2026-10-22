import { useState, useEffect, useReducer, useRef } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'

import { Loading } from '@/components/loading'

import { usePhoneInput, isValidPhone } from '@/lib/phone-input'
import { useSession } from '@/lib/session'
import { userKeys, getUserForm, updateUser } from '@/lib/queries'

export default function UpdateForm({ id, embedded, onReady, onUpdated }) {
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

  const ready = isSuccess && status === 'authenticated' && Object.keys(formData).length > 0

  useEffect(() => {
    if (ready)
      onReady()
    /* eslint-disable react-hooks/exhaustive-deps */
  }, [ready])

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
  const phoneRef = usePhoneInput()

  const handleChange = (e) => {
    setFormData({ [e.target.name]: e.target.value })
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (!isValidPhone(formRef.current.elements.phone.value)) {
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

  if (!ready)
    return <Loading className="text-center" />

  return (
    <form id={id} ref={formRef} noValidate onSubmit={handleSubmit}>
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
              <>
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
              </>
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
    </form>
  )
}
