import { useState, useReducer, useEffect, useMemo } from 'react';
import { useRouter } from 'next/router';
import Link from 'next/link';
import { dehydrate, QueryClient, useQuery } from 'react-query';

import Offcanvas from 'react-bootstrap/Offcanvas';

import PageLayout from '@/components/layout/page';
import ProductCard from '@/components/product/card';
import ProductFilter from '@/components/product/filter';
import PageSelector, { SmallPageSelector } from '@/components/page-selector';

import { categoryKeys, productKeys, loadCategories, loadCategory, loadProducts } from '@/lib/queries';
import { useToolbar } from '@/lib/toolbar';
import useCatalog from '@/lib/catalog';
import rupluralize from '@/lib/rupluralize';

const baseFilters = [
    { field: 'enabled', value: 1}
];
const defaultOrder = 'title';

function filterReducer(filters, action) {
    switch (action.type) {
        case 'reset':
            return action.filters;
        case 'set':
            const {field, value} = action.filter;
            const newFilters = filters.filter(filter => filter.field !== field);
            if (value !== undefined)
                newFilters.push({field, value});
            return newFilters;
        default:
            return filters;
    }
}

/*
  TODO:
  - refactor price filter on server side
  - более строгие фильтры не на первой странице приводят к пустой странице
  - debounce currentFilters (useDeferredValue does not work)
*/
export default function Category({path, currentPage, pageSize, order, filters}) {
    const [currentFilters, setFilter] = useReducer(filterReducer, filters);
    const [currentOrder, setOrder] = useState(order);
    const [showFilters, setShowFilters] = useState(false);

    // reset filters on page change
    useEffect(() => {
        setFilter({type: 'reset', filters});
    }, [filters]);

    const router = useRouter();
    useCatalog();

    const { data: category, isSuccess } = useQuery(
        categoryKeys.detail(path),
        () => loadCategory(path),
        {
            enabled: !!path // path is not set on first render
        }
    );

    const toolbarItem = useMemo(() => {
        return category.filters ? (
            <a className="d-table-cell handheld-toolbar-item" onClick={() => setShowFilters(true)}>
                <span className="handheld-toolbar-icon"><i className="ci-filter-alt" /></span>
                <span className="handheld-toolbar-label">Фильтры</span>
            </a>
        ) : undefined
    }, [category]);

    useToolbar(toolbarItem);

    const { data: products, isSuccess: isProductsSuccess } = useQuery(
        productKeys.list(currentPage, pageSize, currentFilters, currentOrder),
        () => loadProducts(currentPage, pageSize, currentFilters, currentOrder),
        {
            enabled: isSuccess,
            keepPreviousData : true // required for filters not to loose choices and attributes
        }
    );

    const selectedFilters = useMemo(() => {
        if (!isSuccess || !!!category.filters)
            return {};

        return category.filters.reduce((filters, filter) => {
            let value = undefined;
            if (filter.widget === 'PriceWidget') {
                const minValue = currentFilters.reduce((value, f) => f.field === filter.name + '_min' ? f.value : value, undefined);
                const maxValue = currentFilters.reduce((value, f) => f.field === filter.name + '_max' ? f.value : value, undefined);
                if (minValue !== undefined || maxValue !== undefined)
                    value = [minValue, maxValue];
            } else {
                value = currentFilters.reduce((value, f) => f.field === filter.name ? f.value : value, undefined);
            }
            filters[filter.name] = value;
            return filters;
        }, {});
    }, [currentFilters, category, isSuccess]);

    const handleFilterChanged = (field, value) => {
        console.log(field, value);
        const filter = category.filters.reduce((value, filter) => field === filter.name ? filter : value, undefined);
        if (filter.widget === 'PriceWidget') {
            setFilter({type: 'set', filter: {field: `${field}_min`, value: value?.[0]}});
            setFilter({type: 'set', filter: {field: `${field}_max`, value: value?.[1]}});
        } else {
            setFilter({type: 'set', filter: {field, value}});
        }
    };

    const handleOrderSelect = (value) => {
        setOrder(value);
    };

    if (router.isFallback) {
        // TODO: Test and make user friendly
        return <div>Loading...</div>
    }

    if (isSuccess)
        return (
            <div className="container pb-5 mb-2 mb-md-4">
                <div className="row">
                    { (category.children || category.filters) && (
                        <aside className="col-lg-4">
                            <Offcanvas
                                show={showFilters}
                                onHide={() => setShowFilters(false)}
                                responsive="lg"
                                className="offcanvas bg-white w-100 rounded-3 shadow-lg py-1"
                                style={{maxWidth: "22rem"}}>
                                <Offcanvas.Header className="align-items-center shadow-sm" closeButton>
                                    <h2 className="h5 mb-0">Фильтры</h2>
                                </Offcanvas.Header>
                                <Offcanvas.Body className="py-grid-gutter px-lg-grid-gutter">
                                    { category.children && (
                                        <div className={"widget widget-links d-none d-lg-block mb-4 pb-4" + (category.filters ? " border-bottom" : "")}>
                                            <h3 className="widget-title">Категории</h3>
                                            <ul className="widget-list">
                                                {category.children.map((subcategory) => (
                                                    <li className="widget-list-item" key={subcategory.id}>
                                                        <Link className="widget-list-link" href={{ pathname: router.pathname, query: { path: [...path, subcategory.slug] } }}>
                                                            { subcategory.name }
                                                        </Link>
                                                    </li>
                                                ))}
                                            </ul>
                                        </div>
                                    )}
                                    { category.filters && category.filters.map((filter, index) => (
                                        <div className={"widget" + (index === category.filters.length-1 ? "" : " pb-4 mb-4 border-bottom")} key={filter.id}>
                                            <h3 className="widget-title">{ filter.label }</h3>
                                            <ProductFilter
                                                filter={{...filter, ...products?.filters?.[filter.name]}}
                                                filterValue={selectedFilters[filter.name]}
                                                onFilterChanged={handleFilterChanged} />
                                        </div>
                                    ))}
                                </Offcanvas.Body>
                            </Offcanvas>
                        </aside>
                    )}
                    <section className={`col-lg-${(category.children || category.filters) ? 8 : 12}`}>
                        <div className="d-flex justify-content-center justify-content-sm-between align-items-center pt-2 pb-4 pb-sm-5">
                            <div className="d-flex flex-wrap">
                                <div className="d-flex align-items-center flex-nowrap me-3 me-sm-4 pb-3">
                                    <label className="text-light opacity-75 text-nowrap fs-sm me-2 d-none d-sm-block" htmlFor="sorting">Сортировать:</label>
                                    <select className="form-select" id="sorting" value={currentOrder} onChange={(event) => handleOrderSelect(event.target.value)}>
                                        <option value={order}>по-умолчанию</option>
                                        { order !== '-price' && <option value="-price">от дорогих к дешёвым</option> }
                                        { order !== 'price' && <option value="price">сначала дешёвые</option> }
                                        { order !== 'title' && <option value="title">по алфавиту</option> }
                                        { order !== '-title' && <option value="-title">по алфавиту, наоборот</option> }
                                    </select>
                                    { isProductsSuccess && (
                                        <span className="fs-sm text-light opacity-75 text-nowrap ms-2 d-none d-md-block">
                                            из
                                            {' '}{ products.count }{' '}
                                            { rupluralize(products.count, ['товара','товаров','товаров']) }
                                        </span>
                                    )}
                                </div>
                            </div>
                            { products?.totalPages > 1 && (
                                <SmallPageSelector
                                    pathname={router.pathname}
                                    query={router.query}
                                    path={path}
                                    totalPages={products.totalPages}
                                    currentPage={products.currentPage} />
                            )}
                        </div>


                        { (category.description && currentPage == 1) && (
                            <div className="card mb-grid-gutter">
                                <div className="card-body px-4" dangerouslySetInnerHTML={{__html: category.description }}></div>
                            </div>
                        )}

                        { category.children && (
                            <div className="d-lg-none card mb-grid-gutter">
                                <div className="card-body px-4">
                                    <h5 className="card-title">Категории</h5>
                                    <ul className="widget-list">
                                        {category.children.map((subcategory) => (
                                            <li className="widget-list-item" key={subcategory.id}>
                                                <Link className="widget-list-link" href={{ pathname: router.pathname, query: { path: [...path, subcategory.slug] } }}>
                                                    { subcategory.name }
                                                </Link>
                                            </li>
                                        ))}
                                    </ul>
                                </div>
                            </div>
                        )}

                        <div className="row mx-n2">
                            {isProductsSuccess && products.results.map((product) => (
                                <div className={((category.children || category.filters) ? "" : "col-lg-3 ") + "col-md-4 col-sm-6 px-2 mb-4"} key={product.id}>
                                    <ProductCard product={product} />
                                    <hr className="d-sm-none" />
                                </div>
                            ))}
                        </div>

                        { products?.totalPages > 1 && (
                            <>
                                <hr className="my-3" />
                                <PageSelector
                                    pathname={router.pathname}
                                    query={router.query}
                                    path={path}
                                    totalPages={products.totalPages}
                                    currentPage={products.currentPage} />
                            </>
                        )}
                    </section>
                </div>
            </div>
        )

    return null
}

