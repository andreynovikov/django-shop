import Image from 'next/image'

import BuyButton from '@/components/product/buy-button'
import { buttonClass } from '@/components/ui/button'
import NoImage from '@/components/product/no-image'

import { Category, ProductInfo } from '@/lib/types'

import { ProductCardImpression, ProductCardLink } from './ecommerce'

interface ProductCardProps {
  product: ProductInfo
  gtmCategory?: Pick<Category, 'name'>
  gtmList?: string
  gtmPosition?: number
}

// Free of hooks so server components can render it
export default function ProductCard({ product, gtmCategory = undefined, gtmList = '', gtmPosition = 0 }: ProductCardProps) {
  const linkProps = { product, gtmCategory, gtmList, gtmPosition }

  return (
    <div className="product_display">
      <ProductCardImpression product={product} gtmList={gtmList} gtmPosition={gtmPosition} />
      <div className="thumb text-center">
        <ProductCardLink {...linkProps}>
          {product.image ? (
            <div className="relative mx-auto" style={{ width: 160, height: 160 }}>
              <Image
                src={product.image}
                fill
                style={{ objectFit: 'contain' }}
                sizes="160px"
                alt={`${product.whatis ? product.whatis + ' ' : ''}${product.title}`} />
            </div>
          ) : (
            <NoImage size={160} />
          )}
        </ProductCardLink>
      </div>
      <p className="title">
        <ProductCardLink {...linkProps}>
          {product.title}
        </ProductCardLink>
      </p>

      <div className="description">
        <p>{product.whatis} {product.partnumber}</p>
        <div dangerouslySetInnerHTML={{ __html: product.shortdescr }} />
      </div>

      {product.price > 0 && (
        <div className="text-center">
          <div className="mb-2">
            {product.discount > 0 && (
              <div className="mb-1 text-xs">
                <s>{product.price.toLocaleString('ru')}</s>&nbsp;руб.
              </div>
            )}
            <span className="text-lg font-bold">{product.cost.toLocaleString('ru')}</span>&nbsp;руб.
          </div>
          {product.instock > 1 ? (
            <div className="product-nal-true">Есть в наличии</div>
          ) : product.instock == 1 ? (
            <div className="product-nal-true">Мало</div>
          ) : (
            <div className="product-nal-false">Закончились</div>
          )}

          <BuyButton product={product} className={`${buttonClass({ size: 'sm' })} mt-2 font-bold`} />
        </div>
      )}
      {product.wb_link && <div className="text-center mt-2">
        <a href={product.wb_link} className={`${buttonClass({ variant: 'wb', size: 'xs' })} font-bold`} role="button">Купить на WB</a>
      </div>}
      {product.ozon_link && <div className="text-center mt-2">
        <a href={product.ozon_link} className={`${buttonClass({ variant: 'ozon', size: 'xs' })} font-bold`} role="button">Купить на Ozon</a>
      </div>}

      {product.sales_notes && <div className="mt-2 text-center text-xs">{product.sales_notes}</div>}
    </div>
  )
}
