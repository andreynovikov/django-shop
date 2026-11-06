'use client'

import Link from 'next/link'

import { buttonClass } from '@/components/ui/button'

import rupluralize from '@/lib/rupluralize'
import useBasket from '@/lib/basket'

export default function CartNotice() {
  const { basket, isEmpty } = useBasket()

  if (isEmpty)
    return (
      <span className="my-1 text-center sm:text-end">
        {/* eslint-disable-next-line @next/next/no-img-element */}
        <img src="/i/cart.svg" alt="Корзина" height="33" className="inline h-[33px] w-auto" />Корзина пуста
      </span>
    )

  return (
    <span className="my-2 text-center sm:text-end">
      <Link href="/cart/">
        {/* eslint-disable-next-line @next/next/no-img-element */}
        <img src="/i/cart.svg" alt="Корзина" height="33" className="inline h-[33px] w-auto" />
        {' '}
        <span className="whitespace-nowrap">
          <span className="font-bold">{basket.quantity}</span>
          {' '}{rupluralize(basket.quantity, ['товар', 'товара', 'товаров'])}
          {' '}на{' '}
          <span className="font-bold">{basket.total.toLocaleString('ru')}</span>
          &nbsp;руб
        </span>
        <span className={`${buttonClass({ variant: 'success', size: 'sm' })} ms-2 font-bold`}>Оформить заказ</span>
      </Link>
    </span>
  )
}
