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

const balloonIconProps = { size: 16, className: 'me-2 mt-0.5 shrink-0 text-primary' }

function StoreBalloon({ store }: { store: StoreInfo }) {
  return (
    <>
      <h6 className="mb-2 text-sm leading-[1.1] font-bold">{store.name}</h6>
      {store.address && (
        <div className="flex">
          <IconMapPin {...balloonIconProps} />
          <span>
            {store.address}
            {store.address2 && <><br />{store.address2}</>}
          </span>
        </div>
      )}
      {store.hours && (
        <div className="mt-1 flex">
          <IconClock {...balloonIconProps} />
          <span>{store.hours}</span>
        </div>
      )}
      {store.phone && (
        <div className="mt-1 flex">
          <IconPhone {...balloonIconProps} />
          <span>
            {store.phone}
            {store.phone2 && <><br />{store.phone2}</>}
          </span>
        </div>
      )}
      {store.url && (
        <div className="mt-1 flex">
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
        <section className="container">
          <div className="relative min-h-72 overflow-hidden" style={{ height: 400 }}>
            <MarkersMap markers={markers} />
          </div>
        </section>
        <section className="container pb-12">
          {storeGroups.map(({ country, cities }) => (
            <div key={country.id}>
              <h2 className="mt-6 mb-4 text-3xl leading-[1.1] font-bold text-muted lg:text-[2.7rem]">{country.name}</h2>
              <div className="grid gap-x-6 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
                {cities.map(({ city, items }) => (
                  items.map((store) => (
                    <div key={store.id}>
                      <div className="bg-gray-100 px-6 py-5">
                        <h6 className="leading-[1.1] font-bold tracking-widest uppercase">{city.name}</h6>
                      </div>
                      <div className="mb-2 bg-gray-100 px-6 pt-1 pb-5">
                        <p className="mb-4">
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
