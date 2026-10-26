'use client'

import * as React from 'react'
import * as ReactDOM from 'react-dom'
import { ReactNode, useMemo, useState } from 'react'
import Script from 'next/script'
import Link from 'next/link'

import type { LngLat, YMapLocationRequest } from '@yandex/ymaps3-types'

import { Store } from '@/lib/types'

const DEFAULT_LOCATION: YMapLocationRequest = { center: [37.64, 55.76], zoom: 10 }

async function loadReactify() {
  const [ymaps3React] = await Promise.all([ymaps3.import('@yandex/ymaps3-reactify'), ymaps3.ready])
  return ymaps3React.reactify.bindTo(React, ReactDOM).module(ymaps3)
}

type YMapComponents = Awaited<ReturnType<typeof loadReactify>>

// Bind reactify once per page load, so components keep their identity between mounts
let reactified: Promise<YMapComponents> | null = null

function YMaps({ children }: { children: (ymaps: YMapComponents) => ReactNode }) {
  const [ymaps, setYMaps] = useState<YMapComponents | null>(null)

  const setupYMaps = () => {
    reactified ??= loadReactify()
    reactified.then(setYMaps)
  }

  return (
    <>
      {ymaps && children(ymaps)}
      <Script
        id="ymaps"
        src={"https://api-maps.yandex.ru/v3/?lang=ru_RU&apikey=" + process.env.NEXT_PUBLIC_YMAPS_API_KEY}
        onReady={setupYMaps} />
    </>
  )
}

function StoreMarkerIcon({ store, clickable = false }: { store: Store, clickable?: boolean }) {
  return (
    // eslint-disable-next-line @next/next/no-img-element
    <img
      src={store.logo ? `/i/shoplogos/marks/${store.logo}.png` : '/i/shoplogos/marks/other.png'}
      alt={store.name}
      width={27}
      height={26}
      style={{ position: 'absolute', left: -10, top: -23, cursor: clickable ? 'pointer' : 'auto', maxWidth: 'none' }} />
  )
}

function StoreBalloon({ store, onClose }: { store: Store, onClose: () => void }) {
  return (
    <div className="card shadow fs-xs" style={{ position: 'absolute', left: '-8rem', bottom: '1.75rem', width: '16rem', cursor: 'auto' }}>
      <div className="card-body p-2">
        <button type="button" className="btn-close float-end" aria-label="Закрыть" onClick={onClose}></button>
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
      </div>
    </div>
  )
}

export function StoreMap({ stores, focusPoints }: { stores: Store[] | undefined, focusPoints: LngLat[] }) {
  const [selected, setSelected] = useState<number | null>(null)

  const location = useMemo<YMapLocationRequest>(() => {
    if (focusPoints.length === 0)
      return DEFAULT_LOCATION

    if (focusPoints.length === 1)
      return { center: focusPoints[0], zoom: 14, duration: 500 }

    // Set map bounds to make all city stores visible
    const lngs = focusPoints.map(([lng]) => lng)
    const lats = focusPoints.map(([, lat]) => lat)
    return {
      bounds: [[Math.min(...lngs), Math.max(...lats)], [Math.max(...lngs), Math.min(...lats)]],
      duration: 500
    }
  }, [focusPoints])

  return (
    <div className="iframe-full-height">
      <YMaps>
        {(ymaps) => (
          <ymaps.YMap location={location} margin={[100, 100, 100, 100]}>
            <ymaps.YMapDefaultSchemeLayer />
            <ymaps.YMapDefaultFeaturesLayer />
            {stores?.filter((store) => store.latitude && store.longitude).map((store) => (
              <ymaps.YMapMarker
                key={store.id}
                coordinates={[store.longitude!, store.latitude!]}
                zIndex={selected === store.id ? 1 : 0}
                onClick={() => setSelected(selected === store.id ? null : store.id)}>
                <StoreMarkerIcon store={store} clickable />
                {selected === store.id && <StoreBalloon store={store} onClose={() => setSelected(null)} />}
              </ymaps.YMapMarker>
            ))}
          </ymaps.YMap>
        )}
      </YMaps>
    </div>
  )
}

export function StoreLocationMap({ store, coordinates }: { store: Store, coordinates: LngLat }) {
  // A new location object on every render would move the map back after user panning
  const location = useMemo<YMapLocationRequest>(() => ({ center: coordinates, zoom: 14 }), [coordinates])

  return (
    <div className="iframe-full-height">
      <YMaps>
        {(ymaps) => (
          <ymaps.YMap location={location}>
            <ymaps.YMapDefaultSchemeLayer />
            <ymaps.YMapDefaultFeaturesLayer />
            <ymaps.YMapMarker coordinates={coordinates}>
              <StoreMarkerIcon store={store} />
            </ymaps.YMapMarker>
          </ymaps.YMap>
        )}
      </YMaps>
    </div>
  )
}
