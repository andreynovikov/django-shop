import { dehydrate, QueryClient, useQuery } from '@tanstack/react-query'
import Link from 'next/link'
import Head from 'next/head'

import BaseLayout from '@/components/layout/base'
import ProductCard from '@/components/product/card'
import TopCategoriesCard from '@/components/top-categories-card'

import { advertKeys, productKeys, loadAdverts, loadProducts } from '@/lib/queries'
import { useCatalog, recomendedProductsFilters, newProductsFilters } from '@/lib/catalog'

const itemsPerSection = 16
const sort = '-price'

function Adverts({ adverts }) {
  return adverts.length > 0 && (
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
  )
}

export default function Index() {
  const { data: recomendedProducts, isSuccess: isRecomendedSuccess } = useQuery({
    queryKey: productKeys.list(null, itemsPerSection, recomendedProductsFilters, sort),
    queryFn: () => loadProducts(null, itemsPerSection, recomendedProductsFilters, sort)
  })
  const { data: newProducts, isSuccess: isNewSuccess } = useQuery({
    queryKey: productKeys.list(null, itemsPerSection, newProductsFilters, sort),
    queryFn: () => loadProducts(null, itemsPerSection, newProductsFilters, sort)
  })

  const { data: adverts } = useQuery({
    queryKey: advertKeys.list(['mainTop', 'mainMiddle', 'mainBottom', 'index_top_new', 'index_middle_new', 'index_bottom_new']),
    queryFn: () => loadAdverts(['mainTop', 'mainMiddle', 'mainBottom', 'index_top_new', 'index_middle_new', 'index_bottom_new'])
  })

  const mainTopAdvert = adverts?.find(advert => advert.place === 'mainTop')
  const mainMiddleAdvert = adverts?.find(advert => advert.place === 'mainMiddle')
  const mainBottomAdvert = adverts?.find(advert => advert.place === 'mainBottom')
  const topAdverts = adverts?.filter(advert => advert.place === 'index_top_new') ?? []
  const middleAdverts = adverts?.filter(advert => advert.place === 'index_middle_new') ?? []
  const bottomAdverts = adverts?.filter(advert => advert.place === 'index_bottom_new') ?? []

  useCatalog()

  return (
    <>
      <Head>
        {process.env.NEXT_PUBLIC_GOOGLE_VERIFICATION && <meta name="google-site-verification" content={process.env.NEXT_PUBLIC_GOOGLE_VERIFICATION} />}
        {process.env.NEXT_PUBLIC_YANDEX_VERIFICATION && <meta name="yandex-verification" content={process.env.NEXT_PUBLIC_YANDEX_VERIFICATION} />}
      </Head>
      <div className="mb-3">
        <section className="pb-5">
          <div className="bg-info">
            <div className="d-none d-md-flex justify-content-between">
              <div><img src="/i/tree_left.svg" /></div>
              <div><img src="/i/tree_right.svg" /></div>
            </div>
          </div>
        </section>

        <div className="d-flex flex-column position-relative pt-3 pt-lg-0 mt-md-n25" style={{ zIndex: 10 }}>
          <section className="container order-2 order-sm-1">
            <TopCategoriesCard />
          </section>

          {mainTopAdvert && (
            <section className="container pt-0 pt-sm-5 order-1 order-sm-2">
              <div className="row mx-n2" dangerouslySetInnerHTML={{ __html: mainTopAdvert.content }} />
            </section>
          )}
        </div>

        <Adverts adverts={topAdverts} />

        {isRecomendedSuccess && recomendedProducts.results.length > 0 && (
          <section className="container pt-5">
            <div className="d-flex flex-wrap align-items-end border-bottom border-header border-2 pt-1 pb-0 mb-4">
              <div className="d-none d-sm-block"><img src="/i/categories/heart.svg" alt="*" /></div>
              <Link href="/catalog/promo/">
                <h2 className="h3 mb-0 pt-3 pb-2 me-2 flex-grow-1">Специальные предложения</h2>
              </Link>
            </div>
            <div className="row pt-2 mx-n2">
              {recomendedProducts.results.map((product, index) => (
                <div className="col-lg-3 col-md-4 col-sm-6 px-2 mb-4" key={product.id}>
                  <ProductCard product={product} gtmList="Первая страница акции" gtmPosition={index} />
                  <hr className="d-sm-none" />
                </div>
              ))}
            </div>
          </section>
        )}
        {mainMiddleAdvert && (
          <section className="container pt-0 pt-sm-5 order-1 order-sm-2">
            <div className="row mx-n2" dangerouslySetInnerHTML={{ __html: mainMiddleAdvert.content }} />
          </section>
        )}

        <Adverts adverts={middleAdverts} />

        {isNewSuccess && newProducts.results.length > 0 && (
          <section className="container pt-5">
            <div className="d-flex flex-wrap align-items-end border-bottom border-header border-2 pt-1 pb-0 mb-4">
              <div className="d-none d-sm-block"><img src="/i/categories/stars.svg" alt="*" /></div>
              <Link href="/catalog/New/">
                <h2 className="h3 mb-0 pt-3 pb-2 me-2 flex-grow-1">Новинки</h2>
              </Link>
            </div>
            <div className="row pt-2 mx-n2">
              {newProducts.results.map((product, index) => (
                <div className="col-lg-3 col-md-4 col-sm-6 px-2 mb-4" key={product.id}>
                  <ProductCard product={product} gtmList="Первая страница акции" gtmPosition={index} />
                  <hr className="d-sm-none" />
                </div>
              ))}
            </div>
          </section>
        )}
        {mainBottomAdvert && (
          <section className="container pt-0 pt-sm-5 order-1 order-sm-2">
            <div className="row mx-n2" dangerouslySetInnerHTML={{ __html: mainBottomAdvert.content }} />
          </section>
        )}

        <Adverts adverts={bottomAdverts} />

        <div className="container text-center">
          <div className="row">
            <div className="col-md-3 p-4">
              <h2 className="text-primary">Бренд №1</h2>
              <p>по&nbsp;объёму продаж швейного оборудования в&nbsp;мире</p>
            </div>
            <div className="col-md-3 p-4">
              <h2 className="text-primary">3 собственных завода</h2>
              <p>в Японии, Таиланде и на Тайване</p>
            </div>
            <div className="col-md-3 p-4">
              <h2 className="text-primary">Официальные</h2>
              <p>поставки в&nbsp;Россию</p>
            </div>
            <div className="col-md-3 p-4">
              <h2 className="text-primary">В 1921 году</h2>
              <p>основана первая фабрика в&nbsp;Японии</p>
            </div>
          </div>
        </div>
      </div>
    </>
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
    queryKey: productKeys.list(null, itemsPerSection, recomendedProductsFilters, sort),
    queryFn: () => loadProducts(null, itemsPerSection, recomendedProductsFilters, sort)
  })
  await queryClient.prefetchQuery({
    queryKey: productKeys.list(null, itemsPerSection, newProductsFilters, sort),
    queryFn: () => loadProducts(null, itemsPerSection, newProductsFilters, sort)
  })

  return {
    props: {
      dehydratedState: dehydrate(queryClient)
    }
  }
}
