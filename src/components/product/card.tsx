import Link from 'next/link'
import Image from 'next/image'

import { IconSearch } from '@tabler/icons-react'

import NoImage from '@/components/product/no-image'
import ProductRibbons from '@/components/product/ribbons'
import { buttonClass } from '@/components/ui/button'

import { ProductInfo } from '@/lib/types'

export default function ProductCard({ product }: { product: ProductInfo }) {
  const href = `/products/${product.code}/`

  return (
    <div className="mb-6">
      {/* the overlay with the details button shows on hover */}
      <div className="group relative border-b-2 border-gray-700 text-center hover:border-primary">
        <ProductRibbons product={product} />
        {product.image ? (
          <div className="relative mx-auto aspect-square w-full max-w-[350px]">
            <Image
              src={product.image}
              fill
              style={{ objectFit: "contain" }}
              sizes="350px"
              loading="lazy"
              alt={`${product.title} ${product.whatis}`} />
          </div>
        ) : (
          <NoImage size={350} block className="max-w-full" style={{ padding: 100 }} />
        )}
        <div className="absolute inset-0 flex items-center justify-center bg-white/92 opacity-0 transition-opacity duration-300 group-hover:opacity-100">
          <Link className="absolute inset-0" href={href} />
          <div className="z-3">
            <Link className={`${buttonClass({ size: 'overlay' })} mx-2`} href={href}>
              <IconSearch />
              <span className="ms-2">Подробнее</span>
            </Link>
          </div>
        </div>
      </div>
      <div className="py-2">
        <p className="mb-1 text-xs text-muted">{product.whatis}</p>
        <h3 className="mb-1 text-[.9rem] leading-[1.1] font-bold tracking-widest uppercase">
          <Link className="text-dark" href={href}>
            {product.title}
          </Link>
        </h3>
      </div>
    </div>
  )
}
