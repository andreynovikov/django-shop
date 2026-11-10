'use client'

import { useEffect, useRef } from 'react'
import Link from 'next/link'
import { useRouter } from 'next/navigation'
import { useMutation, useQueryClient } from '@tanstack/react-query'

import { IconAlertTriangle } from '@tabler/icons-react'

import { Loading } from '@/components/loading'
import { Alert } from '@/components/ui/alert'

import { basketKeys, clearBasket, restoreBasket } from '@/lib/queries'

// A link in the abandoned basket email: puts its products into the visitor's basket, unless they have one,
// or empties the basket it was sent for. Then the cart opens, with the link's query for the statistics.
export default function BasketLink({ action, value }: { action: 'restore' | 'clear', value: string }) {
  const router = useRouter()
  const queryClient = useQueryClient()
  const sent = useRef(false)

  const { mutate, isError } = useMutation({
    mutationFn: () => action === 'restore'
      ? restoreBasket(value, new URLSearchParams(window.location.search).get('utm_source'))
      : clearBasket(value),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: basketKeys.all })
      router.replace('/cart/' + window.location.search)
    },
  })

  useEffect(() => {
    if (!sent.current) { // StrictMode runs effects twice
      sent.current = true
      mutate()
    }
  }, [mutate])

  if (isError)
    return (
      <Alert variant="danger" icon={<IconAlertTriangle size={18} stroke={1.5} />}>
        {action === 'restore' ? 'Не удалось восстановить корзину.' : 'Ссылка недействительна.'}
        {' '}Перейти в <Link href="/cart/">корзину</Link>.
      </Alert>
    )

  return <Loading className="my-12 py-12 text-center" mega />
}
