import Link from 'next/link'
import { IconChevronRight } from '@tabler/icons-react'

import TopCategoriesCard from '@/components/top-categories-card'
import CurrentCatalog from '@/components/current-catalog'
import ProductCard from '@/components/product/card'
import { buttonClass } from '@/components/ui/button'
import { cardClass } from '@/components/ui/card'

import { loadAdverts, loadProducts } from '@/lib/queries'
import { recomendedProductsFilters, newProductsFilters } from '@/lib/catalog'
import { Advert, ProductInfo } from '@/lib/types'
import { advertClass } from '@/components/ui/content'

export const revalidate = 3600

const itemsPerSection = 16
const sort = '-price'

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
  linkTitle: string
  href: string
}

function ProductsSection({ products, id, title, linkTitle, href }: ProductsSectionProps) {
  return (
    <section id={id} className="container pt-12" itemScope itemType="http://schema.org/OfferCatalog">
      <div className="mb-6 flex flex-wrap items-center justify-between border-b pt-1 pb-6">
        <h2 className="me-2 mb-0 pt-4 text-h3" itemProp="name">{title}</h2>
        <div className="pt-4">
          <Link className={buttonClass({ variant: 'accent', size: 'sm' })} href={href}>
            {linkTitle}
            <IconChevronRight size={14} stroke={1.5} className="-me-1 ms-1" />
          </Link>
        </div>
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

export default async function HomePage() {
  const recomendedProducts = await loadProducts(null, itemsPerSection, recomendedProductsFilters, sort)
  const newProducts = await loadProducts(null, itemsPerSection, newProductsFilters, sort)

  const adverts = await loadAdverts(['main', 'index_top_new', 'index_middle_new', 'index_bottom_new'])

  const mainAdvert = adverts.find(advert => advert.place === 'main')
  const topAdverts = adverts.filter(advert => advert.place === 'index_top_new')
  const middleAdverts = adverts.filter(advert => advert.place === 'index_middle_new')
  const bottomAdverts = adverts.filter(advert => advert.place === 'index_bottom_new')

  return (
    <div className="mb-4">
      <section className="pb-12">
        <div className="bg-dark py-12"></div>
        <div className="py-4"></div>
      </section>

      <div className="relative z-10 -mt-40 flex flex-col pt-4 lg:pt-0">
        <section className="container order-2 sm:order-1">
          <TopCategoriesCard />
          <CurrentCatalog />
        </section>

        {mainAdvert && (
          <section className="container order-1 pt-0 sm:order-2 sm:pt-12">
            <div className={`${advertClass} -mx-2`} dangerouslySetInnerHTML={{ __html: mainAdvert.content }} />
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