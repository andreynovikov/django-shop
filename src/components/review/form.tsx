import { useState, useEffect, ChangeEvent, SubmitEvent } from 'react'
import { useQuery, useMutation, useQueryClient, skipToken } from '@tanstack/react-query'
import { IconAlertCircle, IconCircleCheck } from '@tabler/icons-react'

import { Alert } from '@/components/ui/alert'
import { buttonClass } from '@/components/ui/button'
import { feedbackClass, formTextClass, inputClass, labelClass, selectClass } from '@/components/ui/form'

import { Loading } from '@/components/loading'
import UserUpdateModal from '@/components/user/update-modal'

import { useSession } from '@/lib/session'
import { reviewKeys, getReviewForm, loadProductReview, createProductReview, updateProductReview, HttpError } from '@/lib/queries'
import { Product, ProductReview, User } from '@/lib/types'

type FieldErrors = Record<string, string[]>

interface ReviewFormProps {
  product: Product
  review?: number  // id of the user's review, it is edited instead of adding a new one
}

// Value of a form field in the edited review, the rating is an object with its value
function reviewValue(review: ProductReview | undefined, name: string) {
  const value = review?.[name as keyof ProductReview]
  if (typeof value === 'object' && value !== null && 'value' in value)
    return value.value
  return typeof value === 'string' || typeof value === 'number' ? value : undefined
}

export default function ReviewForm({ product, review: reviewId }: ReviewFormProps) {
  const [updated, setUpdated] = useState(false)
  const [error, setError] = useState<FieldErrors>({})
  const queryClient = useQueryClient()
  const [showUpdateModal, setShowUpdateModal] = useState(false)
  const { user: sessionUser, status } = useSession()
  const user = status === 'authenticated' ? sessionUser as User : undefined

  const { data: form, isSuccess: isFormSuccess } = useQuery({
    queryKey: reviewKeys.form(product.id),
    queryFn: () => getReviewForm(product.id),
  })

  const { data: review, isSuccess: isReviewSuccess } = useQuery({
    queryKey: reviewKeys.detail(product.id, reviewId ?? 0),
    queryFn: reviewId !== undefined ? () => loadProductReview(product.id, reviewId) : skipToken,
  })

  useEffect(() => {
    if (updated) {
      const timer = setTimeout(() => setUpdated(false), 5 * 1000)
      return () => {
        clearTimeout(timer)
      }
    }
  }, [updated])

  const saveReviewMutation = useMutation({
    mutationFn: (data: FormData) => reviewId !== undefined
      ? updateProductReview(product.id, reviewId, data)
      : createProductReview(product.id, data),
    onSuccess: () => {
      if (reviewId !== undefined)
        queryClient.invalidateQueries({ queryKey: reviewKeys.detail(product.id, reviewId) })
      queryClient.invalidateQueries({ queryKey: reviewKeys.list(product.id) })
    }
  })

  const handleChange = (e: ChangeEvent<HTMLSelectElement>) => {
    const field = e.currentTarget.name
    if (field in error)
      setError(Object.fromEntries(Object.entries(error).filter(([key]) => key !== field)))
  }

  const handleSubmit = (e: SubmitEvent<HTMLFormElement>) => {
    e.preventDefault()
    saveReviewMutation.mutate(new FormData(e.currentTarget), {
      onSuccess: () => {
        setUpdated(true)
      },
      onError: async (error) => {
        console.error(error)
        if (error instanceof HttpError && error.response.headers.get('content-type')?.toLowerCase().includes('application/json'))
          setError(await error.response.json())
      }
    })
  }

  if (!isFormSuccess || (reviewId !== undefined && !isReviewSuccess))
    return <Loading className="text-center" />

  return (
    <>
      {review && !review.is_public && (
        <Alert variant="accent" className="mb-4 text-sm">Ваш отзыв в настоящее время находится на проверке</Alert>
      )}

      <h3 className="mb-3 pb-2 text-h4">{reviewId ? "Изменить" : "Оставить"} отзыв</h3>

      {user?.username === '' && (
        <>
          <UserUpdateModal show={showUpdateModal} onHide={() => setShowUpdateModal(false)} />
          <Alert variant="warning" icon={<IconAlertCircle size={18} stroke={1.5} />} className="mb-4">
            Вы можете{' '}
            <a onClick={() => setShowUpdateModal(true)}>указать</a>
            {' '}псевдоним, если не хотите, чтобы отображалось Ваше реальное имя.
          </Alert>
        </>
      )}

      <form noValidate onSubmit={handleSubmit}>
        {updated && (
          <Alert variant="success" icon={<IconCircleCheck size={18} stroke={1.5} />} className="mb-4">
            Изменения успешно сохранены.
          </Alert>
        )}

        <div className="grid gap-y-4">
          {form.map((field) => (
            <div style={{ display: (field.widget === 'HiddenInput' || field.name === 'honeypot') ? "none" : "initial" }} key={field.id}>
              {field.widget !== 'HiddenInput' && (
                <label className={labelClass} htmlFor={field.id}>
                  {field.label}{field.required && <span className="text-danger">*</span>}
                </label>
              )}
              {field.widget === 'HiddenInput' ? (
                <input
                  type="hidden"
                  name={field.name}
                  value={field.value}
                  required={field.required} />
              ) : field.widget === 'Select' ? (
                <select
                  className={selectClass({ invalid: field.name in error })}
                  id={field.id}
                  name={field.name}
                  defaultValue={reviewValue(review, field.name)}
                  onChange={handleChange}
                  required={field.required}>
                  {field.choices?.map((choice) => (
                    <option value={choice[0]} key={choice[0]}>
                      {choice[1]}
                      {' '}
                      {choice[0] && <>({choice[0]})</>}
                    </option>
                  ))}
                </select>
              ) : field.widget === 'Textarea' ? (
                <textarea
                  className={inputClass({ invalid: field.name in error })}
                  id={field.id}
                  name={field.name}
                  defaultValue={reviewValue(review, field.name)}
                  rows={Number(field.attrs?.rows) || 5}
                  maxLength={Number(field.attrs?.maxlength) || 5000}
                  required={field.required} />
              ) : (
                <input
                  className={inputClass({ invalid: field.name in error })}
                  id={field.id}
                  name={field.name}
                  defaultValue={reviewValue(review, field.name) || field.value}
                  required={field.required} />
              )}
              {error[field.name]?.map((err, index) => (
                <div className={feedbackClass} key={index}>{err}</div>
              ))}
              {field.help && <small className={formTextClass}>{field.help}</small>}
            </div>
          ))}
        </div>
        <button className={`${buttonClass({ shadow: true })} mt-6`} type="submit">Опубликовать отзыв</button>
      </form>
    </>
  )
}
