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

export interface MarkerPin {
  icon: string  // 24x24 image drawn inside the pin
  color: string
}

// Same shape as YMapDefaultMarker of @yandex/ymaps3-default-ui-theme in normal size,
// which can't be used directly because it only shows icons of its own set
const PIN_HEIGHT = 61
const PIN_PATH = 'M23 61a2 2 0 1 1 0-4 2 2 0 0 1 0 4M28.342 45.376q-4.614 1.395-4.831 6.147a.5.5 0 0 1-.5.477h-.022a.5.5 0 0 1-.5-.477q-.216-4.752-4.831-6.147C7.53 42.968 0 33.863 0 23 0 10.298 10.298 0 23 0s23 10.298 23 23c0 10.863-7.531 19.968-17.658 22.376'

function MarkerIcon({ pin, title, clickable = false }: { pin: MarkerPin, title: string, clickable?: boolean }) {
  return (
    <div style={{ position: 'absolute', cursor: clickable ? 'pointer' : 'auto' }}>
      <svg
        width={46}
        height={PIN_HEIGHT}
        viewBox={`0 0 46 ${PIN_HEIGHT}`}
        style={{
          position: 'absolute',
          display: 'block',
          maxWidth: 'none',
          transform: 'translate(-50%, calc(-100% + 2px))',
          filter: 'drop-shadow(0px 2px 6px rgba(24, 27, 34, 0.4))',
        }}>
        <path fill={pin.color} d={PIN_PATH} />
      </svg>
      {/* eslint-disable-next-line @next/next/no-img-element */}
      <img
        src={pin.icon}
        alt={title}
        width={24}
        height={24}
        style={{ position: 'absolute', display: 'block', maxWidth: 'none', transform: `translate(-50%, ${-PIN_HEIGHT + 2 + 10}px)` }} />
    </div>
  )
}

function MarkerBalloon({ children, onClose }: { children: ReactNode, onClose: () => void }) {
  return (
    <div className="card shadow fs-xs" style={{ position: 'absolute', left: '-8rem', bottom: PIN_HEIGHT + 6, width: '16rem', cursor: 'auto' }}>
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
  pin: MarkerPin
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
                <MarkerIcon pin={marker.pin} title={marker.title} clickable />
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

export function LocationMap({ coordinates, pin, title }: { coordinates: LngLat, pin: MarkerPin, title: string }) {
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
              <MarkerIcon pin={pin} title={title} />
            </ymaps.YMapMarker>
          </ymaps.YMap>
        )}
      </YMaps>
    </div>
  )
}
