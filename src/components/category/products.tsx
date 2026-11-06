'use client'

import { useQuery } from '@tanstack/react-query'

import ProductCard from '@/components/product/card'

import { productKeys, loadProducts } from '@/lib/queries'
import { ProductSearchParamsType } from '@/lib/search-params'
import { ProductList } from '@/lib/types'

export interface CategoryProductsQuery {
  filters: ProductSearchParamsType
  order: string
  pageSize: number
}

interface CategoryProductsProps {
  categoryName: string
  query: CategoryProductsQuery
  initialProducts: ProductList
  loadedAt: number  // when the server loaded initialProducts
}

// Product list of the category as the server rendered it. The page is rendered once a day, so the list
// is loaded again in the browser once it is older than the products' stale time, to show current stock.
export default function CategoryProducts({ categoryName, query: { filters, order, pageSize }, initialProducts, loadedAt }: CategoryProductsProps) {
  const { data: products } = useQuery({
    queryKey: productKeys.list(1, pageSize, filters, order),
    queryFn: () => loadProducts(1, pageSize, filters, order),
    initialData: initialProducts,
    initialDataUpdatedAt: loadedAt,
  })

  return (
    <div className="product-list py-2">
      {products.results.map((product, index) => (
        <ProductCard
          product={product}
          key={product.id}
          gtmCategory={{ name: categoryName }}
          gtmList="Каталог"
          gtmPosition={index} />
      ))}
    </div>
  )
}
