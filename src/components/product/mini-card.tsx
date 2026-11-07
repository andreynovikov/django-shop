import Link from 'next/link'
import Image from 'next/image'

import NoImage from '@/components/product/no-image'
import ProductPrice from '@/components/product/price'

import { ProductInfo } from '@/lib/types'

export default function ProductMiniCard({ product }: { product: ProductInfo }) {
  return (
    <div className="relative flex min-w-0 flex-col rounded-lg bg-white pb-5 min-[500px]:pb-0">
      <Link
        className="relative inline-block aspect-4/3 w-full overflow-hidden"
        href={`/products/${product.code}`}>
        {product.image ? (
          <Image
            src={product.image}
            fill
            style={{ objectFit: "contain" }}
            sizes="(min-width: 640px) 50vw, (min-width: 768px) 33vw, (min-width: 1100px) 25vw, 100vw"
            loading="lazy"
            alt={`${product.whatis ? product.whatis + ' ' : ''}${product.title}`} />
        ) : (
          <NoImage />
        )}
      </Link>
      <div className="flex-auto px-5 py-2">
        <Link className="block pb-1 text-xs text-muted transition-colors hover:text-gray-700" href={`/products/${product.code}`}>
          {product.whatis} {product.partnumber}
        </Link>
        <h3 className="mb-3 text-sm leading-[1.2] font-medium">
          <Link className="text-heading transition-colors hover:text-primary" href={`/products/${product.code}`}>
            {product.title}
          </Link>
        </h3>
        <div className="flex justify-between">
          <div className="text-accent"><ProductPrice product={product} /></div>
        </div>
      </div>
    </div>
  )
}
