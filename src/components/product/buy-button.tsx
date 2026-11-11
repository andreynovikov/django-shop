'use client'

import { ButtonLoading } from '@/components/loading'

import useBasket from '@/lib/basket'
import { Product, ProductInfo } from '@/lib/types'

// Puts the product in the basket, also when it is out of stock
export default function BuyButton({ product, className }: { product: ProductInfo | Product, className: string }) {
  const { addItem, addingProductId } = useBasket()
  const isAdding = addingProductId === product.id

  const handleClick = () => {
    if (!product.variations)
      addItem(product)
  }

  return (
    <button className={className} type="button" onClick={handleClick} disabled={isAdding}>
      {product.instock > 0 ? "Купить" : "Сообщить о поступлении"}
      {isAdding && <ButtonLoading />}
    </button>
  )
}
