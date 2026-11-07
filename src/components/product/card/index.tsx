import Link from 'next/link'
import Image from 'next/image'
import { IconEye } from '@tabler/icons-react'

import NoImage from '@/components/product/no-image'
import ProductPrice from '@/components/product/price'
import { buttonClass } from '@/components/ui/button'
import { contentClass } from '@/components/ui/content'

import { Category, ProductInfo } from '@/lib/types'

import FavoriteIcon from './favorite-icon'
import BasketButton from './basket-button'
import { ProductCardImpression, ProductCardLink } from './ecommerce'

export interface SearchProduct {
  id: number
  code: string | undefined
  instock: boolean
  title: string
  price: number
  cost: number
  image: string | undefined
  isnew: undefined
  recomended: undefined
  enabled: true
  variations: false
  partnumber: undefined
  whatisit: undefined
  whatis: undefined
  shortdescr: undefined
  sales: undefined
  sales_notes: undefined
}

interface ProductCardProps {
  product: ProductInfo | SearchProduct 
  limitedBadges?: boolean
  gtmCategory?: Pick<Category, 'name'>
  gtmList?: string
  gtmPosition?: number
}
export default function ProductCard({ product, limitedBadges = false, gtmCategory = undefined, gtmList = '', gtmPosition = 0 }: ProductCardProps) {
  return (
    // Cartzilla's product card: from lg up hovering raises it with a shadow and shows its hidden body below
    <div className="group relative flex h-full min-w-0 flex-col rounded-lg bg-white pb-5 transition-all duration-150 min-[500px]:pb-0 lg:hover:z-10 lg:hover:shadow-lg" itemProp="itemListElement" itemScope itemType="http://schema.org/Offer">
      <ProductCardImpression product={product} gtmList={gtmList} gtmPosition={gtmPosition} />
      <FavoriteIcon product={product} />
      <ProductCardLink className="mt-4 block" product={product} gtmCategory={gtmCategory} gtmList={gtmList} gtmPosition={gtmPosition}>
        <div className="m-4 p-4">
          <div className="relative aspect-square overflow-hidden p-4">
            {product.image ? (
              <Image
                src={product.image}
                fill
                style={{ objectFit: "contain" }}
                sizes="(min-width: 640px) 50vw, (min-width: 768px) 33vw, 100vw"
                loading="lazy"
                alt={`${product.title} ${product.whatisit ?? product.whatis}`}
                itemProp="image" />
            ) : (
              <NoImage />
            )}
          </div>
        </div>
      </ProductCardLink>
      <div className="relative z-2 flex flex-auto flex-col rounded-lg bg-white px-5 py-2">
        <ProductCardLink className="block pb-1 text-xs text-muted transition-colors hover:text-gray-700" product={product} gtmCategory={gtmCategory} gtmList={gtmList} gtmPosition={gtmPosition}>
          {product.whatisit ?? product.whatis} {product.partnumber}
        </ProductCardLink>
        <h3 className="mb-3 text-base leading-[1.2] font-medium">
          <ProductCardLink className="text-heading transition-colors hover:text-primary" product={product} gtmCategory={gtmCategory} gtmList={gtmList} gtmPosition={gtmPosition} itemProp="url">
            <span itemProp="name">{product.title}</span>
          </ProductCardLink>
        </h3>
        <div className="mt-auto">
          {product.enabled && (
            <div>
              {(product.isnew && !limitedBadges) && <span className="me-2 text-[.8em] font-bold text-warning">Новинка</span>}
              {(product.recomended && !limitedBadges) && <span className="me-2 text-[.8em] font-bold text-success">Рекомендуем</span>}
              {product.sales && product.sales.map((notice, index) => (
                notice && <span className="me-2 text-[.8em] font-bold text-danger" key={index}>{notice}</span>
              ))}
            </div>
          )}
          <div className="flex items-center justify-between">
            <div className="text-accent">
              {product.variations && "от "}
              <ProductPrice product={product} microdata />
            </div>
            <div>
              {product.variations ? (
                <Link className={buttonClass({ variant: 'secondary', size: 'sm', block: true })} href={product.variations} aria-label="Выбрать вариант">
                  <IconEye size={14} stroke={1.5} />
                </Link>
              ) : product.enabled && product.instock ? (
                <>
                  <link itemProp="availability" href="http://schema.org/InStock" />
                  <BasketButton product={product} />
                </>
              ) : (
                <>
                  <link itemProp="availability" href="http://schema.org/OutOfStock" />
                  <ProductCardLink className={buttonClass({ variant: 'secondary', size: 'sm', block: true })} product={product} gtmCategory={gtmCategory} gtmList={gtmList} gtmPosition={gtmPosition} aria-label="Подробнее">
                    <IconEye size={14} stroke={1.5} />
                  </ProductCardLink>
                </>
              )}
            </div>
            { /* TODO
                        <ReviewRating value={3} />
                        */
            }
          </div>
        </div>
      </div>
      <div className="invisible absolute top-full left-0 z-1 -mt-5 w-full rounded-b-lg bg-white p-5 opacity-0 transition-all duration-150 lg:group-hover:visible lg:group-hover:opacity-100 lg:group-hover:shadow-lg">
        {product.shortdescr && <div className={`${contentClass({ size: 'ms' })} pb-2`} dangerouslySetInnerHTML={{ __html: product.shortdescr }} itemProp="description"></div>}
        {product.sales_notes && <div className="pb-2 text-ms text-info">{product.sales_notes}</div>}
        {/*
                <div className="mb-2 flex">
                    { product.variations ? (
                        <Link className={buttonClass({ variant: 'success', size: 'sm', block: true })} href={product.variations}>
                            Выбрать
                        </Link>
                    ) : product.enabled && product.instock ? (
                        <button className={buttonClass({ variant: 'success', size: 'sm', block: true })} type="button" onClick={handleCartClick}>
                            <IconShoppingCart size={14} stroke={1.5} className="me-1" />
                            Купить
                        </button>
                    ) : (
                        <Link className={buttonClass({ variant: 'secondary', size: 'sm', block: true })} href={`/products/${product.code}`}>
                            Подробное описание
                        </Link>
                    )}
                </div>
                */
        }
      </div>
    </div>
  )
}
