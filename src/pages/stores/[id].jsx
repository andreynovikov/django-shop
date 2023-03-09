import { useState, useEffect } from 'react';
import Script from 'next/script';
import { dehydrate, QueryClient, useQuery } from 'react-query';

import PageLayout from '@/components/layout/page';

import { storeKeys, loadStores, loadStore } from '@/lib/queries';

export default function Store({ id }) {
    const [ymapsReady, setYMapsReady] = useState(false);

    const { data: store, isSuccess } = useQuery(storeKeys.detail(id), () => loadStore(id));

    useEffect(() => {
        if (!ymapsReady || !isSuccess)
            return;

        const coords = [store.latitude, store.longitude];
        const myMap = new ymaps.Map('map-container', {
            center: coords,
            zoom: 14,
            controls: ['zoomControl', 'fullscreenControl', 'geolocationControl', 'rulerControl']
        });
        const myPlacemark = new ymaps.Placemark(coords, {}, {preset: 'islands#blueStarCircleIcon'});
        myMap.geoObjects.add(myPlacemark);

        return () => myMap.destroy();
    }, [ymapsReady, isSuccess]); //eslint-disable-line react-hooks/exhaustive-deps

    const setupYMaps = () => {
        ymaps.ready(function() {
            setYMapsReady(true);
        });
    };

    const cols = store.url ? 3 : 4;

    if (!isSuccess)
        return null;

    return (
        <>
            <section class="container py-3 py-lg-5">
                <p class="lead">Продажа швейных машин, оверлоков, вязальных машин и аксессуаров для рукоделия в г. { store.city.name }</p>
            </section>
            <section class="container-fluid">
                <div class="row">
                    <div class={`col-xl-${cols} col-md-6 mb-grid-gutter`}>
                        <a class="card" href="#map" data-scroll>
                            <div class="card-body text-center">
                                <i class="ci-location h3 mt-2 mb-4 text-primary" />
                                <h3 class="h6 mb-3">Адрес</h3>
                                <ul class="list-unstyled fs-sm text-muted mb-0">
                                    <li>{ store.address }</li>
                                    { store.address2 && <li>{ store.address2 }</li> }
                                </ul>
                                { store.latitude && store.longitude && (
                                    <div class="fs-sm text-primary">
                                        Посмотреть на карте
                                        <i class="ci-arrow-right fs-xs ms-1" />
                                    </div>
                                )}
                            </div>
                        </a>
                    </div>
                    { store.hours && (
                        <div class={`col-xl-${cols} col-md-6 mb-grid-gutter`}>
                            <div class="card">
                                <div class="card-body text-center">
                                    <i class="ci-time h3 mt-2 mb-4 text-primary" />
                                    <h3 class="h6 mb-3">Часы работы</h3>
                                    <ul class="list-unstyled fs-sm text-muted mb-0">
                                        {store.hours.split(',').map((hours, index) => (
                                            <li className={index === store.hours.length - 1 ? 'mb-0' : ''} key={index}>
                                                {hours.trim()}
                                            </li>
                                        ))}
                                    </ul>
                                </div>
                            </div>
                        </div>
                    )}
                    <div class={`col-xl-${cols} col-md-6 mb-grid-gutter`}>
                        <div class="card">
                            <div class="card-body text-center">
                                <i class="ci-phone h3 mt-2 mb-4 text-primary" />
                                <h3 class="h6 mb-3">Телефон{ store.phones.length > 1 && 'ы'}</h3>
                                <ul class="list-unstyled fs-sm mb-0">
                                    {store.phones.map((phone, index) => (
                                        <li className={index === store.phones.length - 1 ? 'mb-0' : ''} key={index}>
                                            <a class="nav-link-style" href={'tel:' + phone.replace(/[ -]/g, '')}>{ phone }</a>
                                        </li>
                                    ))}
                                </ul>
                            </div>
                        </div>
                    </div>
                    { store.url && (
                        <div class={`col-xl-${cols} col-md-6 mb-grid-gutter`}>
                            <div class="card">
                                <div class="card-body text-center">
                                    <i class="ci-dribbble h3 mt-2 mb-4 text-primary" />
                                    <h3 class="h6 mb-3">Сайт магазина</h3>
                                    <ul class="list-unstyled fs-sm mb-0">
                                        <li class="mb-0">
                                            <a class="nav-link-style" href="{ store.url }">{ store.url }</a>
                                        </li>
                                    </ul>
                                </div>
                            </div>
                        </div>
                    )}
                </div>
            </section>
            { store.description && (
                <section class="container py-3 py-lg-5 mt-4 mb-3">
                    <div dangerouslySetInnerHTML={{__html: store.description }}></div>
                </section>
            )}
            { store.latitude && store.longitude && (
                <div class="container-fluid px-0 pt-3 pt-lg-5" id="map">
                    <div class="row g-0">
                        <div class="col-lg-12 iframe-full-height-wrap" style={{ minHeight: '28rem' }}>
                            <div class="iframe-full-height" id="map-container"></div>
                        </div>
                    </div>
                </div>
            )}
            <Script
                id="ymaps"
                src={"https://api-maps.yandex.ru/2.1/?lang=ru_RU&apikey=" + process.env.NEXT_PUBLIC_YMAPS_API_KEY}
                onReady={setupYMaps}
                onLoad={setupYMaps} />
        </>
    )
}

Store.getLayout = function getLayout(page) {
    return (
        <PageLayout title={page.props.title}>
            {page}
        </PageLayout>
    )
}

export async function getStaticProps(context) {
    const id = context.params?.id;
    const queryClient = new QueryClient();
    const store = await queryClient.fetchQuery(storeKeys.detail(id), () => loadStore(id));

    return {
        props: {
            dehydratedState: dehydrate(queryClient),
            title: store.name + ' - ' + store.city.name,
            id
        }
    };
}

export async function getStaticPaths() {
    const stores = await loadStores();
    const paths = stores.filter(store => store.logo === 'sewingworld').map((store) => ({
        params: { id: store.id.toString() },
    }));
    return { paths, fallback: false }
}
