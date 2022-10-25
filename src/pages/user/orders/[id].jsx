import { useMemo } from 'react';
import Script from 'next/script';
import { useSession } from 'next-auth/react';
import { useQuery } from 'react-query';

import { withSession, orderKeys, loadOrder } from '@/lib/queries';
import { formatPhone } from '@/lib/format';

import UserPageLayout from '@/components/layout/user-page';
import UserTopbar from '@/components/user/topbar';
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
    PAYMENT_CASH,
    PAYMENT_CARD,
    PAYMENT_CREDIT,
    PAYMENT_TRANSFER,
    PAYMENT_UNKNOWN
} from '@/components/order/status-badge';

import moment from 'moment';
import 'moment/locale/ru';

moment.locale('ru');

export default function Order({id}) {
    const {data: session, status} = useSession();

    const { data: order, isSuccess, isLoading, isError } = useQuery(
        orderKeys.detail(id),
        () => withSession(session, loadOrder, id),
        {
            enabled: status === 'authenticated'
        }
    );

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

    if (!isSuccess)
        return (
            <div>Loading...</div>
        )

    return (
        <>
            <Script id="bootstrap" src="/js/bootstrap.bundle.js" onReady={initializeBootstrap} onLoad={initializeBootstrap} />
            <UserTopbar>
                <div className="d-flex w-100 text-light text-center me-3">
                    <div className="fs-ms px-3">
                        <div className="fw-medium">Дата оформления</div>
                        <div className="fs-lg opacity-60 sw-order-created" title={ moment(order.created).format('LLL') } data-bs-toggle="tooltip" data-bs-placement="bottom">{ created }</div>
                    </div>
                    <div className="fs-ms px-3">
                        <div className="fw-medium">Статус</div>
                        <div className="fs-lg"><OrderStatusBadge status={order.status} text={order.status_text} /></div>
                    </div>
                    <div className="fs-ms px-3">
                        <div className="fw-medium">{ order.paid ? "Стоимость заказа" : "Всего к оплате" }</div>
                        <div className="fs-lg opacity-60">{ order.total.toLocaleString('ru') }<small>&nbsp;руб</small></div>
                    </div>
                </div>
            </UserTopbar>
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

            <div className="bg-secondary rounded-3 px-4 pt-4 pb-2 mb-4">
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
                                        <>
                                            <li>Заказ передан в службу доставки</li>
                                            { /* TODO: fix widget */ }
                                            <li style={{width: "0px"}}>
                                                <meta name="ydWidgetData" id="f526c05f4e50090a3bffbb04d40e07b3" content="" data-sender_id="15938" data-weight="0" data-cost="0"
                                                      data-height="0" data-length="0" data-width="0" data-city_from="Москва" data-geo_id_from="213" data-css_name="tracking_tpl"
                                                      data-tpl_name="tracking_tpl" data-container_tag_id="f96bae27a7dbbcfc794595702bd9024d" data-resource_id="21272"
                                                      data-resource_key="1780931b94c77b42c08b895fb88747d2" data-tracking_method_key="43df8cf1b0d40baaef3a3363458314f1"
                                                      data-autocomplete_method_key="fd34c231b276f9bea3db9b60ac09506e"></meta>
                                                <script src="https://delivery.yandex.ru/widget/widgetJsLoader?dataTagID=f526c05f4e50090a3bffbb04d40e07b3" charSet="utf-8"></script>
                                                <msw id="f96bae27a7dbbcfc794595702bd9024d" className="yd-widget-container"></msw>
                                            </li>
                                        </>
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
                                                    { /* TODO: external link */ }
                                                    <a className="btn btn-primary" href="'yandex_kassa:payment'">
                                                        { order.payment === PAYMENT_CREDIT ? (
                                                            <>
                                                                <i className="ci-money-bag fs-lg me-2" />Оформить кредит
                                                            </>
                                                        ) : (
                                                            <>
                                                                <i className="ci-card fs-lg me-2" />Оплатить заказ
                                                            </>
                                                        )}
                                                    </a>
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
                        <a className="d-inline-block flex-shrink-0 mx-auto" href="{% url 'product' item.product.code %}" style={{width: "10rem"}}>
                            { item.product.thumbnail ? (
                                <img
                                    src={item.product.thumbnail.url}
                                    width={item.product.thumbnail.width}
                                    height={item.product.thumbnail.height}
                                    alt={`${item.product.title} ${item.product.whatis}`} />
                            ) : (
                                <i className="d-inline-block ci-camera text-muted" style={{width: "160px", height: "160px", fontSize: "80px", padding: "40px"}} />
                            )}
                        </a>
                        <div className="ps-sm-4 pt-2">
                            <h3 className="product-title fs-base mb-2">
                                <a href="item.product.code">{ item.product.title }</a>
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
            { [STATUS_NEW, STATUS_ACCEPTED, STATUS_COLLECTING, STATUS_FROZEN, STATUS_COLLECTED].includes(order.status) && (
                <div className="alert alert-info d-flex mt-5" role="alert">
                    <div className="alert-icon"><i className="ci-bell" /></div>
                    <div>
                        Если Вы хотите внести изменения в заказ, позвоните по телефону <a className="alert-link" href="tel:shop_info.inet_phone_E164">shop_info.inet_phone</a>
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
