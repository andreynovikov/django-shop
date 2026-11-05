import Link from 'next/link'
import Image from 'next/image'

import { IconSearch } from '@tabler/icons-react'

import NoImage from '@/components/product/no-image'

import { ProductInfo } from '@/lib/types'

export default function ProductCard({ product }: { product: ProductInfo }) {
  const href = `/products/${product.code}/`

  return (
    <div className="product">
      <div className="product-image text-center">
        {product.isnew && <div className="ribbon ribbon-primary">Новинка</div>}
        {product.recomended && <div className="ribbon ribbon-info">Рекомендуем</div>}
        {product.image ? (
          <div className="position-relative" style={{ width: 350, aspectRatio: 1 }}>
            <Image
              src={product.image}
              fill
              style={{ objectFit: "contain" }}
              sizes="350px"
              loading="lazy"
              alt={`${product.title} ${product.whatis}`} />
          </div>
        ) : (
          <NoImage size={350} style={{ padding: 100 }} />
        )}
        <div className="product-hover-overlay">
          <Link className="product-hover-overlay-link" href={href} />
          <div className="product-hover-overlay-buttons">
            <Link className="btn btn-dark btn-buy" href={href}>
              <IconSearch />
              <span className="btn-buy-label ms-2">Подробнее</span>
            </Link>
          </div>
        </div>
      </div>
      <div className="py-2">
        <p className="text-muted text-sm mb-1">{product.whatis}</p>
        <h3 className="h6 text-uppercase mb-1">
          <Link className="text-dark" href={href}>
            {product.title}
          </Link>
        </h3>
      </div>
    </div>
  )
}
