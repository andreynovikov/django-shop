import Link from 'next/link'
import { dehydrate, QueryClient, useQuery } from '@tanstack/react-query'

import PageLayout from '@/components/layout/page'

import { salesActionKeys, loadSalesActions } from '@/lib/queries'

export default function SalesActions() {
  const { data: actions, isSuccess } = useQuery({
    queryKey: salesActionKeys.lists(),
    queryFn: () => loadSalesActions()
  })

  if (!isSuccess)
    return null

  return (
    <div className="container py-5 mb-2 mb-md-4">
      {actions.map(action => (
        <>
          <h3>{action.name}</h3>
          <Link className="d-block mb-5" href={{ pathname: '/actions/[slug]', query: { slug: action.slug } }}>
            <img
              class="d-block img-fluid"
              src={action.image}
              width={action.image_width}
              height={action.image_height} />
          </Link>
        </>
      ))}
    </div>
  )
}

SalesActions.getLayout = function getLayout(page) {
  return (
    <PageLayout htmlTitle="Все акции" title="Акции сети магазинов &laquo;Швейный Мир&raquo;">
      {page}
    </PageLayout>
  )
}

export async function getStaticProps() {
  const queryClient = new QueryClient()
  await queryClient.prefetchQuery({
    queryKey: salesActionKeys.lists(),
    queryFn: () => loadSalesActions()
  })

  return {
    props: {
      dehydratedState: dehydrate(queryClient)
    }
  }
}
