import { Metadata } from 'next'

import { IconClock, IconMapPin, IconPhone, IconWorld } from '@tabler/icons-react'

import { pageContentWrapper } from '@/components/layout/page-content-wrapper'
import { groupByCountryAndCity } from '@/components/location-groups'
import { MapMarker, MarkerPin, MarkersMap } from '@/components/map'

import { loadStores } from '@/lib/queries'
import { StoreInfo } from '@/lib/types'

export const metadata: Metadata = {
  title: 'Где купить',
}

const storePin: MarkerPin = { icon: '/i/shoplogos/marks/other.svg', color: '#E63946' }

const balloonIconProps = { size: 16, className: 'text-primary flex-shrink-0 me-2 mt-1' }

function StoreBalloon({ store }: { store: StoreInfo }) {
  return (
    <>
      <h6 className="fs-sm mb-2">{store.name}</h6>
      {store.address && (
        <div className="d-flex">
          <IconMapPin {...balloonIconProps} />
          <span>
            {store.address}
            {store.address2 && <><br />{store.address2}</>}
          </span>
        </div>
      )}
      {store.hours && (
        <div className="d-flex mt-1">
          <IconClock {...balloonIconProps} />
          <span>{store.hours}</span>
        </div>
      )}
      {store.phone && (
        <div className="d-flex mt-1">
          <IconPhone {...balloonIconProps} />
          <span>
            {store.phone}
            {store.phone2 && <><br />{store.phone2}</>}
          </span>
        </div>
      )}
      {store.url && (
        <div className="d-flex mt-1">
          <IconWorld {...balloonIconProps} />
          <span><a href={store.url}>{store.url}</a></span>
        </div>
      )}
    </>
  )
}

// Static, the backend revalidates it when stores are saved
export default async function StoresPage() {
  const stores = await loadStores()

  const storeGroups = groupByCountryAndCity(stores)

  const markers: MapMarker[] = stores
    .filter((store) => store.publish && store.latitude && store.longitude)
    .map((store) => ({
      id: store.id,
      coordinates: [store.longitude!, store.latitude!],
      pin: storePin,
      title: store.name,
      balloon: <StoreBalloon store={store} />,
    }))

  return pageContentWrapper({
    title: 'Где купить машины Family',
    description: 'Эксклюзивное право представления и распространения продукции бренда “Family” в России и странах СНГ принадлежит компании “Торговый Дом Швейных Машин”. Со списком проверенных официальных дилеров вы можете ознакомиться ниже:',
    children: (
      <>
        <section>
          <div className="container">
            <div className="iframe-full-height-wrap" style={{ height: 400 }}>
              <MarkersMap markers={markers} />
            </div>
          </div>
        </section>
        <section className="pb-5">
          {storeGroups.map(({ country, cities }) => (
            <div className="container" key={country.id}>
              <h2 className="mt-4 mb-3 text-muted">{country.name}</h2>
              <div className="row">
                {cities.map(({ city, items }) => (
                  items.map((store) => (
                    <div className="col-xl-3 col-lg-4 col-sm-6" key={store.id}>
                      <div className="block-header">
                        <h6 className="text-uppercase mb-0">{city.name}</h6>
                      </div>
                      <div className="block-body bg-light pt-1 mb-2">
                        <p>
                          <strong>{store.name}</strong><br />
                          {store.address && <>{store.address}<br /></>}
                          {store.address2 && <>{store.address2}<br /></>}
                          {store.phone && <>{store.phone}<br /></>}
                          {store.url && <a href={store.url}>{store.url}</a>}
                        </p>
                      </div>
                    </div>
                  ))
                ))}
              </div>
            </div>
          ))}
        </section>
      </>
    )
  })
}
