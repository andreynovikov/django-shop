import { useState, useEffect } from 'react';
import { useRouter } from 'next/router';
import Link from 'next/link';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';

import PageLayout from '@/components/layout/page';
import NoImage from '@/components/product/no-image';
import { STATUS_NEW } from '@/components/order/status-badge';

import useBasket from '@/lib/basket';
import { useSession } from '@/lib/session';
import { basketKeys, orderKeys, createOrder, loadOrder, updateOrder } from '@/lib/queries';

export default function Confirmation() {
    const [orderId, setOrderId] = useState(0);
    const [orderStatus, setOrderStatus] = useState(STATUS_NEW);
    const [updated, setUpdated] = useState(false);

    const router = useRouter();

    const { user, status } = useSession({
        onUnauthenticated() {
            router.push('/cart');
        }
    });

    const { isEmpty, isLoading } = useBasket();

    const queryClient = useQueryClient();

    const createOrderMutation = useMutation({
        mutationFn: () => createOrder(),
        onSuccess: (data) => {
            queryClient.invalidateQueries({queryKey: basketKeys.all});
            queryClient.invalidateQueries({queryKey: orderKeys.lists()});
            queryClient.setQueryData(orderKeys.detail(data.id), data);
        }
    });

    const updateOrderMutation = useMutation({
        mutationFn: (formData) => updateOrder(order.id, formData),
        onSuccess: () => {
            queryClient.invalidateQueries({queryKey: orderKeys.details(order.id)});
        }
    });

    useEffect(() => {
        if (isLoading || status !== 'authenticated')
            return; // wait for basket and authentication

        if (!isEmpty && orderId === 0) { // register new order
            console.log("create order");
            createOrderMutation.mutate(undefined, {
                onSuccess: (data) => {
                    console.error("success");
                    console.error(data);
                    sessionStorage.setItem('lastOrder', data.id);
                    setOrderId(data.id);
                },
                onError: (error) => {
                    console.error(error);
                }
            });
        } else {
            if (orderId === 0) {
                const id = sessionStorage.getItem('lastOrder');
                if (+id > 0) { // page was reloaded
                    setOrderId(id);
                } else { // we know nothing about last order
                    router.push({pathname: '/user/orders'});
                }
            }
        }
        /* eslint-disable react-hooks/exhaustive-deps */
    }, [isLoading, isEmpty, status, orderId]);

    const { data: order, isSuccess, isFetching, isError } = useQuery({
        queryKey: orderKeys.detail(orderId),
        queryFn: () => loadOrder(orderId),
        enabled: orderId > 0 && status === 'authenticated',
        refetchInterval: orderStatus === STATUS_NEW ? 60 * 1000 : false // check for updates every minute
    });

    useEffect(() => {
        if (order)
            setOrderStatus(order.status);
    }, [order]);

    const handleSubmit = (e) => {
        e.preventDefault();
        e.stopPropagation();

        const formData = Object.fromEntries(new FormData(e.target).entries());
        updateOrderMutation.mutate(formData, {
            onSuccess: () => {
                setUpdated(true);
            },
            onError: (error) => {
                console.error(error);
            }
        });
    }

    if (!isSuccess)
        return (
            <section className="col-lg-8">
                <div className="d-flex justify-content-between align-items-center pt-3 pb-2 pb-sm-5 mt-1">
                    <h2 className="h6 text-light mb-0">
                        { isFetching ? "Загружается..." : "" }
                    </h2>
                </div>
                { isFetching ? (
                    <div className="spinner-border" style={{width: "5rem", height: "5rem"}} role="status">
                        <span className="visually-hidden">Загружается...</span>
                    </div>
                ) : isError ? (
                    <div className="lead">Что-то пошло не так...</div>
                ) : (
                    null
                )}
            </section>
        );

    return (
        <>
            <section className="col-lg-8">
                <div className="d-flex justify-content-between align-items-center pt-3 pb-2 pb-sm-5 mt-1">
                    <h2 className="h1 text-light mb-0">№{ order.id }</h2>
                </div>

                { (updated || order.status !== STATUS_NEW) ? (
                    <>
                        <h3>Спасибо за заказ!</h3>
                        <p>
                            Регистрационный номер Вашего заказа: <b>{ order.id }</b>.
                        </p>
                        <p>
                            Наш менеджер свяжется с Вами, уточнит состав заказа, согласует способ оплаты,
                            стоимость и способ доставки, и договорится об удобном времени доставки.
                        </p>
                        <p>
                            Узнать о состоянии заказа Вы можете по ссылке{" "}
                            <Link href="/user/orders?track">
                                &laquo;Отслеживание заказа&raquo;
                            </Link>
                            {" "}вверху страницы.
                        </p>
                    </>
                ) : (
                    <form onSubmit={handleSubmit}>
                        <div className="mb-3">
                            <label className="form-label" htmlFor="order-name-input">Фамилия Имя Отчество:</label>
                            <input type="text" name="name" className="form-control form-control-lg" id="order-name-input" defaultValue={ order.name || user.name } autoComplete="name" />
                        </div>
                        <div className="mb-3">
                            <label className="form-label" htmlFor="order-email-input">E-mail для уведомлений:</label>
                            <input type="text" name="email" className="form-control form-control-lg" id="order-email-input" defaultValue={ order.email || user.email } autoComplete="email" />
                        </div>
                        <div className="mb-3">
                            <label className="form-label" htmlFor="order-address-input">Адрес доставки:</label>
                            <input type="text" name="address" className="form-control form-control-lg" id="order-address-input"
                                   defaultValue={ order.address || user.address } autoComplete="postal-code address-level2 street-address" />
                        </div>
                        <div className="mb-3">
                            <label className="form-label" htmlFor="order-comment-input">Комментарии к заказу:</label>
                            <textarea name="comment" className="form-control form-control-lg" id="order-comment-input" defaultValue={ order.comment } rows="3"></textarea>
                        </div>
                        <hr className="mt-4 mb-3" />
                        <div className="text-end">
                            <button type="submit" className="btn btn-primary btn-lg"><i className="ci-basket-alt fs-lg me-2" />Оформить заказ</button>
                        </div>
                    </form>
                )}
            </section>
            <aside className="col-lg-4 pt-4 pt-lg-0 ps-xl-5">
                <div className="bg-white rounded-3 shadow-lg p-4 ms-lg-auto">
                    <div className="py-2 px-xl-2">
                        <div className="widget mb-3">
                            <h2 className="widget-title text-center">Детали заказа</h2>
                            {order.items.map((item, index) => (
                                <div className={"d-flex align-items-center border-bottom " + (index === 0 ? "pb-3" : "py-3")} key={item.product.id}>
                                    <Link className="d-block flex-shrink-0" href={{ pathname: '/products/[code]', query: { code: item.product.code }}}>
                                        { item.product.thumbnail_small ? (
                                            <img
                                                src={item.product.thumbnail_small.url}
                                                width={item.product.thumbnail_small.width}
                                                height={item.product.thumbnail_small.height}
                                                alt={`${item.product.title} ${item.product.whatis}`} />
                                        ) : (
                                            <NoImage size={64} />
                                        )}
                                    </Link>
                                    <div className="ps-2">
                                        <h6 className="widget-product-title">
                                            <Link href={{ pathname: '/products/[code]', query: { code: item.product.code }}}>
                                                { item.product.title }
                                            </Link>
                                        </h6>
                                        <div className="widget-product-meta">
                                            <span className="text-accent me-2">{ item.cost.toLocaleString('ru') }<small>&nbsp;руб</small></span>
                                            <span className="text-muted">x { item.quantity }</span>
                                        </div>
                                    </div>
                                </div>
                            ))}
                        </div>
                        <h3 className="fw-normal text-center my-4">
                            { order.total.toLocaleString('ru') }<small>&nbsp;руб</small>
                        </h3>
                    </div>
                </div>
            </aside>
        </>
    )
}

Confirmation.getLayout = function getLayout(page) {
    return (
        <PageLayout title="Оформление заказа" dark overlapped hideCartNotice>
            <div className="container pb-5 mb-2 mb-md-4">
                <div className="row">
                    {page}
                </div>
            </div>
        </PageLayout>
    )
}
