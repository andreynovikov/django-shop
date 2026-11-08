'use client'

import { createContext, MouseEvent, ReactNode, Suspense, useContext, useEffect, useEffectEvent, useMemo, useRef, useState, useSyncExternalStore } from 'react'
import Link from 'next/link'
import { useRouter } from 'next/navigation'
import { ParsedUrlQuery } from 'querystring'
import { useInfiniteQuery, useQuery } from '@tanstack/react-query'
import { useQueryStates } from 'nuqs'

import ProductCard from '@/components/product/card'
import ProductFilter from '@/components/product/filter'
import PageSelector, { getPageHref } from '@/components/page-selector'
import { ButtonLoading, Loading } from '@/components/loading'
import { IconAdjustmentsHorizontal } from '@tabler/icons-react'
import { buttonClass } from '@/components/ui/button'
import { handheldIconClass, handheldItemClass, handheldLabelClass } from '@/components/ui/handheld-toolbar'
import Offcanvas, { OffcanvasHeader, OffcanvasBody } from '@/components/ui/offcanvas'
import { widgetTitleClass } from '@/components/ui/widget'

import { productKeys, loadProducts } from '@/lib/queries'
import { useToolbar } from '@/lib/toolbar'
import { productSearchParams, productSearchParamsSerializer, ProductSearchParamsType } from '@/lib/search-params'
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
  page: number  // the first page shown, from the path; the following ones are loaded as the user scrolls
  pageSize: number
}

