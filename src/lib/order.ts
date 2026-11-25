import { useTransition } from 'react'
import { useRouter } from 'next/navigation'
import { useMutation, useQueryClient } from '@tanstack/react-query'

import { basketScope } from '@/lib/basket'
import { orderKeys, createOrder, HttpError } from '@/lib/queries'
import { eCommerce } from '@/lib/ymec'

// The order waits for the basket changes made before it, such as a quantity sent when its field lost focus
// to the click on the order button. isPending covers the wait and the navigation to confirmation.
export function useCreateOrder() {
  const router = useRouter()
  const queryClient = useQueryClient()
  const [isNavigating, startTransition] = useTransition()

  const mutation = useMutation({
    mutationFn: createOrder,
    // Retry a lost response or server error with the same basket ID, even if Django has deleted the basket.
    retry: (failureCount, error) => failureCount < 1 && (!(error instanceof HttpError) || error.status >= 500),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: orderKeys.lists() })
      queryClient.setQueryData(orderKeys.detail(data.id), data)
      if (sessionStorage.getItem('lastOrder') !== String(data.id)) {
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
      }
      startTransition(() => router.push('/confirmation'))
    },
    onError: (error) => {
      console.error(error)
    },
    scope: basketScope
  })

  return { ...mutation, isPending: mutation.isPending || isNavigating }
}
