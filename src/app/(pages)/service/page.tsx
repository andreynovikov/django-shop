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

const balloonIconProps = { size: 16, className: 'me-2 mt-0.5 shrink-0 text-primary' }

function ServiceBalloon({ service }: { service: ServiceCenter }) {
  return (
    <>
      <h6 className="mb-2 text-sm leading-[1.1] font-bold">{service.city.name}</h6>
      {service.address && (
        <div className="flex">
          <IconMapPin {...balloonIconProps} />
          <span>{service.address}</span>
        </div>
      )}
      {service.phone && (
        <div className="mt-1 flex">
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
    description: 'Получить консультации по выбору и использованию швейной техники можно по телефону в Москве: <strong class="font-bold">+7&nbsp;495&nbsp;744-00-87</strong> или в чате <strong class="font-bold">WhatsApp:&nbsp;+7&nbsp;985&nbsp;766-56-75</strong>',
    children: (
      <>
        <section className="container">
          <div className="relative min-h-72 overflow-hidden" style={{ height: 400 }}>
            <MarkersMap markers={markers} />
          </div>
        </section>
        <section className="container pb-12">
          {serviceGroups.map(({ country, cities }) => (
            <div key={country.id}>
              <h2 className="mt-6 mb-4 text-3xl leading-[1.1] font-bold text-muted lg:text-[2.7rem]">{country.name}</h2>
              <div className="grid gap-x-6 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
                {cities.map(({ city, items }) => (
                  items.map((center) => (
                    <div key={center.id}>
                      <div className="bg-gray-100 px-6 py-5">
                        <h6 className="leading-[1.1] font-bold tracking-widest uppercase">{city.name}</h6>
                      </div>
                      <div className="mb-2 bg-gray-100 px-6 pt-1 pb-5">
                        <p className="mb-4">
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
