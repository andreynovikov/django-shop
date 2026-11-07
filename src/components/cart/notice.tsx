'use client'

import Link from 'next/link'
import Image from 'next/image'
import { useRouter } from 'next/navigation'
import { IconBasket, IconChevronRight, IconShoppingCart } from '@tabler/icons-react'

import { ButtonLoading } from '@/components/loading'
import NoImage from '@/components/product/no-image'
import { badgeClass } from '@/components/ui/badge'
import { buttonClass } from '@/components/ui/button'
import { handheldBadgeClass, handheldIconClass, handheldItemClass, handheldLabelClass } from '@/components/ui/handheld-toolbar'
import { hoverMenuClass } from '@/components/ui/menu'
import { navbarToolCaptionClass, navbarToolClass, navbarToolIconClass, navbarToolLabelClass, navbarToolTextClass } from '@/components/ui/navbar'
import { widgetProductMetaClass, widgetProductTitleClass } from '@/components/ui/widget'

import useBasket from '@/lib/basket'
import { useCreateOrder } from '@/lib/order'
import { useSession } from '@/lib/session'
import { BasketItemProduct } from '@/lib/types'

export function MobileCartNotice({ extraItemsCount }: { extraItemsCount: number }) {
  const { basket, isEmpty } = useBasket()

  return (
    <Link className={`${handheldItemClass} ${isEmpty && extraItemsCount > 2 ? 'max-md:hidden' : ''}`} href="/cart" aria-label="Корзина">
      <span className={handheldIconClass}>
        <IconShoppingCart size={20} stroke={1.5} />
        {!isEmpty && <span className={handheldBadgeClass} title="Товаров в корзине">{basket.quantity}</span>}
      </span>
      <span className={handheldLabelClass}>
        {isEmpty ? <>Корзина&nbsp;пуста</> : <>{basket.total.toLocaleString('ru')}&nbsp;руб</>}
      </span>
    </Link>
  )
}

export default function CartNotice() {
  const { status } = useSession()
  const { basket, isEmpty, removeItem } = useBasket()
  const { mutate, isPending } = useCreateOrder()
  const router = useRouter()

  const handleRemoveItem = (product: BasketItemProduct) => {
    removeItem(product)
  }

  const handleCreateOrder = () => {
    if (status === 'authenticated')
      mutate()
    else
      router.push('/cart')
  }

  if (isEmpty)
    return (
      <div className={`${navbarToolClass} ms-4 hidden lg:flex`}>
        <span className={navbarToolIconClass({ secondary: true })}><IconShoppingCart size={20} stroke={1.5} /></span>
        <span className={navbarToolTextClass()}><small className={navbarToolCaptionClass}>Корзина</small>пуста</span>
      </div>
    )

  return (
    <div className={`${navbarToolClass} ms-4 hidden lg:flex`}>
      <Link className={navbarToolIconClass({ secondary: true })} href="/cart" aria-label="Корзина">
        <span className={navbarToolLabelClass} title="Товаров в корзине">{basket.quantity}</span><IconShoppingCart size={20} stroke={1.5} />
      </Link>
      <Link className={navbarToolTextClass({ dropdown: true })} href="/cart">
        <small className={navbarToolCaptionClass}>Корзина</small>{basket.total.toLocaleString('ru')}<small>&nbsp;руб</small>
      </Link>
      <div className={hoverMenuClass}>
        <div className="w-[25rem] px-4 pt-2 pb-4">
          <div className="h-60 overflow-y-auto pe-4 [scrollbar-width:thin]">
            {basket.items.map((item, index) => (
              <div key={item.product.id} className={`group/item relative border-b ${index === 0 ? 'pb-2' : 'py-2'}`}>
                <button
                  className="invisible absolute top-1/2 left-0 -translate-y-1/2 text-2xl leading-none font-light text-danger opacity-0 transition-[visibility,opacity] duration-250 group-hover/item:visible group-hover/item:opacity-100"
                  onClick={() => handleRemoveItem(item.product)}
                  aria-label="Удалить">
                  <span aria-hidden="true">&times;</span>
                </button>
                <div className="flex items-center transition-transform duration-250 group-hover/item:translate-x-[1.125rem]">
                  <Link
                    className="relative block size-16 shrink-0"
                    href={`/products/${item.product.code}`}>
                    {item.product.image ? (
                      <Image
                        src={item.product.image}
                        fill
                        style={{ objectFit: 'contain' }}
                        sizes="64px"
                        loading="lazy"
                        alt={`${item.product.whatis ? item.product.whatis + ' ' : ''}${item.product.title}`} />
                    ) : (
                      <NoImage size={64} />
                    )}
                  </Link>
                  <div className="ps-2">
                    <h6 className={`mb-1 ${widgetProductTitleClass}`}>
                      <Link href={`/products/${item.product.code}`}>
                        {item.product.title}
                      </Link>
                    </h6>
                    <div className={widgetProductMetaClass}>
                      <span className="me-2 text-accent">{item.cost.toLocaleString('ru')}<small>&nbsp;руб</small></span>
                      <span className="text-muted">x {item.quantity}</span>
                      {item.product.instock < 1 && <span className="ms-1 text-lg"><sup><span className={`${badgeClass({ pill: true })} bg-warning text-white`}>нет в наличии</span></sup></span>}
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
          <div className="flex flex-wrap items-center justify-between py-4">
            <div className="me-2 py-2 text-sm">
              <span className="text-muted">Всего:</span>
              <span className="ms-1 text-base text-accent">{basket.total.toLocaleString('ru')}<small>&nbsp;руб</small></span>
            </div>
            <Link className={buttonClass({ variant: 'outline-secondary', size: 'sm' })} href="/cart">
              Открыть корзину<IconChevronRight size={14} stroke={1.5} className="-me-1 ms-1" />
            </Link>
          </div>
          <button className={buttonClass({ size: 'sm', block: true })} type="button" onClick={handleCreateOrder} disabled={isPending}>
            <IconBasket size={16} stroke={1.5} className="me-2" />Оформить заказ
            {isPending && <ButtonLoading />}
          </button>
        </div>
      </div>
    </div>
  )
};
