import Link from 'next/link'

import TopCategoriesCard from '@/components/top-categories-card'
import CurrentCatalog from '@/components/current-catalog'
import ProductCard from '@/components/product/card'

import { loadAdverts, loadProducts } from '@/lib/queries'
import { recomendedProductsFilters, newProductsFilters } from '@/lib/catalog'
import { Advert, Product } from '@/lib/types'

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
  products: Product[]
  id: string
  title: string
  linkTitle: string
  href: string
}

function ProductsSection({ products, id, title, linkTitle, href }: ProductsSectionProps) {
  return (
    <section id={id} className="container pt-5">
      <div className="d-flex flex-wrap justify-content-between align-items-center pt-1 border-bottom pb-4 mb-4">
        <h2 className="h3 mb-0 pt-3 me-2">{title}</h2>
        <div className="pt-3">
          <Link className="btn btn-accent btn-sm" href={href}>
            {linkTitle}
            <i className="ci-arrow-right ms-1 me-n1" />
          </Link>
        </div>
      </div>
      <div className="row pt-2 mx-n2">
        {products.map((product, index) => (
          <div className="col-lg-3 col-md-4 col-sm-6 px-2 mb-4" key={product.id}>
            <ProductCard product={product} gtmList="Первая страница акции" gtmPosition={index} />
            <hr className="d-sm-none" />
          </div>
        ))}
      </div>
    </section>
  )
}

export default async function HomePage() {
  const recomendedProducts = await loadProducts(null, itemsPerSection, recomendedProductsFilters, sort)
  const newProducts = await loadProducts(null, itemsPerSection, newProductsFilters, sort)

  const adverts = await loadAdverts(['main', 'index_top_new', 'index_middle_new', 'index_bottom_new'])

  const mainAdvert = adverts.find(advert => advert.place === 'main')
  const topAdverts = adverts.filter(advert => advert.place === 'index_top_new')
  const middleAdverts = adverts.filter(advert => advert.place === 'index_middle_new')
  const bottomAdverts = adverts.filter(advert => advert.place === 'index_bottom_new')

  return (
    <div className="mb-3">
      <section className="pb-5">
        <div className="bg-dark py-5"></div>
        <div className="py-3"></div>
      </section>

      <div className="d-flex flex-column position-relative pt-3 pt-lg-0 mt-n10" style={{ zIndex: 10 }}>
        <section className="container order-2 order-sm-1">
          <TopCategoriesCard />
          <CurrentCatalog />
        </section>

        {mainAdvert && (
          <section className="container pt-0 pt-sm-5 order-1 order-sm-2">
            <div className="row mx-n2" dangerouslySetInnerHTML={{ __html: mainAdvert.content }} />
          </section>
        )}
      </div>

      <Adverts adverts={topAdverts} />

      {recomendedProducts.results.length > 0 && (
        <ProductsSection products={recomendedProducts.results} id="sw-recomended" title="Специальные предложения" linkTitle="Больше специальных предложений" href="/catalog/promo/" />
      )}

      <Adverts adverts={middleAdverts} />

      {newProducts.results.length > 0 && (
        <ProductsSection products={newProducts.results} id="sw-new" title="Новинки" linkTitle="Больше новинок" href="/catalog/New/" />
      )}

      <Adverts adverts={bottomAdverts} />
    </div>
  )
}