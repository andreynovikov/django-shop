import { useState, useEffect } from 'react';
import { useRouter } from 'next/router';
import Link from 'next/link';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';

import Layout from '@/components/layout';
import NoImage from '@/components/product/no-image';
import { STATUS_NEW } from '@/components/order/status-badge';

import { useSession } from '@/lib/session';
import { basketKeys, orderKeys, loadOrder, updateOrder } from '@/lib/queries';

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

    const queryClient = useQueryClient();

    const updateOrderMutation = useMutation({
        mutationFn: (formData) => updateOrder(order.id, formData),
        onSuccess: () => {
            queryClient.invalidateQueries(orderKeys.details(order.id));
        }
    });

    useEffect(() => {
        // we do it here otherwise cart page flickers on order registration
        queryClient.invalidateQueries(basketKeys.all);
    }, []);

    useEffect(() => {
        if (status !== 'authenticated')
            return; // wait for authentication

        if (orderId === 0) {
            const id = sessionStorage.getItem('lastOrder');
            if (+id > 0) {
                setOrderId(id);
            } else { // we know nothing about last order
                router.push({pathname: '/user/orders'});
            }
        }
        /* eslint-disable react-hooks/exhaustive-deps */
    }, [status, orderId]);

    const { data: order, isSuccess, isFetching, isError } = useQuery({
        queryKey: orderKeys.detail(orderId),
        queryFn: () => loadOrder(orderId),
        enabled: orderId > 0,
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
    };

    if (!isSuccess)
        return (
            <section className="col-lg-8">
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
                { (updated || order.status !== STATUS_NEW) ? (
                    <>
                        <h2>Спасибо за заказ!</h2>
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
                        <div className="text-start">
                            <button type="submit" className="btn btn-primary btn-lg">Оформить заказ</button>
                        </div>
                    </form>
                )}
            </section>
            <aside className="col-lg-4 pt-4 pt-lg-0 ps-xl-5">
                <div className="bg-white rounded-3 shadow-lg p-4 ms-lg-auto">
                    <div className="py-2 px-xl-2">
                        <div className="mb-3">
                            <h4 className="text-center mb-3">Детали заказа</h4>
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
                                            <NoImage className="d-inline-block text-muted" size={64} />
                                        )}
                                    </Link>
                                    <div className="ps-2">
                                        <h6>
                                            <Link href={{ pathname: '/products/[code]', query: { code: item.product.code }}}>
                                                { item.product.title }
                                            </Link>
                                        </h6>
                                        <div>
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
        <Layout title="Оформление заказа" hideTitleBorder>
            <div className="row">
                {page}
            </div>
        </Layout>
    )
}
