import { cache } from 'react'
import { Metadata } from 'next'
import Image from 'next/image'
import { notFound } from 'next/navigation'

import { pageContentWrapper } from '@/components/layout/page-content-wrapper'
import PageSelector from '@/components/page-selector'
import ProductCard from '@/components/product/card'

import { HttpError, loadSalesAction, loadSalesActionProducts, loadSalesActions } from '@/lib/queries'
import { parsePageParam } from '@/lib/pagination'

export const revalidate = 3600

// Shared by generateMetadata and the page, so the action is fetched once per render
const getAction = cache(async (slug: string) => {
  try {
    return await loadSalesAction(slug)
  } catch (err) {
    if (err instanceof HttpError && err.status === 404)
      notFound()
    throw err
  }
})

async function getProducts(slug: string, page: number) {
  try {
    return await loadSalesActionProducts(slug, page)
  } catch (err) {
    // backend returns 404 for pages beyond the last one
    if (err instanceof HttpError && err.status === 404)
      notFound()
    throw err
  }
}

export async function generateMetadata({ params }: PageProps<'/actions/[slug]/[[...page]]'>): Promise<Metadata> {
  const { slug } = await params
  const action = await getAction(slug)
  return { title: action.name }
}

export default async function SalesActionPage({ params }: PageProps<'/actions/[slug]/[[...page]]'>) {
  const { slug, page } = await params
  const pathname = `/actions/${slug}/`
  const currentPage = parsePageParam(page, pathname)
  const action = await getAction(slug)
  // without products there are no pages beyond the first one
  if (!action.show_products && currentPage > 1)
    notFound()
  const products = action.show_products ? await getProducts(slug, currentPage) : undefined

  return pageContentWrapper({
    title: action.name,
    breadcrumbs: [{ label: 'Все акции', href: '/actions/' }],
    children: (
      <div className="container py-5 mb-2 mb-md-4">
        {action.image !== undefined && (
          <Image
            className="d-block mb-5 img-fluid"
            src={action.image}
            width={action.image_width}
            height={action.image_height}
            alt={action.name}
            preload />
        )}
        <div dangerouslySetInnerHTML={{ __html: action.description }}></div>
        {products !== undefined && (
          <>
            <div className="row pt-2 mx-n2" itemScope itemType="http://schema.org/OfferCatalog">
              <meta itemProp="name" content={action.name} />
              {products.results.map((product, index) => (
                <div className="col-lg-3 col-md-4 col-sm-6 px-2 mb-4" key={product.id}>
                  <ProductCard product={product} gtmList={`Рекламная акция ${action.name}`} gtmPosition={index} />
                  <hr className="d-sm-none" />
                </div>
              ))}
            </div>
            {products.totalPages > 1 && (
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
        )}
      </div>
    )
  })
}

export async function generateStaticParams() {
  if (process.env.NODE_ENV !== 'production' || process.env.PLAYWRIGHT_TEST === 'true')
    return []

  const actions = await loadSalesActions()
  return actions.map(action => ({ slug: action.slug, page: [] }))
}
