import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'

import { basketKeys, loadBasket, createBasket, addBasketItem, removeBasketItem, updateBasketItem } from '@/lib/queries'
import { eCommerce } from '@/lib/ymec'

function report(action, product, price, quantity) {
  eCommerce({
    [action]: {
      products: [{
        id: `${product.id}`,
        name: `${product.partnumber ? product.partnumber + ' ' : ''}${product.title}`,
        price,
        quantity
      }]
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
              onSuccess: async () => report('addToCart', 'add', product, product.cost, product.quantity)
            }
          )
        }
      })
    } else {
      addBasketItemMutation.mutate(
        { basketId: baskets[0].id, product, quantity },
        {
          onSuccess: async () => report('add', product, product.cost, quantity)
        }
      )
    }
  }

  const removeItem = (product) => {
    const item = basket.items?.find(item => item.product.id === product.id)
    const cost = item?.price
    const quantity = item?.quantity
    removeBasketItemMutation.mutate(
      { basketId: baskets[0].id, product },
      {
        onSuccess: async () => report('remove', product, cost, quantity)
      }
    )
  }

  const setQuantity = (product, quantity) => {
    const previousQuantity = basket.items?.find(item => item.product.id === product.id)?.quantity
    updateBasketItemMutation.mutate(
      { basketId: baskets[0].id, product, quantity },
      {
        onSuccess: async () => {
          if (previousQuantity < quantity)
            report('add', product, product.cost, quantity - previousQuantity)
        }
      }
    )
  }

  return { basket, addItem, removeItem, setQuantity, isEmpty, isSuccess, isLoading, isError }
}
