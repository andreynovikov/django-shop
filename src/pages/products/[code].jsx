import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/router';
import { dehydrate, QueryClient, useQuery } from 'react-query';

import Layout from '@/components/layout';
import FieldHelp from '@/components/product/field-help';
import NoImage from '@/components/product/no-image';
import Popover from '@/components/popover';

import useBasket from '@/lib/basket';
import { productKeys, loadProducts, loadProductByCode, getProductFields } from '@/lib/queries';

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
    value = value.replaceAll('col-md-8', 'col-md-4');
    value = value.replaceAll('col-md-10', 'col-md-5');
    value = value.replaceAll('col-md-12', 'col-md-6');
    // value = value.replaceAll('<h3>', '<h5>');
    // value = value.replaceAll('</h3>', '</h5>');
    // value = value.replaceAll('<h4>', '<h6>');
    // value = value.replaceAll('</h4>', '</h6>');
    value = value.replaceAll('embed-responsive embed-responsive-4by3', 'ratio ratio-4x3');
    value = value.replaceAll('embed-responsive embed-responsive-16by9', 'ratio ratio-16x9');
    return value;
}

export default function Product({code, title}) {
    const [glightboxModule, setGlightboxModule] = useState(null);
    const [productFields, setProductFields] = useState([]);
    const [fieldNames, setFieldNames] = useState({});
    const [anchorDiscountElement, setAnchorDiscountElement] = useState(null);
    const [anchorDeshevleElement, setAnchorDeshevleElement] = useState(null);

    const router = useRouter();

    const { addItem } = useBasket();

    const { data: fields } = useQuery(productKeys.fields(), () => getProductFields());

    const { data: product, isSuccess, isLoading } = useQuery(productKeys.detail(code), () => loadProductByCode(code), {
        enabled: code !== undefined
    });

    useEffect(() => {
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
        if (isSuccess && product.image && glightboxModule !== null) {
            const lightbox = glightboxModule.default({
                touchNavigation: true
            });
            return () => {
                lightbox.destroy();
            }
        }
    }, [product, isSuccess, glightboxModule]);

    const handlePrimaryClick = () => {
        if (product.variations) {
        } else {
            addItem(product.id);
        }
    };

    const handleDiscountClick = (event) => {
        setAnchorDiscountElement(event.currentTarget);
    };

    const handleDiscountClose = () => {
        setAnchorDiscountElement(null);
    };

    const handleDeshevleClick = (event) => {
        setAnchorDeshevleElement(event.currentTarget);
    };

    const handleDeshevleClose = () => {
        setAnchorDeshevleElement(null);
    };

    if (router.isFallback || isLoading || !isSuccess)
        return (
            <>
                <h1>{ title }</h1>
                <div className="container d-flex align-items-center justify-content-center text-secondary my-5">
                    <div className="spinner-border mx-3" role="status" aria-hidden="true"></div>
                    <strong>Загружается...</strong>
                </div>
            </>
        )

    return (
        <div className="product-page" itemScope itemType="http://schema.org/Product">
            <h1 className="prodname" itemProp="name">
                { product.title }
                <sup>
                    { product.ishot && <span className="label sw-action">Акция</span> }
                    { product.isnew && <span className="label sw-new">Новинка</span> }
                    { product.recomended && <span className="label sw-recomended">Рекомендуем</span> }
                    { product.utilisation && <span className="label sw-action">Скидка по &laquo;Утилизации&raquo;</span> }
                </sup>
            </h1>

            { product.partnumber && <p>Код производителя: { product.partnumber }</p> }
            { (product.runame || product.whatis) && <p>{ product.whatis } { product.runame }</p> }

            <div className="d-flex flex-column-reverse flex-sm-row" style={{gap: 10}}>
                <div className="flex-grow-1">
                    <div className="product-image">
                        { product.image ? (
                            <div className="text-center">
                                <a className="glightbox" href={product.big_image || product.image} data-title={product.title}>
                                    <img
                                        className="img-responsive"
                                        src={product.image}
                                        alt={`${product.title} ${product.whatis}`}
                                        itemProp="image" />
                                </a>
                            </div>
                        ) : (
                            <NoImage className="d-none d-lg-block text-muted mx-auto" />
                        )}
                    </div>
                </div>

                <div className="card align-self-stretch align-self-sm-start">
                    <div className="card-body">
                        { product.enabled ? (
                            <div itemProp="offers" itemScope itemType="http://schema.org/Offer">
                                { product.discount > 0 && (
                                    <>
                                        <p className="oldprice">
                                            <del>{ product.price.toLocaleString('ru') }&nbsp;руб.</del>
                                            <img onClick={handleDiscountClick} src="/i/icons/more_icon.png" className="opacity-50 align-baseline btn btn-link p-0 ps-1" alt="" />
                                        </p>
                                        <Popover
                                            anchorElement={anchorDiscountElement}
                                            onClose={handleDiscountClose}>
                                            <h5>Скидка!</h5>
                                            <div className="my-2">
                                                Базовая цена в магазинах &laquo;Швейный Мир&raquo; без учета скидок:{' '}
                                                <b>{ product.price.toLocaleString('ru') }&nbsp;руб.</b>
                                            </div>
                                            <div>
                                                Скидка при покупке в интернет-магазине составляет:{' '}
                                                <b>{ product.discount.toLocaleString('ru') }&nbsp;руб.</b>
                                            </div>
                                        </Popover>
                                    </>
                                )}
                                <div>
                                    <span className="align-middle fs-md fw-bold">
                                        <span className="lead fw-bold sw-price" itemProp="price">{ product.cost.toLocaleString('ru') }</span>&nbsp;руб.
                                    </span>

                                    <button className="btn btn-success fw-bold ms-2 align-middle" type="button" onClick={handlePrimaryClick}>
                                        { product.instock > 0 ? "Купить" : "Сообщить о поступлении" }
                                    </button>

                                    <span itemProp="priceCurrency" className="d-none">RUB</span>
                                </div>

                                { product.deshevle && (
                                    <div className="my-1">
                                        <button type="button" className="btn btn-link p-0" onClick={handleDeshevleClick}>Нашли дешевле?</button>
                                        <Popover
                                            page="/dialog/deshevle/"
                                            anchorElement={anchorDeshevleElement}
                                            onClose={handleDeshevleClose} />
                                    </div>
                                )}

                                <div className="mt-3">
                                    <span className="product-nal-caption">Наличие:</span>{" "}
                                    { product.instock > 1 ? (
                                        <span className="product-nal-true">Есть</span>
                                    ) : product.instock == 1 ? (
                                        <span className="product-nal-true">Мало</span>
                                    ) : (
                                        <span className="product-nal-false">Нет</span>
                                    )}
                                </div>

                                { product.sales_notes && <p className="mt-3">{ product.sales_notes }</p> }
                            </div>
                        ) : (
                            <span className="product-nal-false">Товар снят с продажи</span>
                        )}
                    </div>
                </div>
            </div>

            { product.images && (
                <div className="mt-2">
                    { product.images.map((image, index) => (
                    <a className="glightbox me-1" href={image.url} data-title={`${product.title} - фото №${index + 2}`} key={index}>
                        <img
                            src={image.thumbnail.url}
                            width={image.thumbnail.width}
                            height={image.thumbnail.height}
                            alt={`${product.title} - фото №${index + 2}`} />
                    </a>
                    ))}
                </div>
            )}

            <div className="mt-3" />

            { product.descr && (
                <div className="pb-3" itemProp="description" dangerouslySetInnerHTML={{__html: rebootstrap(product.descr) }} />
            )}
            { product.spec && (
                <div className="pb-3" dangerouslySetInnerHTML={{__html: rebootstrap(product.spec) }} />
            )}

            { product.manuals && (
                <>
                    <h2>Инструкции для { product.title }:</h2>
                    <div className="pb-3" dangerouslySetInnerHTML={{__html: product.manuals.replaceAll('/static', '') }} />
                </>
            )}

            { Object.keys(fieldNames).length > 0 && productFields.length > 0 && (
                <>
                    <h2>Характеристики{ product.kind ? " " + product.title : "" }:</h2>
                    <dl className="product-spec">
                        { productFields.map((field) => (
                            <React.Fragment key={field}>
                                <dt>
                                    <span>
                                        { fieldNames[field][0] }
                                        <FieldHelp field={field} />
                                    </span>
                                </dt>
                                <dd>
                                    { prettify(field, product[field]) }
                                    { fieldNames[field][1] }
                                </dd>
                            </React.Fragment>
                        ))}
                    </dl>
                </>
            )}

            { product.stitches && (
                <>
                    <h2>Строчки { product.title }:</h2>
                    <div className="py-3" dangerouslySetInnerHTML={{__html: product.stitches }} />
                </>
            )}

            { product.complect && (
                <>
                    <h2>Комплектация{ product.kind ? " " + product.title : "" }:</h2>
                    <div className="py-3" dangerouslySetInnerHTML={{__html: product.complect }} />
                </>
            )}

        </div>
    )
}

Product.getLayout = function getLayout(page) {
    return (
        <Layout title={page.props.title} hideTitle>
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
    // Pre-build only products with kind (machines and overlocks)
    const products = await loadProducts(null, 1000, [{field: 'kind', 'value': [1, 2]}], null);
    const paths = products.results.map((product) => ({
        params: { code: product.code }
    }))
    return { paths, fallback: true }
}
