import { Fragment, useState, useEffect, useMemo } from 'react';
import { dehydrate, QueryClient, useQuery } from '@tanstack/react-query';

import Link from 'next/link';
import Script from 'next/script';

import PageLayout from '@/components/layout/page';

import { serviceCenterKeys, loadServiceCenters } from '@/lib/queries';

export default function Service() {
    const [ymapsReady, setYMapsReady] = useState(false);

    const { data: services, isSuccess } = useQuery({
        queryKey: serviceCenterKeys.lists(),
        queryFn: () => loadServiceCenters()
    });

    useEffect(() => {
        if (!ymapsReady || !isSuccess)
            return;

        const coords = [55.76, 37.64];
        const map = new ymaps.Map('map', {
            center: coords,
            zoom: 10,
            controls: ['zoomControl', 'fullscreenControl', 'geolocationControl', 'rulerControl']
        });
        map.margin.setDefaultMargin(100);

        const location = ymaps.geolocation;
        location.get({
            provider: 'yandex'
        }).then((result) => {
            const userCoodinates = result.geoObjects.get(0).geometry.getCoordinates();
            myMap.setCenter(userCoodinates);
        });

        services.filter((service) => service.latitude && service.longitude).map((service) => {
            map.geoObjects.add(new ymaps.Placemark([service.latitude, service.longitude], {
                balloonContentHeader: '',
                balloonContent:
                    `<div><i class="ci-location text-primary d-inline-block me-2"></i>
                    <span class="d-inline-block align-top">${service.address}</span></div>
                    <div class="mt-1"><i class="ci-phone text-primary d-inline-block me-2"></i>
                    <span class="d-inline-block align-top">${service.phone}</span></div>`,
                balloonContentFooter: ''
            },
            {
                iconLayout: 'default#image',
                iconImageHref: '/i/shoplogos/workshop.png',
                iconImageSize: [27, 26], iconImageOffset: [-10, -23]
            }));
        });

        return () => map.destroy();
    }, [ymapsReady, isSuccess]); //eslint-disable-line react-hooks/exhaustive-deps

    const serviceGroups = useMemo(() => {
        if (!isSuccess)
            return [];

        const { groups } = services.reduce(({ groups, country, city }, service) => {
            if (service.city.country.id !== country) {
                groups.push({country: service.city.country, cities: []});
                country = service.city.country.id;
                city = null;
            }
            const curCountry = groups.length - 1;
            if (service.city.id !== city) {
                groups[curCountry].cities.push({city: service.city, services: []});
                city = service.city.id;
            }
            groups[curCountry].cities[groups[curCountry].cities.length - 1].services.push(service);
            return { groups, country, city };
        }, {groups: [], country: null, city: null});

        return groups;
    }, [services, isSuccess]);

    const setupYMaps = () => {
        ymaps.ready(function() {
            setYMapsReady(true);
        });
    };

    return (
        <>
            <main className="container-fluid px-0">
                <section className="row g-0">
                    <div
                        className="col-md-6 bg-position-center bg-size-cover bg-secondary order-md-2"
                        style={{minHeight: '15rem', backgroundImage: 'url(https://cartzilla.createx.studio/img/about/02.jpg)'}} />
                    <div className="col-md-6 px-3 px-md-5 py-5 order-md-1">
                        <div className="mx-auto py-lg-5" style={{maxWidth: '35rem'}}>
                            <p className="lead">Наши сервисные центры предлагают следующие работы и услуги:</p>
                            <ul className="list-style pb-3 text-muted">
                                <li>
                                    Гарантийный ремонт и обслуживание швейных машин, вышивальных машин, оверлоков,
                                    вязальных машин и другого оборудования производства компаний
                                    Pfaff, Husqvarna Viking, Family, Janome, Silver Reed и ряда других фирм.
                                </li>
                                <li>Поставку запасных частей для швейного оборудования.</li>
                                <li>Послегарантийный ремонт машин Pfaff, Husqvarna, Family, Janome, Silver Reed и NewHome.</li>
                            </ul>
                        </div>
                    </div>
                </section>
                <section className="row g-0">
                    <div className="col-lg-6 iframe-full-height-wrap" style={{minHeight: '26rem'}}>
                        <div className="iframe-full-height" id="map"></div>
                    </div>
                    <div className="col-md-6 px-3 px-md-5 py-5">
                        <div className="mx-auto py-lg-5" style={{maxWidth: '35rem'}}>
                            <h2 className="h3 pb-3">Новости</h2>
                            <ul className="list-style pb-3">
                                <li>Сервисный центр на &laquo;Академической&raquo; переехал с ул. Кедрова по адресу ул. Дмитрия Ульянова д.31<br/>Телефон: +7 495 718-86-02</li>
                                <li><Link className="nav-link-style" href="/blog/O/">Наши механики прошли обучение в Швеции</Link></li>
                                <li>Теперь в наших сервисных центрах можно купить педали для швейных машин</li>
                            </ul>
                        </div>
                    </div>
                </section>
                <hr />

                <section className="container-fluid pt-grid-gutter mt-md-4 mb-5">
                    { serviceGroups.length > 0 && serviceGroups.map(({ country, cities }) => (
                        <Fragment key={country.id}>
                            <h2 className="h3 mb-3">{ country.name }</h2>
                            <div className="row">
                                { cities.map(({ city, services }) => (
                                    <Fragment key={city.id}>
                                        { services.map((service) => (
                                            <div className="col-xl-3 col-lg-4 col-sm-6 mb-grid-gutter" key={service.id}>
                                                <div className="card border-0 shadow-sm">
                                                    <div className="card-body" itemScope itemType="http://schema.org/Organization">
                                                        <h6 className="card-title" itemProp="name">{ city.name }</h6>
                                                        <ul className="list-unstyled mb-0">
                                                            <li className="d-flex">
                                                                <i className="ci-location fs-lg my-1 text-primary" />
                                                                <div className="ps-3 fs-sm" itemProp="address" itemScope itemType="http://schema.org/PostalAddress">
                                                                    <span itemProp="streetAddress">{ service.address }</span>
                                                                    <span className="d-none" itemProp="addressLocality">{ city.name }</span>
                                                                    <span className="d-none" itemProp="addressCountry">{ country.name }</span>
                                                                </div>
                                                            </li>
                                                            <li className="d-flex pt-2 mt-2 mb-0 border-top">
                                                                <i className="ci-phone fs-lg my-1 text-primary" />
                                                                <div className="ps-3 fs-sm">
                                                                    {service.phone.split(',').map((phone, index) => (
                                                                        <a
                                                                            className={'d-block nav-link-style' + (index > 0 ? ' mt-2' : '')}
                                                                            href={'tel:' + phone.trim().replace(' ', '')}
                                                                            itemProp="telephone"
                                                                            key={index}>
                                                                            { phone.trim() }
                                                                        </a>
                                                                    ))}
                                                                </div>
                                                            </li>
                                                        </ul>
                                                    </div>
                                                </div>
                                            </div>
                                        ))}
                                    </Fragment>
                                ))}
                            </div>
                        </Fragment>
                    ))}
            </section>
            </main>
            <Script
                id="ymaps"
                src={"https://api-maps.yandex.ru/2.1/?lang=ru_RU&apikey=" + process.env.NEXT_PUBLIC_YMAPS_API_KEY}
                onReady={setupYMaps}
                onLoad={setupYMaps} />
        </>
    )
}

Service.getLayout = function getLayout(page) {
    return (
        <PageLayout htmlTitle="Сервисные центры" title={<>Сервисное обслуживание и ремонт<span className="d-lg-none"> швейных машин, оверлоков, вышивальных и вязальных машин</span></>}>
            {page}
        </PageLayout>
    )
}

export async function getStaticProps() {
    const queryClient = new QueryClient();
    await queryClient.prefetchQuery({
        queryKey: serviceCenterKeys.lists(),
        queryFn: () => loadServiceCenters()
    });

    return {
        props: {
            dehydratedState: dehydrate(queryClient)
        }
    };
}
