'use client'

import { SubmitEvent, useEffect, useRef, useState } from 'react'

import { useMutation, useQueryClient } from '@tanstack/react-query'

import LoginForm from '@/components/user/login-form'

import { useSession } from '@/lib/session'
import { createSerial, HttpError, serialKeys } from '@/lib/queries'

import { Serial } from '@/lib/types'
import { buttonClass } from '@/components/ui/button'
import { inputClass } from '@/components/ui/form'

export default function ExtendWarrantyForm() {
  const [sn, setSN] = useState<string>()
  const [serial, setSerial] = useState<Serial>()
  const [errors, setErrors] = useState<string[]>()
  const registered = useRef(false)

  const session = useSession()

  const queryClient = useQueryClient()

  const { mutate } = useMutation<Serial, HttpError, string>({
    mutationFn: (number) => createSerial({ number }),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: serialKeys.lists() })
      setSerial(data)
    },
    // TODO: process errors
    // onError: (error) => setErrors(error.response?.json())
  })

  useEffect(() => {
    if (!registered.current && sn !== undefined && session?.status === 'authenticated') {
      registered.current = true
      mutate(sn)
    }
  }, [mutate, sn, session?.status])

  const handleSubmit = async (event: SubmitEvent<HTMLFormElement>) => {
    event.preventDefault()
    const form = event.currentTarget
    const input = form.elements.namedItem('sn') as HTMLInputElement
    if (input.value) {
      setSN(input.value)
    }
  }

  return (
    <div className="container mb-2 py-12 md:mb-6">
      {errors !== undefined ? (
        /* серийный номер уже был зарегистрирован */
        errors.map(error => (
          <p className="mb-4" key={error}>{error}</p>
        ))
      ) : serial !== undefined ? (
        /* серийный номер зарегистрирован */
        <p className="mb-4">
          Серийный номер <b>{serial.number}</b> зарегистрирован.{' '}
          {serial.approved ? 'И' : 'После проверки и'}нформация о нём
          {!serial.approved && ' будет'}{' '}доступна в личном кабинете.
        </p>
      ) : sn !== undefined && session?.status !== 'authenticated' ? (
        /* сюда мы попадаем только, если пользователь не авторизован */
        <LoginForm ctx="warranty" embedded="warranty" />
      ) : (
        /* первичный экран */
        <>
          <h3 className="mb-3 pb-2 text-h4">Заполните форму и увеличьте период бесплатного ремонта</h3>
          <p className="mb-4">
            Введите серийный номер швейной машины и продлите право на бесплатное устранение недостатков, возникших по вине изготовителя.
          </p>
          <p className="mb-4">
            Серийный номер указан на самой швейной машине (как правило, на наклейке на задней стороне корпуса), а также на упаковочной коробке
          </p>
          <form onSubmit={handleSubmit}>
            <div className="flex gap-4">
              <input type="text" name="sn" placeholder="Серийный номер" aria-label="Серийный номер" autoComplete="off" className={inputClass({ size: 'lg' })} />
              <button type="submit" className={buttonClass({ size: 'lg' })}>Продлить</button>
            </div>
          </form>
        </>
      )}
    </div>
  )
}
