import { Metadata } from 'next'

import { pageContentWrapper } from '@/components/layout/page-content-wrapper'
import { MapMarker, MarkersMap } from '@/components/map'

import { loadServiceCenters } from '@/lib/queries'
import { parsePhones } from '@/lib/format'
import { Country, ServiceCenter } from '@/lib/types'
import { navLinkClass } from '@/components/ui/nav'
import { IconMapPin, IconPhone } from '@tabler/icons-react'

export const revalidate = 3600

export const metadata: Metadata = {
  title: 'Сервисные центры',
}

type CountryGroup = {
  country: Country
  services: ServiceCenter[]
}

const balloonIcon = { size: 16, stroke: 1.5, className: 'me-2 inline-block align-top text-primary' }

function ServiceBalloon({ service }: { service: ServiceCenter }) {
  return (
    <>
      <h6 className="mb-2 text-sm leading-[1.2] font-medium">{service.city.name}</h6>
      <div>
        <IconMapPin {...balloonIcon} />
        <span className="inline-block align-top">{service.address}</span>
      </div>
      <div className="mt-1">
        <IconPhone {...balloonIcon} />
        <span className="inline-block align-top">{service.phone}</span>
      </div>
    </>
  )
}

// A line of a service center card, with its icon
const storeIcon = { size: 18, stroke: 1.5, className: 'my-1 text-primary' }

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
    title: <>Сервисное обслуживание и ремонт<span className="lg:hidden"> швейных машин, оверлоков, вышивальных и вязальных машин</span></>,
    children: (
      <div className="w-full">
        <section className="grid md:grid-cols-2">
          <div className="relative min-h-[26rem] overflow-hidden md:order-2 md:col-span-2 lg:col-span-1">
            <MarkersMap markers={markers} />
          </div>
          <div className="px-4 py-12 md:order-1 md:px-12">
            <div className="mx-auto max-w-[35rem] lg:py-12">
              <p className="mb-4 text-xl font-light">Наши сервисные центры предлагают следующие работы и услуги:</p>
              <ul className="list-disc ps-8 pb-4 text-muted marker:text-accent *:mb-[.4rem]">
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

        <section className="mb-12 w-full px-[.9375rem] pt-7.5 md:mt-6 xl:px-7.5">
          {countryGroups.map(({ country, services }) => (
            <div key={country.id}>
              <h2 className="mb-3 text-h3">{country.name}</h2>
              <div className="grid gap-x-7.5 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
                {services.map((service) => (
                  <div className="mb-7.5" key={service.id}>
                    <div className="relative flex min-w-0 flex-col rounded-lg bg-white shadow-sm">
                      <div className="p-5" itemScope itemType="http://schema.org/Organization">
                        <h6 className="mb-3 text-h6" itemProp="name">{service.city.name}</h6>
                        <ul>
                          <li className="flex">
                            <IconMapPin {...storeIcon} />
                            <div className="ps-4 text-sm" itemProp="address" itemScope itemType="http://schema.org/PostalAddress">
                              <span itemProp="streetAddress">{service.address}</span>
                              <span className="hidden" itemProp="addressLocality">{service.city.name}</span>
                              <span className="hidden" itemProp="addressCountry">{country.name}</span>
                            </div>
                          </li>
                          <li className="mt-2 flex border-t pt-2">
                            <IconPhone {...storeIcon} />
                            <div className="ps-4 text-sm">
                              {parsePhones([service.phone]).map(({ label, number, note, href }, index) => (
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
