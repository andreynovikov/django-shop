import Link from 'next/link'
import Image from 'next/image'

import NoImage from '@/components/product/no-image'
import ProductPrice from '@/components/product/price'

export default function ProductMiniCard({ product }) {
  return (
    <div className="card product-card card-static">
      <Link
        className="d-inline-block overflow-hidden position-relative w-100"
        style={{ aspectRatio: "4/3" }}
        href={{ pathname: '/products/[code]', query: { code: product.code } }}>
        {product.image ? (
          <Image
            src={product.image}
            fill
            style={{ objectFit: "contain" }}
            sizes="(min-width: 500px) 50vw, (min-width: 768px) 33vw, (min-width: 1100px) 25vw, 100vw"
            loading="lazy"
            alt={`${product.whatis ? product.whatis + ' ' : ''}${product.title}`} />
        ) : (
          <NoImage />
        )}
      </Link>
      <div className="card-body py-2">
        <Link className="product-meta d-block fs-xs pb-1" href={{ pathname: '/products/[code]', query: { code: product.code } }}>
          {product.whatis} {product.partnumber}
        </Link>
        <h3 className="product-title fs-sm">
          <Link href={{ pathname: '/products/[code]', query: { code: product.code } }}>
            {product.title}
          </Link>
        </h3>
        <div className="d-flex justify-content-between">
          <div className="product-price text-accent"><ProductPrice product={product} /></div>
        </div>
      </div>
    </div>
  )
}
