import { Fragment, useState, useEffect, useMemo } from 'react'
import Link from 'next/link'
import Script from 'next/script'
import { useQuery } from '@tanstack/react-query'

import PageLayout from '@/components/layout/page'

import { rows } from '@/lib/partition'
import { storeKeys, loadStores } from '@/lib/queries'

export default function Stores({marketplace, lottery}) {
  const [ymapsReady, setYMapsReady] = useState(false)
  const [ymap, setYMap] = useState(null)
  const [currentCity, setCurrentCity] = useState(null)

  const { data: stores, isSuccess } = useQuery({
    queryKey: storeKeys.lists({marketplace, lottery}),
    queryFn: () => loadStores({marketplace, lottery})
  })

  useEffect(() => {
    if (!ymapsReady || !isSuccess)
      return

    const coords = [55.76, 37.64]
    const map = new ymaps.Map('map', {
      center: coords,
      zoom: 10,
      controls: ['zoomControl', 'fullscreenControl', 'geolocationControl', 'rulerControl']
    })
    map.margin.setDefaultMargin(100)

    stores.filter((store) => store.latitude && store.longitude).map((store) => {
      map.geoObjects.add(new ymaps.Placemark([store.latitude, store.longitude], {
        balloonContentHeader:
          `<a href="/stores/${store.id}/">${store.name}</a>`,
        balloonContent:
          '<div><i class="ci-location text-primary d-inline-block me-2"></i>' +
          `<span class="d-inline-block align-top">${store.address}${store.address2 ? '<br/>' + store.address2 : ''}</span></div>` +
          (store.hours ?
            '<div class="mt-1"><i class="ci-time text-primary d-inline-block me-2"></i>' +
            `<span class="d-inline-block align-top">${store.hours}</span></div>`
            : '') +
          (store.phone ?
            '<div class="mt-1"><i class="ci-phone text-primary d-inline-block me-2"></i>' +
            `<span class="d-inline-block align-top">${store.phone}${store.phone2 ? '<br/>' + store.phone2 : ''}</span></div>`
            : '') +
          (store.url ?
            '<div class="mt-1"><i class="ci-dribbble text-primary d-inline-block me-2"></i>' +
            `<span class="d-inline-block align-top"><a href="${store.url}">${store.url}</a></span></div>`
            : ''),
        balloonContentFooter:
          store.logo !== 'sewingworld' ? '<small>*магазин-партнер. Рекламные акции Швейного Мира могут не действовать в этом магазине</small>' : ''
      },
        {
          iconLayout: 'default#image',
          iconImageHref: store.logo ? `/i/shoplogos/marks/${store.logo}.png` : '/i/shoplogos/marks/other.png',
          iconImageSize: [27, 26], iconImageOffset: [-10, -23]
        }))
    })

    const location = ymaps.geolocation
    location.get({
      provider: 'yandex'
    }).then(function (result) {
      console.log(result)
      // TODO: select city based on location
      //var userCoodinates = result.geoObjects.get(0).geometry.getCoordinates();
      //myMap.setCenter(userCoodinates);
    }, function (err) {
      console.log(err)
    })

    setYMap(map)

    return () => {
      map.destroy()
      setYMap(null)
    }
  }, [ymapsReady, isSuccess]) //eslint-disable-line react-hooks/exhaustive-deps

  const storeGroups = useMemo(() => {
    if (!isSuccess)
      return []

    const { groups } = stores.reduce(({ groups, city }, store) => {
      if (store.city.id !== city) {
        groups.push({ city: store.city, stores: [] })
        city = store.city.id
      }
      groups[groups.length - 1].stores.push(store)
      return { groups, city }
    }, { groups: [], city: null })

    return groups.sort((a, b) => a.city.name.localeCompare(b.city.name))
  }, [stores, isSuccess])

  const handleCitySelect = (id) => {
    setCurrentCity(id)
    if (ymap === null)
      return

    const { city, stores } = storeGroups.find(({ city }) => city.id === id)
    if (stores.length === 1 && stores[0].latitude && stores[0].longitude) {
      ymap.setCenter([stores[0].latitude, stores[0].longitude])
      ymap.setZoom(14)
      return
    }

    const points = stores.reduce((points, store) => {
      if (store.latitude && store.longitude)
        points.push([store.latitude, store.longitude])
      return points
    }, [])
    if (points.length > 0) {
      // Set map bounds to make all city stores visible
      ymap.setBounds(ymaps.util.bounds.fromPoints(points), {
        checkZoomRange: true,
        preciseZoom: !ymap.options.get('avoidFractionalZoom'),
        useMapMargin: true
      }).then(() => {
        ymap.setZoom(Math.min(14, ymap.getZoom()))
      })
    } else if (city.latitude !== undefined && city.longitude !== undefined) {
      ymap.setCenter([city.latitude, city.longitude])
      ymap.setZoom(12)
    } else {
      const str = 'город ' + city.name + ' ' + city.country.name
      ymaps.geocode(str, { results: 1 }).then((res) => {
        ymap.setCenter(res.geoObjects.get(0).geometry.getCoordinates())
        ymap.setZoom(12)
      })
    }
  }

  const setupYMaps = () => {
    ymaps.ready(function () {
      setYMapsReady(true)
    })
  }

  return (
    <>
      <div className="container-fluid px-0">
        <div className="row g-0">
          <div className="col-lg-6 iframe-full-height-wrap" style={{ minHeight: '26rem' }}>
            <div className="iframe-full-height" id="map"></div>
          </div>
          <div className="col-lg-6 px-4 px-xl-5 py-4">
            <div>
              <button className={`btn ${currentCity === 2 ? 'btn-info' : 'btn-light'} btn-link p-1 fw-bold`} onClick={() => handleCitySelect(2)}>
                Москва
              </button>
            </div>
            <div>
              <button className={`btn ${currentCity === 21 ? 'btn-info' : 'btn-light'} btn-link p-1 fw-bold`} onClick={() => handleCitySelect(21)}>
                Санкт-Петербург
              </button>
            </div>
            <div className="d-flex mt-1">
              {storeGroups.length > 0 && rows(storeGroups, 4).map((column, index) => (
                <div className="pe-1" key={index}>
                  {column.map(({ city }) => (
                    <button
                      key={city.id}
                      className={`d-block btn ${currentCity === city.id ? 'btn-info' : 'btn-light'} btn-sm btn-link p-1`}
                      onClick={() => handleCitySelect(city.id)}>
                      {city.name}
                    </button>
                  ))}
                </div>
              ))}
            </div>
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
                          <Link href={{ pathname: '/stores/[id]', query: { id: store.id } }} itemProp="name">
                            &quot;{store.name}&quot; - {city.name}
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
                              {store.phones.map((phone, index) => (
                                <a
                                  className={'d-block nav-link-style' + (index > 0 ? ' mt-2' : '')}
                                  href={'tel:' + phone.replace(' ', '')}
                                  itemProp="telephone"
                                  key={index}>
                                  {phone}
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
                        {store.url && (
                          <li className="d-flex pt-2 mt-2 mb-0 border-top">
                            <i className="ci-dribbble fs-lg my-1 text-primary" />
                            <div className="ps-3 fs-sm">
                              <a className="nav-link-style" href={store.url}>{store.url}</a>
                            </div>
                          </li>
                        )}
                        {store.logo !== 'sewingworld' && (
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
      <Script
        id="ymaps"
        src={"https://api-maps.yandex.ru/2.1/?lang=ru_RU&apikey=" + process.env.NEXT_PUBLIC_YMAPS_API_KEY}
        onReady={setupYMaps}
        onLoad={setupYMaps} />
    </>
  )
}

Stores.getLayout = function getLayout(page) {
  console.log(page.props)
  const title =
    page.props.marketplace !== false ? "В этих магазинах можно пройти бесплатное обучение работе на швейной машине при предъявлении гарантийного талона" :
      page.props.lottery !== false ? "Покупатели этих магазинов принимают участие в юбилейной лотерее" :
        "Наши магазины рядом с Вами"

  return (
    <PageLayout htmlTitle="Адреса магазинов" title={title}>
      {page}
    </PageLayout>
  )
}

export async function getServerSideProps(context) {
  const marketplace = context.query?.marketplace ?? false
  const lottery = context.query?.lottery ?? false

  return {
    props: {
      marketplace,
      lottery
    }
  }
}
