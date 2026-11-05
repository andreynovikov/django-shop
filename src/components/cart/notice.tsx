'use client'

import Link from 'next/link'

import { buttonClass } from '@/components/ui/button'

import rupluralize from '@/lib/rupluralize'
import useBasket from '@/lib/basket'

export default function CartNotice() {
  const { basket, isEmpty } = useBasket()

  if (isEmpty)
    return (
      // eslint-disable-next-line @next/next/no-img-element
      <span><img className="inline" src="/i/cart.svg" alt="Корзина" height="33" />Корзина пуста</span>
    )

  return (
    <span>
      <Link href="/cart/">
        {/* eslint-disable-next-line @next/next/no-img-element */}
        <img className="inline" src="/i/cart.svg" alt="Корзина" height="33" />
        <span className="font-bold text-white">{basket.quantity}</span>
        {' '}{rupluralize(basket.quantity, ['товар', 'товара', 'товаров'])}
        {' '}на{' '}
        <span className="font-bold text-white">{basket.total.toLocaleString('ru')}</span>
        &nbsp;руб
        <span className={`${buttonClass({ variant: 'warning', size: 'sm' })} ms-2 font-bold`}>Оформить заказ</span>
      </Link>
    </span>
  )
}
