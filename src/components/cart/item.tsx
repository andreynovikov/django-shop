import Image from 'next/image'

import { IconTrashX } from '@tabler/icons-react'

import NoImage from '@/components/product/no-image'
import QuantityInput from '@/components/cart/quantity-input'
import { labelClass } from '@/components/ui/form'

import { BasketItem, BasketItemProduct } from '@/lib/types'

interface CartItemProps {
  item: BasketItem
  first: boolean
  last: boolean
  removeItem: (product: BasketItemProduct) => void
  setQuantity: (product: BasketItemProduct, quantity: number) => void
}

// Dor Tak has no product pages, so the item isn't linked. The quantity is changed in packs where the product is sold in packs.
export default function CartItem({ item, first, last, removeItem, setQuantity }: CartItemProps) {
  return (
    <div className={"my-2 items-center justify-between sm:flex " + (first ? "pb-4" : "py-4") + (last ? "" : " border-b")}>
      <div className="block items-center text-center sm:flex sm:text-start">
        {item.product.image ? (
          <div className="relative" style={{ width: 160, height: 160 }}>
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
        <div className="pt-2">
          <h3 className="mb-2 text-h6">
            {item.product.title}
          </h3>
          <div className="text-sm"><span className="me-2 text-muted">Цена:</span>{item.product.price.toLocaleString('ru')}<small>&nbsp;руб</small></div>
          {item.discount > 0 && <div className="text-sm"><span className="me-2 text-muted">Скидка:</span>{item.discount_text}</div>}
          <div className="pt-2 text-lg text-accent"><span>{item.price.toLocaleString('ru')}</span><small>&nbsp;руб</small></div>
        </div>
      </div>
      <div className="mx-auto pt-2 text-center sm:mx-0 sm:ps-4 sm:pt-0 sm:text-start" style={{ maxWidth: "9rem" }}>
        <label className={labelClass}>Количество</label>
        <QuantityInput
          quantity={item.quantity}
          setQuantity={(quantity) => setQuantity(item.product, quantity)}
          packOnly={item.product.ws_pack_only}
          packFactor={item.product.pack_factor} />
        <button className="inline-flex items-center border border-transparent py-1.5 text-danger underline" type="button" onClick={() => removeItem(item.product)}>
          <IconTrashX size={20} stroke={1.5} className="me-1" />
          Удалить
        </button>
      </div>
    </div>
  )
}
