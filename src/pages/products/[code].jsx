import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/router';
import Link from 'next/link';
import Script from 'next/script';
import { dehydrate, QueryClient, useQuery } from 'react-query';

import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faBalanceScale, faScaleUnbalanced } from '@fortawesome/free-solid-svg-icons';

import SvgIcon from '@/components/svg-icon';
import Layout from '@/components/layout';
import FieldHelp from '@/components/product/field-help';
import ProductRating from '@/components/product/rating';
import ProductReviews from '@/components/product/reviews';

import useComparison from '@/lib/comparison';
import { useSession } from '@/lib/session';
import { productKeys, loadProductByCode, getProductFields } from '@/lib/queries';
import { columns, rows } from '@/lib/partition';

const fieldList = ['km_class', 'km_font', 'km_needles', 'km_prog', 'km_rapport',
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
                   'prom_button_diainner', 'prom_needle_height', 'prom_stitch_type', 'prom_autothread',
                   'developer_country', 'country', 'warranty'];

const noImageStyle = {
    width: '300px',
    fontSize: '300px'
};

const renderer = {
    'country': (value) => value.name,
    'developer_country': (value) => value.name
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
    value = value.replaceAll('embed-responsive embed-responsive-4by3', 'ratio ratio-4x3');
    value = value.replaceAll('embed-responsive embed-responsive-16by9', 'ratio ratio-16x9');
    return value;
}

