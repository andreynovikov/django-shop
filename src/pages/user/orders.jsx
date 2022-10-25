import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/router';
import Link from 'next/link';
import { useSession } from 'next-auth/react';
import { useQuery } from 'react-query';

import UserPageLayout from '@/components/layout/user-page';
import UserTopbar from '@/components/user/topbar';
import OrderStatusBadge from '@/components/order/status-badge';

import { withSession, orderKeys, loadOrders } from '@/lib/queries';

import moment from 'moment';
import 'moment/locale/ru';

moment.locale('ru');

export default function Orders({filter, page}) {
    const [currentFilter, setFilter] = useState(filter);
    const [minPage, setMinPage] = useState(0);
    const [maxPage, setMaxPage] = useState(0);
    const router = useRouter();
    const {data: session, status} = useSession();

    const { data: orders, isSuccess, isLoading, isError } = useQuery(
        orderKeys.list(page || 1, currentFilter),
        () => withSession(session, loadOrders, page || 1, currentFilter),
        {
            enabled: status === 'authenticated'
        }
    );

    useEffect(() => {
        if (isSuccess) {
            // количество переключателей страниц лимитировано дизайном
            const pageRange = orders.next && orders.previous ? 7 : 10;
            let min = orders.currentPage - pageRange + Math.min(4, orders.totalPages - orders.currentPage)
            if (min < 4)
                min = 1;
            let max = orders.currentPage + pageRange - Math.min(4, orders.currentPage - 1)
            if (max > orders.totalPages - 3)
                max = orders.totalPages;
            setMinPage(min);
            setMaxPage(max);
        }
    }, [orders, isSuccess]);

    const onFilterChanged = (value) => {
        if (+page > 1) {
            router.push({
                pathname: router.pathname,
                query: { ...router.query, page: 1 }
            });
        }
        setFilter(value);
    };

    const handleRowClick = (id) => {
        router.push({
            pathname: '/user/orders/[id]',
            query: { id }
        });
    };

    return (
        <>
            <UserTopbar>
                <div className="d-flex align-items-center flex-nowrap me-3 me-sm-4">
                    { isSuccess && (orders.results.length > 0 || filter !== '') && (
                        <>
                            <label className="text-light opacity-75 text-nowrap fs-sm me-2 d-none d-sm-block" htmlFor="sw-order-filter">Отображать:</label>
                            <select className="form-select" id="sw-order-filter" value={filter} onChange={(e) => onFilterChanged(e.target.value)}>
                                <option value="">Все</option>
                                <option value="active">Активные</option>
                                <option value="done">Выполненные</option>
                                <option value="canceled">Отмененные</option>
                            </select>
                        </>
                    )}
                </div>
            </UserTopbar>

            { isSuccess && orders.results.length > 0 ? (
                <>
                    <div className="table-responsive fs-md">
                        <table className="table table-hover mb-0">
                            <thead>
                                <tr>
                                    <th><span className="d-none d-sm-inline">Заказ </span>№</th>
                                    <th>Дата<span className="d-none d-sm-inline"> оформления</span></th>
                                    <th>Статус</th>
                                    <th className="d-none d-sm-block">Сумма</th>
                                </tr>
                            </thead>
                            <tbody>
                                { orders.results.map((order, index) => (
                                    <tr key={order.id} onClick={() => handleRowClick(order.id)} style={{cursor: "pointer"}}>
                                        <td className="py-3">
                                            <Link href={{ pathname: '/user/orders/[id]', query: { id: order.id } }}>
                                                <a className="nav-link-style fw-medium fs-sm">{ order.id }</a>
                                            </Link>
                                        </td>
                                        <td className="py-3">{ moment(order.created).format('LLL') }</td>
                                        <td className="py-3"><OrderStatusBadge status={order.status} text={order.status_text} /></td>
                                        <td className="d-none d-sm-block py-3">{ order.total.toLocaleString('ru') }<small>&nbsp;руб</small></td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                    { orders.totalPages > 1 && (
                        <nav className="d-flex justify-content-between pt-2" aria-label="Переключение страниц">
                            { orders.currentPage > 1 && (
                                <ul className="pagination">
                                    <li className="page-item">
                                        <Link href={{ pathname: router.pathname, query: { ...router.query, page: orders.currentPage - 1 } }}>
                                            <a className="page-link">
                                                <i className="ci-arrow-left me-2" />
                                                Пред<span className="d-none d-sm-inline d-md-none d-xl-inline">ыдущая</span>
                                            </a>
                                        </Link>
                                    </li>
                                </ul>
                            )}
                            <ul className="pagination">
                                <li className="page-item d-sm-none">
                                    <span className="page-link page-link-static">{ orders.currentPage } / { orders.totalPages }</span>
                                </li>
                                {Array(orders.totalPages).fill().map((_, i) => i+1).map((page) => (
                                    page === orders.currentPage ? (
                                        <li className="page-item active d-none d-sm-block" aria-current="page" key={page}>
                                            <span className="page-link">{ page }<span className="visually-hidden">(текущая)</span></span>
                                        </li>
                                    ) : (page >= minPage && page <= maxPage || page === 1 || page === orders.totalPages) ? (
                                        <React.Fragment key={page}>
                                            { (maxPage < orders.totalPages && page === orders.totalPages) && (
                                                <li className="page-item d-none d-md-block">&hellip;</li>
                                            )}
                                            <li className="page-item d-none d-sm-block">
                                                <Link href={{ pathname: router.pathname, query: { ...router.query, page } }}>
                                                    <a className="page-link">{ page }</a>
                                                </Link>
                                            </li>
                                            { (minPage > 1 && page === 1) && (
                                                <li className="page-item d-none d-md-block">&hellip;</li>
                                            )}
                                        </React.Fragment>
                                    ) : ( null )
                                ))}
                            </ul>
                            { orders.currentPage < orders.totalPages && (
                                <ul className="pagination">
                                    <li className="page-item">
                                        <Link href={{ pathname: router.pathname, query: { ...router.query, page: orders.currentPage + 1 } }}>
                                            <a className="page-link">
                                                След<span className="d-none d-sm-inline d-md-none d-xl-inline">ующая</span>
                                                <i className="ci-arrow-right ms-2" />
                                            </a>
                                        </Link>
                                    </li>
                                </ul>
                            )}
                        </nav>
                    )}
                </>
            ) : isLoading ? (
                <p className="lead">Загружается...</p>
            ) : (
                <p className="lead">У вас нет {
                    filter === 'active' ? "активных"
                        : filter === 'done' ? "выполненных"
                        : filter === 'canceled' ? "отменённых"
                        : "оформленных"
                } заказов</p>
            )}
        </>
    )
}

Orders.getLayout = function getLayout(page) {
    return (
        <UserPageLayout title="Список заказов">
            {page}
        </UserPageLayout>
    )
}

export async function getServerSideProps(context) {
    return {
        props: context.query || {}
    }
}
