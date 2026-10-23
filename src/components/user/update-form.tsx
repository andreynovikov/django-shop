import { useState, useEffect, ChangeEvent, SubmitEvent } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'

import { Loading } from '@/components/loading'

import { usePhoneInput, isValidPhone } from '@/lib/phone-input'
import { useSession } from '@/lib/session'
import { userKeys, getUserForm, updateUser, HttpError } from '@/lib/queries'
import { User, UserEdit } from '@/lib/types'

type FieldErrors = Partial<Record<keyof UserEdit, string[]>>

interface UpdateFormProps {
  id: string
  embedded?: boolean
  onReady: () => void
  onUpdated?: () => void
}

export default function UpdateForm({ id, embedded = false, onReady, onUpdated }: UpdateFormProps) {
  const [updated, setUpdated] = useState(false)
  const [error, setError] = useState<FieldErrors>({})
  // Keep only edited values, otherwise form is reset on each window focus
  const [edits, setEdits] = useState<Partial<UserEdit>>({})
  const queryClient = useQueryClient()

  const { user: sessionUser, status } = useSession()
  const user = status === 'authenticated' ? sessionUser as User : undefined

  const { data: form, isSuccess } = useQuery({
    queryKey: userKeys.form(),
    queryFn: () => getUserForm(),
  })

  const ready = isSuccess && user !== undefined

  const fieldValue = (name: keyof UserEdit) => edits[name] ?? user?.[name] ?? ''

  useEffect(() => {
    if (ready)
      onReady()
  }, [onReady, ready])

  useEffect(() => {
    if (updated) {
      const timer = setTimeout(() => setUpdated(false), 5 * 1000)
      return () => {
        clearTimeout(timer)
      }
    }
  }, [updated])

  const updateUserMutation = useMutation({
    mutationFn: (data: User) => updateUser(data.id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: userKeys.details() })
    }
  })

  const phoneRef = usePhoneInput()

  const handleChange = (e: ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.currentTarget
    if (name in error)
      setError(Object.fromEntries(Object.entries(error).filter(([key]) => key !== name)))
    setEdits((edits) => ({ ...edits, [name]: value }))
  }

  const handleSubmit = (e: SubmitEvent<HTMLFormElement>) => {
    e.preventDefault()
    if (!user)
      return
    if (!isValidPhone(fieldValue('phone'))) {
      setError({ phone: ["Введите корректный номер"] })
    } else {
      updateUserMutation.mutate({ ...user, ...edits }, {
        onSuccess: () => {
          if (onUpdated !== undefined)
            onUpdated()
          else
            setUpdated(true)
        },
        onError: async (error) => {
          console.error(error)
          if (error instanceof HttpError && error.status === 400)
            setError(await error.response.json())
        }
      })
    }
  }

  if (!ready)
    return <Loading className="text-center" />

  return (
    <form id={id} noValidate onSubmit={handleSubmit}>
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
              <input
                ref={phoneRef}
                className={"form-control" + (error[field.name] ? " is-invalid" : "")}
                id={field.id}
                name={field.name}
                value={fieldValue(field.name)}
                onChange={handleChange}
                type="tel"
                placeholder="(999) 111-22-33"
                autoComplete="phone"
                required={field.required} />
            ) : (
              <input
                className={"form-control" + (error[field.name] ? " is-invalid" : "")}
                id={field.id}
                name={field.name}
                value={fieldValue(field.name)}
                onChange={handleChange}
                required={field.required} />
            )}
            {error[field.name]?.map((err, index) => (
              <div className="invalid-feedback" key={index}>{err}</div>
            ))}
            {field.help && <small className="form-text text-muted">{field.help}</small>}
          </div>
        ))}
      </div>
    </form>
  )
}
