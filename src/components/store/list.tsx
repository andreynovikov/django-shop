
'use client'

import { Fragment, useMemo } from 'react'
import Link from 'next/link'

import { IconClock, IconMapPin, IconPhone } from '@tabler/icons-react'

import { navLinkClass } from '@/components/ui/nav'

import { City, StoreInfo } from '@/lib/types'
import { parsePhones } from '@/lib/format'
import { StoreMap } from './map'

// A line of a store card, with its icon
const itemClass = 'mt-2 flex border-t pt-2'
const storeIcon = { size: 18, stroke: 1.5, className: 'my-1 text-primary' }

type StoreGroup = {
  city: City
  stores: StoreInfo[]
}

export function StoreList({ stores }: { stores: StoreInfo[] }) {
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

  return (
    <>
      <div className="container">
        <div className="relative min-h-[26rem] overflow-hidden">
          <StoreMap stores={stores} focusPoints={[]} />
        </div>
      </div>

      <section className="container mb-12 pt-7.5 md:mt-6">
        <div className="grid grid-cols-2 gap-x-7.5">
          {storeGroups.length > 0 && storeGroups.map(({ city, stores }) => (
            <Fragment key={city.id}>
              {stores.map((store) => (
                <div className="mb-7.5" key={store.id}>
                  <div className="relative flex min-w-0 flex-col rounded-lg bg-white shadow-sm">
                    <div className="p-5" itemScope itemType="http://schema.org/Organization">
                      <h6 className="mb-3 text-h6">
                        {store.logo === 'janome' ?
                          <Link href={`/stores/${store.id}`} itemProp="url">
                            <span itemProp="name">{store.name}</span>
                          </Link>
                          :
                          <span itemProp="name">{store.name}</span>
                        }
                      </h6>
                      <ul>
                        <li className="flex">
                          <IconMapPin {...storeIcon} />
                          <div className="ps-4 text-sm" itemProp="address" itemScope itemType="http://schema.org/PostalAddress">
                            <span className="hidden" itemProp="addressCountry">{city.country.name}</span>
                            <span itemProp="addressLocality">{city.name}</span>,{" "}
                            <span itemProp="streetAddress">
                              {store.address}
                              {store.address2 && <><br />{store.address2}</>}
                            </span>
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
                        {store.logo !== 'janome' && (
                          <li className="mt-2 pt-2">
                            <small className="text-muted">
                              Магазин-партнер: рекламные акции Janome могут не действовать в этом магазине
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