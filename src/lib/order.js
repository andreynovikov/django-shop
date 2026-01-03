import { useRouter } from 'next/router'
import { useMutation, useQueryClient } from '@tanstack/react-query'

import { orderKeys, createOrder } from '@/lib/queries'
import { eCommerce } from '@/lib/ymec'

export function useCreateOrder() {
  const router = useRouter()
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: () => createOrder(),
    onSuccess: (data) => {
      queryClient.invalidateQueries(orderKeys.lists())
      queryClient.setQueryData(orderKeys.detail(data.id), data)
      sessionStorage.setItem('lastOrder', data.id)
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
      router.push('/confirmation')
      console.log(data)
    },
    onError: (error) => {
      console.error(error)
    }
  })
}