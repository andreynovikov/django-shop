'use client'

import { ParsedUrlQuery } from 'querystring'
import { ReadonlyURLSearchParams, useSearchParams } from 'next/navigation'
import { useQuery, keepPreviousData } from '@tanstack/react-query'
import { useQueryStates, parseAsString, parseAsInteger } from 'nuqs'

import { pageContentWrapper } from '@/components/layout/page-content-wrapper'
import ProductCard from '@/components/product/card'
import PageSelector, { SmallPageSelector } from '@/components/page-selector'
import { PageLoading } from '@/components/loading'

import { productKeys, loadProducts } from '@/lib/queries'
import { useCatalog } from '@/lib/catalog/hooks'
import rupluralize from '@/lib/rupluralize'

const pathname = '/search/'
const pageSize = 24
const ordering = '' // the backend orders found products by relevance

// The page selector takes the query as an object, a repeated key as an array
function convertSearchParams(searchParams: ReadonlyURLSearchParams): ParsedUrlQuery {
  const query: ParsedUrlQuery = {}
  searchParams.forEach((value, key) => {
    const existing = query[key]
    query[key] = existing === undefined ? value : Array.isArray(existing) ? [...existing, value] : [existing, value]
  })
  return query
}

const searchParams = {
  text: parseAsString,
  page: parseAsInteger.withDefault(1),
}

const searchTitle = (text: string | null) => text ? `Поиск товаров: ${text}` : 'Поиск товаров'

// Shown while search params are not available, i.e. in the statically rendered page
export function SearchResultsLoading() {
  return pageContentWrapper({
    title: searchTitle(null),
    children: <PageLoading />,
  })
}

// Products are searched on the backend in the browser, so reading search params needs a Suspense boundary
export default function SearchResults() {
  const [{ text, page }] = useQueryStates(searchParams)
  const query = convertSearchParams(useSearchParams())

  useCatalog()

  const filters = { text }
  const { data: products, isSuccess, isLoading, isError } = useQuery({
    queryKey: productKeys.list(page, pageSize, filters, ordering),
    queryFn: () => loadProducts(page, pageSize, filters, ordering),
    placeholderData: keepPreviousData
  })

  let content
  if (isSuccess) {
    content = (
      <div className="container">
        <div className="pb-3">
          <div className="d-flex justify-content-between align-items-center">
            <div>
              {products.count > 0 && (
                <span className="text-nowrap">
                  {rupluralize(products.count, ['Найден', 'Найдены', 'Найдены'])}
                  {' '}{products.count}{' '}
                  {rupluralize(products.count, ['товар', 'товара', 'товаров'])}
                </span>
              )}
            </div>
            {products.totalPages > 1 && (
              <SmallPageSelector
                pathname={pathname}
                query={query}
                totalPages={products.totalPages}
                currentPage={products.currentPage} />
            )}
          </div>
        </div>

        {products.count > 0 ? (
          <div className="product-list py-2">
            {products.results.map((product, index) => (
              <ProductCard product={product} key={product.id} gtmList="Результаты поиска" gtmPosition={index} />
            ))}
          </div>
        ) : (
          <div className="lead my-4">Ничего не найдено</div>
        )}

        {products.totalPages > 1 && (
          <>
            <hr className="my-3" />
            <PageSelector
              pathname={pathname}
              query={query}
              totalPages={products.totalPages}
              currentPage={products.currentPage} />
          </>
        )}
      </div>
    )
  } else if (isLoading) {
    content = <PageLoading />
  } else if (isError) {
    content = (
      <div className="container pb-5 mb-2 mb-md-4">
        <div className="d-flex align-items-center my-5 py-5">
          <div className="lead ms-3">Error!</div>
        </div>
      </div>
    )
  }

  return pageContentWrapper({
    title: searchTitle(text),
    children: content,
  })
}
