import { cache } from 'react'
import { Metadata } from 'next'
import { notFound } from 'next/navigation'

import { pageContentWrapper } from '@/components/layout/page-content-wrapper'
import { ScrollLink } from '@/components/scroll-link'
import { StoreLocationMap } from '@/components/store/map'
import { cardClass } from '@/components/ui/card'
import { contentClass } from '@/components/ui/content'
import { navLinkClass } from '@/components/ui/nav'
import { IconChevronRight, IconClock, IconMapPin, IconPhone, IconWorld } from '@tabler/icons-react'

// A card about the store: an icon, a title and the details
const infoBodyClass = 'flex-auto p-5 text-center'
const infoTitleClass = 'mb-4 text-h6'
const infoIcon = { size: 28, stroke: 1.5, className: 'mt-2 mb-6 text-primary' }

import { HttpError, loadStore, loadStores } from '@/lib/queries'
import { parsePhones } from '@/lib/format'

// Shared by generateMetadata and the page, so the store is fetched once per render
const getStore = cache(async (id: string) => {
  const storeId = Number(id)
  if (!Number.isInteger(storeId))
    notFound()

  try {
    return await loadStore(storeId)
  } catch (err) {
    if (err instanceof HttpError && err.status === 404)
      notFound()
    throw err
  }
})

export async function generateMetadata({ params }: PageProps<'/stores/[id]'>): Promise<Metadata> {
  const { id } = await params
  const store = await getStore(id)
  return { title: `${store.name} - ${store.city.name}` }
}

export default async function StorePage({ params }: PageProps<'/stores/[id]'>) {
  const { id } = await params
  const store = await getStore(id)

  const cols = store.url ? 3 : 4
  const hours = store.hours ? store.hours.split(',') : []
  const hasLocation = store.latitude !== undefined && store.longitude !== undefined

  return pageContentWrapper({
    title: `${store.name} - ${store.city.name}`,
    breadcrumbs: [{ label: 'Магазины', href: '/stores/' }],
    children: (
      <>
        <section className="container py-4 lg:py-12">
          <p className="mb-4 text-xl font-light">Продажа швейных машин, оверлоков, вязальных машин и аксессуаров для рукоделия в г. {store.city.name}</p>
        </section>
        <section className="w-full px-[.9375rem] xl:px-7.5">
          <div className={`grid gap-x-7.5 md:grid-cols-2 ${cols === 3 ? 'xl:grid-cols-4' : 'xl:grid-cols-3'}`}>
            <div className="mb-7.5">
              <ScrollLink className={`${cardClass} h-full`} href="#map">
                <div className={infoBodyClass}>
                  <IconMapPin {...infoIcon} />
                  <h3 className={infoTitleClass}>Адрес</h3>
                  <ul className="mb-0 text-sm text-muted *:mb-[.4rem]">
                    <li>{store.address}</li>
                    {store.address2 && <li>{store.address2}</li>}
                  </ul>
                  {hasLocation && (
                    <div className="text-sm text-primary">
                      Посмотреть на карте
                      <IconChevronRight size={12} stroke={2} className="ms-1" />
                    </div>
                  )}
                </div>
              </ScrollLink>
            </div>
            {hours.length > 0 && (
              <div className="mb-7.5">
                <div className={`${cardClass} h-full`}>
                  <div className={infoBodyClass}>
                    <IconClock {...infoIcon} />
                    <h3 className={infoTitleClass}>Часы работы</h3>
                    <ul className="mb-0 text-sm text-muted *:mb-[.4rem] *:last:mb-0">
                      {hours.map((item, index) => (
                        <li key={index}>
                          {item.trim()}
                        </li>
                      ))}
                    </ul>
                  </div>
                </div>
              </div>
            )}
            {store.phones && store.phones.length > 0 && (
              <div className="mb-7.5">
                <div className={`${cardClass} h-full`}>
                  <div className={infoBodyClass}>
                    <IconPhone {...infoIcon} />
                    <h3 className={infoTitleClass}>Телефон{store.phones.length > 1 && 'ы'}</h3>
                    <ul className="mb-0 text-sm *:mb-[.4rem] *:last:mb-0">
                      {parsePhones(store.phones).map(({ label, number, note, href }, index) => (
                        <li key={index}>
                          {label && <>{label} </>}
                          {number && <a className={navLinkClass()} href={href}>{number}</a>}
                          {note && <> {note}</>}
                        </li>
                      ))}
                    </ul>
                  </div>
                </div>
              </div>
            )}
            {store.url && (
              <div className="mb-7.5">
                <div className={`${cardClass} h-full`}>
                  <div className={infoBodyClass}>
                    <IconWorld {...infoIcon} />
                    <h3 className={infoTitleClass}>Сайт магазина</h3>
                    <ul className="mb-0 text-sm">
                      <li>
                        <a className={navLinkClass()} href={store.url}>{store.url}</a>
                      </li>
                    </ul>
                  </div>
                </div>
              </div>
            )}
          </div>
        </section>
        {store.description && (
          <section className="container mt-6 mb-4 py-4 lg:py-12">
            <div className={contentClass()} dangerouslySetInnerHTML={{ __html: store.description }}></div>
          </section>
        )}
        {hasLocation && (
          <div className="w-full pt-4 lg:pt-12" id="map">
            <div className="relative min-h-[28rem] overflow-hidden">
              <StoreLocationMap store={store} coordinates={[store.longitude!, store.latitude!]} />
            </div>
          </div>
        )}
      </>
    )
  })
}

export async function generateStaticParams() {
  if (process.env.NODE_ENV !== 'production' || process.env.PLAYWRIGHT_TEST === 'true')
    return []

  const stores = await loadStores()
  return stores
    .filter(store => store.logo === 'sewingworld')
    .map(store => ({ id: store.id.toString() }))
}
