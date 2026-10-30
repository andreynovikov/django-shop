'use client'

import { createContext, ReactNode, Suspense, useContext, useMemo, useState, useSyncExternalStore } from 'react'
import { useQuery } from '@tanstack/react-query'
import { useQueryStates } from 'nuqs'

import ProductCard from '@/components/product/card'
import ProductFilter from '@/components/product/filter'
import PageSelector from '@/components/page-selector'
import { Loading } from '@/components/loading'
import Offcanvas, { OffcanvasHeader, OffcanvasBody } from '@/components/ui/offcanvas'

import { productKeys, loadProducts } from '@/lib/queries'
import { useToolbar } from '@/lib/toolbar'
import { productSearchParams, ProductSearchParamsType } from '@/lib/search-params'
import { CategoryFilter, ProductFilterFacet, ProductList } from '@/lib/types'

const pageStaleTime = 3600

// nothing changes after hydration, so there is nothing to subscribe to
const subscribeNothing = () => () => {}

type FilterValues = Partial<Record<string, unknown>>
type FilterChangeHandler = (name: string, value: unknown) => void

// Product list of the category as the server rendered it, filters from the query are applied on the client
export interface CategoryProductsQuery {
  categoryId: number
  filters: ProductSearchParamsType  // category filters, they take precedence over the query ones
  order: string
  page: number
  pageSize: number
}

interface CategoryProductsContextValue {
  query: CategoryProductsQuery
  initialProducts: ProductList
  initialRecommended?: ProductList
}

const CategoryProductsContext = createContext<CategoryProductsContextValue | null>(null)

// Holds the server loaded products once for both the filters and the product grid
export function CategoryProductsProvider({ children, ...value }: CategoryProductsContextValue & { children: ReactNode }) {
  return (
    <CategoryProductsContext.Provider value={value}>
      {children}
    </CategoryProductsContext.Provider>
  )
}

function useCategoryProductsContext() {
  const context = useContext(CategoryProductsContext)
  if (context === null)
    throw new Error('CategoryProductsProvider is missing')
  return context
}

// Reads search params, so callers need a Suspense boundary to keep the rest of the page statically rendered
function useCategoryProducts() {
  const { query: { categoryId, filters, order, page, pageSize }, initialProducts, initialRecommended } = useCategoryProductsContext()
  const [values, setValues] = useQueryStates(productSearchParams)

  // the page comes from the path
  const queryFilters = { ...values, page: undefined }
  // native array params are empty instead of null when unset
  const isFiltered = Object.values(queryFilters).some((value) =>
    value !== null && value !== undefined && !(Array.isArray(value) && value.length === 0))

  const productFilters = { ...queryFilters, ...filters }
  const products = useQuery({
    queryKey: productKeys.list(page, pageSize, productFilters, order),
    queryFn: () => loadProducts(page, pageSize, productFilters, order),
    initialData: isFiltered ? undefined : initialProducts,
    // keeps filter choices and ranges while the next filtered list is loaded
    placeholderData: (previousData, previousQuery) => {
      const previousKey = previousQuery?.queryKey[2] as { filters?: ProductSearchParamsType } | undefined
      return previousKey?.filters?.categories === categoryId ? previousData : undefined
    },
    staleTime: pageStaleTime * 1000
  })

  const recommendedFilters = { ...filters, categories: null, in_category: [categoryId], recomended: true }
  const recommended = useQuery({
    queryKey: productKeys.list(page, pageSize, recommendedFilters, order),
    queryFn: () => loadProducts(page, pageSize, recommendedFilters, order),
    initialData: isFiltered ? undefined : initialRecommended,
    enabled: products.isSuccess && products.data.count === 0,
    staleTime: pageStaleTime * 1000
  })

  const setFilter: FilterChangeHandler = (name, value) => {
    setValues({ [name]: value } as Partial<typeof values>)
  }

  // The server has no results for filtered lists. Suspense boundaries hydrate one by one, so a list loaded
  // meanwhile for another boundary would not match the server HTML, it is shown once this one is hydrated.
  const hydrated = useSyncExternalStore(subscribeNothing, () => true, () => false)
  const showResults = hydrated || !isFiltered

  return {
    values: values as FilterValues,
    setFilter,
    productList: showResults ? products.data : undefined,
    recommendedList: showResults ? recommended.data : undefined,
    loading: hydrated && (products.isLoading || recommended.isLoading),
  }
}

