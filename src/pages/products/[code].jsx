import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/router';
import Link from 'next/link';
import { dehydrate, QueryClient, useQuery } from 'react-query';

import PageLayout from '@/components/layout/page';
import FieldHelp from '@/components/product/field-help';
import ProductMiniCard from '@/components/product/mini-card';
import ProductPrice from '@/components/product/price';

import useBasket from '@/lib/basket';
import useFavorites from '@/lib/favorites';
import useComparison from '@/lib/comparison';
import { useSession } from '@/lib/session';
import { productKeys, loadProductByCode, getProductFields } from '@/lib/queries';

const fieldList = ['fabric_verylite', 'km_class', 'km_font', 'km_needles', 'km_prog', 'km_rapport',
                   'sw_hoopsize', 'sw_datalink', 'sm_software', 'sm_shuttletype', 'sm_stitchwidth',
                   'sm_stitchlenght', 'sm_maxi', 'sm_stitchquantity', 'sm_buttonhole', 'sm_alphabet',
                   'sm_dualtransporter', 'sm_platformlenght', 'sm_freearm', 'sm_feedwidth',
                   'sm_footheight', 'sm_constant', 'sm_speedcontrol', 'sm_needleupdown', 'sm_threader',
                   'sm_autocutter', 'sm_spool', 'sm_presscontrol', 'sm_power', 'sm_light', 'sm_organizer',
                   'sm_autostop', 'sm_ruler', 'sm_wastebin', 'sm_cover', 'sm_display', 'sm_advisor',
                   'sm_memory', 'sm_mirror', 'sm_startstop', 'sm_kneelift', 'sm_diffeed',
                   'sm_easythreading', 'ov_freearm', 'sm_needles', 'prom_transporter_type',
                   'prom_shuttle_type', 'prom_speed', 'prom_needle_type', 'prom_stitch_lenght',
                   'prom_foot_lift', 'prom_fabric_type', 'prom_oil_type', 'weight', 'prom_weight',
                   'prom_cutting', 'prom_threads_num', 'prom_power', 'prom_bhlenght',
                   'prom_overstitch_lenght', 'prom_overstitch_width', 'prom_stitch_width',
                   'prom_needle_width', 'prom_needle_num', 'prom_platform_type', 'prom_button_diaouter',
                   'prom_button_diainner', 'prom_needle_height', 'prom_stitch_type', 'prom_autothread'];

const noImageStyle = {
    width: '300px',
    fontSize: '300px'
};

const gallerySettings = {
    download: false,
    videojs: false, // may be add this in future
    youtubePlayerParams: {
        modestbranding: 1,
        showinfo: 0,
        rel: 0
    },
    vimeoPlayerParams: {
        byline: 0,
        portrait: 0,
        color: 'fe696a'
    }
};

const sliderSettings = {
    mouseDrag: true,
    items: 2,
    controls: true,
    nav: false,
    // autoHeight: true,
    controlsText: ['<i class="ci-arrow-left"></i>', '<i class="ci-arrow-right"></i>'],
    // navPosition: 'bottom',
    speed: 500,
    autoplayHoverPause: true,
    autoplayButtonOutput: false,
    responsive: {
        0: {
            items: 1
        },
        500: {
            items: 2,
            gutter: 18
        },
        768: {
            items: 3,
            gutter: 20
        },
        1100: {
            items: 4,
            gutter: 30
        }
    }
};

function prettify(value) {
    if (typeof value === 'string')
        return value.trim();
    return value;
}

function rebootstrap(value) {
    if (typeof value !== 'string')
        return value;
    value = value.replaceAll('col-md-8', 'col-md-4');
    value = value.replaceAll('col-md-10', 'col-md-5');
    value = value.replaceAll('col-md-12', 'col-md-6');
    value = value.replaceAll('<h3>', '<h5>');
    value = value.replaceAll('</h3>', '</h5>');
    value = value.replaceAll('<h4>', '<h6>');
    value = value.replaceAll('</h4>', '</h6>');
    return value;
}