Category.getLayout = function getLayout(page) {
    return (
        <PageLayout title={page.props.title} dark overlapped>
            {page}
        </PageLayout>
    )
}

export async function getStaticProps(context) {
    let path = context.params?.path;
    let currentPage = '1';
    if (+path[path.length - 1] > 0) {
        currentPage = path.pop();

        if (currentPage === '1') {
            return {
                redirect: {
                    destination: '/catalog/' + path.join('/') + '/',
                    permanent: false,
                },
            }
        }
    }
    const queryClient = new QueryClient();
    const category = await queryClient.fetchQuery(categoryKeys.detail(path), () => loadCategory(path));

    const pageSize = 1000; // category.categories || category.filters ? 15 : 16;
    const productFilters = [{field: 'categories', value: category.id}, ...baseFilters];
    const productOrder = category.product_order || defaultOrder;
    await queryClient.prefetchQuery(productKeys.list(currentPage, pageSize, productFilters, productOrder), () => loadProducts(currentPage, pageSize, productFilters, productOrder));

    return {
        props: {
            dehydratedState: dehydrate(queryClient),
            title: category.name,
            filters: productFilters,
            order: productOrder,
            path,
            currentPage,
            pageSize
        },
        revalidate: 60 * 60 // <--- ISR cache: once an hour
    };
}

export async function getStaticPaths() {
    const getPaths = ({paths, root}, category) => {
        const path = root.concat([category.slug]);
        paths.push({
            params: {path},
        });
        if (category.children) {
            const {paths: rpaths} = category.children.reduce(getPaths, {paths, root: path});
            return {paths: rpaths, root};
        }
        return {paths, root};
    };

    const categories = await loadCategories();
    const {paths} = categories.reduce(getPaths, {paths: [], root: []});
    return { paths, fallback: true };
}