function FilterList({ filters, facets, values, onFilterChanged }: {
  filters: CategoryFilter[]
  facets?: Record<string, ProductFilterFacet>
  values: FilterValues
  onFilterChanged: FilterChangeHandler
}) {
  return filters.map((filter, index) => (
    <div className={"widget" + (index === filters.length - 1 ? "" : " pb-4 mb-4 border-bottom")} key={filter.id}>
      <h3 className="widget-title">{filter.label}</h3>
      <ProductFilter
        filter={{ ...filter, ...facets?.[filter.name] }}
        filterValue={values[filter.name] ?? null}
        onFilterChanged={onFilterChanged} />
    </div>
  ))
}

function CurrentFilterList({ filters }: { filters: CategoryFilter[] }) {
  const { initialProducts } = useCategoryProductsContext()
  const { values, setFilter, productList } = useCategoryProducts()

  // choices of the unfiltered list until the first filtered one is loaded
  const facets = productList?.filters ?? initialProducts.filters
  return <FilterList filters={filters} facets={facets} values={values} onFilterChanged={setFilter} />
}

const ignoreFilterChange = () => {}

// Filters in the sidebar from lg up, in an offcanvas opened from the handheld toolbar below lg
export function CategoryFilters({ filters }: { filters: CategoryFilter[] }) {
  const { initialProducts } = useCategoryProductsContext()
  const [showFilters, setShowFilters] = useState(false)

  const toolbarItem = useMemo(() => (
    <a className="d-table-cell handheld-toolbar-item" onClick={() => setShowFilters(true)} style={{ cursor: 'pointer' }}>
      <span className="handheld-toolbar-icon"><i className="ci-filter-alt" /></span>
      <span className="handheld-toolbar-label">Фильтры</span>
    </a>
  ), [])

  useToolbar(toolbarItem)

  return (
    <Offcanvas
      show={showFilters}
      onHide={() => setShowFilters(false)}
      className="bg-white w-100 rounded-3 shadow-lg py-1"
      style={{ maxWidth: "22rem" }}>
      <OffcanvasHeader className="align-items-center shadow-sm">
        <h2 className="h5 mb-0">Фильтры</h2>
      </OffcanvasHeader>
      <OffcanvasBody className="py-grid-gutter px-lg-grid-gutter">
        {/* the server renders unset filters, the query is applied after hydration */}
        <Suspense fallback={<FilterList filters={filters} facets={initialProducts.filters} values={{}} onFilterChanged={ignoreFilterChange} />}>
          <CurrentFilterList filters={filters} />
        </Suspense>
      </OffcanvasBody>
    </Offcanvas>
  )
}

interface ProductGridProps {
  categoryName: string
  pathname: string  // path of the first page, the page number is appended to it
  columnClassName: string
  children?: ReactNode  // shown before the products
}

function ProductGrid({ products, recommended, loading, categoryName, pathname, columnClassName, children }: ProductGridProps & {
  products: ProductList | undefined
  recommended: boolean
  loading: boolean
}) {
  return (
    <>
      <div className="row mx-n2">
        {children}
        {loading && (
          <Loading className={`${columnClassName} d-flex align-items-center justify-content-center`} mega />
        )}
        {products?.results.map((product, index) => (
          <div className={columnClassName} key={product.id}>
            <ProductCard
              product={product}
              gtmCategory={{ name: categoryName }}
              gtmList={recommended ? "Рекомендуем в каталоге" : "Каталог"}
              gtmPosition={index} />
            <hr className="d-sm-none" />
          </div>
        ))}
      </div>

      {products !== undefined && products.totalPages > 1 && (
        <>
          <hr className="my-3" />
          <PageSelector
            pathname={pathname}
            pageInPath
            totalPages={products.totalPages}
            currentPage={products.currentPage} />
        </>
      )}
    </>
  )
}

function CurrentProductGrid(props: ProductGridProps) {
  const { productList, recommendedList, loading } = useCategoryProducts()

  const found = productList !== undefined && productList.count > 0
  return (
    <ProductGrid
      products={found ? productList : recommendedList}
      recommended={!found}
      loading={loading}
      {...props} />
  )
}

// Recommended products of the category are shown when nothing is found
export function CategoryProducts(props: ProductGridProps) {
  const { initialProducts, initialRecommended } = useCategoryProductsContext()

  const found = initialProducts.count > 0
  return (
    // the server renders unfiltered products, the query is applied after hydration
    <Suspense fallback={<ProductGrid products={found ? initialProducts : initialRecommended} recommended={!found} loading={false} {...props} />}>
      <CurrentProductGrid {...props} />
    </Suspense>
  )
}
