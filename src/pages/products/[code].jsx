import { useState, useEffect, Suspense, lazy } from 'react';
import { useRouter } from 'next/router';
import Link from 'next/link';
import { dehydrate, QueryClient, useQuery } from '@tanstack/react-query';
import { useInView } from 'react-intersection-observer';

import Accordion from 'react-bootstrap/Accordion';
import OverlayTrigger from 'react-bootstrap/OverlayTrigger';
import Tooltip from 'react-bootstrap/Tooltip';

import PageLayout from '@/components/layout/page';
import FieldHelp from '@/components/product/field-help';
import NoImage from '@/components/product/no-image';
import ProductMiniCard from '@/components/product/mini-card';
import ProductPrice from '@/components/product/price';
import ProductRating from '@/components/product/rating';
import Loading from '@/components/loading';

import useBasket from '@/lib/basket';
import useFavorites from '@/lib/favorites';
import useComparison from '@/lib/comparison';
import { useSession } from '@/lib/session';
import { productKeys, loadProducts, loadProductByCode, getProductFields } from '@/lib/queries';
import { recomendedFilters, giftsFilters, firstPageFilters } from '@/lib/catalog';

const ProductReviews = lazy(() => import('@/components/product/reviews'));
const ProductStock = lazy(() => import('@/components/product/stock'));

const gana = require('gana');

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

