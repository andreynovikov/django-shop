import { useTransition } from 'react'
import { useRouter } from 'next/navigation'
import { useMutation, useQueryClient } from '@tanstack/react-query'

import { basketScope } from '@/lib/basket'
import { orderKeys, createOrder } from '@/lib/queries'
import { eCommerce } from '@/lib/ymec'

// The order waits for the basket changes made before it, such as a quantity sent when its field lost focus
// to the click on the order button. isPending covers the wait too, and lasts until the confirmation page is shown:
// the basket stays on screen until then, and a second click would order it again.
export function useCreateOrder() {
  const router = useRouter()
  const queryClient = useQueryClient()
  const [isNavigating, startTransition] = useTransition()

  const mutation = useMutation({
    mutationFn: () => createOrder(),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: orderKeys.lists() })
      queryClient.setQueryData(orderKeys.detail(data.id), data)
      sessionStorage.setItem('lastOrder', String(data.id))
      eCommerce({
        purchase: {
          actionField: {
            id: data.id
          },
          products: data.items.map(item => ({
            id: item.product.id,
            name: item.product.title,
            price: item.price,
            quantity: item.quantity
          }))
        }
      })
      startTransition(() => router.push('/confirmation'))
    },
    onError: (error) => {
      console.error(error)
    },
    scope: basketScope
  })

  return { ...mutation, isPending: mutation.isPending || isNavigating }
}