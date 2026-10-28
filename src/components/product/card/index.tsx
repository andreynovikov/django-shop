import Link from 'next/link'
import Image from 'next/image'

import NoImage from '@/components/product/no-image'
import ProductPrice from '@/components/product/price'

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
    <div className="card product-card h-100" itemProp="itemListElement" itemScope itemType="http://schema.org/Offer">
      <ProductCardImpression product={product} gtmList={gtmList} gtmPosition={gtmPosition} />
      <FavoriteIcon product={product} />
      <ProductCardLink className="d-block mt-3 p-6" product={product} gtmCategory={gtmCategory} gtmList={gtmList} gtmPosition={gtmPosition}>
        <div className="m-3 p-3">
          <div className="position-relative p-3 overflow-hidden" style={{ aspectRatio: 1 }}>
            {product.image ? (
              <Image
                src={product.image}
                fill
                style={{ objectFit: "contain" }}
                sizes="(min-width: 500px) 50vw, (min-width: 768px) 33vw, 100vw"
                loading="lazy"
                alt={`${product.title} ${product.whatisit ?? product.whatis}`}
                itemProp="image" />
            ) : (
              <NoImage />
            )}
          </div>
        </div>
      </ProductCardLink>
      <div className="d-flex flex-column card-body py-2">
        <ProductCardLink className="product-meta d-block fs-xs pb-1" product={product} gtmCategory={gtmCategory} gtmList={gtmList} gtmPosition={gtmPosition}>
          {product.whatisit ?? product.whatis} {product.partnumber}
        </ProductCardLink>
        <h3 className="product-title fs-6">
          <ProductCardLink product={product} gtmCategory={gtmCategory} gtmList={gtmList} gtmPosition={gtmPosition} itemProp="url">
            <span itemProp="name">{product.title}</span>
          </ProductCardLink>
        </h3>
        <div className="mt-auto">
          {product.enabled && (
            <div>
              {(product.isnew && !limitedBadges) && <span className="small fw-bold me-2 text-info">Новинка</span>}
              {(product.recomended && !limitedBadges) && <span className="small fw-bold me-2 text-success">Рекомендуем</span>}
              {product.sales && product.sales.map((notice, index) => (
                notice && <span className="small fw-bold me-2 text-danger" key={index}>{notice}</span>
              ))}
            </div>
          )}
          <div className="d-flex justify-content-between align-items-center">
            <div className="product-price text-accent">
              {product.variations && "от "}
              <ProductPrice product={product} microdata />
            </div>
            <div>
              {product.variations ? (
                <Link className="btn btn-secondary btn-sm d-block w-100" href={product.variations}>
                  <i className="ci-eye fs-sm" />
                </Link>
              ) : product.enabled && product.instock ? (
                <>
                  <link itemProp="availability" href="http://schema.org/InStock" />
                  <BasketButton product={product} />
                </>
              ) : (
                <>
                  <link itemProp="availability" href="http://schema.org/OutOfStock" />
                  <ProductCardLink className="btn btn-secondary btn-sm d-block w-100" product={product} gtmCategory={gtmCategory} gtmList={gtmList} gtmPosition={gtmPosition}>
                    <i className="ci-eye fs-sm" />
                  </ProductCardLink>
                </>
              )}
            </div>
            { /* TODO
                        <div className="star-rating">
                            <i className="star-rating-icon ci-star-filled active"></i>
                            <i className="star-rating-icon ci-star-filled active"></i>
                            <i className="star-rating-icon ci-star-filled active"></i>
                            <i className="star-rating-icon ci-star"></i>
                            <i className="star-rating-icon ci-star"></i>
                        </div>
                        */
            }
          </div>
        </div>
      </div>
      <div className="card-body card-body-hidden">
        {product.shortdescr && <div className="fs-ms pb-2" dangerouslySetInnerHTML={{ __html: product.shortdescr }} itemProp="description"></div>}
        {product.sales_notes && <div className="fs-ms text-info pb-2">{product.sales_notes}</div>}
        {/*
                <div className="d-flex mb-2">
                    { product.variations ? (
                        <Link className="btn btn-success btn-sm d-block w-100" href={product.variations}>
                            Выбрать
                        </Link>
                    ) : product.enabled && product.instock ? (
                        <button className="btn btn-success btn-sm d-block w-100" type="button" onClick={handleCartClick}>
                            <i className="ci-cart fs-sm me-1" />
                            Купить
                        </button>
                    ) : (
                        <Link className="btn btn-secondary btn-sm d-block w-100" href={{ pathname: '/products/[code]', query: { code: product.code }}}>
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
