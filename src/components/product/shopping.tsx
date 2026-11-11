'use client'

import { useState, useMemo } from 'react'

import Link from 'next/link'
import { IconShoppingCart } from '@tabler/icons-react'

import { ButtonLoading } from '@/components/loading'
import { buttonClass } from '@/components/ui/button'
import { selectClass } from '@/components/ui/form'

import useBasket from '@/lib/basket'
import { Product } from '@/lib/types'

export default function ProductShopping({ product }: { product: Product }) {
  const [quantity, setAddQuantity] = useState(1)
  const { basket, addItem, removeItem, setQuantity, addingProductId, isChanging, isEmpty, isSuccess } = useBasket()
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

  const handleSetQuantity = (delta: number) => {
    const quantity = Math.max(0, Math.min(10000, basketQuantity + delta))
    if (quantity === 0)
      removeItem(product)
    else
      setQuantity(product, quantity)
  }

  const handleCartClick = () => {
    // TODO: {% if utm_source %}?utm_source={{ utm_source }}{% endif %}
    addItem(product, quantity)
  }

  return basketQuantity > 0 ? (
    <>
      <div className="flex items-center justify-between">
        <button className={buttonClass({ variant: 'success', size: 'wide', shadow: true })} type="button" onClick={() => handleSetQuantity(-1)} disabled={isChanging} aria-label="Убрать одну штуку">
          -
        </button>
        <span className="px-2">
          <span className="hidden md:inline">В корзине: </span>
          {basketQuantity} шт
          {isChanging && <ButtonLoading />}
        </span>
        <button className={buttonClass({ variant: 'success', size: 'wide', shadow: true })} type="button" onClick={() => handleSetQuantity(+1)} disabled={isChanging} aria-label="Добавить ещё одну">
          +
        </button>
      </div>
      <Link href="/cart" className={`${buttonClass({ block: true })} mt-6`}>Оформить заказ</Link>
    </>
  ) : (
    <div className="flex items-center justify-between">
      {product.instock > 5 && (
        <select className={`${selectClass({ full: false })} me-4 w-20 shrink-0`} value={quantity} onChange={(e) => setAddQuantity(+e.target.value)} aria-label="Количество">
          <option value="1">1</option>
          <option value="2">2</option>
          <option value="3">3</option>
          <option value="4">4</option>
          <option value="5">5</option>
        </select>
      )}
      <button className={buttonClass({ variant: 'success', block: true, shadow: true })} type="button" onClick={handleCartClick} disabled={isAdding}>
        <IconShoppingCart size={18} stroke={1.5} className="me-2" />Купить
        {isAdding && <ButtonLoading />}
      </button>
    </div>
  )
}
