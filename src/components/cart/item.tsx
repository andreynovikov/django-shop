import { KeyboardEventHandler, useState, useEffect, FocusEventHandler } from 'react'
import Image from 'next/image'

import { IconCircleX } from '@tabler/icons-react'

import { buttonClass } from '@/components/ui/button'
import { formTextClass, inputClass, labelClass } from '@/components/ui/form'
import NoImage from '@/components/product/no-image'
import ProductLink from '@/components/product/product-link'

import { useDebounce } from '@/lib/debounce'
import { useSite } from '@/lib/site'
import { BasketItem, BasketItemProduct } from '@/lib/types'

// The quantity typed, in whole packs up to 10000, or the current one when nothing is typed
function getUpdatedQuantity(value: string, quantity: number, pack: number) {
  if (!value || isNaN(+value))
    return quantity
  return Math.min(Math.ceil(Math.max(1, +value) / pack), Math.floor(10000 / pack)) * pack
}

interface CartItemProps {
  item: BasketItem
  first: boolean
  last: boolean
  removeItem: (product: BasketItemProduct) => void
  setQuantity: (product: BasketItemProduct, quantity: number) => void
  isChanging: boolean  // a change from the cart is on its way to the basket, until the basket is loaded again
}

// The basket gets the typed quantity after a pause in typing, or right away when the field loses focus,
// e.g. to a click on the order button: basket changes run one at a time, and the order waits for it
export default function CartItem({ item, first, last, removeItem, setQuantity, isChanging }: CartItemProps) {
  const { site } = useSite()
  // a wholesale site sells the products sold in packs only in whole packs
  const pack = site.wholesale && item.product.ws_pack_only ? Math.max(1, item.product.pack_factor) : 1
  const [inputValue, setInputValue] = useState(String(item.quantity))
  const [isEditing, setIsEditing] = useState(false)
  const debouncedInput = useDebounce(inputValue, 500)
  // Out of the field it shows the quantity the basket gets, in whole packs. The site loads after the basket,
  // so the pack can become known after the quantity was typed, or with a basket quantity that isn't whole packs.
  const fieldValue = isEditing ? inputValue : String(getUpdatedQuantity(inputValue, item.quantity, pack))

  const handleKeyDown: KeyboardEventHandler<HTMLInputElement> = (e) => {
    if (e.key === 'Enter') {
      e.preventDefault()
      e.currentTarget.blur()
    }
  }

  const handleFocus: FocusEventHandler<HTMLInputElement> = () => {
    setIsEditing(true)
    setInputValue(fieldValue)
  }

  const handleBlur: FocusEventHandler<HTMLInputElement> = () => {
    setIsEditing(false)
    const quantity = getUpdatedQuantity(inputValue, item.quantity, pack)
    setQuantity(item.product, quantity)
    if (String(quantity) !== inputValue)
      setInputValue(String(quantity))
  }

  // After a pause in typing. It skips a value the field has moved on from, waits for the change on its way
  // and runs again when that is done, with the basket up to date, so the same quantity isn't sent twice.
  useEffect(() => {
    if (debouncedInput === '' || debouncedInput !== inputValue || isChanging)
      return
    const quantity = getUpdatedQuantity(debouncedInput, item.quantity, pack)
    setQuantity(item.product, quantity)
  }, [debouncedInput, inputValue, isChanging, item.product, item.quantity, pack, setQuantity])

  return (
    <div className={`my-2 items-center justify-between sm:flex ${first ? "pb-4" : "py-4"} ${last ? "" : "border-b"}`}>
      <div className="block items-center text-center sm:flex sm:text-start">
        <ProductLink className="mx-auto inline-block shrink-0 sm:me-6" code={item.product.code}>
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
        </ProductLink>
        <div className="pt-2">
          <h3 className="mb-2 text-base leading-[1.2] font-medium">
            <ProductLink className="text-heading hover:text-primary" code={item.product.code}>
              {item.product.title}
            </ProductLink>
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
          min={pack}
          max="10000"
          step={pack}
          value={fieldValue}
          onChange={(e) => setInputValue(e.currentTarget.value)}
          onFocus={handleFocus}
          onBlur={handleBlur}
          onKeyDown={handleKeyDown} />
        {pack > 1 && <span className={formTextClass}>кратно {pack}</span>}
        <button className={buttonClass({ variant: 'link-danger', size: 'flush' })} type="button" onClick={() => removeItem(item.product)}>
          <IconCircleX size={16} stroke={1.5} className="me-2" />Удалить
        </button>
      </div>
    </div>
  )
}
