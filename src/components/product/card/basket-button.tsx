'use client'

import { useMemo } from 'react'
import { IconShoppingCart } from '@tabler/icons-react'

import { Spinner } from '@/components/loading'
import { buttonClass } from '@/components/ui/button'

import useBasket from '@/lib/basket'
import { Product, ProductInfo } from '@/lib/types'

import { SearchProduct } from '.'

export default function BasketButton({ product }: { product: ProductInfo | SearchProduct }) {
  const { basket, addItem, addingProductId, isSuccess, isEmpty } = useBasket()
  const isAdding = addingProductId === product.id

  const basketQuantity = useMemo(() => {
    if (!isSuccess || isEmpty)
      return 0
    const items = basket.items.filter(item => item.product.id == product.id)
    if (items.length > 0)
      return items[0].quantity
    else
      return 0
  }, [basket, product, isSuccess, isEmpty])

  const handleCartClick = () => {
    addItem(product as Product)
  }

  return (
    <button className={`${buttonClass({ variant: 'success', size: 'sm', block: true })} relative`} type="button" onClick={handleCartClick} disabled={isAdding} aria-label="В корзину">
      {isAdding ? <Spinner size="sm" /> : <IconShoppingCart size={14} stroke={1.5} />}
      {basketQuantity > 0 && <span className="absolute -top-2.5 -right-2.5 size-5 rounded-full bg-primary text-center text-xs leading-5 font-medium text-white">{basketQuantity}</span>}
    </button>
  )
}