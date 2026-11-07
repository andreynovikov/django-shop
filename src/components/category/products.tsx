'use client'

import { createContext, ReactNode, Suspense, useContext, useMemo, useState, useSyncExternalStore } from 'react'
import { useQuery } from '@tanstack/react-query'
import { useQueryStates } from 'nuqs'

import ProductCard from '@/components/product/card'
import ProductFilter from '@/components/product/filter'
import PageSelector from '@/components/page-selector'
import { Loading } from '@/components/loading'
import { IconAdjustmentsHorizontal } from '@tabler/icons-react'
import { handheldIconClass, handheldItemClass, handheldLabelClass } from '@/components/ui/handheld-toolbar'
import Offcanvas, { OffcanvasHeader, OffcanvasBody } from '@/components/ui/offcanvas'
import { widgetTitleClass } from '@/components/ui/widget'

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
    <div className={index === filters.length - 1 ? "" : "mb-6 border-b pb-6"} key={filter.id}>
      <h3 className={widgetTitleClass}>{filter.label}</h3>
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
    <button type="button" className={handheldItemClass} onClick={() => setShowFilters(true)}>
      <span className={handheldIconClass}><IconAdjustmentsHorizontal size={20} stroke={1.5} /></span>
      <span className={handheldLabelClass}>Фильтры</span>
    </button>
  ), [])

  useToolbar(toolbarItem)

  return (
    <Offcanvas show={showFilters} onHide={() => setShowFilters(false)}>
      <OffcanvasHeader>
        <h2 className="mb-0 text-h5">Фильтры</h2>
      </OffcanvasHeader>
      <OffcanvasBody>
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
  gridClassName: string  // grid columns of the products
  children?: ReactNode  // shown before the products, each in a column with mb-6
}

function ProductGrid({ products, recommended, loading, categoryName, pathname, gridClassName, children }: ProductGridProps & {
  products: ProductList | undefined
  recommended: boolean
  loading: boolean
}) {
  return (
    <>
      <div className={`grid gap-x-4 ${gridClassName}`}>
        {children}
        {loading && (
          <Loading className="mb-6 flex items-center justify-center" mega />
        )}
        {products?.results.map((product, index) => (
          <div className="mb-6" key={product.id}>
            <ProductCard
              product={product}
              gtmCategory={{ name: categoryName }}
              gtmList={recommended ? "Рекомендуем в каталоге" : "Каталог"}
              gtmPosition={index} />
            <hr className="sm:hidden" />
          </div>
        ))}
      </div>

      {products !== undefined && products.totalPages > 1 && (
        <>
          <hr className="my-4" />
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
