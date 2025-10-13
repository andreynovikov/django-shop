import { useState, useEffect } from 'react';
import { useRouter } from 'next/router';
import Link from 'next/link';
import { useQuery, useQueries } from '@tanstack/react-query';

import PageLayout from '@/components/layout/page';
import FieldHelp from '@/components/product/field-help';
import NoImage from '@/components/product/no-image';
import ProductPrice from '@/components/product/price';

import useBasket from '@/lib/basket';
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

export default function Compare({kindId, productIds}) {
    const router = useRouter();
    const { addItem } = useBasket();

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

    const handleCartClick = (product) => {
        if (product.variations) {
        } else {
            addItem(product.id);
        }
    };

    if (productIds.length === 0 && kindId === null && comparisons.length === 0)
        return (
            <div className="alert alert-danger" role="alert">Отсутствуют товары для сравнения</div>
        )

    if (kindId !== null || (productIds.length > 0 && !isProductsSuccess) || !isKindsSuccess)
        return (
            <div>Loading...</div>
        )

    return (
        <>
            { isKindsSuccess && kinds.length > 1 ? (
                <div className="btn-group btn-group-lg mb-5" role="group">
                    { kinds.map((kind) => (
                        <Link className={"btn btn-" + (kind.id === currentKind ? "dark" : "secondary")} href={{ pathname: router.pathname, query: { kind: kind.id }}} key={kind.id}>
                            { kind.name }
                        </Link>
                    ))}
                </div>
            ) : (
                <h2 className="h3 pb-3">{ isKindSuccess ? kind.name : "Товары" }</h2>
            )}

            {products.length === 1 && (
                <div className="alert alert-secondary mb-5" role="alert">Добавьте ещё как минимум один товар в сравнение</div>
            )}

            <div className="table-responsive">
                <table className="table table-bordered table-layout-fixed fs-sm" style={{minWidth: "45rem"}} id="comparison">
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
                                        <i className="ci-trash me-1" />Удалить
                                    </button>
                                    <Link className="d-inline-block mb-3" href={{ pathname: '/products/[code]', query: { code: product.code }}}>
                                        { product.thumbnail_small ? (
                                            <img
                                                src={product.thumbnail_small.url}
                                                width={product.thumbnail_small.width}
                                                height={product.thumbnail_small.height}
                                                alt={`${product.title} ${product.whatis}`} />
                                        ) : (
                                            <NoImage size={80} />
                                        )}
                                    </Link>
                                    <h3 className="product-title fs-sm">
                                        <Link href={{ pathname: '/products/[code]', query: { code: product.code }}}>
                                            { product.title }
                                        </Link>
                                    </h3>
                                    { product.enabled && product.instock > 0 && (
                                        <button type="button" className="btn btn-success btn-sm" onClick={() => handleCartClick(product)}>
                                            { product.variations ? "Выбрать" : "Купить" }
                                        </button>
                                    )}
                                </td>
                            ))}
                        </tr>
                    </thead>
                    <tbody>
                        { Object.keys(fieldNames).length > 0 && productFields.length > 0 && productFields.map(({field, differ}) => (
                            <tr className={ (differ && !different) ? "table-danger" : "" } key={field}>
                                <th className="text-dark">
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
                        <tr>
                            <th className="text-dark">Цена</th>
                            {products.map(({data: product}) => (
                                <td key={product.id}>
                                    { product.enabled && product.price > 0 && <ProductPrice product={product} delFs="xs" /> }
                                </td>
                            ))}
                        </tr>
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
                        { productFields.length > 5 && (
                            <tr>
                                <th></th>
                                {products.map(({data: product}) => (
                                    <td key={product.id}>
                                        { product.instock > 0 && (
                                            <button type="button" className="btn btn-success d-block w-100" onClick={() => handleCartClick(product)}>
                                                { product.variations ? "Выбрать" : "Купить" }
                                            </button>
                                        )}
                                    </td>
                                ))}
                            </tr>
                        )}
                    </tbody>
                </table>
            </div>

        </>
    )
}

Compare.getLayout = function getLayout(page) {
    return (
        <PageLayout title="Сравнение товаров" dark>
            <div className="container py-5 mb-2">
                {page}
            </div>
        </PageLayout>
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
