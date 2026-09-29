import { KeyboardEventHandler, useState, useEffect, FocusEventHandler } from 'react'
import Link from 'next/link'
import Image from 'next/image'

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
    <div className={"d-sm-flex justify-content-between align-items-center my-2 " + (first ? "pb-3" : "py-3") + (!last && " border-bottom")}>
      <div className="d-block d-sm-flex align-items-center text-center text-sm-start">
        <Link className="d-inline-block flex-shrink-0 mx-auto me-sm-4" href={{ pathname: '/products/[code]', query: { code: item.product.code } }}>
          {item.product.image ? (
            <div className="position-relative" style={{ width: 160, height: 160 }}>
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
          <h3 className="product-title fs-base mb-2">
            <Link href={{ pathname: '/products/[code]', query: { code: item.product.code } }}>
              {item.product.title}
            </Link>
          </h3>
          <div className="fs-sm"><span className="text-muted me-2">Цена:</span>{item.product.price.toLocaleString('ru')}<small>&nbsp;руб</small></div>
          {item.discount > 0 && <div className="fs-sm"><span className="text-muted me-2">Скидка:</span>{item.discount_text}</div>}
          <div className="fs-lg text-accent pt-2"><span>{item.price.toLocaleString('ru')}</span><small>&nbsp;руб</small></div>
        </div>
      </div>
      <div className="pt-2 pt-sm-0 ps-sm-3 mx-auto mx-sm-0 text-center text-sm-start" style={{ maxWidth: "9rem" }}>
        <label className="form-label" htmlFor="quantity">Количество</label>
        <input
          className="form-control"
          type="number"
          min="1"
          max="10000"
          value={inputValue}
          onChange={(e) => setInputValue(e.currentTarget.value)}
          onBlur={handleBlur}
          onKeyDown={handleKeyDown} />
        <button className="btn btn-link px-0 text-danger" type="button" onClick={() => removeItem(item.product)}>
          <i className="ci-close-circle me-2" />Удалить
        </button>
      </div>
    </div>
  )
}