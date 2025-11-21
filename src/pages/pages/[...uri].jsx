import { dehydrate, QueryClient, useQuery } from '@tanstack/react-query'

import PageLayout from '@/components/layout/page'

import { pageKeys, loadPages, loadPage } from '@/lib/queries'

export default function Page({ uri }) {
  const { data, isSuccess } = useQuery({
    queryKey: pageKeys.detail(uri),
    queryFn: () => loadPage(uri)
  })

  return (
    <div className="container py-5 mb-2 mb-md-4">
      {isSuccess && <div dangerouslySetInnerHTML={{ __html: data.content }}></div>}
    </div>
  )
}

Page.getLayout = function getLayout(page) {
  return (
    <PageLayout title={page.props.title}>
      {page}
    </PageLayout>
  )
}

export async function getStaticProps(context) {
  const uri = context.params?.uri
  const queryClient = new QueryClient()
  const data = await queryClient.fetchQuery({
    queryKey: pageKeys.detail(uri),
    queryFn: () => loadPage(uri)
  })

  return {
    props: {
      dehydratedState: dehydrate(queryClient),
      title: data.title,
      uri
    }
  }
}

export async function getStaticPaths() {
  const pages = await loadPages()
  const paths = pages.filter(page => !page.url.startsWith('/help/')).map((page) => ({
    params: { uri: page.url.slice(1, -1).split('/') },
  }))
  return { paths, fallback: false }
}
