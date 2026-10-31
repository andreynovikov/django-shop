
'use client'

import { Fragment, useState, useMemo, ReactNode } from 'react'
import Link from 'next/link'

import { Collapsible } from '@base-ui/react/collapsible'

import type { LngLat } from '@yandex/ymaps3-types'

import { useBreakpoint } from '@/lib/breakpoint'
import { City, Store } from '@/lib/types'
import { rows } from '@/lib/partition'
import { parsePhones } from '@/lib/format'
import { StoreMap } from './map'

function Collapsable({
  id,
  name,
  children,
  selected,
  onSelect,
  className
}: {
  id: number,
  name: string,
  children: ReactNode,
  selected: number | null,
  onSelect: () => void,
  className: string
}) {
  return (
    <Collapsible.Root open={selected === id} onOpenChange={onSelect}>
      <Collapsible.Trigger className={`d-block btn ${selected === id ? 'btn-info' : 'btn-light'} btn-link p-1 ${className}`}>
        {name}
      </Collapsible.Trigger>
      <Collapsible.Panel className="sw-collapse" keepMounted>
        {children}
      </Collapsible.Panel>
    </Collapsible.Root>
  )
}

type StoreGroup = {
  city: City
  stores: Store[]
}

export function StoreList({ stores }: { stores: Store[] }) {
  const [currentCity, setCurrentCity] = useState<number | null>(null)
  const [mapFocusPoints, setMapFocusPoints] = useState<LngLat[]>([])
  const breakpoint = useBreakpoint()
  const cols = ['xs', 'sm'].includes(breakpoint)
    ? 2 : ['md', 'lg'].includes(breakpoint) ? 3 : 4

  const storeGroups: Array<StoreGroup> = useMemo(() => {
    if (!stores)
      return []

    const { groups } = stores.reduce(({ groups, city }, store) => {
      if (store.city.id !== city) {
        groups.push({ city: store.city, stores: [] })
        city = store.city.id
      }
      groups[groups.length - 1].stores.push(store)
      return { groups, city }
    }, { groups: [] as Array<StoreGroup>, city: null as number | null })

    return groups.sort((a, b) => a.city.name.localeCompare(b.city.name))
  }, [stores])

  const handleCitySelect = (id: number) => {
    setCurrentCity(id)

    const storeGroup = storeGroups.find(({ city }) => city.id === id)
    if (storeGroup === undefined)
      return

    const points = storeGroup.stores.reduce((points, store) => {
      if (store.latitude && store.longitude)
        points.push([store.longitude, store.latitude])
      return points
    }, [] as LngLat[])
    setMapFocusPoints(points)
  }

  return (
    <>
      <div className="container-fluid px-0">
        <div className="row g-0">
          <div className="col-lg-6 iframe-full-height-wrap" style={{ minHeight: '26rem' }}>
            <StoreMap stores={stores} focusPoints={mapFocusPoints} />
          </div>
          <div className="col-lg-6 px-4 px-xl-5 py-4">
            <div>
              <Collapsable
                id={2}
                name="Москва"
                selected={currentCity}
                onSelect={() => handleCitySelect(2)}
                className="fw-bold">
                {stores && stores.filter(({ city }) => city.id === 2).map((store) => (
                  <div className="fs-xs pt-1 ps-2" key={store.id}>
                    <Link href={`/stores/${store.id}`}>
                      {store.address}
                    </Link>
                    {store.phones && (
                      <>
                        <br />
                        {store.phones[0]}
                      </>
                    )}
                  </div>
                ))}
              </Collapsable>
            </div>
            <div>
              <Collapsable
                id={21}
                name="Санкт-Петербург"
                selected={currentCity}
                onSelect={() => handleCitySelect(21)}
                className="fw-bold">
                {stores && stores.filter(({ city }) => city.id === 21).map((store) => (
                  <div className="fs-xs pt-1 ps-2" key={store.id}>
                    <Link href={`/stores/${store.id}`}>
                      {store.address}
                    </Link>
                    {store.phones && (
                      <>
                        <br />
                        {store.phones[0]}
                      </>
                    )}
                  </div>
                ))}
              </Collapsable>
            </div>
            {/*
            <div className="d-flex gap-1 mt-1">
              {storeGroups.length > 0 && rows(storeGroups, cols).map((column, index) => (
                <div key={index} style={{ flex: "1 1 0" }}>
                  {column.map(({ city, stores }) => (
                    <Collapsable
                      key={city.id}
                      id={city.id}
                      name={city.name}
                      selected={currentCity}
                      onSelect={() => handleCitySelect(city.id)}
                      className="btn-sm">
                      {stores.map((store) => (
                        <div className="fs-xs pt-1 ps-2" key={store.id}>
                          <Link href={`/stores/${store.id}`}>
                            {store.address}
                          </Link>
                          {store.phones && (
                            <>
                              <br />
                              {store.phones[0]}
                            </>
                          )}
                        </div>
                      ))}
                    </Collapsable>
                  ))}
                </div>
              ))}
            </div>
            */}
          </div>
        </div>
      </div>

      <section className="container-fluid pt-grid-gutter mt-md-4 mb-5">
        <div className="row">
          {storeGroups.length > 0 && storeGroups.filter(({ city }) => currentCity === null || city.id === currentCity).map(({ city, stores }) => (
            <Fragment key={city.id}>
              {stores.map((store) => (
                <div className="col-xl-3 col-lg-4 col-sm-6 mb-grid-gutter" key={store.id}>
                  <div className="card border-0 shadow-sm">
                    <div className="card-body" itemScope itemType="http://schema.org/Organization">
                      <h6 className="card-title">
                        {store.logo === 'sewingworld' ?
                          <Link href={`/stores/${store.id}`} itemProp="url">
                            <span itemProp="name">&quot;{store.name}&quot; - {city.name}</span>
                          </Link>
                          :
                          <span itemProp="name">&quot;{store.name}&quot; ({city.name})</span>
                        }
                      </h6>
                      <ul className="list-unstyled mb-0">
                        <li className="d-flex">
                          <i className="ci-location fs-lg my-1 text-primary" />
                          <div className="ps-3 fs-sm" itemProp="address" itemScope itemType="http://schema.org/PostalAddress">
                            <span itemProp="streetAddress">
                              {store.address}
                              {store.address2 && <><br />{store.address2}</>}
                            </span>
                            <span className="d-none" itemProp="addressLocality">{city.name}</span>
                            <span className="d-none" itemProp="addressCountry">{city.country.name}</span>
                          </div>
                        </li>
                        {store.phones && (
                          <li className="d-flex pt-2 mt-2 mb-0 border-top">
                            <i className="ci-phone fs-lg my-1 text-primary" />
                            <div className="ps-3 fs-sm">
                              {parsePhones(store.phones).map(({ label, number, note, href }, index) => (
                                <a
                                  className={'d-block nav-link-style' + (index > 0 ? ' mt-2' : '')}
                                  href={href || undefined}
                                  key={index}>
                                  {label && <>{label} </>}
                                  {number && <span itemProp="telephone">{number}</span>}
                                  {note && <> {note}</>}
                                </a>
                              ))}
                            </div>
                          </li>
                        )}
                        {store.hours && (
                          <li className="d-flex pt-2 mt-2 mb-0 border-top">
                            <i className="ci-time fs-lg my-1 text-primary" />
                            <div className="ps-3 fs-sm">
                              {store.hours.split(',').map((hours, index) => (
                                <div className={index > 0 ? 'mt-2' : ''} key={index}>
                                  {hours.trim()}
                                </div>
                              ))}
                            </div>
                          </li>
                        )}
                        {store.logo !== 'janome' && (
                          <li className="pt-2 mt-2 mb-0">
                            <small className="text-muted">
                              Магазин-партнер: рекламные акции Швейного Мира могут не действовать в этом магазине
                            </small>
                          </li>
                        )}
                      </ul>
                    </div>
                  </div>
                </div>
              ))}
            </Fragment>
          ))}
        </div>
      </section>
    </>
  )
}