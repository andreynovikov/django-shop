'use client'

import { useMemo, useState } from 'react'
import { ParsedUrlQuery } from 'querystring'
import { ReadonlyURLSearchParams, useSearchParams } from 'next/navigation'
import { useQuery, keepPreviousData } from '@tanstack/react-query'
import { useQueryStates, parseAsString, parseAsBoolean, parseAsInteger, parseAsArrayOf } from 'nuqs'

import { pageContentWrapper } from '@/components/layout/page-content-wrapper'
import ProductSearchCard from '@/components/product/search-card'
import MultipleChoiceFilter from '@/components/product/filters/multiple-choice-filter'
import PriceFilter from '@/components/product/filters/price-filter'
import PageSelector, { SmallPageSelector } from '@/components/page-selector'
import { PageLoading } from '@/components/loading'
import Offcanvas, { OffcanvasHeader, OffcanvasBody } from '@/components/ui/offcanvas'
import { checkClass, checkInputClass, checkLabelClass } from '@/components/ui/form'
import { handheldIconClass, handheldItemClass, handheldLabelClass } from '@/components/ui/handheld-toolbar'
import { widgetTitleClass } from '@/components/ui/widget'
import { IconAdjustmentsHorizontal } from '@tabler/icons-react'

import { productKeys } from '@/lib/queries'
import { ProductSearchParamsType } from '@/lib/search-params'
import { loadProducts } from '@/lib/diginetica'
import { useToolbar } from '@/lib/toolbar'
import { useCatalog } from '@/lib/catalog/hooks'
import rupluralize from '@/lib/rupluralize'

const pathname = '/search/'
const pageSize = 15

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
  price: parseAsArrayOf(parseAsInteger, '-'),
  manufacturer: parseAsArrayOf(parseAsString, ';'),
  available: parseAsBoolean.withDefault(false),
  page: parseAsInteger.withDefault(1),
}

const searchTitle = (text: string | null) => text ? `Поиск товаров: ${text}` : 'Поиск товаров'

// Shown while search params are not available, i.e. in the statically rendered page
export function SearchResultsLoading() {
  return pageContentWrapper({
    title: searchTitle(null),
    dark: true,
    overlapped: true,
    children: <PageLoading className="pt-12" />,
  })
}

