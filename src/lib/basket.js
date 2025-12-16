import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'

import { basketKeys, loadBasket, createBasket, addBasketItem, removeBasketItem, updateBasketItem } from '@/lib/queries'
import { eCommerce } from '@/lib/ymec'

function report(event, product, quantity) {
  eCommerce({
    event,
    ecommerce: {
      currencyCode: 'RUB',
      add: {
        products: [{
          id: `${product.id}`,
          name: `${product.partnumber ? product.partnumber + ' ' : ''}${product.title}`,
          price: `${product.cost}`,
          quantity
        }]
      }
    }
  })
}

export default function useBasket() {
  const queryClient = useQueryClient()

  const { data: baskets, isSuccess, isLoading, isError } = useQuery({
    queryKey: basketKeys.details(),
    queryFn: () => loadBasket()
  })

  const isEmpty = baskets === undefined || baskets.length === 0 || baskets[0].items.length === 0
  const basket = isEmpty ? {} : baskets[0]

  const createBasketMutation = useMutation({
    mutationFn: () => createBasket()
  })
  const addBasketItemMutation = useMutation({
    mutationFn: ({ basketId, product, quantity }) => addBasketItem(basketId, product.id, quantity),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: basketKeys.all })
    }
  })
  const removeBasketItemMutation = useMutation({
    mutationFn: ({ basketId, product }) => removeBasketItem(basketId, product.id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: basketKeys.all })
    }
  })
  const updateBasketItemMutation = useMutation({
    mutationFn: ({ basketId, product, quantity }) => updateBasketItem(basketId, product.id, quantity),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: basketKeys.all })
    }
  })

  const addItem = (product, quantity = 1) => {
    if (baskets.length === 0) {
      createBasketMutation.mutate(undefined, {
        onSuccess: (data) => {
          addBasketItemMutation.mutate(
            { basketId: data.id, product, quantity },
            {
              onSuccess: async () => report('addToCart', product, quantity)
            }
          )
        }
      })
    } else {
      addBasketItemMutation.mutate(
        { basketId: baskets[0].id, product, quantity },
        {
          onSuccess: async () => report('addToCart', product, quantity)
        }
      )
    }
  }

  const removeItem = (product) => {
    removeBasketItemMutation.mutate({ basketId: baskets[0].id, product })
  }

  const setQuantity = (product, quantity) => {
    updateBasketItemMutation.mutate({ basketId: baskets[0].id, product, quantity })
  }

  return { basket, addItem, removeItem, setQuantity, isEmpty, isSuccess, isLoading, isError }
}
