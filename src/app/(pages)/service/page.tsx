import { Metadata } from 'next'

import { pageContentWrapper } from '@/components/layout/page-content-wrapper'
import { MapMarker, MarkersMap } from '@/components/map'

import { loadServiceCenters } from '@/lib/queries'
import { Country, ServiceCenter } from '@/lib/types'

export const revalidate = 3600

export const metadata: Metadata = {
  title: 'Сервисные центры',
}

type CountryGroup = {
  country: Country
  services: ServiceCenter[]
}

function ServiceBalloon({ service }: { service: ServiceCenter }) {
  return (
    <>
      <h6 className="fs-sm mb-2">{service.city.name}</h6>
      <div>
        <i className="ci-location text-primary d-inline-block me-2"></i>
        <span className="d-inline-block align-top">{service.address}</span>
      </div>
      <div className="mt-1">
        <i className="ci-phone text-primary d-inline-block me-2"></i>
        <span className="d-inline-block align-top">{service.phone}</span>
      </div>
    </>
  )
}

export default async function ServicePage() {
  const services = await loadServiceCenters()

  // backend returns service centers ordered by country
  const countryGroups = services.reduce((groups, service) => {
    const last = groups.at(-1)
    if (last?.country.id === service.city.country.id)
      last.services.push(service)
    else
      groups.push({ country: service.city.country, services: [service] })
    return groups
  }, [] as CountryGroup[])

  const markers: MapMarker[] = services
    .filter((service) => service.latitude && service.longitude)
    .map((service) => ({
      id: service.id,
      coordinates: [service.longitude!, service.latitude!],
      pin: { icon: '/i/shoplogos/marks/workshop.svg', color: '#3163ad' },
      title: service.address,
      balloon: <ServiceBalloon service={service} />,
    }))

  return pageContentWrapper({
    title: <>Сервисное обслуживание и ремонт<span className="d-lg-none"> швейных машин, оверлоков, вышивальных и вязальных машин</span></>,
    children: (
      <div className="container-fluid px-0">
        <section className="row g-0">
          <div className="col-lg-6 iframe-full-height-wrap order-md-2" style={{ minHeight: '26rem' }}>
            <MarkersMap markers={markers} />
          </div>
          <div className="col-md-6 px-3 px-md-5 py-5 order-md-1">
            <div className="mx-auto py-lg-5" style={{ maxWidth: '35rem' }}>
              <p className="lead">Наши сервисные центры предлагают следующие работы и услуги:</p>
              <ul className="list-style pb-3 text-muted">
                <li>
                  Гарантийный ремонт и обслуживание швейных машин, вышивальных машин, оверлоков,
                  вязальных машин и другого оборудования производства компаний
                  Pfaff, Husqvarna Viking, Family, Janome, Singer, Silver Reed, Hague.
                </li>
                <li>
                  Поставку запасных частей для швейного оборудования.
                </li>
                <li>
                  Послегарантийный ремонт машин Pfaff, Husqvarna Viking, Family, Janome, Singer,
                  Silver Reed, Hague и New Home и ряда других фирм.
                </li>
              </ul>
            </div>
          </div>
        </section>
        <hr />

        <section className="container-fluid pt-grid-gutter mt-md-4 mb-5">
          {countryGroups.map(({ country, services }) => (
            <div key={country.id}>
              <h2 className="h3 mb-3">{country.name}</h2>
              <div className="row">
                {services.map((service) => (
                  <div className="col-xl-3 col-lg-4 col-sm-6 mb-grid-gutter" key={service.id}>
                    <div className="card border-0 shadow-sm">
                      <div className="card-body" itemScope itemType="http://schema.org/Organization">
                        <h6 className="card-title" itemProp="name">{service.city.name}</h6>
                        <ul className="list-unstyled mb-0">
                          <li className="d-flex">
                            <i className="ci-location fs-lg my-1 text-primary" />
                            <div className="ps-3 fs-sm" itemProp="address" itemScope itemType="http://schema.org/PostalAddress">
                              <span itemProp="streetAddress">{service.address}</span>
                              <span className="d-none" itemProp="addressLocality">{service.city.name}</span>
                              <span className="d-none" itemProp="addressCountry">{country.name}</span>
                            </div>
                          </li>
                          <li className="d-flex pt-2 mt-2 mb-0 border-top">
                            <i className="ci-phone fs-lg my-1 text-primary" />
                            <div className="ps-3 fs-sm">
                              {service.phone.split(',').map((phone, index) => (
                                <a
                                  className={'d-block nav-link-style' + (index > 0 ? ' mt-2' : '')}
                                  href={'tel:' + phone.trim().replace(/[ -]/g, '')}
                                  itemProp="telephone"
                                  key={index}>
                                  {phone.trim()}
                                </a>
                              ))}
                            </div>
                          </li>
                        </ul>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          ))}
        </section>
      </div>
    )
  })
}
