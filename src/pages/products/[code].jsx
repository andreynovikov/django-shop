import { useState, useEffect } from 'react';
import { useRouter } from 'next/router';
import Script from 'next/script';
import { dehydrate, QueryClient, useQuery } from 'react-query';

import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faScaleUnbalanced } from '@fortawesome/free-solid-svg-icons';

import Layout from '@/components/layout';
import PageTitle from '@/components/layout/page-title';
import FieldHelp from '@/components/product/field-help';
import ProductRating from '@/components/product/rating';
import ProductReviews from '@/components/product/reviews';

import useComparison from '@/lib/comparison';
import { productKeys, loadProducts, loadProductByCode, getProductFields } from '@/lib/queries';
import { rows } from '@/lib/partition';

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

export default function Product({code, title}) {
    const [bootstrapLoaded, setBootstrapLoaded] = useState(false);
    const [tnsModule, setTnsModule] = useState(null);
    const [glightboxModule, setGlightboxModule] = useState(null);
    const [productFields, setProductFields] = useState([]);
    const [fieldNames, setFieldNames] = useState({});

    const router = useRouter();

    const { comparisons, compare } = useComparison();

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
        if (Object.keys(fieldNames).length > 0 && productFields.length > 0)
            setupTabs();
    }, [fieldNames, productFields]);

    useEffect(() => {
        if (bootstrapLoaded && isSuccess)
            setupTabs();
    }, [bootstrapLoaded, isSuccess]);

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
        const stickyNavbar = document.querySelector("nav.navbar-sticky");
        if (stickyNavbar) {
            let offset = stickyNavbar.getBoundingClientRect().bottom;
            if (!stickyNavbar.classList.contains("fixed-top"))
                offset = offset * 2; // because it will become fixed during scroll
            window.scrollTo({
                behavior: 'smooth',
                top: document.getElementById("reviews_tab").getBoundingClientRect().top -
                    document.body.getBoundingClientRect().top - offset
            });
        } else {
            document.getElementById("reviews_tab").scrollIntoView({
                behavior: 'smooth'
            });
        }
    }

    const setupTabs = () => {
        if (!bootstrapLoaded) // this can happen if product fields are ready before bootstrap is loaded
            return;
        const triggerTabList = [].slice.call(document.querySelectorAll('.tab-content a.detail-nav-link'));
        triggerTabList.forEach(function (triggerEl) {
            var tabTrigger = new bootstrap.Tab(triggerEl);
            triggerEl.addEventListener('click', function (event) {
                event.preventDefault();
                tabTrigger.show();
            })
        })
        const triggerFirstTabEl = document.querySelector('.tab-content li:first-child a.detail-nav-link');
        if (triggerFirstTabEl)
            bootstrap.Tab.getInstance(triggerFirstTabEl).show(); // Select first tab
    };

    const initializeBootstrap = () => {
        setBootstrapLoaded(true);
    };

    if (router.isFallback || isLoading || !isSuccess)
        return (
            <>
                <PageTitle title={title} />
                <div className="container d-flex align-items-center justify-content-center text-secondary mb-6">
                    <div className="spinner-border mx-3" role="status" aria-hidden="true"></div>
                    <strong>Загружается...</strong>
                </div>
            </>
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
		                        { product.stitches && (
                                    <li className="nav-item"><a className="nav-link detail-nav-link" href="#stitches_tab" role="tab">Строчки</a></li>
                                )}
                                { Object.keys(fieldNames).length > 0 && productFields.length > 0 && (
                                    <li className="nav-item"><a className="nav-link detail-nav-link" href="#specification_tab" role="tab">Технические характеристики</a></li>
                                )}
                                { product.allow_reviews && (
                                    <li className="nav-item"><a className="nav-link detail-nav-link" href="#reviews_tab" role="tab">Отзывы</a></li>
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
		                    { product.stitches && (
		                        <div className="tab-pane py-3" id="stitches_tab" role="tabpanel">
                                    <div dangerouslySetInnerHTML={{__html: product.stitches }} />
                                </div>
                            )}
                            { Object.keys(fieldNames).length > 0 && productFields.length > 0 && (
		                        <div className="tab-pane py-3" id="specification_tab" role="tabpanel">
                                    <div className="row">
                                        {rows(productFields, 2).map((row, index) => (
                                            <div className="col-lg-6" key={index}>
                                                <table className="table text-sm">
                                                    <tbody>
                                                        { row.map((field, index) => (
                                                            <tr key={field}>
                                                                <th className={"text-uppercase fw-normal" + (index === row.length -1 ? " border-0" : "")}>
                                                                    { fieldNames[field][0] }
                                                                    <FieldHelp field={field} />
                                                                </th>
                                                                <td className={"text-muted" + (index === row.length -1 ? " border-0" : "")}>
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
        <Script id="bootstrap" src="/js/bootstrap.bundle.js" onLoad={initializeBootstrap} onReady={initializeBootstrap} />
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
    const fieldsQuery = queryClient.prefetchQuery(productKeys.fields(), () => getProductFields());
    const dataQuery = queryClient.fetchQuery(productKeys.detail(code), () => loadProductByCode(code));
    // run queries in parallel
    await fieldsQuery;
    const data = await dataQuery;

    return {
        props: {
            code,
            dehydratedState: dehydrate(queryClient),
            title: data.title
        },
        revalidate: 60 * 60 * 24 // <--- ISR cache: once a day
    };
}

export async function getStaticPaths() {
    const products = await loadProducts(null, 1000, null, null);
    const paths = products.results.map((product) => ({
        params: { code: product.code }
    }))
    return { paths, fallback: true }
}
