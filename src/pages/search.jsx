import { useState, useReducer, useMemo } from 'react';
import { useRouter } from 'next/router';
import { useQuery } from 'react-query';

import Offcanvas from 'react-bootstrap/Offcanvas';

import PageLayout from '@/components/layout/page';
import ProductCard from '@/components/product/card';
import MultipleChoiceFilter from '@/components/product/filters/multiple-choice-filter';
import PriceFilter from '@/components/product/filters/price-filter';
import PageSelector, { SmallPageSelector } from '@/components/page-selector';

import { productKeys, loadProducts } from '@/lib/queries';
import { useToolbar } from '@/lib/toolbar';
import useCatalog from '@/lib/catalog';
import rupluralize from '@/lib/rupluralize';

function filterReducer(filters, {field, value}) {
    const newFilters = filters.filter(filter => filter.field !== field);
    if (value !== undefined)
        newFilters.push({field, value});
    return newFilters;
}

export default function Search({text, page}) {
    const [showFilters, setShowFilters] = useState(false);
    const [currentFilters, setFilter] = useReducer(filterReducer, [{field: 'text', value: text}]);

    const router = useRouter();

    useCatalog();

    const toolbarItem = useMemo(() => {
        return (
            <a className="d-table-cell handheld-toolbar-item" onClick={() => setShowFilters(true)}>
                <span className="handheld-toolbar-icon"><i className="ci-filter-alt" /></span>
                <span className="handheld-toolbar-label">Фильтры</span>
            </a>
        )
    }, []);

    useToolbar(toolbarItem);

    const { data: products, isSuccess, isLoading, isError } = useQuery(
        productKeys.list(page || 1, 15, currentFilters, null),
        () => loadProducts(page || 1, 15, currentFilters, null),
        {
            keepPreviousData : true // required for filters not to loose choices and attributes
        }
    );

    const selectedFilters = useMemo(() => {
        const filters = {};
        const minPrice = currentFilters.reduce((value, f) => f.field === 'price_min' ? f.value : value, undefined);
        const maxPrice = currentFilters.reduce((value, f) => f.field === 'price_max' ? f.value : value, undefined);
        filters['price'] = [minPrice, maxPrice];
        const manufacturer = currentFilters.reduce((value, f) => f.field === 'manufacturer' ? f.value : value, undefined);
        filters['manufacturer'] = manufacturer;
        filters['available'] = currentFilters.reduce((value, f) => f.field === 'instock' ? f.value : value, undefined);
        return filters;
    }, [currentFilters]);

    const handleFilterChanged = (field, value) => {
        console.log(field, value);
        router.push({
            pathname: router.pathname,
            query: { ...router.query, page: 1 }
        });
        if (field === 'price') {
            setFilter({field: `${field}_min`, value: value?.[0]});
            setFilter({field: `${field}_max`, value: value?.[1]});
        } else {
            setFilter({field, value});
        }
    };

    const handleAvailableChange = (e) => {
        const value = e.currentTarget.checked ? 1 : undefined;
        setFilter({field: 'enabled', value});
        setFilter({field: 'instock', value});
    }

    if (isSuccess) {
        return (
            <div className="container pb-5 mb-2 mb-md-4">
                <div className="row">
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
                                <div className="widget pb-4 mb-4 border-bottom">
                                    <h3 className="widget-title">Производитель</h3>
                                    <MultipleChoiceFilter
                                        filter={{name: 'manufacturer', ...products.filters['manufacturer']}}
                                        filterValue={selectedFilters['manufacturer']}
                                        onFilterChanged={handleFilterChanged} />
                                </div>
                                <div className="widget pb-4 mb-4 border-bottom">
                                    <h3 className="widget-title">Цена</h3>
                                    <PriceFilter
                                        filter={{name: 'price', unit: 'руб', ...products.filters['price']}}
                                        filterValue={selectedFilters['price']}
                                        onFilterChanged={handleFilterChanged} />
                                </div>
                                <div className="widget">
                                    <div className="form-check">
                                        <input
                                            className="form-check-input"
                                            type="checkbox"
                                            id="sw-awailable-check"
                                            checked={selectedFilters['available'] !== undefined}
                                            onChange={handleAvailableChange} />
                                        <label className="form-check-label" htmlFor="sw-awailable-check">Доступно к покупке</label>
                                    </div>
                                </div>
                            </Offcanvas.Body>
                        </Offcanvas>
                    </aside>

                    <section className="col-lg-8">
                        <div className="d-flex justify-content-center justify-content-sm-between align-items-center pt-2 pb-4 pb-sm-5">
                            <div className="d-flex pb-3">
                                { products.count > 0 && (
                                    <span className="text-light opacity-75 text-nowrap">
                                        { rupluralize(products.count, ['Найден','Найдены','Найдены']) }
                                        {' '}{ products.count }{' '}
                                        { rupluralize(products.count, ['товар','товара','товаров']) }
                                    </span>
                                )}
                            </div>
                            { products?.totalPages > 1 && (
                                <SmallPageSelector
                                    pathname={router.pathname}
                                    query={router.query}
                                    totalPages={products.totalPages}
                                    currentPage={products.currentPage} />
                            )}
                        </div>

                        <div className="row mx-n2">
                            { products.count > 0 ? (
                                products.results.map((product) => (
                                    <div className="col-md-4 col-sm-6 px-2 mb-4" key={product.id}>
                                        <ProductCard product={product} />
                                        <hr className="d-sm-none" />
                                    </div>
                                ))
                            ) : (
                                <div className="lead my-4">Ничего не найдено</div>
                            )}
                        </div>

                        { products.totalPages > 1 && (
                            <>
                                <hr className="my-3" />
                                <PageSelector
                                    pathname={router.pathname}
                                    query={router.query}
                                    totalPages={products.totalPages}
                                    currentPage={products.currentPage} />
                            </>
                        )}
                    </section>
                </div>
            </div>
        );
    }

    if (isLoading) {
        return (
            <div className="container pb-5 mb-2 mb-md-4">
                <div className="d-flex align-items-center pt-2 pb-5">
                    <div className="spinner-border text-light" role="status"></div>
                    <div className="lead ms-3 text-light">Загружается...</div>
                </div>
            </div>
        )
    }

    if (isError) {
        return (
            <div className="container pb-5 mb-2 mb-md-4">
                <div className="d-flex align-items-center my-5 py-5">
                    <div className="lead ms-3">Error!</div>
                </div>
            </div>
        );
    }

    return <></>;
}

Search.getLayout = function getLayout(page) {
    return (
        <PageLayout title={"Поиск товаров: " + page.props.text} dark overlapped>
            {page}
        </PageLayout>
    )
}

export async function getServerSideProps(context) {
    return {
        props: context.query || {}
    }
}
