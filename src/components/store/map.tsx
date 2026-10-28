'use client'

import { useMemo } from 'react'
import Link from 'next/link'

import type { LngLat } from '@yandex/ymaps3-types'

import { LocationMap, MapMarker, MarkersMap } from '@/components/map'

import { Store } from '@/lib/types'

const storeIcon = (store: Store) =>
  store.logo ? `/i/shoplogos/marks/${store.logo}.png` : '/i/shoplogos/marks/other.png'

function StoreBalloon({ store }: { store: Store }) {
  return (
    <>
      <h6 className="fs-sm mb-2">
        <Link href={`/stores/${store.id}/`}>{store.name}</Link>
      </h6>
      <div>
        <i className="ci-location text-primary d-inline-block me-2"></i>
        <span className="d-inline-block align-top">
          {store.address}
          {store.address2 && <><br />{store.address2}</>}
        </span>
      </div>
      {store.hours && (
        <div className="mt-1">
          <i className="ci-time text-primary d-inline-block me-2"></i>
          <span className="d-inline-block align-top">{store.hours}</span>
        </div>
      )}
      {store.phone && (
        <div className="mt-1">
          <i className="ci-phone text-primary d-inline-block me-2"></i>
          <span className="d-inline-block align-top">
            {store.phone}
            {store.phone2 && <><br />{store.phone2}</>}
          </span>
        </div>
      )}
      {store.url && (
        <div className="mt-1">
          <i className="ci-dribbble text-primary d-inline-block me-2"></i>
          <span className="d-inline-block align-top"><a href={store.url}>{store.url}</a></span>
        </div>
      )}
      {store.logo !== 'sewingworld' && (
        <small className="d-block mt-2 text-muted">
          *магазин-партнер. Рекламные акции Швейного Мира могут не действовать в этом магазине
        </small>
      )}
    </>
  )
}

export function StoreMap({ stores, focusPoints }: { stores: Store[] | undefined, focusPoints: LngLat[] }) {
  const markers = useMemo<MapMarker[]>(() => (stores ?? [])
    .filter((store) => store.latitude && store.longitude)
    .map((store) => ({
      id: store.id,
      coordinates: [store.longitude!, store.latitude!],
      icon: storeIcon(store),
      title: store.name,
      balloon: <StoreBalloon store={store} />,
    })), [stores])

  return <MarkersMap markers={markers} focusPoints={focusPoints} />
}

export function StoreLocationMap({ store, coordinates }: { store: Store, coordinates: LngLat }) {
  return <LocationMap coordinates={coordinates} icon={storeIcon(store)} title={store.name} />
}
