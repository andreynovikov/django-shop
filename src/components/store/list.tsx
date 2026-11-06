
'use client'

import { Fragment, useMemo } from 'react'
import Link from 'next/link'

import { City, StoreInfo } from '@/lib/types'
import { parsePhones } from '@/lib/format'
import { StoreMap } from './map'

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
        <div className="iframe-full-height-wrap" style={{ minHeight: '26rem' }}>
          <StoreMap stores={stores} focusPoints={[]} />
        </div>
      </div>

      <section className="container pt-grid-gutter mt-md-4 mb-5">
        <div className="row">
          {storeGroups.length > 0 && storeGroups.map(({ city, stores }) => (
            <Fragment key={city.id}>
              {stores.map((store) => (
                <div className="col-6 mb-grid-gutter" key={store.id}>
                  <div className="card border-0 shadow-sm">
                    <div className="card-body" itemScope itemType="http://schema.org/Organization">
                      <h6 className="card-title">
                        {store.logo === 'janome' ?
                          <Link href={`/stores/${store.id}`} itemProp="url">
                            <span itemProp="name">{store.name}</span>
                          </Link>
                          :
                          <span itemProp="name">{store.name}</span>
                        }
                      </h6>
                      <ul className="list-unstyled mb-0">
                        <li className="d-flex">
                          <i className="ci-location fs-lg my-1 text-primary" />
                          <div className="ps-3 fs-sm" itemProp="address" itemScope itemType="http://schema.org/PostalAddress">
                            <span className="d-none" itemProp="addressCountry">{city.country.name}</span>
                            <span itemProp="addressLocality">{city.name}</span>,{" "}
                            <span itemProp="streetAddress">
                              {store.address}
                              {store.address2 && <><br />{store.address2}</>}
                            </span>
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