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

type AddMutationType = Omit<ItemMutationType, 'basketId'> & {
  basketId: number | undefined // made on the first addition
}

// Basket changes and orders run one at a time in the order they were made, from any component:
// TanStack Query starts a mutation of a scope only when the one before it, with its onSuccess, is done.
// So two changes can't arrive in the wrong order, and an order includes every change made before it.
export const basketScope = { id: 'basket' }

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

  // Each mutation is pending until the basket is loaded again, so its button stays disabled
  // until the page shows the change, and a second tap can't send the request again
  const refetchBasket = () => queryClient.invalidateQueries({ queryKey: basketKeys.all })

  const { mutate: mutateAddBasketItem, isPending: isAddPending, variables: addVariables } = useMutation({
    mutationFn: async ({ basketId, product, quantity }: AddMutationType) =>
      addBasketItem(basketId ?? (await createBasket()).id, product.id, quantity),
    onSuccess: refetchBasket,
    scope: basketScope
  })
  const { mutate: mutateRemoveBasketItem, isPending: isRemovePending } = useMutation({
    mutationFn: ({ basketId, product }: Omit<ItemMutationType, 'quantity'>) => removeBasketItem(basketId, product.id),
    onSuccess: refetchBasket,
    scope: basketScope
  })
  const { mutate: mutateUpdateBasketItem, isPending: isUpdatePending } = useMutation({
    mutationFn: ({ basketId, product, quantity }: ItemMutationType) => updateBasketItem(basketId, product.id, quantity),
    onSuccess: refetchBasket,
    scope: basketScope
  })

  const addItem = useCallback((product: ProductInfo | Product, quantity = 1) => {
    mutateAddBasketItem(
      { basketId: basket.id, product, quantity },
      {
        onSuccess: async () => report('add', product, product.cost, quantity)
      }
    )
  }, [basket, mutateAddBasketItem])

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
    // The loaded quantity is out of date while a change of the product is on its way or waiting in the scope:
    // with 1 loaded and 5 on its way, 1 has to be sent again
    const isProductChanging = queryClient.isMutating({
      predicate: m => m.options.scope?.id === basketScope.id && (m.state.variables as { product?: BasketProduct } | undefined)?.product?.id === product.id
    }) > 0
    if (previousQuantity === quantity && !isProductChanging)
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
  }, [basket, mutateUpdateBasketItem, queryClient])

  // the product of this hook's addItem() call in progress, for the button that made it
  const addingProductId = isAddPending ? addVariables?.product.id : undefined
  // a removeItem() or setQuantity() call of this hook in progress
  const isChanging = isRemovePending || isUpdatePending

  return { basket, addItem, removeItem, setQuantity, addingProductId, isChanging, isEmpty, isSuccess, isLoading, isError }
}
