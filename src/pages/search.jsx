import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/router';
import Link from 'next/link';
import { useQuery } from '@tanstack/react-query';

import { IconChevronCompactLeft, IconChevronCompactRight } from '@tabler/icons-react';

import Layout from '@/components/layout';
import ProductCard from '@/components/product/card';

import { productKeys, loadProducts } from '@/lib/queries';
import rupluralize from '@/lib/rupluralize';

export default function Search({text, page}) {
    const router = useRouter();
    //const [currentFilters, setFilter] = useReducer(filterReducer, [{field: 'text', value: text}]);
    const [minPage, setMinPage] = useState(0);
    const [maxPage, setMaxPage] = useState(0);

    const currentFilters = [{field: 'text', value: text}];

    const { data: products, isSuccess, isLoading, isError } = useQuery({
        queryKey: productKeys.list(page || 1, 24, currentFilters, null),
        queryFn: () => loadProducts(page || 1, 24, currentFilters, null),
        keepPreviousData : true // required for filters not to loose choices and attributes
    });

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

    if (isSuccess) {
        return (
            <>
                <div className="container pb-3">
                    <div className="d-flex justify-content-between align-items-center">
                        <div>
                            { products.count > 0 && (
                                <span className="text-nowrap">
                                    { rupluralize(products.count, ['Найден','Найдены','Найдены']) }
                                    {' '}{ products.count }{' '}
                                    { rupluralize(products.count, ['товар','товара','товаров']) }
                                </span>
                            )}
                        </div>
                        { products?.totalPages > 1 && (
                            <div className="d-flex">
                                { products.currentPage > 1 && (
                                    <Link className="me-3" href={{ pathname: router.pathname, query: { ...router.query, page: products.currentPage - 1 } }}>
                                        <IconChevronCompactLeft size={20} stroke={1.5} />
                                    </Link>
                                )}
                                <span className="fs-md">{ products.currentPage } / { products.totalPages }</span>
                                { products.currentPage < products.totalPages && (
                                    <Link className="ms-3" href={{ pathname: router.pathname, query: { ...router.query, page: products.currentPage + 1 } }}>
                                        <IconChevronCompactRight size={20} stroke={1.5} />
                                    </Link>
                                )}
                            </div>
                        )}
                    </div>
                </div>

                { products.count > 0 ? (
                    <div className="d-flex flex-wrap justify-content-between py-2" style={{gap: "20px"}}>
                        { products.results.map((product) => (
                            <ProductCard product={product} key={product.id} />
                        ))}
                    </div>
                ) : (
                    <div className="lead my-4">Ничего не найдено</div>
                )}

                { products.totalPages > 1 && (
                    <>
                        <hr className="my-3" />
                        <nav className="d-flex justify-content-between pt-2" aria-label="Переключение страниц">
                            { products.currentPage > 1 && (
                                <ul className="pagination">
                                    <li className="page-item">
                                        <Link className="page-link" href={{ pathname: router.pathname, query: { ...router.query, page: products.currentPage - 1 } }}>
                                            <IconChevronCompactLeft size={20} stroke={1.5} className="me-2 align-text-bottom" />
                                            Пред<span className="d-none d-sm-inline d-md-none d-xl-inline">ыдущая</span>
                                        </Link>
                                    </li>
                                </ul>
                            )}
                            <ul className="pagination d-sm-none">
                                <li className="page-item">
                                    <span className="page-link page-link-static">{ products.currentPage } / { products.totalPages }</span>
                                </li>
                            </ul>
                            <ul className="pagination d-none d-sm-flex">
                                {Array(products.totalPages).fill().map((_, i) => i+1).map((page) => (
                                    page === products.currentPage ? (
                                        <li className="page-item active" aria-current="page" key={page}>
                                            <span className="page-link">{ page }<span className="visually-hidden">(текущая)</span></span>
                                        </li>
                                    ) : (page >= minPage && page <= maxPage || page === 1 || page === products.totalPages) ? (
                                        <React.Fragment key={page}>
                                            { (maxPage < products.totalPages && page === products.totalPages) && (
                                                <li className="page-item d-none d-md-block">
                                                    <span className="page-link page-link-static">&hellip;</span>
                                                </li>
                                            )}
                                            <li className="page-item">
                                                <Link className="page-link" href={{ pathname: router.pathname, query: { ...router.query, page } }}>
                                                    { page }
                                                </Link>
                                            </li>
                                            { (minPage > 1 && page === 1) && (
                                                <li className="page-item d-none d-md-block">
                                                    <span className="page-link page-link-static">&hellip;</span>
                                                </li>
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
                                            <IconChevronCompactRight size={20} stroke={1.5} className="ms-2 align-text-bottom" />
                                        </Link>
                                    </li>
                                </ul>
                            )}
                        </nav>
                    </>
                )}
            </>
        );
    }

    if (isLoading) {
        return (
            <div className="container pb-5 mb-2 mb-md-4">
                <div className="d-flex align-items-center pt-2 pb-5">
                    <div className="spinner-border" role="status"></div>
                    <div className="lead ms-3">Загружается...</div>
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
        <Layout title={"Поиск товаров: " + page.props.text}>
            {page}
        </Layout>
    )
}

export async function getServerSideProps(context) {
    return {
        props: context.query || {}
    }
}
