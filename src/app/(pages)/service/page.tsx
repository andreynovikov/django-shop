import { Metadata } from 'next'

import { IconMapPin, IconPhone } from '@tabler/icons-react'

import { pageContentWrapper } from '@/components/layout/page-content-wrapper'
import { groupByCountryAndCity } from '@/components/location-groups'
import { MapMarker, MarkerPin, MarkersMap } from '@/components/map'

import { loadServiceCenters } from '@/lib/queries'
import { ServiceCenter } from '@/lib/types'

export const revalidate = 3600

export const metadata: Metadata = {
  title: 'Ремонт швейных машин и оверлоков Family',
}

const servicePin: MarkerPin = { icon: '/i/shoplogos/marks/workshop.svg', color: '#E63946' }

const balloonIconProps = { size: 16, className: 'text-primary flex-shrink-0 me-2 mt-1' }

function ServiceBalloon({ service }: { service: ServiceCenter }) {
  return (
    <>
      <h6 className="fs-sm mb-2">{service.city.name}</h6>
      {service.address && (
        <div className="d-flex">
          <IconMapPin {...balloonIconProps} />
          <span>{service.address}</span>
        </div>
      )}
      {service.phone && (
        <div className="d-flex mt-1">
          <IconPhone {...balloonIconProps} />
          <span>{service.phone}</span>
        </div>
      )}
    </>
  )
}

export default async function ServicePage() {
  const services = await loadServiceCenters()

  const serviceGroups = groupByCountryAndCity(services)

  const markers: MapMarker[] = services
    .filter((service) => service.latitude && service.longitude)
    .map((service) => ({
      id: service.id,
      coordinates: [service.longitude!, service.latitude!],
      pin: servicePin,
      title: service.address,
      balloon: <ServiceBalloon service={service} />,
    }))

  return pageContentWrapper({
    title: 'Сервис и поддержка',
    description: 'Получить консультации по выбору и использованию швейной техники можно по телефону в Москве: <strong class="fw-bold">+7&nbsp;495&nbsp;744-00-87</strong> или в чате <strong class="fw-bold">WhatsApp:&nbsp;+7&nbsp;985&nbsp;766-56-75</strong>',
    children: (
      <>
        <section>
          <div className="container">
            <div className="iframe-full-height-wrap" style={{ height: 400 }}>
              <MarkersMap markers={markers} />
            </div>
          </div>
        </section>
        <section className="pb-5">
          {serviceGroups.map(({ country, cities }) => (
            <div className="container" key={country.id}>
              <h2 className="mt-4 mb-3 text-muted">{country.name}</h2>
              <div className="row">
                {cities.map(({ city, items }) => (
                  items.map((center) => (
                    <div className="col-xl-3 col-lg-4 col-sm-6" key={center.id}>
                      <div className="block-header">
                        <h6 className="text-uppercase mb-0">{city.name}</h6>
                      </div>
                      <div className="block-body bg-light pt-1 mb-2">
                        <p>
                          {center.address && <>{center.address}<br /></>}
                          {center.phone && <>{center.phone}<br /></>}
                        </p>
                      </div>
                    </div>
                  ))
                ))}
              </div>
            </div>
          ))}
        </section>
      </>
    )
  })
}