export default function Product({code}) {
    const [tnsModule, setTnsModule] = useState(null);
    const [glightboxModule, setGlightboxModule] = useState(null);
    const [productFields, setProductFields] = useState([]);
    const [fieldNames, setFieldNames] = useState({});
    const [quantity, setQuantity] = useState(1);

    const router = useRouter();

    const { comparisons, compare, uncompare } = useComparison();

    const { data: fields } = useQuery(productKeys.fields(), () => getProductFields());

    const { data: product, isSuccess, isLoading } = useQuery(productKeys.detail(code), () => loadProductByCode(code), {
        enabled: code !== undefined
    });

    useEffect(() => {
        import('tiny-slider').then((module) => {
            setTnsModule(module);
        });
        import('glightbox').then((module) => {
            setGlightboxModule(module);
        });
    }, []);

    useEffect(() => {
        if (isSuccess)
            setProductFields(fieldList.filter(field => field in product && product[field] && ((field !== 'developer_country' && field !== 'country') || product[field].enabled)));
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
        if (Object.keys(fieldNames).length > 0 && productFields.length > 0) {
            initializeBootstrap();
        }
    }, [fieldNames, productFields]);

    useEffect(() => {
        if (isSuccess && product.image && tnsModule !== null && glightboxModule !== null) {
            const carousel = tnsModule.tns({
                container: '.carousel',
                items: 1,
                lazyload: true,
                controls: false,
                autoHeight: true,
                nav: true,
                navPosition: 'bottom',
            });
            carousel.events.on('transitionEnd', carousel.updateSliderHeight);
            const lightbox = glightboxModule.default({
                touchNavigation: true
            });
            return () => {
                carousel.destroy(); // we need this because tiny-slider is not reentrant safe
                lightbox.destroy(); // just for similarity
            }
        }
    }, [product, isSuccess, tnsModule, glightboxModule]);

    const handleComparisonClick = () => {
        if (comparisons.includes(product.id))
            router.push({
                pathname: '/compare',
                query: { kind: product.kind[0] }
            });
        else
            compare(product.id);
    }

    const handleReviewsClick = () => {
        var triggerEl = document.querySelector("[href='#reviews_tab']")
        var tab = bootstrap.Tab.getInstance(triggerEl)
        tab.show();
        document.getElementById("reviews_tab").scrollIntoView({
            behavior: 'smooth'
        });
    }

    const initializeBootstrap = () => {
        if (window && 'bootstrap' in window && bootstrap.Tab) {
            const triggerTabList = [].slice.call(document.querySelectorAll('.tab-content a.detail-nav-link'));
            triggerTabList.forEach(function (triggerEl) {
                console.log(triggerEl);
                var tabTrigger = new bootstrap.Tab(triggerEl);
                triggerEl.addEventListener('click', function (event) {
                    event.preventDefault();
                    tabTrigger.show();
                })
            })
            var triggerFirstTabEl = document.querySelector('.tab-content li:first-child a.detail-nav-link');
            bootstrap.Tab.getInstance(triggerFirstTabEl).show(); // Select first tab
        }
    };

    if (isLoading || !isSuccess)
        return (
            <div>Loading...</div>
        )

    return (
        <>
            <div itemScope itemType="http://schema.org/Product">
                <section className="product-details py-3">
                    <div className="container">
                        <div className="row">
                            <div className="col-lg-7 order-2 order-lg-1">
                                <div className="row">
                                    <div className="col-12 detail-carousel">
                                        { product.ishot && <div className="ribbon ribbon-dark">Акция</div> }
				                        { product.isnew && <div className="ribbon ribbon-primary">Новинка</div> }
				                        { product.recomended && <div className="ribbon ribbon-info">Рекомендуем</div> }
                                        { product.image ? (
                                            <div className="carousel text-center">
                                                <a className="glightbox" href={product.big_image || product.image} data-title={product.title}>
                                                    <img
                                                        src={product.image}
                                                        alt={`${product.title} ${product.whatis}`}
                                                        itemProp="image" />
                                                </a>
                                                { product.images && (
                                                    product.images.map((image, index) => (
                                                        <a className="glightbox" href={image.url} data-title={`${product.title} - фото №${index + 2}`} key={index}>
                                                            <img
                                                                src="data:image/gif;base64,R0lGODlhAQABAPAAAMzMzAAAACH5BAAAAAAALAAAAAABAAEAAAICRAEAOw=="
                                                                className="tns-lazy-img"
                                                                data-src={image.url}
                                                                alt={`${product.title} - фото №${index + 2}`} />
                                                        </a>
                                                    ))
                                                )}
                                            </div>
                                        ) : (
                                            <div className="d-none d-lg-block">
                                                <i className="d-block ci-camera text-muted mx-auto" style={ noImageStyle } />
                                            </div>
                                        )}
                                    </div>
                                </div>
                            </div>

                            <div className="col-lg-5 pl-lg-4 order-1 order-lg-2">
                                <h1 className="mb-3 display-4 font-weight-bold text-uppercase" itemProp="name">{ product.title }</h1>
                                <div itemProp="offers" itemScope itemType="http://schema.org/Offer">
			                        <div className="d-flex flex-column flex-sm-row align-items-sm-center justify-content-sm-end mb-4">
                                        { product.allow_reviews && (
                                            <a className="d-flex align-items-center text-primary sw-rating-link" onClick={handleReviewsClick}>
                                                <ProductRating product={product.id} />
                                            </a>
                                        )}
                                    </div>
			                    </div>
			                    { product.partnumber && <p classNamr="mb-4 text-muted">Код производителя: { product.partnumber }</p> }
			                    { (product.runame || product.whatis) && <p className="mb-4 text-muted">{ product.whatis } { product.runame }</p> }

                                <ul className="list-inline">
                                    { product.kind && (
                                        <li className="list-inline-item">
                                            <button
                                                type="button"
                                                onClick={handleComparisonClick}
                                                className="btn btn-outline-secondary mb-1">
                                                <FontAwesomeIcon icon={faScaleUnbalanced} className="me-2" />
                                                <span>
                                                    { comparisons.includes(product.id) ? "Сравнение" : "Добавить в сравнение" }
                                                </span>
                                            </button>
                                        </li>
                                    )}
                                </ul>
                            </div>
                        </div>
                    </div>
                </section>

                <section className="mt-5">
                    <div className="container">
	                    <div className="tab-content py-4">
                            <ul className="nav nav-tabs flex-column flex-sm-row" role="tablist">
		                        { product.descr && (
                                    <li className="nav-item"><a className="nav-link detail-nav-link" href="#description_tab" role="tab">Описание</a></li>
                                )}
		                        { product.manuals && (
                                    <li className="nav-item"><a className="nav-link detail-nav-link" href="#manuals_tab" role="tab">Инструкция</a></li>
                                )}
		                        { product.complect && (
                                    <li className="nav-item"><a className="nav-link detail-nav-link" href="#complect_tab" role="tab">Комплектация</a></li>
                                )}
                                { /*
		                            {% if 'images/'|add:product.manufacturer.code|add:'/stitches/'|add:product.code|add:'_stitches.jpg'|file_exists or product.stitches %}
                                    <li class="nav-item"><a class="nav-link detail-nav-link" href="#stitches_tab" role="tab">Строчки</a></li>
		                            {% endif %}
                                  */
                                }
                                { Object.keys(fieldNames).length > 0 && productFields.length > 0 && (
                                    <li className="nav-item"><a className="nav-link detail-nav-link" href="#specification_tab" role="tab">Технические характеристики</a></li>
                                )}
                                { product.allow_reviews && (
                                    <li className="nav-item"><a className="nav-link detail-nav-link" href="#reviews_tab" role="tab">Обзоры</a></li>
                                )}
                            </ul>

		                    { product.descr && (
	                            <div className="tab-pane py-3" id="description_tab" role="tabpanel" itemProp="description">
		                            <div className="container">
                                        <div className="pb-3 mb-md-3" itemProp="description" dangerouslySetInnerHTML={{__html: rebootstrap(product.descr) }} />
                                        <div className="pb-3 mb-md-3" dangerouslySetInnerHTML={{__html: rebootstrap(product.spec) }} />
                                    </div>
                                </div>
                            )}
		                    { product.manuals && (
	                            <div className="tab-pane py-3" id="manuals_tab" role="tabpanel">
                                    <div dangerouslySetInnerHTML={{__html: product.manuals.replaceAll('/static', '') }} />
                                </div>
                            )}
		                    { product.complect && (
		                        <div className="tab-pane py-3" id="complect_tab" role="tabpanel">
                                    <div dangerouslySetInnerHTML={{__html: product.complect }} />
                                </div>
                            )}
                            { Object.keys(fieldNames).length > 0 && productFields.length > 0 && (
		                        <div className="tab-pane py-3" id="specification_tab" role="tabpanel">
                                    <div class="row">
                                        {rows(productFields, 2).map((row, index) => (
                                            <div class="col-lg-6" key={index}>
                                                <table class="table text-sm">
                                                    <tbody>
                                                        { row.map((field, index) => (
                                                            <tr key={field}>
                                                                <th class={"text-uppercase fw-normal" + (index === row.length -1 ? " border-0" : "")}>
                                                                    { fieldNames[field][0] }
                                                                    <FieldHelp field={field} />
                                                                </th>
                                                                <td class={"text-muted" + (index === row.length -1 ? " border-0" : "")}>
                                                                    { field in renderer ? renderer[field](product[field]) : prettify(product[field]) }
                                                                    { fieldNames[field][1] }
                                                                </td>
                                                            </tr>
                                                        ))}
                                                    </tbody>
                                                </table>
                                            </div>
                                        ))}
                                    </div>
                                </div>
                            )}
                            { product.allow_reviews && (
                                <div className="tab-pane py-3" id="reviews_tab" role="tabpanel">
                                    <ProductReviews product={product} />
                                </div>
                            )}

                        </div>
                    </div>
                </section>

            </div>
        { /*
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
                                            { product.discount > 0 && (
                                                <span
                                                    className="badge bg-primary badge-shadow align-middle mt-n2"
                                                    data-bs-toggle="tooltip"
                                                    data-bs-placement="right"
                                                    data-bs-html="true"
                                                    title="Базовая цена в магазинах &laquo;Швейный Мир&raquo; без учета скидок <b>{{ product.price|quantize:"1" }}</b>&nbsp;руб. Скидка при покупке в интернет-магазине составляет <b>{{ product.discount|quantize:"1" }}</b>&nbsp;руб.">
                                                    Скидка
                                                </span>
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
                        <div className="container pt-md-2" id="reviews">
                            <ProductReviews product={product} />
                        </div>
                    </div>
            )}
          */
        }
            <Script id="bootstrap" src="/js/bootstrap.bundle.js" onReady={initializeBootstrap} onLoad={initializeBootstrap} />
        </>
    )
}

Product.getLayout = function getLayout(page) {
    return (
        <Layout title={page.props.title}>
            {page}
        </Layout>
    )
}

export async function getStaticProps(context) {
    const code = context.params?.code;
    const queryClient = new QueryClient();
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
    // const pages = await loadPages(); TODO: pre-build products
    // const paths = pages.map((page) => ({
    //     params: { uri: page.url.slice(1, -1).split('/') },
    // }))
    return { paths: [], fallback: true }
}
