import Link from 'next/link'

import TopCategoriesCard from '@/components/top-categories-card'
import CurrentCatalog from '@/components/current-catalog'
import ProductCard from '@/components/product/card'

import { loadAdverts, loadProducts } from '@/lib/queries'
import { recomendedProductsFilters, newProductsFilters } from '@/lib/catalog'
import { Advert, ProductInfo } from '@/lib/types'

export const revalidate = 3600

const itemsPerSection = 16
const sort = '-price'

function Adverts({ adverts }: { adverts: Advert[] }) {
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

interface ProductsSectionProps {
  products: ProductInfo[]
  id: string
  title: string
  img: string
  href: string
}

function ProductsSection({ products, id, title, img, href }: ProductsSectionProps) {
  return (
    <section id={id} className="container pt-5" itemScope itemType="http://schema.org/OfferCatalog">
      <div className="d-flex flex-wrap align-items-end border-bottom border-header border-2 pt-1 pb-0 mb-4">
        <div className="d-none d-sm-block"><img src={`/i/categories/${img}`} alt="*" /></div>
        <Link href={href}>
          <h2 className="h3 mb-0 pt-3 pb-2 me-2 flex-grow-1" itemProp="name">{title}</h2>
        </Link>
      </div>
      <div className="row pt-2 mx-n2">
        {products.map((product, index) => (
          <div className="col-lg-3 col-md-4 col-sm-6 px-2 mb-4" key={product.id}>
            <ProductCard product={product} gtmList="Первая страница акции" gtmPosition={index} />
            <hr className="d-sm-none" />
          </div>
        ))}
      </div>
    </section >
  )
}

export default async function HomePage() {
  const recomendedProducts = await loadProducts(null, itemsPerSection, recomendedProductsFilters, sort)
  const newProducts = await loadProducts(null, itemsPerSection, newProductsFilters, sort)

  const adverts = await loadAdverts(['mainTop', 'mainMiddle', 'mainBottom', 'index_top_new', 'index_middle_new', 'index_bottom_new'])

  const mainTopAdvert = adverts?.find(advert => advert.place === 'mainTop')
  const mainMiddleAdvert = adverts?.find(advert => advert.place === 'mainMiddle')
  const mainBottomAdvert = adverts?.find(advert => advert.place === 'mainBottom')
  const topAdverts = adverts.filter(advert => advert.place === 'index_top_new')
  const middleAdverts = adverts.filter(advert => advert.place === 'index_middle_new')
  const bottomAdverts = adverts.filter(advert => advert.place === 'index_bottom_new')

  return (
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
          <CurrentCatalog />
        </section>

        {mainTopAdvert && (
          <section className="container pt-0 pt-sm-5 order-1 order-sm-2">
            <div className="row mx-n2" dangerouslySetInnerHTML={{ __html: mainTopAdvert.content }} />
          </section>
        )}
      </div>

      <Adverts adverts={topAdverts} />

      {recomendedProducts.results.length > 0 && (
        <ProductsSection products={recomendedProducts.results} id="sw-recomended" title="Специальные предложения" img="heart.svg" href="/catalog/promo/" />
      )}

      {mainMiddleAdvert && (
        <section className="container pt-0 pt-sm-5 order-1 order-sm-2">
          <div className="row mx-n2" dangerouslySetInnerHTML={{ __html: mainMiddleAdvert.content }} />
        </section>
      )}

      <Adverts adverts={middleAdverts} />

      {newProducts.results.length > 0 && (
        <ProductsSection products={newProducts.results} id="sw-new" title="Новинки" img="stars.svg" href="/catalog/New/" />
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
  )
}