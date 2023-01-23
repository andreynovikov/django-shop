import React, { useState, useReducer, useEffect } from 'react';
import { useRouter } from 'next/router';
import Link from 'next/link';
import { useQuery } from 'react-query';

import PageLayout from '@/components/layout/page';
import ProductCard from '@/components/product/card';
import MultipleChoiceFilter from '@/components/product/filters/multiple-choice-filter';
import PriceFilter from '@/components/product/filters/price-filter';

import { productKeys, loadProducts } from '@/lib/queries';
import useCatalog from '@/lib/catalog';
import rupluralize from '@/lib/rupluralize';

function filterReducer(filters, {field, value}) {
    const newFilters = filters.filter(filter => filter.field !== field);
    if (value !== undefined)
        newFilters.push({field, value});
    return newFilters;
}

export default function Search({text, page}) {
    const router = useRouter();
    const [currentFilters, setFilter] = useReducer(filterReducer, [{field: 'text', value: text}]);
    const [minPage, setMinPage] = useState(0);
    const [maxPage, setMaxPage] = useState(0);

    useCatalog();

    const { data: products, isSuccess, isLoading, isError } = useQuery(
        productKeys.list(page || 1, 15, currentFilters, null),
        () => loadProducts(page || 1, 15, currentFilters, null),
        {
            keepPreviousData : true // required for filters not to loose choices and attributes
        }
    );

    useEffect(() => {
        if (isSuccess) {
            // количество переключателей страниц лимитировано дизайном
            const pageRange = products.next && products.previous ? 7 : 10;
            let min = products.currentPage - pageRange + Math.min(4, products.totalPages - products.currentPage)
            if (min < 4)
                min = 1;
            let max = products.currentPage + pageRange - Math.min(4, products.currentPage - 1)
            if (max > products.totalPages - 3)
                max = products.totalPages;
            setMinPage(min);
            setMaxPage(max);
        }
    }, [products, isSuccess]);

    const onFilterChanged = (field, value) => {
        router.push({
            pathname: router.pathname,
            query: { ...router.query, page: 1 }
        });
        setFilter({field, value});
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
                        <div className="offcanvas offcanvas-collapse bg-white w-100 rounded-3 shadow-lg py-1" id="shop-sidebar" style={{maxWidth: "22rem"}}>
                            <div className="offcanvas-header align-items-center shadow-sm">
                                <h2 className="h5 mb-0">Фильтры</h2>
                                <button className="btn-close ms-auto" type="button" data-bs-dismiss="offcanvas" aria-label="Закрыть"></button>
                            </div>
                            <div className="offcanvas-body py-grid-gutter px-lg-grid-gutter">
                                <div className="widget pb-4 mb-4 border-bottom">
                                    <h3 className="widget-title">Производитель</h3>
                                    <MultipleChoiceFilter filter={{name: 'manufacturer', ...products.filters['manufacturer']}} onFilterChanged={onFilterChanged} />
                                </div>
                                <div className="widget pb-4 mb-4 border-bottom">
                                    <h3 className="widget-title">Цена</h3>
                                    <PriceFilter filter={{name: 'price', unit: 'руб', ...products.filters['price']}} onFilterChanged={onFilterChanged} />
                                </div>
                                <div className="widget">
                                    <div className="form-check">
                                        <input className="form-check-input" type="checkbox" id="sw-awailable-check" onChange={handleAvailableChange} />
                                        <label className="form-check-label" htmlFor="sw-awailable-check">Доступно к покупке</label>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </aside>

                    <section className="col-lg-8">
                        <div className="d-flex justify-content-center justify-content-sm-between align-items-center pt-2 pb-4 pb-sm-5">
                            <div className="d-flex pb-3">
                                { products.count > 0 && (
                                    <span className="text-light opacity-75 text-nowrap d-none d-md-block">
                                        { rupluralize(products.count, ['Найден','Найдены','Найдены']) }
                                        {' '}{ products.count }{' '}
                                        { rupluralize(products.count, ['товар','товара','товаров']) }
                                    </span>
                                )}
                            </div>
                            { products?.totalPages > 1 && (
                                <div className="d-flex pb-3">
                                    { products.currentPage > 1 && (
                                        <Link
                                            className="nav-link-style nav-link-light me-3"
                                            href={{ pathname: router.pathname, query: { ...router.query, page: products.currentPage - 1 } }}>
                                            <i className="ci-arrow-left" />
                                        </Link>
                                    )}
                                    <span className="fs-md text-light">{ products.currentPage } / { products.totalPages }</span>
                                    { products.currentPage < products.totalPages && (
                                        <Link
                                            className="nav-link-style nav-link-light ms-3"
                                            href={{ pathname: router.pathname, query: { ...router.query, page: products.currentPage + 1 } }}>
                                            <i className="ci-arrow-right" />
                                        </Link>
                                    )}
                                </div>
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
                                <nav className="d-flex justify-content-between pt-2" aria-label="Переключение страниц">
                                    { products.currentPage > 1 && (
                                    <ul className="pagination">
                                        <li className="page-item">
                                            <Link className="page-link" href={{ pathname: router.pathname, query: { ...router.query, page: products.currentPage - 1 } }}>
                                                <i className="ci-arrow-left me-2" />
                                                Пред<span className="d-none d-sm-inline d-md-none d-xl-inline">ыдущая</span>
                                            </Link>
                                        </li>
                                    </ul>
                                    )}
                                    <ul className="pagination">
                                        <li className="page-item d-sm-none">
                                            <span className="page-link page-link-static">{ products.currentPage } / { products.totalPages }</span>
                                        </li>
                                        {Array(products.totalPages).fill().map((_, i) => i+1).map((page) => (
                                            page === products.currentPage ? (
                                                <li className="page-item active d-none d-sm-block" aria-current="page" key={page}>
                                                    <span className="page-link">{ page }<span className="visually-hidden">(текущая)</span></span>
                                                </li>
                                            ) : (page >= minPage && page <= maxPage || page === 1 || page === products.totalPages) ? (
                                                <React.Fragment key={page}>
                                                    { (maxPage < products.totalPages && page === products.totalPages) && (
                                                        <li className="page-item d-none d-md-block">&hellip;</li>
                                                    )}
                                                    <li className="page-item d-none d-sm-block">
                                                        <Link className="page-link" href={{ pathname: router.pathname, query: { ...router.query, page } }}>
                                                            { page }
                                                        </Link>
                                                    </li>
                                                    { (minPage > 1 && page === 1) && (
                                                        <li className="page-item d-none d-md-block">&hellip;</li>
                                                    )}
                                                </React.Fragment>
                                            ) : ( null )
                                        ))}
                                    </ul>
                                    { products.currentPage < products.totalPages && (
                                        <ul className="pagination">
                                            <li className="page-item">
                                                <Link className="page-link" href={{ pathname: router.pathname, query: { ...router.query, page: products.currentPage + 1 } }}>
                                                    След<span className="d-none d-sm-inline d-md-none d-xl-inline">ующая</span>
                                                    <i className="ci-arrow-right ms-2" />
                                                </Link>
                                            </li>
                                        </ul>
                                    )}
                                </nav>
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
