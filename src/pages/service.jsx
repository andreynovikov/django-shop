import { useState, useEffect } from 'react';
import Script from 'next/script';
import { dehydrate, QueryClient, useQuery } from 'react-query';

import Layout from '@/components/layout';
import PageTitle from '@/components/layout/page-title';

import { serviceCenterKeys, loadServiceCenters } from '@/lib/queries';

export default function Service() {
    const [ymapsReady, setYMapsReady] = useState(false);
    const [serviceGroups, setServiceGroups] = useState([]);

    const { data: centers, isSuccess } = useQuery(serviceCenterKeys.lists(), () => loadServiceCenters());

    useEffect(() => {
        // Combine centers by country and city
        if (isSuccess) {
            const { groups } = centers.reduce(({ groups, country, city }, center) => {
                if (center.city.country.id !== country) {
                    groups.push({country: center.city.country, cities: []});
                    country = center.city.country.id;
                    city = null;
                }
                const curCountry = groups.length - 1;
                if (center.city.id !== city) {
                    groups[curCountry].cities.push({city: center.city, centers: []});
                    city = center.city.id;
                }
                groups[curCountry].cities[groups[curCountry].cities.length - 1].centers.push(center);
                return { groups, country, city };
            }, {groups: [], country: null, city: null});

            setServiceGroups(groups);
        }
    }, [isSuccess, centers]);

    useEffect(() => {
        if (!ymapsReady || serviceGroups.length === 0)
            return;

        //{% if city %}
        //var coords = [{{ city.latitude|unlocalize }}, {{ city.longitude|unlocalize }}];
        //$("#search_form option[id='city_option_{{ city.id }}']").attr("selected", "selected");
        //{% else %}
        const coords = [55.76, 37.64];
        //{% endif %}
        const myMap = new ymaps.Map('map', {
            center: coords,
            zoom: 10,
            controls: ['zoomControl', 'typeSelector',  'fullscreenControl', 'geolocationControl', 'rulerControl']
        });

        // Создадим выпадающий список
        const listBoxItems = serviceGroups.reduce((items, country) => {
            for (const cityGroup of country.cities) {
                if (!!!cityGroup.city.latitude || !!!cityGroup.city.longitude)
                    continue;
                const item = new ymaps.control.ListBoxItem({
                    data: {
                        content: cityGroup.city.name,
                        center: [cityGroup.city.latitude, cityGroup.city.longitude],
                        zoom: 9
                    }
                });
                items.push(item);
            }
            return items;
        }, []);

        const listBox = new ymaps.control.ListBox({
            items: listBoxItems,
            data: {
                content: 'Выберите город'
            },
			options: {
            }
        });

        listBox.events.add('click', (e) => {
            // Получаем ссылку на объект, по которому кликнули.
            // События элементов списка пропагируются
            // и их можно слушать на родительском элементе.
            var item = e.get('target');
            // Клик на заголовке выпадающего списка обрабатывать не надо.
            if (item != listBox) {
                myMap.setCenter(
                    item.data.get('center'),
                    item.data.get('zoom')
                );
                window.setTimeout(() => { // ждём пока ymaps включит элемент списка
                    listBox.collapse();
                }, 300);
            }
        });

        listBox.events.add('collapse', () => {
            for (const item of listBoxItems)
                item.deselect();
        });

        myMap.controls.add(listBox, {float: 'left'});

        //{% if not city %}
        var location = ymaps.geolocation;
        location.get({
            provider: 'yandex'
        }).then(function(result) {
            var userCoodinates = result.geoObjects.get(0).geometry.getCoordinates();
            myMap.setCenter(userCoodinates);
        }, function(err) {
            console.log('Ошибка: ' + err)
        });
        //{% endif %}

        for (const center of centers) {
            if (center.latitude && center.longitude) {
                const content = [];
                if (center.address)
                    content.push(center.address);
                if (center.phone)
                    content.push(center.phone);
                const placemark = new ymaps.Placemark([center.latitude, center.longitude], {
                    balloonContent: content.join("<br/>"),
                    balloonContentFooter: ''
                },{preset: 'islands#redDotIcon'});
                myMap.geoObjects.add(placemark);
            }
        }
        return () => myMap.destroy();
    }, [ymapsReady, serviceGroups]); //eslint-disable-line react-hooks/exhaustive-deps

    const setupYMaps = () => {
        ymaps.ready(function() {
            setYMapsReady(true);
        });
    };

    return (
        <>
            <PageTitle title="Сервис и поддержка" description="Получить консультации по выбору и использованию швейной техники можно по телефону в Москве: <strong class=&#34;fw-bold&#34;>+7&nbsp;495&nbsp;744-00-87</strong> или в чате <strong class=&#34;fw-bold&#34;>WhatsApp:&nbsp;+7&nbsp;985&nbsp;766-56-75</strong>" />
            <section>
                <div className="container">
                    <div id="map" style={{width: "100%", height: "400px"}} />
                </div>
            </section>
            <main className="pb-5">
                { serviceGroups.length > 0 && serviceGroups.map(({ country, cities }) => (
                    <div className="container" key={country.id}>
                        <h2 className="mt-4 mb-3 text-muted">{ country.name }</h2>
                        <div className="row">
                            { cities.map(({ city, centers }) => (
                                centers.map((center) => (
                                    <div className="col-xl-3 col-lg-4 col-sm-6" key={center.id}>
                                        <div className="block-header">
                                            <h6 className="text-uppercase mb-0">{ city.name }</h6>
                                        </div>
                                        <div className="block-body bg-light pt-1 mb-2">
                                            <p>
                                                { center.address && <>{ center.address }<br /></> }
                                                { center.phone && <>{ center.phone }<br /></> }
                                            </p>
                                        </div>
                                    </div>
                                ))
                            ))}
                        </div>
                    </div>
                ))}
            </main>
            <Script
                id="ymaps"
                src="https://api-maps.yandex.ru/2.1/?apikey=d3198a9f-0921-4cce-8c77-83e21dd524ac&lang=ru_RU"
                onReady={setupYMaps}
                onLoad={setupYMaps} />
        </>
    )
}

Service.getLayout = function getLayout(page) {
    return (
        <Layout title="Ремонт швейных машин и оверлоков Family">
            {page}
        </Layout>
    )
}

export async function getStaticProps() {
    const queryClient = new QueryClient();
    await queryClient.fetchQuery(serviceCenterKeys.lists(), () => loadServiceCenters());

    return {
        props: {
            dehydratedState: dehydrate(queryClient)
        }
    };
}
