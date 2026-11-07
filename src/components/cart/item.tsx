import { KeyboardEventHandler, useState, useEffect, FocusEventHandler } from 'react'
import Link from 'next/link'
import Image from 'next/image'

import { IconCircleX } from '@tabler/icons-react'

import { buttonClass } from '@/components/ui/button'
import { inputClass, labelClass } from '@/components/ui/form'
import NoImage from '@/components/product/no-image'

import { useDebounce } from '@/lib/debounce'
import { BasketItem, BasketItemProduct } from '@/lib/types'

function getUpdatedQuantity(value: string, quantity: number) {
    return value ? Math.min(10000, Math.max(1, +value)) : quantity
}

interface CartItemProps {
  item: BasketItem
  first: boolean
  last: boolean
  removeItem: (product: BasketItemProduct) => void
  setQuantity: (product: BasketItemProduct, quantity: number) => void
}

export default function CartItem({ item, first, last, removeItem, setQuantity }: CartItemProps) {
  const [inputValue, setInputValue] = useState(String(item.quantity))
  const debouncedInput = useDebounce(inputValue, 500)

  const handleKeyDown: KeyboardEventHandler<HTMLInputElement> = (e) => {
    if (e.key === 'Enter') {
      e.preventDefault()
      e.currentTarget.blur()
    }
  }

  const handleBlur: FocusEventHandler<HTMLInputElement> = () => {
    const quantity = getUpdatedQuantity(inputValue, item.quantity)
    setQuantity(item.product, quantity)
    if (String(quantity) !== inputValue)
      setInputValue(String(quantity))
  }

  useEffect(() => {
    if (debouncedInput === '')
      return
    const quantity = getUpdatedQuantity(debouncedInput, item.quantity)
    setQuantity(item.product, quantity)
  }, [debouncedInput, item.product, item.quantity, setQuantity])

  return (
    <div className={`my-2 items-center justify-between sm:flex ${first ? "pb-4" : "py-4"} ${last ? "" : "border-b"}`}>
      <div className="block items-center text-center sm:flex sm:text-start">
        <Link className="mx-auto inline-block shrink-0 sm:me-6" href={`/products/${item.product.code}`}>
          {item.product.image ? (
            <div className="relative size-40">
              <Image
                src={item.product.image}
                fill
                style={{ objectFit: 'contain' }}
                sizes="160px"
                alt={`${item.product.whatis ? item.product.whatis + ' ' : ''}${item.product.title}`} />
            </div>
          ) : (
            <NoImage size={160} />
          )}
        </Link>
        <div className="pt-2">
          <h3 className="mb-2 text-base leading-[1.2] font-medium">
            <Link className="text-heading hover:text-primary" href={`/products/${item.product.code}`}>
              {item.product.title}
            </Link>
          </h3>
          <div className="text-sm"><span className="me-2 text-muted">Цена:</span>{item.product.price.toLocaleString('ru')}<small>&nbsp;руб</small></div>
          {item.discount > 0 && <div className="text-sm"><span className="me-2 text-muted">Скидка:</span>{item.discount_text}</div>}
          <div className="pt-2 text-lg text-accent"><span>{item.price.toLocaleString('ru')}</span><small>&nbsp;руб</small></div>
        </div>
      </div>
      <div className="mx-auto max-w-36 pt-2 text-center sm:mx-0 sm:pt-0 sm:ps-4 sm:text-start">
        <label className={labelClass} htmlFor={`quantity-${item.product.id}`}>Количество</label>
        <input
          className={inputClass()}
          id={`quantity-${item.product.id}`}
          type="number"
          min="1"
          max="10000"
          value={inputValue}
          onChange={(e) => setInputValue(e.currentTarget.value)}
          onBlur={handleBlur}
          onKeyDown={handleKeyDown} />
        <button className={buttonClass({ variant: 'link-danger', size: 'flush' })} type="button" onClick={() => removeItem(item.product)}>
          <IconCircleX size={16} stroke={1.5} className="me-2" />Удалить
        </button>
      </div>
    </div>
  )
}
