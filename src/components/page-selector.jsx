import { Fragment, useMemo } from 'react';
import { useRouter } from 'next/router';
import Link from 'next/link';

export function SmallPageSelector({path, totalPages, currentPage}) {
    const router = useRouter();

    const getQuery = (page) => path !== undefined ? { path: [...path, page] } : { ...router.query, page };

    return (
        <div className="d-flex pb-3">
            { currentPage > 1 && (
                <Link className="nav-link-style nav-link-light me-3" href={{ pathname: router.pathname, query: getQuery(currentPage - 1) }}>
                    <i className="ci-arrow-left" />
                </Link>
            )}
            <span className="fs-md text-light">{ currentPage } / { totalPages }</span>
            { currentPage < totalPages && (
                <Link className="nav-link-style nav-link-light ms-3" href={{ pathname: router.pathname, query: getQuery(currentPage + 1) }}>
                    <i className="ci-arrow-right" />
                </Link>
            )}
        </div>
    );
}

export default function PageSelector({path, totalPages, currentPage}) {
    const router = useRouter();

    const {minPage, maxPage} = useMemo(() => {
        // количество переключателей страниц лимитировано дизайном
        const pageRange = currentPage > 1 && currentPage < totalPages ? 7 : 10;
        let minPage = currentPage - pageRange + Math.min(4, totalPages - currentPage)
        if (minPage < 4)
            minPage = 1;
        let maxPage = currentPage + pageRange - Math.min(4, currentPage - 1)
        if (maxPage > totalPages - 3)
            maxPage = totalPages;
        return {minPage, maxPage};
    }, [totalPages, currentPage]);

    const getQuery = (page) => path !== undefined ? { path: [...path, page] } : { ...router.query, page };

    return (
        <nav className="d-flex justify-content-between pt-2" aria-label="Переключение страниц">
            { currentPage > 1 && (
                <ul className="pagination">
                    <li className="page-item">
                        <Link className="page-link" href={{ pathname: router.pathname, query: getQuery(currentPage - 1) }}>
                            <i className="ci-arrow-left me-2" />
                            Пред<span className="d-none d-sm-inline d-md-none d-xl-inline">ыдущая</span>
                        </Link>
                    </li>
                </ul>
            )}
            <ul className="pagination">
                <li className="page-item d-sm-none">
                    <span className="page-link page-link-static">{ currentPage } / { totalPages }</span>
                </li>
                {Array(totalPages).fill().map((_, i) => i+1).map((page) => (
                    page === currentPage ? (
                        <li className="page-item active d-none d-sm-block" aria-current="page" key={page}>
                            <span className="page-link">{ page }<span className="visually-hidden">(текущая)</span></span>
                        </li>
                    ) : (page >= minPage && page <= maxPage || page === 1 || page === totalPages) ? (
                        <Fragment key={page}>
                            { (maxPage < totalPages && page === totalPages) && (
                                <li className="page-item d-none d-md-block">&hellip;</li>
                            )}
                            <li className="page-item d-none d-sm-block">
                                <Link className="page-link" href={{ pathname: router.pathname, query: getQuery(page) }}>
                                    { page }
                                </Link>
                            </li>
                            { (minPage > 1 && page === 1) && (
                                <li className="page-item d-none d-md-block">&hellip;</li>
                            )}
                        </Fragment>
                    ) : ( null )
                ))}
            </ul>
            { currentPage < totalPages && (
                <ul className="pagination">
                    <li className="page-item">
                        <Link className="page-link" href={{ pathname: router.pathname, query: getQuery(currentPage + 1) }}>
                            След<span className="d-none d-sm-inline d-md-none d-xl-inline">ующая</span>
                            <i className="ci-arrow-right ms-2" />
                        </Link>
                    </li>
                </ul>
            )}
        </nav>
    )
}