const gallerySettings = {
    touchNavigation: true
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

function prettify(field, value) {
    if (field === 'manufacturer')
        return value.name;
    if (field === 'country' || field === 'developer_country')
        return value.enabled ? value.name : "";
    if (field === 'complect')
        return <div dangerouslySetInnerHTML={{__html: value }} />
    if (typeof value === 'string')
        return value.trim();
    return value;
}

function rebootstrap(value) {
    if (typeof value !== 'string')
        return value;
    value = value.replaceAll('col-md-4', 'col-md-2');
    value = value.replaceAll('col-md-8', 'col-md-4');
    value = value.replaceAll('col-md-10', 'col-md-5');
    value = value.replaceAll('col-md-12', 'col-md-6');
    value = value.replaceAll('<h3>', '<h5>');
    value = value.replaceAll('</h3>', '</h5>');
    value = value.replaceAll('<h4>', '<h6>');
    value = value.replaceAll('</h4>', '</h6>');
    value = value.replaceAll('embed-responsive embed-responsive-4by3', 'ratio ratio-4x3');
    value = value.replaceAll('embed-responsive embed-responsive-16by9', 'ratio ratio-16x9');
    return value;
}

function renderTemplate(template, product) {
    const compileFn = gana(template);
    return compileFn({product});
};

export default function Product({code}) {
    const [glightboxModule, setGlightboxModule] = useState(null);
    const [tnsModule, setTnsModule] = useState(null);
    const [productFields, setProductFields] = useState([]);
    const [fieldNames, setFieldNames] = useState({});
    const [stockVisible, setStockVisible] = useState(false);
    const [reviewsVisible, setReviewsVisible] = useState(false);
    const [quantity, setQuantity] = useState(1);

    const router = useRouter();

    const { status } = useSession();
    const { addItem } = useBasket();
    const { favorites, favoritize, unfavoritize } = useFavorites();
    const { comparisons, compare } = useComparison();

    const { data: fields } = useQuery({
        queryKey: productKeys.fields(),
        queryFn: () => getProductFields()
    });

    const { data: product, isSuccess, isLoading } = useQuery({
        queryKey: productKeys.detail(code),
        queryFn: () => loadProductByCode(code),
        enabled: code !== undefined
    });

    useEffect(() => {
        import('glightbox').then((module) => {
            setGlightboxModule(module);
        });
        import('tiny-slider').then((module) => {
            setTnsModule(module);
        });
    }, []);

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
        if (isSuccess && product.image && glightboxModule !== null) {
            const lightbox = glightboxModule.default(gallerySettings);
            return () => {
                lightbox.destroy();
            }
        }
    }, [product, isSuccess, glightboxModule]);

    useEffect(() => {
        if (isSuccess && (product.accessories || product.similar) && tnsModule !== null) {
            const carousels = [];
            const carouselEls = [].slice.call(document.querySelectorAll('.tns-carousel .tns-carousel-inner'));
            carouselEls.map((carouselEl) => {
                const carousel = tnsModule.tns({container: carouselEl, ...sliderSettings});
                // carousel.events.on('transitionEnd', carousel.updateSliderHeight);
                carousels.push(carousel);
            });
            return () => {
                carousels.map((carousel) => carousel.destroy());
            }
        }
    }, [product, isSuccess, tnsModule]);

    const { ref: reviewsRef } = useInView({
        rootMargin: '300px',
        triggerOnce: true,
        onChange: (inView) => setReviewsVisible(inView)
    });

    const handleCartClick = () => {
        // TODO: {% if utm_source %}?utm_source={{ utm_source }}{% endif %}
        addItem(product.id, quantity);
    };

    const handleFavoritesClick = () => {
        if (status === 'authenticated') {
            if (favorites.includes(product.id))
                unfavoritize(product.id);
            else
                favoritize(product.id);
        } // TODO: else show dialog or tooltip
    }

    const handleComparisonClick = () => {
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
            <div className="container">
                <div className="bg-light shadow-lg rounded-3 px-4 py-3 mb-5">
                    <Loading className="text-center my-5 py-5" mega />
                </div>
            </div>
        )

    return (
        <>
            <div className="container">
                <div className="bg-light shadow-lg rounded-3 px-4 py-3 mb-5">
                    <div className="px-lg-3">
                        <div className="row">
                            <div className="col-lg-7 pe-lg-0">
                                { product.image ? (
                                    <div className="d-block">
                                        <a href={product.big_image || product.image}
                                           className="glightbox gallery-item"
                                           data-title={`${product.whatis ? product.whatis + ' ' : ''}${product.title}`}>
                                            <img
                                                src={product.image}
                                                alt={`${product.title} ${product.whatis}`}
                                                itemProp="image" />
                                        </a>
                                        { product.images && (
                                            <div className="d-flex flex-wrap my-2">
                                                { product.images.map((image, index) => (
                                                    <a href={image.src}
                                                       className="glightbox gallery-item rounded border me-4 mb-4"
                                                       data-title={`${product.title} - фото №${index + 2}`}
                                                       key={index}>
                                                        <img
                                                            src={image.thumbnail.src}
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
                                        <NoImage size={300} block />
                                    </div>
                                )}
                            </div>
                            <div className="col-lg-5 pt-4 pt-lg-0">
                                <div className="product-details ms-auto pb-3">
                                    { product.enabled && product.cost > 0 && (
                                        <div className="d-flex flex-row xalign-items-baseline mb-3">
                                            <div className="h3 fw-normal text-accent flex-shrink-1">
                                                <ProductPrice product={product} delFs="lg" itemProp="price" />
                                                <span itemProp="priceCurrency" className="d-none">RUB</span>
                                            </div>
                                            <div className="ms-3 text-end w-100">
                                                { product.discount > 0 && (
                                                    <OverlayTrigger
                                                        placement="bottom"
                                                        overlay={
                                                            <Tooltip>
                                                                Базовая цена в магазинах &laquo;Швейный Мир&raquo;
                                                                без учета скидок <b>{ product.price.toLocaleString('ru') }</b>&nbsp;руб.
                                                                Скидка при покупке в интернет-магазине составляет{' '}
                                                                <b>{ product.discount.toLocaleString('ru') }</b>&nbsp;руб.
                                                            </Tooltip>
                                                        }
                                                    >
                                                        <span className="badge bg-primary badge-shadow ms-2 mb-2">Скидка</span>
                                                    </OverlayTrigger>
                                                )}
                                                { product.ishot && (
                                                    <span className="badge bg-accent badge-shadow ms-2 mb-2">Акция</span>
                                                )}
                                                { product.isnew && (
                                                    <span className="badge bg-info badge-shadow ms-2 mb-2">Новинка</span>
                                                )}
                                                { product.recomended && (
                                                    <span className="badge bg-warning badge-shadow ms-2 mb-2">Рекомендуем</span>
                                                )}
                                                { product.sales && product.sales.filter((action) => !!action.notice && !!!action.brief).map((action) => (
                                                    <span className="badge bg-danger badge-shadow ms-2 mb-2" key={action.id}>{action.notice}</span>
                                                ))}
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
                                        <div className={`product-badge product-${ product.instock < 1 ? "not-" : ""}available mt-${ product.enabled ? "1": "3" }`}>
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
                                                        product.sales.filter((action) => !!action.brief).map((action) => (
                                                            <div className="mb-2" key={action.id}>
                                                                <i className="ci-gift text-danger pe-2" />
                                                                <span dangerouslySetInnerHTML={{__html: renderTemplate(action.brief, product) }}></span>
                                                            </div>
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
                                                        <select className="form-select me-3" style={{width: "5rem"}} value={quantity} onChange={(e) => setQuantity(e.target.value)}>
                                                            <option value="1">1</option>
                                                            <option value="2">2</option>
                                                            <option value="3">3</option>
                                                            <option value="4">4</option>
                                                            <option value="5">5</option>
                                                        </select>
                                                    )}
                                                    { product.instock > 0 ? (
                                                        <button className="btn btn-primary btn-shadow d-block w-100" type="button" onClick={handleCartClick}>
                                                            <span className="d-none spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span>
                                                            <i className="ci-cart fs-lg me-2" />Купить
                                                        </button>
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
                                    <Accordion className={"mb-4" + (product.enabled ? "" : " mt-5")} defaultActiveKey={['information']} alwaysOpen>
                                        <Accordion.Item eventKey="information">
                                            <Accordion.Header>
                                                <i className="ci-lable text-muted lead align-middle mt-n1 me-2" />Информация
                                            </Accordion.Header>
                                            <Accordion.Body className="fs-sm">
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
                                            </Accordion.Body>
                                        </Accordion.Item>
                                        { product.enabled && product.cost > 0 && (
                                            <Accordion.Item eventKey="stock">
                                                <Accordion.Header>
                                                    <i className="ci-location text-muted lead align-middle mt-n1 me-2" />Наличие в магазинах
                                                </Accordion.Header>
                                                <Accordion.Body className="fs-sm" onEnter={() => setStockVisible(true)}>
                                                    { stockVisible && (
                                                        <Suspense fallback={<Loading className="text-center" />}>
                                                            <ProductStock id={product.id} />
                                                        </Suspense>
                                                    )}
                                                </Accordion.Body>
                                            </Accordion.Item>
                                        )}
                                        { product.manuals && (
                                            <Accordion.Item eventKey="instructions">
                                                <Accordion.Header>
                                                    <i className="ci-clip text-muted lead align-middle mt-n1 me-2" />Инструкции
                                                </Accordion.Header>
                                                <Accordion.Body className="fs-sm">
                                                    <div dangerouslySetInnerHTML={{__html: product.manuals }}></div>
                                                </Accordion.Body>
                                            </Accordion.Item>
                                        )}
                                    </Accordion>

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

                { product.descr && (
                    <div className="pb-3 mb-md-3" itemProp="description" dangerouslySetInnerHTML={{__html: rebootstrap(product.descr) }} />
                )}

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
                                        <div className="text-center">
                                            <NoImage size={200} />
                                        </div>
                                    )}
                                    <div className="card-body fs-sm">
                                        <strong>
                                            <Link className="text-muted" href={{ pathname: '/products/[code]', query: { code: item.code }}}>
                                                { item.title }
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
                                                        <Link href="/blog/H/">
                                                            <i className="ci-message fs-ms text-muted" />
                                                        </Link>
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
                                            <span className="col-md pt-1 pt-sm-0 pe-0 ps-2 align-self-end">
                                                { prettify(field, product[field]) }
                                                { fieldNames[field][1] }
                                            </span>
                                        </>
                                    )}
                                </div>
                            ))}
                        </div>
                    </div>
                )}

                { product.stitches && (
                    <div className="pt-lg-2 pb-3 mb-md-3">
                        <h2 className="h3 pb-2">Строчки { product.title }</h2>
                        <div dangerouslySetInnerHTML={{__html: product.stitches }} />
                    </div>
                )}

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

            { product.allow_reviews && (
                <div className="border-top my-lg-3 py-5">
                    <div className="container pt-md-2" id="reviews" ref={reviewsRef}>
                        { reviewsVisible && (
                            <Suspense fallback={<Loading className="text-center" />}>
                                <ProductReviews product={product} />
                            </Suspense>
                        )}
                    </div>
                </div>
            )}
        </>
    )
}

