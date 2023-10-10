import { useState, useEffect, useMemo } from 'react';
import { useRouter } from 'next/router';
import Link from 'next/link';
import Script from 'next/script';
import { useQuery } from 'react-query';

import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faBell } from '@fortawesome/free-regular-svg-icons';

import { useSite } from '@/lib/site';
import { useSession } from '@/lib/session';
import { apiClient, orderKeys, loadOrder } from '@/lib/queries';
import { formatPhone } from '@/lib/format';

import NoImage from '@/components/product/no-image';
import UserPageLayout from '@/components/layout/user-page';
import OrderStatusBadge from '@/components/order/status-badge';
import {
    STATUS_NEW,
    STATUS_ACCEPTED,
    STATUS_COLLECTING,
    STATUS_FROZEN,
    STATUS_COLLECTED,
    STATUS_DELIVERED_STORE,
    DELIVERY_COURIER,
    DELIVERY_CONSULTANT,
    DELIVERY_SELF,
    DELIVERY_YANDEX,
    DELIVERY_TRANSPORT,
    DELIVERY_PICKPOINT,
    DELIVERY_UNKNOWN,
    PAYMENT_CARD,
    PAYMENT_CREDIT,
    PAYMENT_TRANSFER,
    PAYMENT_UNKNOWN
} from '@/components/order/status-badge';

import moment from 'moment';
import 'moment/locale/ru';

moment.locale('ru');

