
'use client'

import { Fragment, useState, useMemo, ReactNode } from 'react'
import Link from 'next/link'

import { Collapsible } from '@base-ui/react/collapsible'
import { IconClock, IconMapPin, IconPhone, IconWorld } from '@tabler/icons-react'

import { navLinkClass } from '@/components/ui/nav'

import type { LngLat } from '@yandex/ymaps3-types'

import { useBreakpoint } from '@/lib/breakpoint'
import { City, StoreInfo } from '@/lib/types'
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
      <Collapsible.Trigger className={`block rounded-md p-1 text-start transition-colors ${selected === id ? 'bg-info text-white' : 'text-gray-700 hover:text-primary'} ${className}`}>
        {name}
      </Collapsible.Trigger>
      <Collapsible.Panel className="h-(--collapsible-panel-height) overflow-hidden transition-[height] duration-350 data-ending-style:h-0 data-starting-style:h-0" keepMounted>
        {children}
      </Collapsible.Panel>
    </Collapsible.Root>
  )
}

// A line of a store card, with its icon
const itemClass = 'mt-2 flex border-t pt-2'
const storeIcon = { size: 18, stroke: 1.5, className: 'my-1 text-primary' }

type StoreGroup = {
  city: City
  stores: StoreInfo[]
}

export function StoreList({ stores }: { stores: StoreInfo[] }) {
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
      <div className="w-full">
        <div className="grid lg:grid-cols-2">
          <div className="relative min-h-[26rem] overflow-hidden">
            <StoreMap stores={stores} focusPoints={mapFocusPoints} />
          </div>
          <div className="p-6 xl:px-12">
            <div>
              <Collapsable
                id={2}
                name="Москва"
                selected={currentCity}
                onSelect={() => handleCitySelect(2)}
                className="text-md font-bold">
                {stores && stores.filter(({ city }) => city.id === 2).map((store) => (
                  <div className="ps-2 pt-1 text-xs" key={store.id}>
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
                className="text-md font-bold">
                {stores && stores.filter(({ city }) => city.id === 21).map((store) => (
                  <div className="ps-2 pt-1 text-xs" key={store.id}>
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
            <div className="mt-1 flex gap-1">
              {storeGroups.length > 0 && rows(storeGroups, cols).map((column, index) => (
                <div key={index} className="flex-1">
                  {column.map(({ city, stores }) => (
                    <Collapsable
                      key={city.id}
                      id={city.id}
                      name={city.name}
                      selected={currentCity}
                      onSelect={() => handleCitySelect(city.id)}
                      className="text-ms">
                      {stores.map((store) => (
                        <div className="ps-2 pt-1 text-xs" key={store.id}>
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
          </div>
        </div>
      </div>

      <section className="mb-12 w-full px-[.9375rem] pt-7.5 md:mt-6 xl:px-7.5">
        <div className="grid gap-x-7.5 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
          {storeGroups.length > 0 && storeGroups.filter(({ city }) => currentCity === null || city.id === currentCity).map(({ city, stores }) => (
            <Fragment key={city.id}>
              {stores.map((store) => (
                <div className="mb-7.5" key={store.id}>
                  <div className="relative flex min-w-0 flex-col rounded-lg bg-white shadow-sm">
                    <div className="p-5" itemScope itemType="http://schema.org/Organization">
                      <h6 className="mb-3 text-h6">
                        {store.logo === 'sewingworld' ?
                          <Link href={`/stores/${store.id}`} itemProp="url">
                            <span itemProp="name">&quot;{store.name}&quot; - {city.name}</span>
                          </Link>
                          :
                          <span itemProp="name">&quot;{store.name}&quot; ({city.name})</span>
                        }
                      </h6>
                      <ul>
                        <li className="flex">
                          <IconMapPin {...storeIcon} />
                          <div className="ps-4 text-sm" itemProp="address" itemScope itemType="http://schema.org/PostalAddress">
                            <span itemProp="streetAddress">
                              {store.address}
                              {store.address2 && <><br />{store.address2}</>}
                            </span>
                            <span className="hidden" itemProp="addressLocality">{city.name}</span>
                            <span className="hidden" itemProp="addressCountry">{city.country.name}</span>
                          </div>
                        </li>
                        {store.phones && (
                          <li className={itemClass}>
                            <IconPhone {...storeIcon} />
                            <div className="ps-4 text-sm">
                              {parsePhones(store.phones).map(({ label, number, note, href }, index) => (
                                <a
                                  className={`block ${navLinkClass()} ${index > 0 ? 'mt-2' : ''}`}
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
                          <li className={itemClass}>
                            <IconClock {...storeIcon} />
                            <div className="ps-4 text-sm">
                              {store.hours.split(',').map((hours, index) => (
                                <div className={index > 0 ? 'mt-2' : ''} key={index}>
                                  {hours.trim()}
                                </div>
                              ))}
                            </div>
                          </li>
                        )}
                        {store.url && (
                          <li className={itemClass}>
                            <IconWorld {...storeIcon} />
                            <div className="ps-4 text-sm">
                              <a className={navLinkClass()} href={store.url}>{store.url}</a>
                            </div>
                          </li>
                        )}
                        {store.logo !== 'sewingworld' && (
                          <li className="mt-2 pt-2">
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