Product.getLayout = function getLayout(page) {
    return (
        <PageLayout
            title={page.props.title}
            titleAddon={
                page.props.allowReviews && (
                    <ProductRating product={page.props.id} anchor="reviews" />
                )}
            dark overlapped>
            {page}
        </PageLayout>
    )
}

export async function getStaticProps(context) {
    const code = context.params.code;

    const queryClient = new QueryClient();
    const fieldsQuery = queryClient.fetchQuery({
        queryKey: productKeys.fields(),
        queryFn: () => getProductFields()
    });
    const dataQuery = queryClient.fetchQuery({
        queryKey: productKeys.detail(code),
        queryFn: () => loadProductByCode(code)
    });
    try {
        // run queries in parallel
        await fieldsQuery;
        const data = await dataQuery;

        return {
            props: {
                code,
                dehydratedState: dehydrate(queryClient),
                title: data.title,
                id: data.id,
                allowReviews: data.allow_reviews
            }
        };
    } catch (error) {
        if (error.response.status === 404)
            return { notFound: true };
        else
            throw(error);
    }
}

export async function getStaticPaths() {
    const filters = [
        recomendedFilters,
        giftsFilters,
        firstPageFilters
    ];
    const included = new Set();
    const paths = [];
    for (let filter of filters) {
        let page = 1;
        while (page !== undefined) {
            const products = await loadProducts(page, 100, filter, null);
            paths.push(...products.results.filter((product) => !included.has(product.id)).map((product) => {
                included.add(product.id);
                return {
                    params: {
                        code: product.code
                    }
                };
            }));
            if (products.totalPages > products.currentPage)
                page += 1;
            else
                page = undefined;
        }
    }
    return { paths, fallback: true }
}
