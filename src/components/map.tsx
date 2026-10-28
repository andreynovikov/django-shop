'use client'

import * as React from 'react'
import * as ReactDOM from 'react-dom'
import { ReactNode, useMemo, useState } from 'react'
import Script from 'next/script'

import type { LngLat, YMapLocationRequest } from '@yandex/ymaps3-types'

const DEFAULT_LOCATION: YMapLocationRequest = { center: [37.64, 55.76], zoom: 10 }
// Kept stable, a new default array on every render would move the map back to the default location
const NO_FOCUS_POINTS: LngLat[] = []

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

function MarkerIcon({ icon, title, clickable = false }: { icon: string, title: string, clickable?: boolean }) {
  return (
    // eslint-disable-next-line @next/next/no-img-element
    <img
      src={icon}
      alt={title}
      width={27}
      height={26}
      style={{ position: 'absolute', left: -10, top: -23, cursor: clickable ? 'pointer' : 'auto', maxWidth: 'none' }} />
  )
}

function MarkerBalloon({ children, onClose }: { children: ReactNode, onClose: () => void }) {
  return (
    <div className="card shadow fs-xs" style={{ position: 'absolute', left: '-8rem', bottom: '1.75rem', width: '16rem', cursor: 'auto' }}>
      <div className="card-body p-2">
        <button type="button" className="btn-close float-end" aria-label="Закрыть" onClick={onClose}></button>
        {children}
      </div>
    </div>
  )
}

export interface MapMarker {
  id: number
  coordinates: LngLat
  icon: string
  title: string
  balloon: ReactNode
}

export function MarkersMap({ markers, focusPoints = NO_FOCUS_POINTS }: { markers: MapMarker[], focusPoints?: LngLat[] }) {
  const [selected, setSelected] = useState<number | null>(null)

  const location = useMemo<YMapLocationRequest>(() => {
    if (focusPoints.length === 0)
      return DEFAULT_LOCATION

    if (focusPoints.length === 1)
      return { center: focusPoints[0], zoom: 14, duration: 500 }

    // Set map bounds to make all focus points visible
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
            {markers.map((marker) => (
              <ymaps.YMapMarker
                key={marker.id}
                coordinates={marker.coordinates}
                zIndex={selected === marker.id ? 1 : 0}
                onClick={() => setSelected(selected === marker.id ? null : marker.id)}>
                <MarkerIcon icon={marker.icon} title={marker.title} clickable />
                {selected === marker.id && (
                  <MarkerBalloon onClose={() => setSelected(null)}>
                    {marker.balloon}
                  </MarkerBalloon>
                )}
              </ymaps.YMapMarker>
            ))}
          </ymaps.YMap>
        )}
      </YMaps>
    </div>
  )
}

export function LocationMap({ coordinates, icon, title }: { coordinates: LngLat, icon: string, title: string }) {
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
              <MarkerIcon icon={icon} title={title} />
            </ymaps.YMapMarker>
          </ymaps.YMap>
        )}
      </YMaps>
    </div>
  )
}
