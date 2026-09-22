import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'

import { basketKeys, loadBaskets, createBasket, addBasketItem, removeBasketItem, updateBasketItem } from '@/lib/queries'
import { Basket, BasketItemProduct, Product, ProductInfo } from '@/lib/types'
import { eCommerce } from '@/lib/ymec'

type BasketProduct = BasketItemProduct | ProductInfo | Product

type ItemMutationType = {
  basketId: number
  product: BasketProduct
  quantity: number
}

function report(action: string, product: BasketProduct, price: number | undefined, quantity: number | undefined) {
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
    queryFn: () => loadBaskets()
  })

  const isEmpty = baskets === undefined || baskets.length === 0 || baskets[0].items.length === 0
  const basket = isEmpty ? {} as Basket : baskets[0]

  const createBasketMutation = useMutation({
    mutationFn: () => createBasket()
  })
  const addBasketItemMutation = useMutation({
    mutationFn: ({ basketId, product, quantity }: ItemMutationType) => addBasketItem(basketId, product.id, quantity),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: basketKeys.all })
    }
  })
  const removeBasketItemMutation = useMutation({
    mutationFn: ({ basketId, product }: Omit<ItemMutationType, 'quantity'>) => removeBasketItem(basketId, product.id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: basketKeys.all })
    }
  })
  const updateBasketItemMutation = useMutation({
    mutationFn: ({ basketId, product, quantity }: ItemMutationType) => updateBasketItem(basketId, product.id, quantity),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: basketKeys.all })
    }
  })

  const addItem = (product: ProductInfo | Product, quantity = 1) => {
    if (baskets === undefined || baskets.length === 0) {
      createBasketMutation.mutate(undefined, {
        onSuccess: (data) => {
          addBasketItemMutation.mutate(
            { basketId: data.id, product, quantity },
            {
              onSuccess: async () => report('add', product, product.cost, quantity)
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

  const removeItem = (product: ProductInfo | Product) => {
    const item = basket.items?.find(item => item.product.id === product.id)
    const cost = item?.price
    const quantity = item?.quantity
    removeBasketItemMutation.mutate(
      { basketId: baskets![0].id, product },
      {
        onSuccess: async () => report('remove', product, cost, quantity)
      }
    )
  }

  const setQuantity = (product: BasketProduct, quantity: number) => {
    const previousQuantity = basket.items?.find(item => item.product.id === product.id)?.quantity ?? 0
    updateBasketItemMutation.mutate(
      { basketId: baskets![0].id, product, quantity },
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
