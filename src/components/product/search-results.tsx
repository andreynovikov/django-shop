'use client'

import { useMemo, useState } from 'react'
import { useSearchParams } from 'next/navigation'
import { useQuery, keepPreviousData } from '@tanstack/react-query'
import { useQueryStates, parseAsString, parseAsBoolean, parseAsInteger, parseAsArrayOf } from 'nuqs'

import { pageContentWrapper } from '@/components/layout/page-content-wrapper'
import ProductSearchCard from '@/components/product/search-card'
import MultipleChoiceFilter from '@/components/product/filters/multiple-choice-filter'
import PriceFilter from '@/components/product/filters/price-filter'
import PageSelector, { SmallPageSelector } from '@/components/page-selector'
import { PageLoading } from '@/components/loading'
import Offcanvas, { OffcanvasHeader, OffcanvasBody } from '@/components/ui/offcanvas'

import { productKeys } from '@/lib/queries'
import { ProductSearchParamsType } from '@/lib/search-params'
import { loadProducts } from '@/lib/diginetica'
import { convertSearchParams } from '@/lib/navigation/app-provider'
import { useToolbar } from '@/lib/toolbar'
import { useCatalog } from '@/lib/catalog/hooks'
import rupluralize from '@/lib/rupluralize'

const pathname = '/search/'
const pageSize = 15

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
    children: <PageLoading className="pt-5" />,
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
      <a className="d-table-cell handheld-toolbar-item" onClick={() => setShowFilters(true)} style={{ cursor: 'pointer' }}>
        <span className="handheld-toolbar-icon"><i className="ci-filter-alt" /></span>
        <span className="handheld-toolbar-label">Фильтры</span>
      </a>
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
      return brandsFacet.values.map((value) => [value.id, value.name])
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
      <div className="container pb-5 mb-2 mb-md-4">
        <div className="row">
          <aside className="col-lg-4">
            <Offcanvas
              show={showFilters}
              onHide={() => setShowFilters(false)}
              className="bg-white w-100 rounded-3 shadow-lg py-1"
              style={{ maxWidth: "22rem" }}>
              <OffcanvasHeader className="align-items-center shadow-sm">
                <h2 className="h5 mb-0">Фильтры</h2>
              </OffcanvasHeader>
              <OffcanvasBody className="py-grid-gutter px-lg-grid-gutter">
                {brandsFilter && <div className="widget pb-4 mb-4 border-bottom">
                  <h3 className="widget-title">Производитель</h3>
                  <MultipleChoiceFilter
                    filter={{ name: 'manufacturer', choices: brandsFilter }}
                    filterValue={filters.manufacturer}
                    onFilterChanged={handleFilterChanged} />
                </div>}
                {priceFilter && <div className="widget pb-4 mb-4 border-bottom">
                  <h3 className="widget-title">Цена</h3>
                  <PriceFilter
                    filter={{ name: 'price', unit: 'руб', attrs: priceFilter }}
                    filterValue={filters.price}
                    onFilterChanged={handleFilterChanged} />
                </div>}
                <div className="widget">
                  <div className="form-check">
                    <input
                      className="form-check-input"
                      type="checkbox"
                      id="sw-awailable-check"
                      checked={filters.available}
                      onChange={(e) => handleFilterChanged('available', e.currentTarget.checked)} />
                    <label className="form-check-label" htmlFor="sw-awailable-check">Доступно к покупке</label>
                  </div>
                </div>
              </OffcanvasBody>
            </Offcanvas>
          </aside>

          <section className="col-lg-8">
            <div className="d-flex justify-content-center justify-content-sm-between align-items-center pt-2 pb-4 pb-sm-5">
              <div className="d-flex pb-3">
                {result.totalHits > 0 && (
                  <span className="text-light opacity-75 text-nowrap">
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

            <div className="row mx-n2" itemScope itemType="http://schema.org/OfferCatalog">
              <meta itemProp="name" content="Результаты поиска" />
              {result.totalHits > 0 ? (
                result.products.map((product, index) => (
                  <div className="col-md-4 col-sm-6 px-2 mb-4" key={product.id}>
                    <ProductSearchCard result={product} position={index} />
                    <hr className="d-sm-none" />
                  </div>
                ))
              ) : (
                <div className="lead my-4">
                  По вашему запросу ничего не найдено.
                  Попробуйте сократить запрос или задать его по-другому.
                  Убедитесь, что название бренда и модели написано правильно.
                </div>
              )}
            </div>

            {pages > 1 && (
              <>
                <hr className="my-3" />
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
    content = <PageLoading className="pt-5" />
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
    title: searchTitle(filters.text),
    dark: true,
    overlapped: true,
    children: content,
  })
}
