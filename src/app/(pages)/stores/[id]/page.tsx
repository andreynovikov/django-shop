import { cache } from 'react'
import { Metadata } from 'next'
import { notFound } from 'next/navigation'

import { pageContentWrapper } from '@/components/layout/page-content-wrapper'
import { ScrollLink } from '@/components/scroll-link'
import { StoreLocationMap } from '@/components/store/map'

import { HttpError, loadStore, loadStores } from '@/lib/queries'

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
        <section className="container py-3 py-lg-5">
          <p className="lead">Продажа швейных машин, оверлоков, вязальных машин и аксессуаров для рукоделия в г. {store.city.name}</p>
        </section>
        <section className="container-fluid">
          <div className="row">
            <div className={`col-xl-${cols} col-md-6 mb-grid-gutter`}>
              <ScrollLink className="card h-100" href="#map">
                <div className="card-body text-center">
                  <i className="ci-location h3 mt-2 mb-4 text-primary" />
                  <h3 className="h6 mb-3">Адрес</h3>
                  <ul className="list-unstyled fs-sm text-muted mb-0">
                    <li>{store.address}</li>
                    {store.address2 && <li>{store.address2}</li>}
                  </ul>
                  {hasLocation && (
                    <div className="fs-sm text-primary">
                      Посмотреть на карте
                      <i className="ci-arrow-right fs-xs ms-1" />
                    </div>
                  )}
                </div>
              </ScrollLink>
            </div>
            {hours.length > 0 && (
              <div className={`col-xl-${cols} col-md-6 mb-grid-gutter`}>
                <div className="card h-100">
                  <div className="card-body text-center">
                    <i className="ci-time h3 mt-2 mb-4 text-primary" />
                    <h3 className="h6 mb-3">Часы работы</h3>
                    <ul className="list-unstyled fs-sm text-muted mb-0">
                      {hours.map((item, index) => (
                        <li className={index === hours.length - 1 ? 'mb-0' : ''} key={index}>
                          {item.trim()}
                        </li>
                      ))}
                    </ul>
                  </div>
                </div>
              </div>
            )}
            {store.phones && store.phones.length > 0 && (
              <div className={`col-xl-${cols} col-md-6 mb-grid-gutter`}>
                <div className="card h-100">
                  <div className="card-body text-center">
                    <i className="ci-phone h3 mt-2 mb-4 text-primary" />
                    <h3 className="h6 mb-3">Телефон{store.phones.length > 1 && 'ы'}</h3>
                    <ul className="list-unstyled fs-sm mb-0">
                      {store.phones.map((phone, index) => (
                        <li className={index === store.phones.length - 1 ? 'mb-0' : ''} key={index}>
                          <a className="nav-link-style" href={'tel:' + phone.replace(/[ -]/g, '')}>{phone}</a>
                        </li>
                      ))}
                    </ul>
                  </div>
                </div>
              </div>
            )}
            {store.url && (
              <div className={`col-xl-${cols} col-md-6 mb-grid-gutter`}>
                <div className="card h-100">
                  <div className="card-body text-center">
                    <i className="ci-dribbble h3 mt-2 mb-4 text-primary" />
                    <h3 className="h6 mb-3">Сайт магазина</h3>
                    <ul className="list-unstyled fs-sm mb-0">
                      <li className="mb-0">
                        <a className="nav-link-style" href={store.url}>{store.url}</a>
                      </li>
                    </ul>
                  </div>
                </div>
              </div>
            )}
          </div>
        </section>
        {store.description && (
          <section className="container py-3 py-lg-5 mt-4 mb-3">
            <div dangerouslySetInnerHTML={{ __html: store.description }}></div>
          </section>
        )}
        {hasLocation && (
          <div className="container-fluid px-0 pt-3 pt-lg-5" id="map">
            <div className="row g-0">
              <div className="col-lg-12 iframe-full-height-wrap" style={{ minHeight: '28rem' }}>
                <StoreLocationMap store={store} coordinates={[store.longitude!, store.latitude!]} />
              </div>
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
