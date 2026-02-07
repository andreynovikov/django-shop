import { useState, useEffect } from 'react';
import { useRouter } from 'next/router';
import Link from 'next/link';
import Image from 'next/image';
import { useQuery, useQueries } from '@tanstack/react-query';

import { IconTrashX } from '@tabler/icons-react';

import SvgIcon from '@/components/svg-icon';
import Layout from '@/components/layout';
import PageTitle from '@/components/layout/page-title';
import FieldHelp from '@/components/product/field-help';

import useComparison from '@/lib/comparison';
import { deepCompare } from '@/lib/compare';

import { kindKeys, productKeys, loadKinds, loadKind, loadProduct, getProductFields } from '@/lib/queries';

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

const noImageStyle = {
    width: '160px',
    height: '160px',
    fontSize: '80px',
    padding: '40px'
}

export default function Compare({kindId, productIds}) {
    const router = useRouter();

    const [currentKind, setCurrentKind] = useState(kindId);
    const [different, setDifferent] = useState(false);
    const [productFields, setProductFields] = useState([]);
    const [fieldNames, setFieldNames] = useState({});

    // if kind is passed get filtered product list...
    const { comparisons, uncompare, isSuccess: isComparisonSuccess } = useComparison({ kind: kindId });

    // ...and redirect to explicit comparison
    useEffect(() => {
        if (kindId !== null && isComparisonSuccess)
            router.replace({
                pathname: router.pathname,
                query: { product: comparisons }
            });
    }, [comparisons, isComparisonSuccess, kindId]);

    // get list of comparable kinds
    const { data: kinds, isSuccess: isKindsSuccess } = useQuery({
        queryKey: kindKeys.list(comparisons),
        queryFn: () => loadKinds(comparisons)
    });

    // if nothing is passed, redirect to first comparable kind
    useEffect(() => {
        if (isComparisonSuccess && comparisons.length > 0 && isKindsSuccess && kinds.length > 0 && kindId === null && productIds.length === 0) {
            console.log(kinds);
            router.replace({
                pathname: router.pathname,
                query: { kind: kinds[0].id }
            });
        }
    }, [isKindsSuccess, kinds, kindId, productIds, isComparisonSuccess, comparisons]);

    // if product list is passed compare them
    const products = useQueries({
        queries: productIds.map(productId => {
            return {
                queryKey: productKeys.detail(productId),
                queryFn: () => loadProduct(productId),
            }
        })
    });

    const isProductsSuccess = productIds.length > 0 && products.every(result => result.isSuccess);

    useEffect(() => {
        if (isProductsSuccess)
            setCurrentKind(products[0].data.kind[0]);
    }, [isProductsSuccess]);

    const { data: kind, isSuccess: isKindSuccess } = useQuery({
        queryKey: kindKeys.detail(currentKind),
        queryFn: () => loadKind(currentKind),
        enabled: currentKind !== null
    });

    const { data: fields } = useQuery({
        queryKey: productKeys.fields(),
        queryFn: () => getProductFields()
    });

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
        if (isKindSuccess && isProductsSuccess) {
            const comparison = kind.comparison.reduce((fields, field) => {
                var differ = false, value = products[0].data[field];
                for (var i = 1; i < products.length; i++) {
                    var val = products[i].data[field];
                    if (!deepCompare(val, value)) { // TODO: refactor to pass all products at once
                        differ = true;
                        break;
                    }
                }
                if (differ || (!different && value !== undefined && value !== ''))
                    fields.push({
                        field,
                        differ
                    });
                return fields;
            }, []);
            setProductFields(comparison);
        }
    }, [isKindSuccess, isProductsSuccess, different]);

    const uncompareProduct = (productId) => {
        uncompare(productId, () => {
            console.log("callback", productIds, productId);
            const ids = productIds.filter(id => +id !== productId);
            console.log(ids);
            router.replace({
                pathname: router.pathname,
                query: { product: ids }
            });
        });
    };

    if (productIds.length === 0 && kindId === null && comparisons.length === 0)
        return (
            <>
                <PageTitle title="Сравнение товаров" />
                <div className="alert alert-danger mx-1 mx-lg-4 mx-xl-6 mb-5" role="alert">Отсутствуют товары для сравнения</div>
            </>
        )

    if (kindId !== null || (productIds.length > 0 && !isProductsSuccess) || !isKindsSuccess)
        return (
            <div>Loading...</div>
        )

    return (
        <>
            { isKindsSuccess && kinds.length > 1 ? (
                <div className="container text-center mt-4">
                    <div className="btn-group btn-group-lg mb-5" role="group">
                        { kinds.map((kind) => (
                            <Link className={"btn btn-" + (kind.id === currentKind ? "dark" : "secondary")} href={{ pathname: router.pathname, query: { kind: kind.id }}} key={kind.id}>
                                { kind.name }
                            </Link>
                        ))}
                    </div>
                </div>
            ) : (
                <PageTitle title={ isKindSuccess ? kind.name : "Товары" } />
            )}

            {products.length === 1 && (
                <div className="alert alert-secondary mx-1 mx-lg-4 mx-xl-6 mb-5" role="alert">Добавьте ещё как минимум один товар в сравнение</div>
            )}

            <div className="table-responsive mx-1 mx-lg-4 mx-xl-6">
                <table className="table table-bordered table-layout-fixed" style={{minWidth: "45rem"}} id="comparison">
                    <thead>
                        <tr>
                            <td className="align-middle">
                                <div className="form-check">
                                    <input className="form-check-input" type="checkbox" id="differences" checked={different} onChange={() => setDifferent(!different)} />
                                    <label className="form-check-label" htmlFor="differences">Только различия</label>
                                </div>
                            </td>
                            {products.map(({data: product}) => (
                                <td className="text-center px-4 pb-4" key={product.id}>
                                    <button type="button" className="btn btn-sm d-block w-100 text-danger mb-2" onClick={() => uncompareProduct(product.id)}>
                                        <IconTrashX className="me-1" />
                                        Удалить
                                    </button>
                                    <Link className="d-inline-block mb-3" href={{ pathname: '/products/[code]', query: { code: product.code }}}>
                                        { product.image ? (
                                            <div className="position-relative" style={{ width: 160, aspectRatio: 1 }}>
                                                <Image
                                                    src={product.image}
                                                    fill
                                                    style={{ objectFit: "contain" }}
                                                    sizes="160px"
                                                    loading="lazy"
                                                    alt={`${product.title} ${product.whatisit ?? product.whatis}`} />
                                              </div>
                                        ) : (
                                            <SvgIcon id="shipping-box-1" className="svg-icon d-inline-block text-muted" style={ noImageStyle } />
                                        )}
                                    </Link>
                                    <h3 className="text-lg">
                                        <Link className="text-dark" href={{ pathname: '/products/[code]', query: { code: product.code }}}>
                                            { product.title }
                                        </Link>
                                    </h3>
                                </td>
                            ))}
                        </tr>
                    </thead>
                    <tbody>
                        { Object.keys(fieldNames).length > 0 && productFields.length > 0 && productFields.map(({field, differ}) => (
                            <tr className={ (differ && !different) ? "table-danger" : "" } key={field}>
                                <th className="text-uppercase text-sm fw-normal">
                                    { fieldNames[field][0] }
                                    <FieldHelp field={field} />
                                </th>
                                {products.map(({data: product}) => (
                                    <td key={product.id}>
                                        { product[field] && (
                                            <>
                                                { prettify(field, product[field]) }
                                                { fieldNames[field][1] }
                                            </>
                                        )}
                                    </td>
                                ))}
                            </tr>
                        ))}
                        { /*
            <tr>
              <th class="text-dark">Рейтинг</th>
              {% for product in products %}
              <td>
              {% if product.allow_reviews %}
              {% get_rating for product as product_rating %}
              {% if product_rating %}
              {{ product_rating|prettify }}/5
              {% endif %}
              {% endif %}
              </td>
              {% endfor %}
            </tr>
                          */
                        }
                    </tbody>
                </table>
            </div>

        </>
    )
}

Compare.getLayout = function getLayout(page) {
    return (
        <Layout title="Сравнение товаров">
            {page}
        </Layout>
    )
}

export async function getServerSideProps(context) {
    const kindId = context.query?.kind || null;
    const product = context.query?.product || [];
    const productIds = Array.isArray(product) ? product: [product];

    return {
        props: {
            kindId,
            productIds
        }
    };
}
