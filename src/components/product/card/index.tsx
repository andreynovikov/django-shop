'use client'

import { ReactNode, useMemo, useState } from 'react'
import Image from 'next/image'
import { useQuery } from '@tanstack/react-query'

import Lightbox from 'yet-another-react-lightbox'

import { IconChevronCompactLeft, IconChevronCompactRight, IconX } from '@tabler/icons-react'

import NoImage from '@/components/product/no-image'
import QuantityInput from '@/components/cart/quantity-input'
import { buttonClass } from '@/components/ui/button'

import useBasket from '@/lib/basket'
import { productKeys, getProductImages } from '@/lib/queries'
import { Category, ProductInfo } from '@/lib/types'

import { ProductCardImpression, ProductCardLink } from './ecommerce'

interface ProductCardProps {
  product: ProductInfo
  gtmCategory?: Pick<Category, 'name'>
  gtmList?: string
  gtmPosition?: number
}

// Dor Tak has no product pages: a product with variations links to their category, any other one opens its images.
// The quantity in the basket is changed right in the card.
export default function ProductCard({ product, gtmCategory = undefined, gtmList = '', gtmPosition = 0 }: ProductCardProps) {
  const [showImage, setShowImage] = useState(false)
  const { basket, addItem, setQuantity, addingProductId, isChanging, isEmpty, isSuccess, isLoading } = useBasket()
  // this card's change is on its way to the basket, the input holds the next one until it is done
  const isPending = addingProductId === product.id || isChanging

  // the extra images are loaded when the lightbox is opened
  const { data: images } = useQuery({
    queryKey: productKeys.images(product.id),
    queryFn: () => getProductImages(product.id),
    enabled: !!product.image && showImage,
    placeholderData: [],
  })

  const item = useMemo(() => {
    if (!isSuccess || isEmpty)
      return null
    return basket.items.find((item) => item.product.id === product.id) ?? null
  }, [basket, isEmpty, isSuccess, product])

  const updateQuantity = (quantity: number) => {
    if (item === null && quantity > 0)
      addItem(product, quantity)
    else if (item !== null && quantity !== item.quantity)
      setQuantity(product, quantity)
  }

  const productAction = (children: ReactNode, className?: string) => product.variations ? (
    <ProductCardLink className={className} product={product} gtmCategory={gtmCategory} gtmList={gtmList} gtmPosition={gtmPosition}>
      {children}
    </ProductCardLink>
  ) : (
    <a className={className} onClick={() => setShowImage(true)} style={{ cursor: 'pointer' }}>
      {children}
    </a>
  )

  return (
    <div className="flex flex-col rounded-md border border-black/10 bg-white max-sm:my-[.2rem]">
      <ProductCardImpression product={product} gtmList={gtmList} gtmPosition={gtmPosition} />
      <div className="flex-auto p-2 text-center">
        {productAction(product.image ? (
          <div className="relative mx-auto" style={{ width: 120, height: 120 }}>
            <Image
              src={product.image}
              fill
              style={{ objectFit: 'contain' }}
              sizes="160px"
              alt={`${product.whatis ? product.whatis + ' ' : ''}${product.title}`} />
          </div>
        ) : (
          <NoImage size={160} className="text-muted" />
        ))}
        <div className="relative pt-4">
          <div className="absolute -top-4">
            {product.isnew && <span className="ps-px opacity-90">Новинка</span>}
            {product.recomended && <span className="ps-px opacity-90">Рекомендуем</span>}
            { /* TODO - list actions */}
          </div>
          <h3 className="mb-2 text-h6 font-bold">
            {productAction(product.title.replace('Dor Tak', ''), 'text-black no-underline')}
          </h3>
          {product.whatis && <p>{product.whatis}</p>}
          {product.shortdescr && <div className="backend-content text-[#555]" dangerouslySetInnerHTML={{ __html: product.shortdescr }} />}
        </div>

        {product.price > 0 && (
          <div className="mt-2">
            {product.variations ? (
              <ProductCardLink className={buttonClass({ variant: 'success', size: 'sm' })} role="button" product={product} gtmCategory={gtmCategory} gtmList={gtmList} gtmPosition={gtmPosition}>
                Выбрать
              </ProductCardLink>
            ) : (product.ws_pack_only && product.instock >= product.pack_factor) || (!product.ws_pack_only && product.instock > 0) ? (
              <QuantityInput
                quantity={item !== null ? item.quantity : undefined}
                setQuantity={updateQuantity}
                packOnly={product.ws_pack_only}
                packFactor={product.pack_factor}
                isLoading={isLoading}
                isPending={isPending} />
            ) : (
              <div className="font-bold text-[#aaa]">Закончились</div>
            )}
            <div className="mt-2 text-xs">
              <span className="text-base font-bold">
                { /* TODO: show user price! */}
                {product.cost.toLocaleString('ru')}
              </span>
              &#8239;&#8381;
              {product.ws_pack_only && "/шт."}
              {(product.ws_pack_only && product.pack_factor !== 1) && (
                <> Продажа упаковками по {product.pack_factor} шт.</>
              )}
            </div>
          </div>
        )}

        {product.sales_notes && <div className="text-center">{product.sales_notes}</div>}
        {product.image && (
          <Lightbox
            open={showImage}
            close={() => setShowImage(false)}
            slides={[{ src: product.image }, ...(images ?? [])]}
            carousel={{
              finite: true
            }}
            render={{
              iconPrev: () => <IconChevronCompactLeft size={64} />,
              iconNext: () => <IconChevronCompactRight size={64} />,
              iconClose: () => <IconX size={64} />
            }}
          />
        )}
      </div>
    </div>
  )
}
