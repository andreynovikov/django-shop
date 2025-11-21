import { dehydrate, QueryClient, useQuery } from '@tanstack/react-query'
import Link from 'next/link'

import BaseLayout from '@/components/layout/base'
import ProductCard from '@/components/product/card'
import TopCategoriesCard from '@/components/top-categories-card'

import { advertKeys, productKeys, loadAdverts, loadProducts } from '@/lib/queries'
import useCatalog, { recomendedFilters, firstPageFilters } from '@/lib/catalog'

const itemsPerSection = 16
const sort = '-price'

export default function Index() {
  const { data: recomended, isSuccess: isRecomendedSuccess } = useQuery({
    queryKey: productKeys.list(null, itemsPerSection, recomendedFilters, sort),
    queryFn: () => loadProducts(null, itemsPerSection, recomendedFilters, sort)
  })
  const { data: firstpage, isSuccess: isFirstPageSuccess } = useQuery({
    queryKey: productKeys.list(null, itemsPerSection, firstPageFilters, sort),
    queryFn: () => loadProducts(null, itemsPerSection, firstPageFilters, sort)
  })

  const { data: adverts, isSuccess: isAdvertsSuccess } = useQuery({
    queryKey: advertKeys.list(['index_top_new']),
    queryFn: () => loadAdverts(['index_top_new'])
  })

  useCatalog()

  return (
    <div className="mb-3">
      <div className="bg-secondary">
        <section className="pb-5">
          <div className="bg-dark py-5"></div>
          <div className="py-3"></div>
        </section>

        <section className="container position-relative pt-3 pt-lg-0 pb-5 mt-n10" style={{ zIndex: 10 }}>
          <TopCategoriesCard />
        </section>
      </div>

      {isAdvertsSuccess && adverts.length > 0 && (
        <section className="container pt-5">
          <div className="row mx-n2">
            {adverts.map((advert) => (
              <div className="col-lg-3 col-sm-6 px-2 mb-4" key={advert.id}>
                <div className="card overflow-hidden h-100" dangerouslySetInnerHTML={{ __html: advert.content }} />
                <hr className="d-sm-none" />
              </div>
            ))}
          </div>
        </section>
      )}

      {isRecomendedSuccess && recomended.results.length > 0 && (
        <section className="container pt-5">
          <div className="d-flex flex-wrap justify-content-between align-items-center pt-1 border-bottom pb-4 mb-4">
            <h2 className="h3 mb-0 pt-3 me-2">Специальные предложения</h2>
            <div className="pt-3">
              <Link className="btn btn-outline-accent btn-sm" href="/catalog/promo/">
                Больше товаров
                <i className="ci-arrow-right ms-1 me-n1" />
              </Link>
            </div>
          </div>
          <div className="row pt-2 mx-n2">
            {recomended.results.map((product) => (
              <div className="col-lg-3 col-md-4 col-sm-6 px-2 mb-4" key={product.id}>
                <ProductCard product={product} />
                <hr className="d-sm-none" />
              </div>
            ))}
          </div>
        </section>
      )}

      {isFirstPageSuccess && firstpage.results.length > 0 && (
        <section className="container pt-5">
          <div className="d-flex flex-wrap justify-content-between align-items-center pt-1 border-bottom pb-4 mb-4">
            <h2 className="h3 mb-0 pt-3 me-2">Новинки</h2>
            <div className="pt-3">
              <Link className="btn btn-outline-accent btn-sm" href="/catalog/New/">
                Больше товаров
                <i className="ci-arrow-right ms-1 me-n1" />
              </Link>
            </div>
          </div>
          <div className="row pt-2 mx-n2">
            {firstpage.results.map((product) => (
              <div className="col-lg-3 col-md-4 col-sm-6 px-2 mb-4" key={product.id}>
                <ProductCard product={product} />
                <hr className="d-sm-none" />
              </div>
            ))}
          </div>
        </section>
      )}
    </div>
  )
}

Index.getLayout = function getLayout(page) {
  return (
    <BaseLayout>
      {page}
    </BaseLayout>
  )
}

export async function getStaticProps() {
  const queryClient = new QueryClient()

  await queryClient.prefetchQuery({
    queryKey: productKeys.list(null, itemsPerSection, recomendedFilters, sort),
    queryFn: () => loadProducts(null, itemsPerSection, recomendedFilters, sort)
  })
  await queryClient.prefetchQuery({
    queryKey: productKeys.list(null, itemsPerSection, firstPageFilters, sort),
    queryFn: () => loadProducts(null, itemsPerSection, firstPageFilters, sort)
  })

  return {
    props: {
      dehydratedState: dehydrate(queryClient)
    }
  }
}
