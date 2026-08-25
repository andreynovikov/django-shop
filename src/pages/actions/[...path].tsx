import { ReactElement } from 'react'
import { GetStaticPropsContext, InferGetStaticPropsType } from 'next'
import Image from 'next/image'
import { useRouter } from 'next/router'
import { dehydrate, QueryClient, useQuery } from '@tanstack/react-query'
import { ParsedUrlQuery } from 'querystring'

import PageLayout from '@/components/layout/page'
import PageSelector from '@/components/page-selector'
import ProductCard from '@/components/product/card'

import { salesActionKeys, loadSalesActions, loadSalesAction, loadSalesActionProducts } from '@/lib/queries'

const pageStaleTime = 3600

export default function SalesAction({ slug, currentPage }: InferGetStaticPropsType<typeof getStaticProps>) {
  const router = useRouter()

  const { data: action, isSuccess } = useQuery({
    queryKey: salesActionKeys.detail(slug),
    queryFn: () => loadSalesAction(slug)
  })

  const { data: products, isSuccess: isSuccessProducts } = useQuery({
    queryKey: salesActionKeys.products(slug, currentPage),
    queryFn: () => loadSalesActionProducts(slug, currentPage),
    enabled: isSuccess && action.show_products,
    staleTime: pageStaleTime * 1000
  })

  if (!isSuccess)
    return null

  return (
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
      {isSuccessProducts && products !== undefined && (
        <>
          <div className="row pt-2 mx-n2">
            {products.results.map((product, index) => (
              <div className="col-lg-3 col-md-4 col-sm-6 px-2 mb-4" key={product.id}>
                <ProductCard product={product} gtmList={`Рекламная акция ${action.name}`} gtmPosition={index} />
                <hr className="d-sm-none" />
              </div>
            ))}
          </div>
          {products?.totalPages > 1 && (
            <>
              <hr className="my-3" />
              <PageSelector
                pathname={router.pathname}
                query={router.query}
                path={[slug]}
                totalPages={products.totalPages}
                currentPage={products.currentPage} />
            </>
          )}
        </>
      )}
    </div>
  )
}

interface IParams extends ParsedUrlQuery {
  path: string[]
}

SalesAction.getLayout = function getLayout(page: ReactElement, pageProps: IParams) {
  const breadcrumbs = [
    {
      label: 'Все акции',
      href: '/actions'
    }
  ]
  return (
    <PageLayout title={pageProps.title} breadcrumbs={breadcrumbs}>
      {page}
    </PageLayout>
  )
}

export async function getStaticProps(context: GetStaticPropsContext<IParams>) {
  const path = context.params?.path ?? []
  let currentPage = 1
  if (+path[path.length - 1] > 0) {
    currentPage = +(path.pop() ?? '1')

    if (currentPage === 1) {
      return {
        redirect: {
          destination: '/actions/' + path.join('/') + '/',
          permanent: false,
        },
      }
    }
  }
  const slug = path[0]
  const queryClient = new QueryClient()
  const action = await queryClient.fetchQuery({
    queryKey: salesActionKeys.detail(slug),
    queryFn: () => loadSalesAction(slug)
  })

  if (action.show_products)
    await queryClient.prefetchQuery({
      queryKey: salesActionKeys.products(slug, currentPage),
      queryFn: () => loadSalesActionProducts(slug, currentPage),
      staleTime: pageStaleTime * 1000
    })

  return {
    props: {
      dehydratedState: dehydrate(queryClient),
      title: action.name,
      slug,
      currentPage
    },
    revalidate: pageStaleTime // <--- ISR cache: once an hour
  }
}

export async function getStaticPaths() {
  const actions = await loadSalesActions()
  const paths = actions.map((action) => ({
    params: { path: [action.slug] },
  }))
  return { paths, fallback: 'blocking' }
}