export default function Product({code}) {
    const [productFields, setProductFields] = useState([]);
    const [fieldNames, setFieldNames] = useState({});

    const router = useRouter();

    const { status } = useSession();
    const { addItem } = useBasket();
    const { favorites, favoritize, unfavoritize } = useFavorites();
    const { comparisons, compare, uncompare } = useComparison();

    const { data: fields } = useQuery(productKeys.fields(), () => getProductFields());

    const { data: product, isSuccess, isLoading } = useQuery(productKeys.detail(code), () => loadProductByCode(code), {
        enabled: code !== undefined
    });

    useEffect(() => {
        if (isSuccess)
            setProductFields(fieldList.filter(field => field in product && product[field]));
    }, [product, isSuccess]);

    useEffect(() => {
        if (fields !== undefined) {
            const names = {};
            Object.keys(fields).forEach((key) => {
                const name = fields[key].split(',');
                if (name.length === 1)
                    name.push('');
                names[key] = name;
            });
            setFieldNames(names);
        }
    }, [fields]);

    useEffect(() => {
        if (isSuccess && (product.accessories || product.similar)) {
            import('tiny-slider').then((module) => {
                const tns = module.tns;
                const carousels = [].slice.call(document.querySelectorAll('.tns-carousel .tns-carousel-inner'));
                carousels.map((carouselEl) => {
                    const carousel = tns({container: carouselEl, ...sliderSettings});
                });
            });
        }
    }, [product, isSuccess]);

    useEffect(() => {
        if (isSuccess && product.image) {
            (async () => {
                await import('@/vendor/lightgallery/js/lightgallery.js');
                await import('@/vendor/lightgallery/js/lg-zoom.js');
                await import('@/vendor/lightgallery/js/lg-fullscreen.js');
                const galleries = [].slice.call(document.querySelectorAll('.gallery'));
                galleries.map((galleryEl) => {
                    const gallery = lightGallery(galleryEl, {selector: '.gallery-item', ...gallerySettings});
                });
            })();
        }
    }, [product, isSuccess]);

    const handleCartClick = () => {
        if (product.variations) {
        } else {
            addItem(product.id);
        }
    };

    const handleFavoritesClick = (e) => {
        if (status === 'authenticated') {
            if (favorites.includes(product.id))
                unfavoritize(product.id);
            else
                favoritize(product.id);
        } // TODO: else show dialog or tooltip
    }

    const handleComparisonClick = (e) => {
        if (comparisons.includes(product.id))
            router.push({
                pathname: '/compare',
                query: { kind: product.kind[0] }
            });
        else
            compare(product.id);
    }

    if (isLoading || !isSuccess)
        return (
            <div>Loading...</div>
        )

    return (
        <>
        <div className="container">
            <div className="bg-light shadow-lg rounded-3 px-4 py-3 mb-5">
                <div className="px-lg-3">
                    <div className="row">
                        <div className="col-lg-7 pe-lg-0">
                            { product.image ? (
                                <div className="d-block gallery">
                                    <a href={product.big_image || product.image} className="gallery-item" data-sub-html={`${product.title} ${product.whatis}`}>
                                        <img
                                            src={product.image}
                                            alt={`${product.title} ${product.whatis}`}
                                            itemProp="image" />
                                    </a>
                                    { product.images && (
                                        <div className="d-flex flex-wrap my-2">
                                            { product.images.map((image, index) => (
                                                <a href={image.url} className="gallery-item rounded border me-4 mb-4" data-sub-html={`${product.title} ${product.whatis}`} key={index}>
                                                    <img
                                                        src={image.thumbnail.url}
                                                        width={image.thumbnail.width}
                                                        height={image.thumbnail.height}
                                                        alt={`${product.title} - фото №${index + 2}`} />
                                                </a>
                                            ))}
                                        </div>
                                    )}
                                </div>
                            ) : (
                                <div className="d-none d-lg-block">
                                    <i className="d-block ci-camera text-muted mx-auto" style={ noImageStyle } />
                                </div>
                            )}

                        </div>
                        <div className="col-lg-5 pt-4 pt-lg-0">
                            <div className="product-details ms-auto pb-3">
                                { product.enabled && product.cost > 0 && (
                                    <div className="d-flex flex-row align-items-baseline mb-3">
                                        <div className="h3 fw-normal text-accent">
                                            <ProductPrice product={product} delFs="lg" itemProp="price" />
                                            <span itemProp="priceCurrency" className="d-none">RUB</span>
                                        </div>
                                        <div className="ms-3">
                                            { /*
                                            { product.discount > 0 && (
                                                <span
                                                    className="badge bg-primary badge-shadow align-middle mt-n2"
                                                    data-bs-toggle="tooltip"
                                                    data-bs-placement="right"
                                                    data-bs-html="true"
                                                    title="Базовая цена в магазинах &laquo;Швейный Мир&raquo; без учета скидок <b>{{ product.price|quantize:"1" }}</b>&nbsp;руб. Скидка при покупке в интернет-магазине составляет <b>{{ product.discount|quantize:"1" }}</b>&nbsp;руб.">
                                                    Скидка
                                                </span>
                                            )}
                                              */
                                            }
                                            { product.ishot && (
                                                <span className="badge bg-accent badge-shadow align-middle mt-n2">Акция</span>
                                            )}
                                            { product.isnew && (
                                                <span className="badge bg-info badge-shadow align-middle mt-n2">Новинка</span>
                                            )}
                                            { product.recomended && (
                                                <span className="badge bg-warning badge-shadow align-middle mt-n2">Рекомендуем</span>
                                            )}
                                        </div>
                                    </div>
                                )}

                                { (product.runame || product.whatis) && (
                                    <div className="fs-sm mb-4">
                                        <span className="text-muted fw-medium me-1">
                                            { product.whatis } { product.runame }
                                        </span>
                                    </div>
                                )}
                                <div className="position-relative me-n4">
                                    <div className={`product-badge product-${ product.instock < 1 ? "not-" : ""}available mt-1`}>
                                        <i className={`ci-security-${ product.instock > 1 ? "check" : product.instock === 1 ? "announcement" : "close"}`} />
                                        { product.enabled ? (
                                            product.instock > 1 ? "В наличии" : product.instock === 1 ? "Осталось мало" : "Закончились"
                                        ) : (
                                            "Товар снят с продажи"
                                        )}
                                    </div>
                                </div>
                                { product.enabled && (
                                    <>
                                        <div className="me-2">
                                            <div className="me-5 pb-4 pe-5 fs-sm">
                                                { product.sales && (
                                                    product.sales.map((action) => (
                                                        action.brief && (
                                                            <div className="mb-2" key={action.id}>
                                                                <i className="ci-gift text-danger pe-2" />
                                                                render_as_template { action.brief }
                                                            </div>
                                                        )
                                                    ))
                                                )}
                                                { product.state && (
                                                    <div className="mb-2">
                                                        <i className="ci-message text-danger pe-2" />
                                                        { product.state }
                                                    </div>
                                                )}
                                                { product.sales_notes && (
                                                    <div className="mb-2">
                                                        <i className="ci-announcement text-danger pe-2" />
                                                        { product.sales_notes }
                                                    </div>
                                                )}
                                                { product.utilisation && (
                                                    <div className="mb-2">
                                                        { /* TODO: refactor - move to actions */ }
                                                        <i className="ci-gift text-danger pe-2" />
                                                        Участник акции <a href="/actions/utilisation/">&laquo;Утилизация&raquo;</a>!
                                                        Скидка по акции <span className="price">{ product.maxdiscount }%</span>!
                                                    </div>
                                                )}
                                            </div>
                                        </div>
                                        { product.cost > 0 ? (
                                            <div className="d-flex align-items-center pt-2 pb-4" itemProp="offers" itemScope itemType="http://schema.org/Offer">
                                                { product.instock > 5 && (
                                                    <select className="form-select me-3 quantity-input" style={{width: "5rem"}}>
                                                        <option value="1">1</option>
                                                        <option value="2">2</option>
                                                        <option value="3">3</option>
                                                        <option value="4">4</option>
                                                        <option value="5">5</option>
                                                    </select>
                                                )}
                                                { product.instock > 0 ? (
                                                    <a className="btn btn-primary btn-shadow d-block w-100 add-to-cart" href="{% url 'shop:add' product.id %}{% if utm_source %}?utm_source={{ utm_source }}{% endif %}">
                                                        <span className="d-none spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span>
                                                        <i className="ci-cart fs-lg me-2" />Купить
                                                    </a>
                                                ) : (
                                                    <a className="btn btn-primary btn-shadow d-block w-100 add-to-cart" href="{% url 'shop:add' product.id %}{% if utm_source %}?utm_source={{ utm_source }}{% endif %}">
                                                        <span className="d-none spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span>
                                                        <i className="ci-loudspeaker fs-lg me-2" />Сообщить о поступлении
                                                    </a>
                                                )}
                                            </div>
                                        ) : (
                                            <div className="py-5"></div>
                                        )}
                                    </>
                                )}
                                { (product.enabled || product.kind) && (
                                    <div className="d-flex mb-4">
                                        { product.enabled && (
                                            <button
                                                type="button"
                                                onClick={handleFavoritesClick}
                                                className={"btn btn-" + (favorites.includes(product.id) ? "accent" : "secondary") + " d-block w-100"}>
                                                <i className="ci-heart fs-lg me-2" />
                                                <span>
                                                    { favorites.includes(product.id) ? "В избранном" : "Отложить" }
                                                </span>
                                            </button>
                                        )}
                                        { product.kind && (
                                            <button
                                                type="button"
                                                onClick={handleComparisonClick}
                                                className={"btn btn-" + (comparisons.includes(product.id) ? "accent" : "secondary") + " d-block w-100 ms-3"}>
                                                <i className="ci-compare fs-lg me-2" />
                                                <span>
                                                    { comparisons.includes(product.id) ? "Сравнение" : "Сравнить" }
                                                </span>
                                            </button>
                                        )}
                                    </div>
                                )}

                                { /* Product panels */ }
                                <div className="accordion mb-4" id="productPanels">
                                    <div className="accordion-item">
                                        <h3 className="accordion-header">
                                            <a className="accordion-button" href="#information" role="button" data-bs-toggle="collapse" aria-expanded="true" aria-controls="information">
                                                <i className="ci-lable text-muted lead align-middle mt-n1 me-2" />Информация
                                            </a>
                                        </h3>
                                        <div className="accordion-collapse collapse show" id="information" data-bs-parent="#productPanels">
                                            <div className="accordion-body fs-sm">
                                                { product.manufacturer && (
                                                    <div className="d-flex justify-content-between pb-2">
                                                        <div className="text-muted fw-light">Производитель</div>
                                                        <div className="fw-normal">{ product.manufacturer.name }</div>
                                                    </div>
                                                )}
                                                { product.partnumber && (
                                                    <div className="d-flex justify-content-between pb-2">
                                                        <div className="text-muted fw-light">Артикул</div>
                                                        <div className="fw-normal">{ product.partnumber }</div>
                                                    </div>
                                                )}
                                                { product.developer_country && product.developer_country.enabled && (
                                                    <div className="d-flex justify-content-between pb-2">
                                                        <div className="text-muted fw-light">Страна разработки</div>
                                                        <div className="fw-normal">{ product.developer_country.name }</div>
                                                    </div>
                                                )}
                                                { product.country && product.country.enabled && (
                                                    <div className="d-flex justify-content-between pb-2">
                                                        <div className="text-muted fw-light">Страна производства</div>
                                                        <div className="fw-normal">{ product.country.name }</div>
                                                    </div>
                                                )}
                                                { product.warranty && (
                                                    <div className="d-flex justify-content-between pb-2">
                                                        <div className="text-muted fw-light">Гарантия</div>
                                                        <div className="fw-normal">{ product.warranty }</div>
                                                    </div>
                                                )}
                                                { product.article && (
                                                    <div className="d-flex justify-content-between pb-2">
                                                        <div className="text-muted fw-light">Код товара</div>
                                                        <div className="fw-normal">{ product.article }</div>
                                                    </div>
                                                )}
                                            </div>
                                        </div>
                                    </div>
                                    { /*
                                    {% if product.enabled and product.cost > 0 %}
                                    <div class="accordion-item">
                                        <h3 class="accordion-header"><a class="accordion-button collapsed" href="#localStore" role="button" data-bs-toggle="collapse" aria-expanded="true" aria-controls="localStore"><i class="ci-location text-muted lead align-middle mt-n1 me-2"></i>Наличие в магазинах</a></h3>
                                        <div class="accordion-collapse collapse" id="localStore" data-bs-parent="#productPanels">
                                            <div class="accordion-body fs-sm">
                                                <div class="text-center"><div class="spinner-border" role="status"><span class="visually-hidden">Загрузка...</span></div></div>
                                            </div>
                                        </div>
                                    </div>
                                    {% if product.width and product.height and product.length and product.weight > 0.1 %}
                                    <div class="accordion-item">
                                        <h3 class="accordion-header"><a class="accordion-button collapsed" href="#delivery" role="button" data-bs-toggle="collapse" aria-expanded="true" aria-controls="delivery"><i class="ci-delivery text-muted lead align-middle mt-n1 me-2"></i>Доставка</a></h3>
                                        <div class="accordion-collapse collapse" id="delivery" data-parent="#productPanels">
                                            <div class="accordion-body fs-sm">
                                                <div id="yaDeliveryWidget"></div>
                                                <div class="text-center"><div class="spinner-border" role="status"><span class="visually-hidden">Загрузка...</span></div></div>
                                            </div>
                                        </div>
                                    </div>
                                    {% endif %}
                                    {% endif %}
                                      */
                                    }
                                    { product.manuals && (
                                        <div className="accordion-item">
                                            <h3 className="accordion-header">
                                                <a className="accordion-button collapsed" href="#instructions" role="button" data-bs-toggle="collapse" aria-expanded="true" aria-controls="instructions">
                                                    <i className="ci-clip text-muted lead align-middle mt-n1 me-2"></i>Инструкции
                                                </a>
                                            </h3>
                                            <div className="accordion-collapse collapse" id="instructions" data-parent="#productPanels">
                                                <div className="accordion-body fs-sm" dangerouslySetInnerHTML={{__html: product.manuals }}></div>
                                            </div>
                                        </div>
                                    )}
                                </div>

                                { product.enabled && product.gifts && (
                                    <>
                                        <div className="mb-1">Покупая { product.title } в интернет-магазине, Вы получите подарок:</div>
                                        <div className="mb-4 mx-auto w-75">
                                            { product.gifts.map((gift) => (
                                                <ProductMiniCard product={gift} key={gift.id} />
                                            ))}
                                        </div>
                                    </>
                                )}
                            </div>
                        </div>
            </div>
        </div>
        </div>

        {product.constituents && (
            <div className="pt-lg-2 pb-3 mb-md-3">
                <h2 className="h3 pb-2">Состав комплекта</h2>
                <div className="container px-0 mx-n2 d-flex flex-wrap">
                    { product.constituents.map((item) => (
                        <div className="card m-2" style={{maxWidth: "230px"}} key={item.id}>
                            { item.thumbnail ? (
                                <img
                                    className="card-img-top"
                                    src={item.thumbnail.url}
                                    width={item.thumbnail.width}
                                    height={item.thumbnail.height}
                                    alt={`${product.title} ${product.whatis}`} />
                            ) : (
                                <i className="d-inline-block ci-camera text-muted card-img-top" style={{
                                       width: '200px',
                                       height: '200px',
                                       fontSize: '100px',
                                       padding: '50px'
                                   }} />
                            )}
                            <div className="card-body fs-sm">
                                <strong>
                                    <Link href={{ pathname: '/products/[code]', query: { code: item.code }}}>
                                        <a className="text-muted">{ item.title }</a>
                                    </Link>
                                    { item.quantity > 1 && (
                                        <>({ item.quantity } шт.)</>
                                    )}
                                </strong>
                                { item.shortdescr && (
                                    <> &mdash; { item.shortdescr }</>
                                )}
                            </div>
                        </div>
                    ))}
                </div>
            </div>
        )}

        { product.descr && (
            <div className="pb-3 mb-md-3" itemProp="description" dangerouslySetInnerHTML={{__html: rebootstrap(product.descr) }} />
        )}

        { product.spec && (
            <div className="pb-3 mb-md-3" dangerouslySetInnerHTML={{__html: rebootstrap(product.spec) }} />
        )}

            { Object.keys(fieldNames).length > 0 && productFields.length > 0 && (
            <div className="pt-lg-2 pb-3 mb-md-3">
                <h2 className="h3 pb-2">Характеристики { product.title }</h2>
                <div className="product-spec container fs-sm">
                    { productFields.map((field) => (
                        <div className="row mb-2" key={field}>
                            { field === 'fabric_verylite' ? (
                                <>
                                    <span className="col-md px-0 text-muted">
                                        <span className="d-block border-bottom">
                                            <span>
                                                Диапазон прошиваемых материалов{" "}
                                                <a className="opener-html" href="/blog/H/">
                                                    <i className="ci-message fs-ms text-muted" />
                                                </a>
                                            </span>
                                        </span>
                                    </span>
                                    <span className="col-md pt-1 pt-sm-0 pe-0 ps-2 align-self-end">
                                        Очень легкие – { product.fabric_verylite }<br />
                                        Легкие – { product.fabric_lite }<br />
                                        Средние и умеренно тяжелые – { product.fabric_medium }<br />
                                        Тяжелые – { product.fabric_hard }<br />
                                        Трикотаж – { product.fabric_stretch }
                                    </span>
                                </>
                            ) : (
                                <>
                                    <span className="col-md px-0 text-muted">
                                        <span className="d-block border-bottom">
                                            { fieldNames[field][0] }
                                            <FieldHelp field={field} />
                                        </span>
                                    </span>
                                    <span className="col-md pt-1 pt-sm-0 pe-0 ps-2 align-self-end">{ prettify(product[field]) }{ fieldNames[field][1] }</span>
                                </>
                            )}
                        </div>
                    ))}
                </div>
            </div>
        )}

        { /*
      {% if 'images/'|add:product.manufacturer.code|add:'/stitches/'|add:product.code|add:'_stitches.jpg'|file_exists or product.stitches %}
      <!-- Stitches -->
      <div class="pt-lg-2 pb-3 mb-md-3">
        <h2 class="h3 pb-2">Строчки {{ product.title }}</h2>
        {% if 'images/'|add:product.manufacturer.code|add:'/stitches/'|add:product.code|add:'_stitches.jpg'|file_exists %}
        <div class="pb-3 mb-md-3">
          <img src="{{ MEDIA_URL }}/images/{{ product.manufacturer.code }}/stitches/{{ product.code }}_stitches.jpg" alt="Строчки швейной машины {{ product.title }}" class="img-responsive">
        </div>
        {% endif %}
        {% if product.stitches %}
        <div>
          {{ product.stitches|safe }}
        </div>
        {% endif %}
      </div>
      {% endif %}
          */
        }

        { product.complect && (
            <div className="pt-lg-2 pb-3 mb-md-3">
                <h2 className="h3 pb-2">Комплектация</h2>
                <div dangerouslySetInnerHTML={{__html: product.complect }} />
            </div>
        )}

    </div>

        { (product.accessories || product.similar) && (
            <div className="border-top pt-5">
                { product.accessories && (
                    <div className="container pt-lg-2 pb-5 mb-md-3">
                        <h2 className="h3 text-center pb-4">Популярные аксессуары для { product.title }</h2>
                        <div className="tns-carousel tns-controls-static tns-controls-outside">
                            <div className="tns-carousel-inner">
                                { product.accessories.map((accessory) => (
                                    <ProductMiniCard product={accessory} key={accessory.id} />
                                ))}
                            </div>
                        </div>
                    </div>
                )}
                { product.similar && (
                    <div className="container pt-lg-2 pb-5 mb-md-3">
                        <h2 className="h3 text-center pb-4">Товары похожие на { product.title }</h2>
                        <div className="tns-carousel tns-controls-static tns-controls-outside">
                            <div className="tns-carousel-inner">
                                { product.similar.map((similar) => (
                                    <ProductMiniCard product={similar} key={similar.id} />
                                ))}
                            </div>
                        </div>
                    </div>
                )}
            </div>
        )}

        { product.dealertxt && (
            <div className="border-top pt-5">
                <div className="container pt-lg-2 pb-5 mb-md-3">
                    <h2 className="h3 text-center pb-4">Обратите внимание!</h2>
                    <div>{ product.dealertxt }</div>
                </div>
            </div>
        )}

        { /*
    {% if product.allow_reviews %}
    {% include '_product_reviews.html' %}
    {% endif %}
          */
        }
        </>
    )
}

Product.getLayout = function getLayout(page) {
    return (
        <PageLayout title={page.props.title} dark overlapped>
            {page}
        </PageLayout>
    )
}

export async function getStaticProps(context) {
    const code = context.params?.code;
    const queryClient = new QueryClient();
    console.log(code);
    const fieldsQuery = queryClient.fetchQuery(productKeys.fields(), () => getProductFields());
    const dataQuery = queryClient.fetchQuery(productKeys.detail(code), () => loadProductByCode(code));
    // run queries in parallel
    await fieldsQuery;
    const data = await dataQuery;

    return {
        props: {
            code,
            dehydratedState: dehydrate(queryClient),
            title: data.title
        }
    };
}

export async function getStaticPaths() {
    // const pages = await loadPages(); TODO: pre-build top(?) products
    // const paths = pages.map((page) => ({
    //     params: { uri: page.url.slice(1, -1).split('/') },
    // }))
    return { paths: [], fallback: true }
}
