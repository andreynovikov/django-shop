import { useState, useEffect } from 'react';
import Script from 'next/script';
import { dehydrate, QueryClient, useQuery } from 'react-query';

import Layout from '@/components/layout';
import PageTitle from '@/components/layout/page-title';

import { storeKeys, loadStores } from '@/lib/queries';

// https://masonry.desandro.com/layout.html

export default function Stores() {
    const [ymapsReady, setYMapsReady] = useState(false);
    const [storeGroups, setStoreGroups] = useState([]);

    const { data: stores, isSuccess } = useQuery(storeKeys.lists(), () => loadStores());

    useEffect(() => {
        // Combine stores by country and city
        if (isSuccess) {
            const { groups } = stores.reduce(({ groups, country, city }, store) => {
                if (store.city.country.id !== country) {
                    groups.push({country: store.city.country, cities: []});
                    country = store.city.country.id;
                    city = null;
                }
                const curCountry = groups.length - 1;
                if (store.city.id !== city) {
                    groups[curCountry].cities.push({city: store.city, stores: []});
                    city = store.city.id;
                }
                groups[curCountry].cities[groups[curCountry].cities.length - 1].stores.push(store);
                return { groups, country, city };
            }, {groups: [], country: null, city: null});

            setStoreGroups(groups);
        }
    }, [isSuccess, stores]);

    useEffect(() => {
        if (!ymapsReady || storeGroups.length === 0)
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
        const listBoxItems = storeGroups.reduce((items, country) => {
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

        listBox.events.add('click', function (e) {
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

        listBox.events.add('collapse', function (e) {
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

        for (const store of stores) {
            if (store.publish && store.latitude && store.longitude) {
                const content = [];
                if (store.address)
                    content.push(store.address);
                if (store.address2)
                    content.push(store.address2);
                if (store.hours)
                    content.push(store.hours);
                if (store.phone)
                    content.push(store.phone);
                if (store.phone2)
                    content.push(store.phone2);
                if (store.url)
                    content.push(`<a href="${store.url}">${store.url}</a>`);
                const placemark = new ymaps.Placemark([store.latitude, store.longitude], {
                    balloonContentHeader: store.name,
                    balloonContent: content.join("<br/>"),
                    balloonContentFooter: ''
                },{preset: 'islands#redDotIcon'});
                myMap.geoObjects.add(placemark);
            }
        }
        return () => myMap.destroy();
    }, [ymapsReady, storeGroups]); //eslint-disable-line react-hooks/exhaustive-deps

    const setupYMaps = () => {
        ymaps.ready(function() {
            setYMapsReady(true);
        });
    };

    return (
        <>
            <PageTitle title="Где купить машины Family" description="Эксклюзивное право представления и распространения продукции бренда “Family” в России и странах СНГ принадлежит компании “Торговый Дом Швейных Машин”. Со списком проверенных официальных дилеров вы можете ознакомиться ниже:" />
            <section>
                <div className="container">
                    <div id="map" style={{width: "100%", height: "400px"}} />
                </div>
            </section>
            <main className="pb-5">
                { storeGroups.length > 0 && storeGroups.map(({ country, cities }) => (
                    <div className="container" key={country.id}>
                        <h2 className="mt-4 mb-3 text-muted">{ country.name }</h2>
                        <div className="row">
                            { cities.map(({ city, stores }) => (
                                stores.map((store) => (
                                    <div className="col-xl-3 col-lg-4 col-sm-6" key={store.id}>
                                        <div className="block-header">
                                            <h6 className="text-uppercase mb-0">{ city.name }</h6>
                                        </div>
                                        <div className="block-body bg-light pt-1 mb-2">
                                            <p>
                                                <strong>{ store.name }</strong><br />
                                                { store.address && <>{ store.address }<br /></> }
                                                { store.address2 && <>{ store.address2 }<br /></> }
                                                { store.phone && <>{ store.phone }<br /></> }
                                                { store.url && <a href={ store.url }>{ store.url }</a> }
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

Stores.getLayout = function getLayout(page) {
    return (
        <Layout title="Где купить">
            {page}
        </Layout>
    )
}

export async function getStaticProps() {
    const queryClient = new QueryClient();
    await queryClient.fetchQuery(storeKeys.lists(), () => loadStores());

    return {
        props: {
            dehydratedState: dehydrate(queryClient)
        }
    };
}
