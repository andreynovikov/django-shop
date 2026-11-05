'use client'

import { Suspense, useSyncExternalStore } from 'react'
import { useQuery } from '@tanstack/react-query'
import { useQueryStates } from 'nuqs'

import ProductCard from '@/components/product/card'

import { productKeys, loadProducts } from '@/lib/queries'
import { productSearchParams, ProductSearchParamsType } from '@/lib/search-params'
import { ProductList } from '@/lib/types'

const pageStaleTime = 3600

// nothing changes after hydration, so there is nothing to subscribe to
const subscribeNothing = () => () => {}

// Product list of the category as the server rendered it, filters from the query are applied on the client
export interface CategoryProductsQuery {
  filters: ProductSearchParamsType  // category filters, they take precedence over the query ones
  order: string
  pageSize: number
}

interface CategoryProductsProps {
  categoryName: string
  query: CategoryProductsQuery
  initialProducts: ProductList
}

function ProductGrid({ products, categoryName }: { products: ProductList | undefined, categoryName: string }) {
  return products?.results.map((product, index) => (
    <ProductCard
      product={product}
      key={product.id}
      gtmCategory={{ name: categoryName }}
      gtmList="Каталог"
      gtmPosition={index} />
  ))
}

// Reads search params, so it needs a Suspense boundary to keep the rest of the page statically rendered
function CurrentProductGrid({ categoryName, query: { filters, order, pageSize }, initialProducts }: CategoryProductsProps) {
  const [values] = useQueryStates(productSearchParams)

  // the list has a single page
  const queryFilters = { ...values, page: undefined }
  // native array params are empty instead of null when unset
  const isFiltered = Object.values(queryFilters).some((value) =>
    value !== null && value !== undefined && !(Array.isArray(value) && value.length === 0))

  const productFilters = { ...queryFilters, ...filters }
  const { data: products } = useQuery({
    queryKey: productKeys.list(1, pageSize, productFilters, order),
    queryFn: () => loadProducts(1, pageSize, productFilters, order),
    initialData: isFiltered ? undefined : initialProducts,
    staleTime: pageStaleTime * 1000
  })

  // The server has no results for filtered lists, they are shown once hydrated so the HTML matches
  const hydrated = useSyncExternalStore(subscribeNothing, () => true, () => false)

  return <ProductGrid products={hydrated || !isFiltered ? products : undefined} categoryName={categoryName} />
}

// Products of the category, the query (e.g. ?instock=1) filters them further
export default function CategoryProducts(props: CategoryProductsProps) {
  return (
    // the server renders unfiltered products, the query is applied after hydration
    <Suspense fallback={<ProductGrid products={props.initialProducts} categoryName={props.categoryName} />}>
      <CurrentProductGrid {...props} />
    </Suspense>
  )
}