export default function Order({id}) {
    const [orderStatus, setOrderStatus] = useState(STATUS_NEW);
    const { site } = useSite();
    const { status } = useSession();

    const router = useRouter();

    const { data: order, isSuccess } = useQuery(
        orderKeys.detail(id),
        () => loadOrder(id),
        {
            enabled: status === 'authenticated',
            refetchInterval: [STATUS_NEW, STATUS_ACCEPTED].includes(orderStatus) ? 60 * 1000 : false // check for updates every minute
        }
    );

    useEffect(() => {
        if (order)
            setOrderStatus(order.status);
    }, [order]);

    const created = useMemo(() =>
        {
            if (isSuccess) {
                const c = moment(order.created);
                const n = moment();  // TODO: test time zones
                const d = n.diff(c, 'days');
                if (d < 3)
                    return c.calendar(n);
                else if (d < 7)
                    return c.format('D MMMM, HH:mm');
                else
                    return c.format('LL');
            } else {
                return null;
            }
        },
        [isSuccess, order]
    );

    const initializeBootstrap = () => {
        if (window && 'bootstrap' in window && bootstrap.Tooltip) {
            return new bootstrap.Tooltip(document.querySelector('.sw-order-created'));
        }
    };

    const handlePayment = () => {
        apiClient.post(`orders/${id}/pay/`, {
            'return_url': process.env.NEXT_PUBLIC_ORIGIN.slice(0, -1) + router.asPath
        }, {
            maxRedirects: 0 // maxRedirects does not work so API returns JSON with location
        }).then(function (response) {
            window.location = response.data.location;
        }).catch(function (error) {
            // handle error
            console.log(error);
        })
    };

    if (!isSuccess)
        return (
            <div>Loading...</div>
        )

    return (
        <>
            <Script id="bootstrap" src="/js/bootstrap.bundle.js" onReady={initializeBootstrap} onLoad={initializeBootstrap} />
            <div className="d-flex justify-content-between w-100 text-center mb-3">
                <div className="fs-ms px-3">
                    <div className="fw-medium mb-1">Дата оформления</div>
                    <div className="fs-lg text-muted sw-order-created" title={ moment(order.created).format('LLL') } data-bs-toggle="tooltip" data-bs-placement="bottom">{ created }</div>
                </div>
                <div className="fs-ms px-3">
                    <div className="fw-medium mb-1">Статус</div>
                    <div className="fs-lg text-muted"><OrderStatusBadge status={order.status} text={order.status_text} /></div>
                </div>
                <div className="fs-ms px-3">
                    <div className="fw-medium mb-1">{ order.paid ? "Стоимость заказа" : "Всего к оплате" }</div>
                    <div className="fs-lg text-muted">{ order.total.toLocaleString('ru') }<small>&nbsp;руб</small></div>
                </div>
            </div>
            { /* Order details (visible on mobile) */ }
            <div className="d-flex d-lg-none flex-wrap bg-secondary text-center rounded-3 pt-4 px-4 pb-1 mb-4">
                <div className="fs-sm px-3 pb-3">
                    <div className="fw-medium">Дата оформления</div>
                    <div className="fs-lg text-muted">{ created }</div>
                </div>
                <div className="fs-sm px-3 pb-3">
                    <div className="fw-medium">Статус</div>
                    <div className="fs-lg text-muted"><OrderStatusBadge status={order.status} text={order.status_text} /></div>
                </div>
                <div className="fs-sm px-3 pb-3">
                    <div className="fw-medium">Всего к оплате</div>
                    <div className="fs-lg text-muted">{ order.total.toLocaleString('ru') }<small>&nbsp;руб</small></div>
                </div>
            </div>

            <div className="bg-white rounded-3 px-4 pt-4 pb-2 mb-4">
                <div className="row">
                    <div className="col-sm-6">
                        <h4 className="h6">Информация о доставке:</h4>
                        <ul className="list-unstyled fs-sm">
                            { order.delivery_price > 0 && (
                                <li>
                                    <span className="text-muted">Стоимость доставки:</span>
                                    {" "}{ order.delivery_price }<small>&nbsp;руб</small>
                                </li>
                            )}
                            { order.delivery === DELIVERY_UNKNOWN && (
                                <li>Способ доставки уточняется</li>
                            )}
                            { order.delivery === DELIVERY_SELF && (
                                <li>
                                    <span className="text-muted">Магазин самовывоза:</span>
                                    {" "}
                                    { order.store ? (
                                        <>
                                            <a className="text-heading" href="order.store.id"><u>{ order.store.city.name }, { order.store.address }</u></a>
                                            { order.store.hours && (
                                                <> (часы работы: { order.store.hours })</>
                                            )}
                                        </>
                                    ) : (
                                        <>уточняется</>
                                    )}
                                </li>
                            )}
                            { order.delivery === DELIVERY_YANDEX && (
                                <>
                                    <li>
                                        <span className="text-muted">Доставка службой доставки по адресу:</span>
                                        {" "}{ order.address }
                                    </li>
                                    { order.status === STATUS_DELIVERED_STORE && (
                                        <li>Заказ передан в службу доставки</li>
                                    )}
                                </>
                            )}
                            { (order.delivery === DELIVERY_COURIER || order.delivery === DELIVERY_CONSULTANT) && (
                                <li>
                                    <span className="text-muted">Доставка курьером по адресу:</span>
                                    {" "}{ order.address }
                                </li>
                            )}
                            { (order.delivery === DELIVERY_TRANSPORT || order.delivery === DELIVERY_PICKPOINT) && (
                                <>
                                    <li>
                                        <span className="text-muted">Доставка транспортной компанией по адресу:</span>
                                        {" "}{ order.address }
                                    </li>
                                    { order.delivery_tracking_number && (
                                        <li>
                                            <span className="text-muted">Трек-код:</span>
                                            {" "}{ order.delivery_tracking_number }
                                        </li>
                                    )}
                                </>
                            )}
                            { order.delivery_info && (
                                <li style={{whiteSpace: "pre-line"}}>{ order.delivery_info }</li>
                            )}
                            { order.delivery_dispatch_date && (
                                <li>
                                    <span className="text-muted">Дата отправки:</span>
                                    {" "}{ moment(order.delivery_dispatch_date).format('D MMMM') }
                                </li>
                            )}
                            { order.delivery_handing_date && (
                                (order.delivery === DELIVERY_COURIER || order.delivery === DELIVERY_CONSULTANT) ? (
                                    <li>
                                        <span className="text-muted">Дата доставки:</span>
                                        {" "}{ moment(order.delivery_handing_date).format('D MMMM') }
                                        { order.delivery_time_from && <> с { moment(order.delivery_time_from, moment.HTML5_FMT.TIME_SECONDS).format('HH:mm') }</>}
                                        { order.delivery_time_till && <> до { moment(order.delivery_time_till, moment.HTML5_FMT.TIME_SECONDS).format('HH:mm') }</>}
                                    </li>
                                ) : order.delivery == DELIVERY_SELF ? (
                                    <li>
                                        <span className="text-muted">Дата получения:</span>
                                        {" "}{ moment(order.delivery_handing_date).format('D MMMM') }
                                        { order.delivery_time_from && <> после { moment(order.delivery_time_from, moment.HTML5_FMT.TIME_SECONDS).format('HH:mm') }</>}
                                    </li>
                                ) : (
                                    <li>
                                        <span className="text-muted">Расчётная дата получения:</span>
                                        {" "}{ moment(order.delivery_handing_date).format('D MMMM') }
                                    </li>
                                )
                            )}
                        </ul>
                    </div>
                    <div className="col-sm-6">
                        <h4 className="h6">Оплата заказа:</h4>
                        <ul className="list-unstyled fs-sm">
                            { order.payment === PAYMENT_UNKNOWN ? (
                                <li>Способ оплаты уточняется</li>
                            ) : (
                                <>
                                    <li><span className="text-muted">Способ оплаты:</span> { order.payment_text }</li>
                                    { order.paid ? (
                                        <li><span className="text-muted">Статус:</span> оплачен</li>
                                    ) : (
                                        order.status === STATUS_COLLECTED ? (
                                            order.payment === PAYMENT_CARD || order.payment === PAYMENT_CREDIT ? (
                                                <li>
                                                    <button type="button" className="btn btn-sm btn-primary mt-2" onClick={handlePayment}>
                                                        { order.payment === PAYMENT_CREDIT ? (
                                                            <>
                                                                Оформить кредит
                                                            </>
                                                        ) : (
                                                            <>
                                                                Оплатить заказ
                                                            </>
                                                        )}
                                                    </button>
                                                </li>
                                            ) : order.payment === PAYMENT_TRANSFER ? (
                                                <li>
                                                    { /* TODO: external link */ }
                                                    <a href="'shop:order_document' order.id 'bill'" target="_blank">
                                                        <i className="ci-clip me-1" />Скачать счёт для оплаты в любом банке
                                                    </a>
                                                </li>
                                            ) : (
                                                null
                                            )
                                        ) : (
                                            (order.payment === PAYMENT_CARD || order.payment === PAYMENT_CREDIT || order.payment === PAYMENT_TRANSFER) && (
                                                <li>
                                                    <div className="alert alert-accent d-flex mt-3" role="alert">
                                                        <div className="alert-icon"><i className="ci-announcement" /></div>
                                                        <div>
                                                            <div className="mb-2">Возможность оплатить заказ онлайн или распечатать счёт
                                                            появится тут после согласования и завершения комплектования заказа.</div>
                                                            <div>Вы получите сообщение об этом. Пожалуйста, посетите эту страницу позже.</div>
                                                        </div>
                                                    </div>
                                                </li>
                                            )
                                        )
                                    )}
                                </>
                            )}
                        </ul>
                    </div>
                    { order.is_firm && (
                        <div className="col-sm-6">
                            <h4 className="h6">Получатель:</h4>
                            <ul className="list-unstyled fs-sm">
                                <li><span className="text-muted">Название организации:</span> { order.firm_name }</li>
                                <li><span className="text-muted">Юридический адрес:</span> { order.firm_address }</li>
                                <li><span className="text-muted">Сведения об организации:</span> { order.firm_details }</li>
                                <li><span className="text-muted">Контактное лицо:</span> { order.name }</li>
                                <li><span className="text-muted">Телефон:</span>&nbsp;{ formatPhone(order.phone) }</li>
                            </ul>
                        </div>
                    )}
                </div>
            </div>
            {order.items.map((item, index) => (
                <div className={"d-sm-flex justify-content-between pb-3 pb-sm-2 " + (index === 0 ? "mb-3" : "my-3") + (!(index === order.items.length - 1) && " border-bottom")} key={item.product.id}>
                    <div className="d-sm-flex text-center text-sm-start">
                        <Link className="d-inline-block flex-shrink-0 mx-auto" style={{width: "10rem"}} href={{ pathname: '/products/[code]', query: { code: item.product.code }}}>
                            { item.product.thumbnail ? (
                                <img
                                    src={item.product.thumbnail.url}
                                    width={item.product.thumbnail.width}
                                    height={item.product.thumbnail.height}
                                    alt={`${item.product.title} ${item.product.whatis}`} />
                            ) : (
                                <NoImage className="d-inline-block text-muted" />
                            )}
                        </Link>
                        <div className="ps-sm-4 pt-2">
                            <h3 className="fs-base mt-0 mb-2">
                                <Link href={{ pathname: '/products/[code]', query: { code: item.product.code }}}>
                                    { item.product.title }
                                </Link>
                            </h3>
                            { item.product.partnumber && (
                                <div className="fs-sm">
                                    <span className="text-muted me-2">Артикул:</span>{ item.product.partnumber }
                                </div>
                            )}
                            { item.product.article && (
                                <div className="fs-sm">
                                    <span className="text-muted me-2">Код товара:</span>{ item.product.article }
                                </div>
                            )}
                            <div className="fs-sm">
                                <span className="text-muted me-2">Цена:</span>{ item.product_price.toLocaleString('ru') }<small>&nbsp;руб</small>
                            </div>
                            { item.discount > 0 && (
                                <div className="fs-sm">
                                    <span className="text-muted me-2">Скидка:</span>{ item.discount_text }
                                </div>
                            )}
                            <div className="fs-lg text-accent pt-2">{ item.price.toLocaleString('ru') }<small>&nbsp;руб</small></div>
                        </div>
                    </div>
                    <div className="pt-2 ps-sm-3 mx-auto mx-sm-0 text-center" style={{maxWidth: "9rem"}}>
                        <div className="text-muted mb-2">Количество:</div>
                        { item.quantity }
                    </div>
                </div>
            ))}
            { site.phone && [STATUS_NEW, STATUS_ACCEPTED, STATUS_COLLECTING, STATUS_FROZEN, STATUS_COLLECTED].includes(order.status) && (
                <div className="alert alert-info d-flex align-items-center mt-5" role="alert">
                    <FontAwesomeIcon icon={faBell} className="me-3" />
                    <div>
                        Если Вы хотите внести изменения в заказ, позвоните по телефону{" "}
                        <a className="alert-link" href={"tel:" + site.phone} style={{whiteSpace: "nowrap"}}>{ formatPhone(site.phone) }</a>
                    </div>
                </div>
            )}
        </>
    )
}

Order.getLayout = function getLayout(page) {
    return (
        <UserPageLayout title={`Заказ №${page.props.id}`}>
            {page}
        </UserPageLayout>
    )
}

export async function getServerSideProps(context) {
    return {
        props: {
            id: context.params.id
        }
    };
}
