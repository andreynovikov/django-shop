import { cache } from 'react'
import { Metadata } from 'next'
import Link from 'next/link'
import { notFound } from 'next/navigation'

import { pageContentWrapper } from '@/components/layout/page-content-wrapper'
import CurrentCatalog from '@/components/current-catalog'
import StickySidebar from '@/components/category/sticky-sidebar'
import { CategoryFilters, CategoryProducts, CategoryProductsProvider, type CategoryProductsQuery } from '@/components/category/products'

import { HttpError, loadAdverts, loadCategories, loadCategory, loadCurrentSite, loadProducts } from '@/lib/queries'
import { baseFilters } from '@/lib/catalog'
import { parsePageParam } from '@/lib/pagination'
import { Category, CategoryTreeItem } from '@/lib/types'

export const revalidate = 3600

const pageSize = 1000
const defaultOrder = 'title'

const categoryPathname = (path: string[]) => `/catalog/${path.join('/')}/`

// Following pages have their number as the last path segment
function parsePath(segments: string[]) {
  const last = segments[segments.length - 1]
  if (segments.length > 1 && /^\d+$/.test(last)) {
    const path = segments.slice(0, -1)
    return { path, currentPage: parsePageParam([last], categoryPathname(path)) }
  }
  return { path: segments, currentPage: 1 }
}

const categoryTitle = (category: Category) =>
  category.subname ? `${category.name} - ${category.subname}` : category.name

// Shared by generateMetadata and the page, so the category is fetched once per render.
// The path is joined because cache() compares arguments by identity.
const getCategory = cache(async (uri: string) => {
  try {
    return await loadCategory(uri.split('/'))
  } catch (err) {
    if (err instanceof HttpError && err.status === 404)
      notFound()
    throw err
  }
})

const getSite = cache(loadCurrentSite)

async function getProducts(...args: Parameters<typeof loadProducts>) {
  try {
    return await loadProducts(...args)
  } catch (err) {
    // backend returns 404 for pages beyond the last one
    if (err instanceof HttpError && err.status === 404)
      notFound()
    throw err
  }
}

export async function generateMetadata({ params }: PageProps<'/catalog/[...path]'>): Promise<Metadata> {
  const { path: segments } = await params
  const { path, currentPage } = parsePath(segments)
  const [category, site] = await Promise.all([getCategory(path.join('/')), getSite()])

  return {
    title: categoryTitle(category),
    alternates: {
      canonical: site.url_prefix + categoryPathname(path) + (currentPage > 1 ? `${currentPage}/` : ''),
    },
  }
}

function SubcategoryLinks({ path, subcategories, compact = false }: { path: string[], subcategories: CategoryTreeItem[], compact?: boolean }) {
  return (
    <ul className="widget-list">
      {subcategories.map((subcategory, index) => (
        <li className={"widget-list-item" + (!compact && index > 0 ? " pt-2" : "")} key={subcategory.id}>
          <Link className="widget-list-link" href={categoryPathname([...path, subcategory.slug])}>
            <span className="fw-medium">{subcategory.name}</span>
            {subcategory.subname && <><br />{subcategory.subname}</>}
          </Link>
        </li>
      ))}
    </ul>
  )
}

export default async function CategoryPage({ params }: PageProps<'/catalog/[...path]'>) {
  const { path: segments } = await params
  const { path, currentPage } = parsePath(segments)
  const category = await getCategory(path.join('/'))

  const query: CategoryProductsQuery = {
    categoryId: category.id,
    filters: { ...baseFilters, categories: category.id },
    order: category.product_order || defaultOrder,
    page: currentPage,
    pageSize,
  }
  const [products, adverts] = await Promise.all([
    getProducts(query.page, query.pageSize, query.filters, query.order),
    loadAdverts(['categories'], category.id),
  ])
  const recommended = products.count === 0
    ? await getProducts(query.page, query.pageSize, { ...query.filters, categories: null, in_category: [category.id], recomended: true }, query.order)
    : undefined

  const subcategories = category.children?.length ? category.children : undefined
  const filters = category.filters?.length ? category.filters : undefined
  const hasSidebar = subcategories !== undefined || filters !== undefined
  const columnClassName = (hasSidebar ? "" : "col-lg-3 ") + "col-md-4 col-sm-6 px-2 mb-4"

  const breadcrumbs = [
    { label: 'Каталог', href: '/catalog/' },
    // the category itself is the page title
    ...category.path.breadcrumbs.slice(0, -1).map((breadcrumb, index, parents) => ({
      label: breadcrumb.name,
      href: categoryPathname(parents.slice(0, index + 1).map(({ slug }) => slug)),
    })),
  ]

  return pageContentWrapper({
    title: categoryTitle(category),
    breadcrumbs,
    dark: true,
    children: (
      <div className="container py-5 mb-2 mb-md-4">
        <CurrentCatalog />
        <CategoryProductsProvider query={query} initialProducts={products} initialRecommended={recommended}>
          <div className="row">
            {hasSidebar && (
              <StickySidebar className="col-lg-4">
                {subcategories && (
                  <div className={"d-none d-lg-block bg-white w-100 rounded-3 shadow-lg py-1" + (filters ? " mb-4" : "")} style={{ maxWidth: "22rem" }}>
                    <div className="py-grid-gutter px-lg-grid-gutter">
                      <div className="widget widget-links">
                        <h3 className="widget-title">Категории</h3>
                        <SubcategoryLinks path={path} subcategories={subcategories} />
                      </div>
                    </div>
                  </div>
                )}
                {filters && <CategoryFilters filters={filters} />}
              </StickySidebar>
            )}
            <section className={`col-lg-${hasSidebar ? 8 : 12}`} itemScope itemType="http://schema.org/OfferCatalog">
              <meta itemProp="name" content={category.name} />

              {(category.description && currentPage === 1) && (
                <div className="card mb-grid-gutter">
                  <div className="card-body px-4" dangerouslySetInnerHTML={{ __html: category.description }} itemProp="description"></div>
                </div>
              )}

              {subcategories && (
                <div className="d-lg-none card mb-grid-gutter">
                  <div className="card-body px-4">
                    <h5 className="card-title">Категории</h5>
                    <SubcategoryLinks path={path} subcategories={subcategories} compact />
                  </div>
                </div>
              )}

              <CategoryProducts categoryName={category.name} pathname={categoryPathname(path)} columnClassName={columnClassName}>
                {adverts.map(advert => (
                  <div className={columnClassName} key={advert.id}>
                    <div className="card overflow-hidden h-100" dangerouslySetInnerHTML={{ __html: advert.content }} />
                    <hr className="d-sm-none" />
                  </div>
                ))}
              </CategoryProducts>
            </section>
          </div>
        </CategoryProductsProvider>
      </div>
    )
  })
}

export async function generateStaticParams() {
  if (process.env.NODE_ENV !== 'production' || process.env.PLAYWRIGHT_TEST === 'true')
    return []

  const collectPaths = (categories: CategoryTreeItem[], parent: string[]): string[][] =>
    categories.flatMap((category) => {
      const path = [...parent, category.slug]
      return [path, ...collectPaths(category.children ?? [], path)]
    })

  return collectPaths(await loadCategories(), []).map((path) => ({ path }))
}
