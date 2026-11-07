/* eslint-disable @next/next/no-img-element */
import Link from 'next/link'

import TopCategoriesCard from '@/components/top-categories-card'
import CurrentCatalog from '@/components/current-catalog'
import ProductCard from '@/components/product/card'
import { cardClass } from '@/components/ui/card'

import { loadAdverts, loadProducts } from '@/lib/queries'
import { recomendedProductsFilters, newProductsFilters } from '@/lib/catalog'
import { Advert, ProductInfo } from '@/lib/types'
import { advertClass } from '@/components/ui/content'

export const revalidate = 3600

const itemsPerSection = 16
const sort = '-price'

// A banner in a row of its own, its HTML holds the column
function MainAdvert({ advert }: { advert: Advert }) {
  return (
    <section className="container order-1 pt-0 sm:order-2 sm:pt-12">
      <div className={`${advertClass} -mx-2`} dangerouslySetInnerHTML={{ __html: advert.content }} />
    </section>
  )
}

function Adverts({ adverts }: { adverts: Advert[] }) {
  return adverts.length > 0 && (
    <section className="container pt-12">
      <div className="grid gap-x-4 sm:grid-cols-2 lg:grid-cols-4">
        {adverts.map((advert) => (
          <div className="mb-6" key={advert.id}>
            <div className={`${cardClass} ${advertClass} h-full overflow-hidden`} dangerouslySetInnerHTML={{ __html: advert.content }} />
            <hr className="sm:hidden" />
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
    <section id={id} className="container pt-12" itemScope itemType="http://schema.org/OfferCatalog">
      <div className="mb-6 flex flex-wrap items-end border-b-2 border-primary pt-1 pb-0">
        <div className="hidden sm:block"><img src={`/i/categories/${img}`} alt="*" /></div>
        <Link href={href}>
          <h2 className="me-2 mb-0 pt-4 pb-2 text-h3" itemProp="name">{title}</h2>
        </Link>
      </div>
      <div className="grid gap-x-4 pt-2 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4">
        {products.map((product, index) => (
          <div className="mb-6" key={product.id}>
            <ProductCard product={product} gtmList="Первая страница акции" gtmPosition={index} />
            <hr className="sm:hidden" />
          </div>
        ))}
      </div>
    </section>
  )
}

const facts = [
  { title: 'Бренд №1', text: <>по&nbsp;объёму продаж швейного оборудования в&nbsp;мире</> },
  { title: '3 собственных завода', text: 'в Японии, Таиланде и на Тайване' },
  { title: 'Официальные', text: <>поставки в&nbsp;Россию</> },
  { title: 'В 1921 году', text: <>основана первая фабрика в&nbsp;Японии</> },
]

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
    <div className="mb-4">
      <section className="pb-12">
        <div className="bg-info">
          <div className="hidden justify-between md:flex">
            <div><img src="/i/tree_left.svg" alt="" /></div>
            <div><img src="/i/tree_right.svg" alt="" /></div>
          </div>
        </div>
      </section>

      <div className="relative z-10 flex flex-col pt-4 md:-mt-100 lg:pt-0">
        <section className="container order-2 sm:order-1">
          <TopCategoriesCard />
          <CurrentCatalog />
        </section>

        {mainTopAdvert && <MainAdvert advert={mainTopAdvert} />}
      </div>

      <Adverts adverts={topAdverts} />

      {recomendedProducts.results.length > 0 && (
        <ProductsSection products={recomendedProducts.results} id="sw-recomended" title="Специальные предложения" img="heart.svg" href="/catalog/promo/" />
      )}

      {mainMiddleAdvert && <MainAdvert advert={mainMiddleAdvert} />}

      <Adverts adverts={middleAdverts} />

      {newProducts.results.length > 0 && (
        <ProductsSection products={newProducts.results} id="sw-new" title="Новинки" img="stars.svg" href="/catalog/New/" />
      )}

      {mainBottomAdvert && <MainAdvert advert={mainBottomAdvert} />}

      <Adverts adverts={bottomAdverts} />

      <div className="container text-center">
        <div className="grid md:grid-cols-4">
          {facts.map(({ title, text }) => (
            <div className="p-6" key={title}>
              <h2 className="mb-3 text-h2 text-primary">{title}</h2>
              <p className="mb-4">{text}</p>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}