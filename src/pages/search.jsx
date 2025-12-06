'use client'

import { useState, useMemo } from 'react'
import { useRouter } from 'next/router'
import { useQuery, keepPreviousData } from '@tanstack/react-query'
import { useQueryStates, parseAsString, parseAsBoolean, parseAsInteger, parseAsArrayOf } from 'nuqs'

import Offcanvas from 'react-bootstrap/Offcanvas'

import PageLayout from '@/components/layout/page'
import ProductSearchCard from '@/components/product/search-card'
import MultipleChoiceFilter from '@/components/product/filters/multiple-choice-filter'
import PriceFilter from '@/components/product/filters/price-filter'
import PageSelector, { SmallPageSelector } from '@/components/page-selector'

import { productKeys } from '@/lib/queries'
import { loadProducts } from '@/lib/diginetica'
import { useToolbar } from '@/lib/toolbar'
import useCatalog from '@/lib/catalog'
import rupluralize from '@/lib/rupluralize'

const searchParams = {
  text: parseAsString,
  price: parseAsArrayOf(parseAsInteger, '-'),
  manufacturer: parseAsArrayOf(parseAsString, ';'),
  available: parseAsBoolean.withDefault(false),
  page: parseAsInteger.withDefault(1),
}

export default function Search({ text, page }) {
  const [showFilters, setShowFilters] = useState(false)
  const [filters, setFilters] = useQueryStates(searchParams)

  const router = useRouter()

  useCatalog()

  const toolbarItem = useMemo(() => {
    return (
      <a className="d-table-cell handheld-toolbar-item" onClick={() => setShowFilters(true)}>
        <span className="handheld-toolbar-icon"><i className="ci-filter-alt" /></span>
        <span className="handheld-toolbar-label">Фильтры</span>
      </a>
    )
  }, [])

  useToolbar(toolbarItem)

  const { data: result, isSuccess, isLoading, isError } = useQuery({
    queryKey: productKeys.search(text, filters, null),
    queryFn: () => loadProducts(text, filters.page, 15, filters),
    placeholderData: keepPreviousData // required for filters not to loose choices and attributes
  })

  const pages = Math.ceil((result?.totalHits ?? 0) / 15)

  const priceFilter = useMemo(() => {
    const priceFacet = result?.facets?.reduce((selected, facet) => facet.name === 'price' ? facet : selected, undefined)
    if (priceFacet !== undefined)
      return priceFacet.values.reduce((filter, value) => {
        filter[`${value.id}_value`] = value.value
        return filter
      }, {})
    return undefined
  }, [result])

  const brandsFilter = useMemo(() => {
    const brandsFacet = result?.facets?.reduce((selected, facet) => facet.name === 'brands' ? facet : selected, undefined)
    if (brandsFacet?.values.length > 1)
      return brandsFacet.values.reduce((filter, value) => {
        filter.push([value.id, value.name])
        return filter
      }, [])
    return undefined
  }, [result])

  const handleFilterChanged = (field, value) => {
    setFilters({
      [field]: value ?? null,
      page: 1
    })
  }

  if (isSuccess) {
    return (
      <div className="container pb-5 mb-2 mb-md-4">
        <div className="row">
          <aside className="col-lg-4">
            <Offcanvas
              show={showFilters}
              onHide={() => setShowFilters(false)}
              responsive="lg"
              className="offcanvas bg-white w-100 rounded-3 shadow-lg py-1"
              style={{ maxWidth: "22rem" }}>
              <Offcanvas.Header className="align-items-center shadow-sm" closeButton>
                <h2 className="h5 mb-0">Фильтры</h2>
              </Offcanvas.Header>
              <Offcanvas.Body className="py-grid-gutter px-lg-grid-gutter">
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
              </Offcanvas.Body>
            </Offcanvas>
          </aside>

          <section className="col-lg-8">
            <div className="d-flex justify-content-center justify-content-sm-between align-items-center pt-2 pb-4 pb-sm-5">
              <div className="d-flex pb-3">
                {result?.totalHits > 0 && (
                  <span className="text-light opacity-75 text-nowrap">
                    {rupluralize(result.totalHits, ['Найден', 'Найдены', 'Найдены'])}
                    {' '}{result.totalHits}{' '}
                    {rupluralize(result.totalHits, ['товар', 'товара', 'товаров'])}
                  </span>
                )}
              </div>
              {pages > 1 && (
                <SmallPageSelector
                  pathname={router.pathname}
                  query={router.query}
                  totalPages={pages}
                  currentPage={filters.page} />
              )}
            </div>

            <div className="row mx-n2">
              {result?.totalHits > 0 ? (
                result.products.map((product) => (
                  <div className="col-md-4 col-sm-6 px-2 mb-4" key={product.id}>
                    <ProductSearchCard result={product} />
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
                  pathname={router.pathname}
                  query={router.query}
                  totalPages={pages}
                  currentPage={filters.page} />
              </>
            )}
          </section>
        </div>
      </div>
    )
  }

  if (isLoading) {
    return (
      <div className="container pb-5 mb-2 mb-md-4">
        <div className="d-flex align-items-center pt-2 pb-5">
          <div className="spinner-border text-light" role="status"></div>
          <div className="lead ms-3 text-light">Загружается...</div>
        </div>
      </div>
    )
  }

  if (isError) {
    return (
      <div className="container pb-5 mb-2 mb-md-4">
        <div className="d-flex align-items-center my-5 py-5">
          <div className="lead ms-3">Error!</div>
        </div>
      </div>
    )
  }

  return <></>
}

Search.getLayout = function getLayout(page) {
  return (
    <PageLayout title={"Поиск товаров: " + page.props.text} dark overlapped>
      {page}
    </PageLayout>
  )
}

export async function getServerSideProps(context) {
  return {
    props: context.query || {}
  }
}