interface CategoryProductsContextValue {
  query: CategoryProductsQuery
  pathname: string  // path of the first page, the page number is appended to it
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

// Query of the page links of a filtered list
function filterQuery(filters: ProductSearchParamsType) {
  const params = new URLSearchParams(productSearchParamsSerializer(filters))
  const query: ParsedUrlQuery = {}
  for (const key of params.keys())
    query[key] = params.getAll(key)
  return query
}

// Reads search params, so callers need a Suspense boundary to keep the rest of the page statically rendered
function useCategoryProducts() {
  const { query: { categoryId, filters, order, page, pageSize }, pathname, initialProducts, initialRecommended } = useCategoryProductsContext()
  const [values, setValues] = useQueryStates(productSearchParams)
  const router = useRouter()

  // the page comes from the path
  const queryFilters = { ...values, page: undefined }
  // native array params are empty instead of null when unset
  const isFiltered = Object.values(queryFilters).some((value) =>
    value !== null && value !== undefined && !(Array.isArray(value) && value.length === 0))

  const productFilters = { ...queryFilters, ...filters }
  const products = useInfiniteQuery({
    queryKey: productKeys.listPages(page, pageSize, productFilters, order),
    queryFn: ({ pageParam }) => loadProducts(pageParam, pageSize, productFilters, order),
    initialPageParam: page,
    getNextPageParam: (lastPage) => lastPage.currentPage < lastPage.totalPages ? lastPage.currentPage + 1 : undefined,
    initialData: isFiltered ? undefined : { pages: [initialProducts], pageParams: [page] },
    // keeps filter choices and ranges while the next filtered list is loaded
    placeholderData: (previousData, previousQuery) => {
      const previousKey = previousQuery?.queryKey[3] as { filters?: ProductSearchParamsType } | undefined
      return previousKey?.filters?.categories === categoryId ? previousData : undefined
    },
    staleTime: pageStaleTime * 1000,
    // the back button returns to the pages loaded on scroll
    gcTime: pageStaleTime * 1000,
  })

  const recommendedFilters = { ...filters, categories: null, in_category: [categoryId], recomended: true }
  const recommended = useQuery({
    queryKey: productKeys.list(page, pageSize, recommendedFilters, order),
    queryFn: () => loadProducts(page, pageSize, recommendedFilters, order),
    initialData: isFiltered ? undefined : initialRecommended,
    enabled: products.isSuccess && products.data.pages[0].count === 0,
    staleTime: pageStaleTime * 1000
  })

  const setFilter: FilterChangeHandler = (name, value) => {
    const change = { [name]: value } as Partial<typeof values>
    if (page > 1)
      // the filtered list starts from its first page
      router.push(productSearchParamsSerializer(pathname + window.location.search, change), { scroll: false })
    else
      setValues(change)
  }

  // The server has no results for filtered lists. Suspense boundaries hydrate one by one, so a list loaded
  // meanwhile for another boundary would not match the server HTML, it is shown once this one is hydrated.
  const hydrated = useSyncExternalStore(subscribeNothing, () => true, () => false)
  const showResults = hydrated || !isFiltered

  const nextPage: NextPageLoader = {
    loading: products.isFetching,
    // after an error the page is loaded by a click only
    auto: !products.isFetchNextPageError && !products.isPlaceholderData,
    onLoad: () => products.fetchNextPage({ cancelRefetch: false }),
  }

  return {
    values: values as FilterValues,
    setFilter,
    productPages: showResults ? products.data?.pages : undefined,
    recommendedList: showResults ? recommended.data : undefined,
    loading: hydrated && (products.isLoading || recommended.isLoading),
    linkQuery: filterQuery(queryFilters),
    nextPage,
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
  const { values, setFilter, productPages } = useCategoryProducts()

  // choices of the unfiltered list until the first filtered one is loaded
  const facets = productPages?.[0].filters ?? initialProducts.filters
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
  gridClassName: string  // grid columns of the products
  children?: ReactNode  // shown before the products, each in a column with mb-6
}

interface NextPageLoader {
  loading: boolean
  auto: boolean  // loads the page when its link comes near
  onLoad: () => void
}

// Robots render the page in a tall window without scrolling. The next page is loaded only after the user has
// scrolled, so robots get the products of this page only and follow the link to the next one.
function NextPageLink({ href, loading = false, auto = false, onLoad }: Partial<NextPageLoader> & { href: string }) {
  const ref = useRef<HTMLAnchorElement>(null)
  const [scrolled, setScrolled] = useState(false)
  const load = useEffectEvent(() => onLoad?.())

  useEffect(() => {
    if (scrolled)
      return
    const handleScroll = () => setScrolled(true)
    window.addEventListener('scroll', handleScroll, { passive: true, once: true })
    return () => window.removeEventListener('scroll', handleScroll)
  }, [scrolled])

  useEffect(() => {
    const link = ref.current
    // the page may be scrolled already, e.g. when the back button returns to it
    if (!auto || loading || link === null || !(scrolled || window.scrollY > 0))
      return
    // a new observer reports the link at once, so the next page follows a short one without scrolling
    const observer = new IntersectionObserver(([entry]) => {
      if (entry.isIntersecting)
        load()
    }, { rootMargin: '0px 0px 100% 0px' })
    observer.observe(link)
    return () => observer.disconnect()
  }, [auto, loading, scrolled])

  const handleClick = (event: MouseEvent<HTMLAnchorElement>) => {
    // the server rendered link, or one opened in a new tab or window, goes to the page
    if (onLoad === undefined || event.button !== 0 || event.ctrlKey || event.metaKey || event.shiftKey || event.altKey)
      return
    event.preventDefault()
    if (!loading)
      onLoad()
  }

  return (
    <div className="mb-6 text-center">
      <Link ref={ref} className={buttonClass({ variant: 'outline-secondary' })} href={href} prefetch={false} onClick={handleClick} aria-busy={loading}>
        Показать ещё
        {loading && <ButtonLoading />}
      </Link>
    </div>
  )
}

// A product moved to the next page between loads would be shown twice
function pageProducts(pages: ProductList[]) {
  const ids = new Set<number>()
  return pages.flatMap((page) => page.results).filter((product) => {
    if (ids.has(product.id))
      return false
    ids.add(product.id)
    return true
  })
}

// Pages loaded one after another are shown as one list, followed by the link to the next page and the page links
function ProductGrid({ pages, recommended, loading, linkQuery, nextPage, categoryName, gridClassName, children }: ProductGridProps & {
  pages: ProductList[] | undefined
  recommended: boolean  // recommended products have no pages of their own, so they are shown without page links
  loading: boolean
  linkQuery?: ParsedUrlQuery  // filters kept in the page links
  nextPage?: NextPageLoader
}) {
  const { pathname } = useCategoryProductsContext()
  const first = pages?.[0]
  const last = pages?.[pages.length - 1]
  // positions are counted from the first page of the category
  const offset = first ? (first.currentPage - 1) * first.pageSize : 0

  return (
    <>
      <div className={`grid gap-x-4 ${gridClassName}`}>
        {children}
        {loading && (
          <Loading className="mb-6 flex items-center justify-center" mega />
        )}
        {pages && pageProducts(pages).map((product, index) => (
          <div className="mb-6" key={product.id}>
            <ProductCard
              product={product}
              gtmCategory={{ name: categoryName }}
              gtmList={recommended ? "Рекомендуем в каталоге" : "Каталог"}
              gtmPosition={offset + index} />
            <hr className="sm:hidden" />
          </div>
        ))}
      </div>

      {(!recommended && first !== undefined && last !== undefined && last.totalPages > 1) && (
        <>
          {last.currentPage < last.totalPages && (
            <NextPageLink href={getPageHref(last.currentPage + 1, pathname, linkQuery, true)} {...nextPage} />
          )}
          <hr className="my-4" />
          <PageSelector
            pathname={pathname}
            query={linkQuery}
            pageInPath
            totalPages={last.totalPages}
            currentPage={first.currentPage}
            lastCurrentPage={last.currentPage} />
        </>
      )}
    </>
  )
}

function CurrentProductGrid(props: ProductGridProps) {
  const { productPages, recommendedList, loading, linkQuery, nextPage } = useCategoryProducts()

  const found = productPages !== undefined && productPages[0].count > 0
  return (
    <ProductGrid
      pages={found ? productPages : recommendedList && [recommendedList]}
      recommended={!found}
      loading={loading}
      linkQuery={linkQuery}
      nextPage={nextPage}
      {...props} />
  )
}

// Recommended products of the category are shown when nothing is found
export function CategoryProducts(props: ProductGridProps) {
  const { initialProducts, initialRecommended } = useCategoryProductsContext()

  const found = initialProducts.count > 0
  return (
    // the server renders unfiltered products, the query is applied after hydration
    <Suspense fallback={<ProductGrid pages={found ? [initialProducts] : initialRecommended && [initialRecommended]} recommended={!found} loading={false} {...props} />}>
      <CurrentProductGrid {...props} />
    </Suspense>
  )
}
