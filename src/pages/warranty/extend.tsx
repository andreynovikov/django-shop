import { FormEvent, useEffect, useRef, useState, type ReactElement } from 'react'

import { useMutation, useQueryClient } from '@tanstack/react-query'

import { AxiosError } from 'axios'

import PageLayout from '@/components/layout/page'
import LoginForm from '@/components/login-form'

import { useSession } from '@/lib/session'
import { createSerial, serialKeys } from '@/lib/queries'

import { Serial } from '@/lib/types'

export default function ExtendWarranty() {
  const [sn, setSN] = useState<string>()
  const [serial, setSerial] = useState<Serial>()
  const [errors, setErrors] = useState<string[]>()
  const registered = useRef(false)

  const session = useSession()

  const queryClient = useQueryClient()

  const createSerialMutation = useMutation<Serial, AxiosError<string[]>, string>({
    mutationFn: (number) => createSerial({ number }),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: serialKeys.lists() })
      setSerial(data)
    },
    onError: (error) => setErrors(error.response?.data)
  })

  useEffect(() => {
    if (!registered.current && sn !== undefined && session?.status === 'authenticated') {
      registered.current = true
      createSerialMutation.mutate(sn)
    }
  }, [createSerialMutation, sn, session?.status])

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    const form = event.currentTarget
    const input = form.elements.namedItem('sn') as HTMLInputElement
    if (input.value) {
      setSN(input.value)
    }
  }

  return (
    <div className="container py-5 mb-2 mb-md-4">
      {errors !== undefined ? (
        /* серийный номер уже был зарегистрирован */
        errors.map(error => (
          <p key={error}>{error}</p>
        ))
      ) : serial !== undefined ? (
        /* серийный номер зарегистрирован */
        <p>
          Серийный номер <b>{serial.number}</b> зарегистрирован.{' '}
          {serial.approved ? 'И' : 'После проверки и'}нформация о нём
          {!serial.approved && ' будет'}{' '}доступна в личном кабинете.
        </p>
      ) : sn !== undefined && session?.status !== 'authenticated' ? (
        /* сюда мы попадаем только, если пользователь не авторизован */
        <LoginForm ctx="warranty" phone="" embedded="warranty" />
      ) : (
        /* первичный экран */
        <>
          <h3 className="h4 pb-2">Заполните форму и увеличьте период бесплатного ремонта</h3>
          <p>
            Введите серийный номер швейной машины и продлите право на бесплатное устранение недостатков, возникших по вине изготовителя.
          </p>
          <p>
            Серийный номер указан на самой швейной машине (как правило, на наклейке на задней стороне корпуса), а также на упаковочной коробке
          </p>
          <form onSubmit={handleSubmit}>
            <div className="d-flex gap-3">
              <input type="text" name="sn" placeholder="Серийный номер" autoComplete="off" className="form-control form-control-lg" />
              <button type="submit" className="btn btn-primary btn-lg"><i className="fs-lg me-2" />Продлить</button>
            </div>
          </form>
        </>
      )}
    </div>
  )
}

ExtendWarranty.getLayout = function getLayout(page: ReactElement) {
  return (
    <PageLayout title="Расширение гарантии" hideSignIn hideCartNotice>
      {page}
    </PageLayout>
  )
}
