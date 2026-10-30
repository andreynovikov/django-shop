'use client'

import { useMemo } from 'react'

import useBasket from '@/lib/basket'
import { Product, ProductInfo } from '@/lib/types'

import { SearchProduct } from '.'

export default function BasketButton({ product }: { product: ProductInfo | SearchProduct }) {
  const { basket, addItem, isSuccess, isEmpty } = useBasket()

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
    <button className="btn btn-success btn-sm d-block w-100 sw-button" type="button" onClick={handleCartClick}>
      <i className="ci-cart fs-sm" />
      {basketQuantity > 0 && <span className="sw-button-label">{basketQuantity}</span>}
    </button>
  )
}