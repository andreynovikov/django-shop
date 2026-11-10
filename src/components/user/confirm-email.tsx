'use client'

import { Suspense, useEffect, useRef } from 'react'
import Link from 'next/link'
import { useSearchParams } from 'next/navigation'
import { useMutation, useQueryClient } from '@tanstack/react-query'

import { IconAlertTriangle, IconCircleCheck } from '@tabler/icons-react'

import { Loading } from '@/components/loading'
import { Alert } from '@/components/ui/alert'

import { confirmEmail, userKeys } from '@/lib/queries'

const alertIcon = { size: 18, stroke: 1.5 }

// Sends the token from the link once. It needs no session: the link may be opened on another device.
function Confirmation() {
  const token = useSearchParams().get('token') ?? ''
  const queryClient = useQueryClient()
  const sent = useRef(false)

  const { mutate, data, isError } = useMutation({
    mutationFn: (token: string) => confirmEmail(token),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: userKeys.details() }),
  })

  useEffect(() => {
    if (token && !sent.current) { // StrictMode runs effects twice
      sent.current = true
      mutate(token)
    }
  }, [token, mutate])

  if (!token || isError)
    return (
      <Alert variant="danger" icon={<IconAlertTriangle {...alertIcon} />}>
        Ссылка недействительна или устарела. Отправьте письмо ещё раз из <Link href="/user/profile/">профиля</Link>.
      </Alert>
    )

  if (data)
    return (
      <Alert variant="success" icon={<IconCircleCheck {...alertIcon} />}>
        Адрес {data.email} подтверждён, на него будут приходить уведомления о заказах.
        Перейти в <Link href="/user/profile/">профиль</Link>.
      </Alert>
    )

  return <Loading className="text-center" />
}

export default function ConfirmEmail() {
  return (
    <Suspense fallback={<Loading className="text-center" />}>
      <Confirmation />
    </Suspense>
  )
}
