import { dehydrate, QueryClient, useQuery } from '@tanstack/react-query'

import PageLayout from '@/components/layout/page'
import ProductCard from '@/components/product/card'

import { salesActionKeys, loadSalesActions, loadSalesAction, loadSalesActionProducts } from '@/lib/queries'

export default function SalesAction({ slug }) {
  const { data: action, isSuccess } = useQuery({
    queryKey: salesActionKeys.detail(slug),
    queryFn: () => loadSalesAction(slug)
  })

  const { data: products, isSuccess: isSuccessProducts } = useQuery({
    queryKey: salesActionKeys.products(slug),
    queryFn: () => loadSalesActionProducts(slug),
    enabled: isSuccess && action.show_products
  })

  if (!isSuccess)
    return null

  return (
    <div className="container py-5 mb-2 mb-md-4">
      <img className="d-block mb-5 img-fluid" src={action.image} width={action.image_width} height={action.image_height} />
      <div dangerouslySetInnerHTML={{ __html: action.description }}></div>
      {isSuccessProducts && products !== undefined && (
        <div className="row pt-2 mx-n2">
          {products.map((product) => (
            <div className="col-lg-3 col-md-4 col-sm-6 px-2 mb-4" key={product.id}>
              <ProductCard product={product} />
              <hr className="d-sm-none" />
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

SalesAction.getLayout = function getLayout(page) {
  const breadcrumbs = [
    {
      label: 'Все акции',
      href: '/actions'
    }
  ]
  return (
    <PageLayout title={page.props.title} breadcrumbs={breadcrumbs}>
      {page}
    </PageLayout>
  )
}

export async function getStaticProps(context) {
  const slug = context.params?.slug
  const queryClient = new QueryClient()
  const action = await queryClient.fetchQuery({
    queryKey: salesActionKeys.detail(slug),
    queryFn: () => loadSalesAction(slug)
  })

  return {
    props: {
      dehydratedState: dehydrate(queryClient),
      title: action.name,
      slug
    }
  }
}

export async function getStaticPaths() {
  const actions = await loadSalesActions()
  const paths = actions.map((action) => ({
    params: { slug: action.slug },
  }))
  return { paths, fallback: 'blocking' }
}
