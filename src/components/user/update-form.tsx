import { useState, useEffect, ChangeEvent, SubmitEvent } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'

import { IconCircleCheck } from '@tabler/icons-react'

import { Loading } from '@/components/loading'
import { Alert } from '@/components/ui/alert'
import { feedbackClass, formTextClass, inputClass, labelClass } from '@/components/ui/form'
import PhoneCodeInput from '@/components/user/phone-code-input'

import { usePhoneInput, isValidPhone } from '@/lib/phone-input'
import { useSession } from '@/lib/session'
import { userKeys, getUserForm, updateUser, sendEmailLink, isPhoneCodeSent, normalizePhone, HttpError } from '@/lib/queries'
import { PhoneCodeSent, User, UserEdit, UserEditField } from '@/lib/types'

type FieldErrors = Partial<Record<keyof UserEdit, string[]>>

interface UpdateFormProps {
  id: string
  embedded?: boolean
  onReady: () => void
  onUpdated?: () => void
}

// Asks for the link that confirms the saved address again
function EmailNotice({ user }: { user: User }) {
  const { mutate, isSuccess, isPending, error } = useMutation({
    mutationFn: () => sendEmailLink(user.id),
  })

  return (
    <small className="mt-1.5 block text-xs text-warning">
      Адрес не подтверждён: перейдите по ссылке из письма.{" "}
      {isSuccess ? (
        "Письмо отправлено."
      ) : error instanceof HttpError && error.status === 429 ? (
        "Письмо уже отправлено недавно, попробуйте позже."
      ) : (
        <a className="text-primary hover:text-link-hover" onClick={() => !isPending && mutate()}>Отправить письмо ещё раз</a>
      )}
    </small>
  )
}

export default function UpdateForm({ id, embedded = false, onReady, onUpdated }: UpdateFormProps) {
  const [updated, setUpdated] = useState(false)
  const [error, setError] = useState<FieldErrors>({})
  // Keep only edited values, otherwise form is reset on each window focus
  const [edits, setEdits] = useState<Partial<UserEdit>>({})
  // A new phone is saved only with the code the backend has sent to it
  const [codeSent, setCodeSent] = useState<PhoneCodeSent>()
  const [delay, setDelay] = useState(-1)
  const [attemptsLeft, setAttemptsLeft] = useState(0)
  const queryClient = useQueryClient()

  const { user: sessionUser, status } = useSession()
  const user = status === 'authenticated' ? sessionUser as User : undefined

  const { data: form, isSuccess } = useQuery({
    queryKey: userKeys.form(),
    queryFn: () => getUserForm(),
  })

  const ready = isSuccess && user !== undefined

  const fieldValue = (name: UserEditField) => edits[name] ?? user?.[name] ?? ''

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
    mutationFn: ({ id, body }: { id: number, body: UserEdit }) => updateUser(id, body),
    onSuccess: (result) => {
      if (!isPhoneCodeSent(result))
        queryClient.invalidateQueries({ queryKey: userKeys.details() })
    }
  })

  const phoneRef = usePhoneInput()

  const handleChange = (e: ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.currentTarget
    if (name in error)
      setError(Object.fromEntries(Object.entries(error).filter(([key]) => key !== name)))
    if (name === 'phone') // the code was for the number typed before
      setCodeSent(undefined)
    if (name !== 'code')
      setEdits((edits) => ({ ...edits, [name]: value }))
  }

  const save = (code?: string) => {
    if (!user)
      return
    const body: UserEdit = { ...user, ...edits, phone: normalizePhone(fieldValue('phone')) }
    if (code !== undefined)
      body.code = code
    updateUserMutation.mutate({ id: user.id, body }, {
      onSuccess: (result) => {
        if (isPhoneCodeSent(result)) {
          setCodeSent(result)
          setDelay(result.retry_after)
          setAttemptsLeft(result.attempts_left)
          return
        }
        setCodeSent(undefined)
        if (onUpdated !== undefined)
          onUpdated()
        else
          setUpdated(true)
      },
      onError: async (error) => {
        console.error(error)
        if (error instanceof HttpError && error.status === 400) {
          const errors: FieldErrors = await error.response.json()
          if ('code' in errors)
            setAttemptsLeft(attempts => attempts - 1)
          setError(errors)
        } else if (error instanceof HttpError && error.status === 429) {
          setError({ phone: ["Слишком много запросов, попробуйте позже"] })
        }
      }
    })
  }

  const handleSubmit = (e: SubmitEvent<HTMLFormElement>) => {
    e.preventDefault()
    if (!isValidPhone(fieldValue('phone'))) {
      setError({ phone: ["Введите корректный номер"] })
      return
    }
    if (codeSent === undefined) {
      save()
      return
    }
    const code = String(new FormData(e.currentTarget).get('code') ?? '')
    if (!/^\d{6}$/.test(code))
      setError({ code: ["Указан неверный код"] })
    else
      save(code)
  }

  const resendCode = () => {
    setDelay(-1)
    setError({})
    save()
  }

  if (!ready)
    return <Loading className="text-center" />

  return (
    <form id={id} noValidate onSubmit={handleSubmit}>
      {updated && (
        <Alert variant="success" icon={<IconCircleCheck size={18} stroke={1.5} />} className="mb-4">
          Изменения успешно сохранены.
        </Alert>
      )}

      <div className={`grid gap-x-6 gap-y-4 ${embedded ? '' : 'md:grid-cols-2'}`}>
        {form.map((field) => (
          <div key={field.id}>
            <label className={labelClass} htmlFor={field.id}>{field.label}:</label>
            {field.name === "phone" ? (
              <input
                ref={phoneRef}
                className={inputClass({ invalid: !!error[field.name] })}
                id={field.id}
                name={field.name}
                value={fieldValue(field.name)}
                onChange={handleChange}
                type="tel"
                placeholder="(999) 111-22-33"
                autoComplete="tel"
                required={field.required} />
            ) : (
              <input
                className={inputClass({ invalid: !!error[field.name] })}
                id={field.id}
                name={field.name}
                value={fieldValue(field.name)}
                onChange={handleChange}
                required={field.required} />
            )}
            {error[field.name]?.map((err, index) => (
              <div className={feedbackClass} key={index}>{err}</div>
            ))}
            {field.help && <small className={formTextClass}>{field.help}</small>}
            {field.name === 'email' && user.email && !user.email_verified && fieldValue('email') === user.email && (
              <EmailNotice user={user} />
            )}
            {field.name === 'phone' && codeSent !== undefined && (
              <div className="mt-4">
                <label className={labelClass} htmlFor={`${id}-code`}>Код из смс, отправленного на новый номер:</label>
                <PhoneCodeInput
                  id={`${id}-code`}
                  delay={delay}
                  attemptsLeft={attemptsLeft}
                  error={error.code?.[0]}
                  onChange={handleChange}
                  onResend={resendCode} />
              </div>
            )}
          </div>
        ))}
      </div>
    </form>
  )
}
