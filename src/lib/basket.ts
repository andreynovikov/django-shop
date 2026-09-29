import { useCallback, useMemo } from 'react'
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
  const basket = useMemo(() => isEmpty ? {} as Basket : baskets[0], [baskets, isEmpty])

  const { mutate: mutateCreateBasket } = useMutation({
    mutationFn: () => createBasket()
  })
  const { mutate: mutateAddBasketItem } = useMutation({
    mutationFn: ({ basketId, product, quantity }: ItemMutationType) => addBasketItem(basketId, product.id, quantity),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: basketKeys.all })
    }
  })
  const { mutate: mutateRemoveBasketItem } = useMutation({
    mutationFn: ({ basketId, product }: Omit<ItemMutationType, 'quantity'>) => removeBasketItem(basketId, product.id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: basketKeys.all })
    }
  })
  const { mutate: mutateUpdateBasketItem } = useMutation({
    mutationFn: ({ basketId, product, quantity }: ItemMutationType) => updateBasketItem(basketId, product.id, quantity),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: basketKeys.all })
    }
  })

  const addItem = useCallback((product: ProductInfo | Product, quantity = 1) => {
    if (basket.id === undefined) {
      mutateCreateBasket(undefined, {
        onSuccess: (data) => {
          mutateAddBasketItem(
            { basketId: data.id, product, quantity },
            {
              onSuccess: async () => report('add', product, product.cost, quantity)
            }
          )
        }
      })
    } else {
      mutateAddBasketItem(
        { basketId: basket.id, product, quantity },
        {
          onSuccess: async () => report('add', product, product.cost, quantity)
        }
      )
    }
  }, [basket, mutateAddBasketItem, mutateCreateBasket])

  const removeItem = useCallback((product: BasketProduct) => {
    const item = basket.items?.find(item => item.product.id === product.id)
    const cost = item?.price
    const quantity = item?.quantity
    mutateRemoveBasketItem(
      { basketId: basket.id, product },
      {
        onSuccess: async () => report('remove', product, cost, quantity)
      }
    )
  }, [basket, mutateRemoveBasketItem])

  const setQuantity = useCallback((product: BasketProduct, quantity: number) => {
    const previousQuantity = basket.items?.find(item => item.product.id === product.id)?.quantity ?? 0
    if (previousQuantity === quantity)
      return
    mutateUpdateBasketItem(
      { basketId: basket.id, product, quantity },
      {
        onSuccess: async () => {
          if (previousQuantity < quantity)
            report('add', product, product.cost, quantity - previousQuantity)
        }
      }
    )
  }, [basket, mutateUpdateBasketItem])

  return { basket, addItem, removeItem, setQuantity, isEmpty, isSuccess, isLoading, isError }
}