// Results come straight from Diginetica in the browser, so reading search params needs a Suspense boundary
export default function SearchResults() {
  const [showFilters, setShowFilters] = useState(false)
  const [filters, setFilters] = useQueryStates(searchParams)
  const query = convertSearchParams(useSearchParams())

  useCatalog()

  const toolbarItem = useMemo(() => {
    return (
      <button type="button" className={handheldItemClass} onClick={() => setShowFilters(true)}>
        <span className={handheldIconClass}><IconAdjustmentsHorizontal size={20} stroke={1.5} /></span>
        <span className={handheldLabelClass}>Фильтры</span>
      </button>
    )
  }, [])

  useToolbar(toolbarItem)

  const { data: result, isSuccess, isLoading, isError } = useQuery({
    // Diginetica filters differ from the backend ones, the key only needs to tell them apart
    queryKey: productKeys.search(filters.text ?? '', filters as unknown as ProductSearchParamsType, ''),
    queryFn: () => loadProducts(filters.text ?? '', filters.page, pageSize, filters),
    placeholderData: keepPreviousData // required for filters not to loose choices and attributes
  })

  const pages = Math.ceil((result?.totalHits ?? 0) / pageSize)

  const priceFilter = useMemo(() => {
    const priceFacet = result?.facets?.find((facet) => facet.name === 'price')
    if (priceFacet !== undefined)
      return Object.fromEntries(priceFacet.values.map((value) => [`${value.id}_value`, value.value]))
    return undefined
  }, [result])

  const brandsFilter = useMemo(() => {
    const brandsFacet = result?.facets?.find((facet) => facet.name === 'brands')
    if (brandsFacet !== undefined && brandsFacet.values.length > 1)
      return brandsFacet.values.map((value): [string, string] => [value.id, value.name])
    return undefined
  }, [result])

  const handleFilterChanged = (field: string, value: unknown) => {
    setFilters({
      [field]: value,
      page: 1
    })
  }

  let content
  if (isSuccess) {
    content = (
      <div className="container mb-2 pb-12 md:mb-6">
        <div className="grid gap-x-7.5 lg:grid-cols-3">
          <aside>
            <Offcanvas show={showFilters} onHide={() => setShowFilters(false)}>
              <OffcanvasHeader>
                <h2 className="mb-0 text-h5">Фильтры</h2>
              </OffcanvasHeader>
              <OffcanvasBody>
                {brandsFilter && <div className="mb-6 border-b pb-6">
                  <h3 className={widgetTitleClass}>Производитель</h3>
                  <MultipleChoiceFilter
                    filter={{ name: 'manufacturer', id: 'sw-manufacturer', choices: brandsFilter }}
                    filterValue={filters.manufacturer}
                    onFilterChanged={handleFilterChanged} />
                </div>}
                {priceFilter && <div className="mb-6 border-b pb-6">
                  <h3 className={widgetTitleClass}>Цена</h3>
                  <PriceFilter
                    filter={{ name: 'price', unit: 'руб', attrs: priceFilter }}
                    filterValue={filters.price}
                    onFilterChanged={handleFilterChanged} />
                </div>}
                <div>
                  <div className={checkClass()}>
                    <input
                      className={checkInputClass()}
                      type="checkbox"
                      id="sw-awailable-check"
                      checked={filters.available}
                      onChange={(e) => handleFilterChanged('available', e.currentTarget.checked)} />
                    <label className={checkLabelClass} htmlFor="sw-awailable-check">Доступно к покупке</label>
                  </div>
                </div>
              </OffcanvasBody>
            </Offcanvas>
          </aside>

          <section className="min-w-0 lg:col-span-2">
            <div className="flex items-center justify-center pt-2 pb-6 sm:justify-between sm:pb-12">
              <div className="flex pb-4">
                {result.totalHits > 0 && (
                  <span className="whitespace-nowrap text-white opacity-75">
                    {rupluralize(result.totalHits, ['Найден', 'Найдены', 'Найдены'])}
                    {' '}{result.totalHits}{' '}
                    {rupluralize(result.totalHits, ['товар', 'товара', 'товаров'])}
                  </span>
                )}
              </div>
              {pages > 1 && (
                <SmallPageSelector
                  pathname={pathname}
                  query={query}
                  totalPages={pages}
                  currentPage={filters.page} />
              )}
            </div>

            <div className="grid gap-x-4 sm:grid-cols-2 md:grid-cols-3" itemScope itemType="http://schema.org/OfferCatalog">
              <meta itemProp="name" content="Результаты поиска" />
              {result.totalHits > 0 ? (
                result.products.map((product, index) => (
                  <div className="mb-6" key={product.id}>
                    <ProductSearchCard result={product} position={index} />
                    <hr className="sm:hidden" />
                  </div>
                ))
              ) : (
                <div className="col-span-full my-6 text-xl font-light">
                  По вашему запросу ничего не найдено.
                  Попробуйте сократить запрос или задать его по-другому.
                  Убедитесь, что название бренда и модели написано правильно.
                </div>
              )}
            </div>

            {pages > 1 && (
              <>
                <hr className="my-4" />
                <PageSelector
                  pathname={pathname}
                  query={query}
                  totalPages={pages}
                  currentPage={filters.page} />
              </>
            )}
          </section>
        </div>
      </div>
    )
  } else if (isLoading) {
    content = <PageLoading className="pt-12" />
  } else if (isError) {
    content = (
      <div className="container mb-2 pb-12 md:mb-6">
        <div className="my-12 flex items-center py-12">
          <div className="ms-4 text-xl font-light">Error!</div>
        </div>
      </div>
    )
  }

  return pageContentWrapper({
    title: searchTitle(filters.text),
    dark: true,
    overlapped: true,
    children: content,
  })
}
