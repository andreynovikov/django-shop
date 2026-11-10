'use client'

import { useMemo } from 'react'
import Image from 'next/image'
import { useQuery } from '@tanstack/react-query'

import { useSite } from '@/lib/site'
import { useSession } from '@/lib/session'
import { orderKeys, loadOrder } from '@/lib/queries'
import { formatPhone } from '@/lib/format'

import { Loading } from '@/components/loading'
import NoImage from '@/components/product/no-image'
import ProductLink from '@/components/product/product-link'
import UserTopbar from '@/components/user/topbar'
import OrderPaymentButton from '@/components/order/payment-button'
import OrderStatusBadge from '@/components/order/status-badge'
import Tooltip from '@/components/ui/tooltip'
import { Alert } from '@/components/ui/alert'
import { IconAlertCircle, IconBell, IconPaperclip } from '@tabler/icons-react'
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
} from '@/components/order/status-badge'

import moment from 'moment'

// The information blocks: delivery, payment and the recipient
const infoTitleClass = 'mb-3 text-h6'
const infoListClass = 'mb-4 text-sm *:mb-[.4rem]'

export default function OrderDetails({ id }: { id: number }) {
  const { site } = useSite()
  const { status } = useSession()

  const { data: order, isSuccess } = useQuery({
    queryKey: orderKeys.detail(id),
    queryFn: () => loadOrder(id),
    enabled: status === 'authenticated',
    refetchInterval: (query) => {
      const orderStatus = query.state.data?.status
      return orderStatus === STATUS_NEW || orderStatus === STATUS_ACCEPTED ? 60 * 1000 : false // check for updates every minute
    }
  })

  const created = useMemo(() => {
    if (isSuccess) {
      const c = moment(order.created)
      const n = moment()  // TODO: test time zones
      const d = n.diff(c, 'days')
      if (d < 3)
        return c.calendar(n)
      else if (d < 7)
        return c.format('D MMMM, HH:mm')
      else
        return c.format('LL')
    } else {
      return null
    }
  },
    [isSuccess, order]
  )

  if (!isSuccess)
    return (
      <div className="mb-2 pb-12 md:mb-6">
        <section>
          <div className="pt-2 pb-6 sm:pb-overlap">
            <div className="pb-4">
              &nbsp;
            </div>
          </div>
          <Loading className="my-4 py-4 text-center" mega />
        </section>
      </div>
    )

  return (
    <>
      <UserTopbar>
        <div className="me-4 flex w-full text-center text-overlap">
          <div className="px-4 text-ms">
            <div className="font-medium">Дата оформления</div>
            <div className="text-lg opacity-60">
              <Tooltip side="bottom" content={moment(order.created).format('LLL')}>
                <span>{created}</span>
              </Tooltip>
            </div>
          </div>
          <div className="px-4 text-ms">
            <div className="font-medium">Статус</div>
            <div className="text-lg"><OrderStatusBadge status={order.status} text={order.status_text} /></div>
          </div>
          <div className="px-4 text-ms">
            <div className="font-medium">{order.paid ? "Стоимость заказа" : "Всего к оплате"}</div>
            <div className="text-lg opacity-60">{order.total.toLocaleString('ru')}<small>&nbsp;руб</small></div>
          </div>
        </div>
      </UserTopbar>
      { /* Order details (visible on mobile) */}
      <div className="mb-6 flex flex-wrap rounded-lg bg-gray-100 px-6 pt-6 pb-1 text-center lg:hidden">
        <div className="px-4 pb-4 text-sm">
          <div className="font-medium">Дата оформления</div>
          <div className="text-lg text-muted">{created}</div>
        </div>
        <div className="px-4 pb-4 text-sm">
          <div className="font-medium">Статус</div>
          <div className="text-lg text-muted"><OrderStatusBadge status={order.status} text={order.status_text} /></div>
        </div>
        <div className="px-4 pb-4 text-sm">
          <div className="font-medium">Всего к оплате</div>
          <div className="text-lg text-muted">{order.total.toLocaleString('ru')}<small>&nbsp;руб</small></div>
        </div>
      </div>

      <div className="mb-6 rounded-lg bg-gray-100 px-6 pt-6 pb-2">
        <div className="grid gap-x-7.5 sm:grid-cols-2">
          <div>
            <h4 className={infoTitleClass}>Информация о доставке:</h4>
            <ul className={infoListClass}>
              {order.delivery_price > 0 && (
                <li>
                  <span className="text-muted">Стоимость доставки:</span>
                  {" "}{order.delivery_price}<small>&nbsp;руб</small>
                </li>
              )}
              {order.delivery === DELIVERY_UNKNOWN && (
                <li>Способ доставки уточняется</li>
              )}
              {order.delivery === DELIVERY_SELF && (
                <li>
                  <span className="text-muted">Магазин самовывоза:</span>
                  {" "}
                  {order.store ? (
                    <>
                      <a className="text-heading" href={`/stores/${order.store.id}/`}><u>{order.store.city.name}, {order.store.address}</u></a>
                      {order.store.hours && (
                        <> (часы работы: {order.store.hours})</>
                      )}
                    </>
                  ) : (
                    <>уточняется</>
                  )}
                </li>
              )}
              {order.delivery === DELIVERY_YANDEX && (
                <>
                  <li>
                    <span className="text-muted">Доставка службой доставки по адресу:</span>
                    {" "}{order.address}
                  </li>
                  {order.status === STATUS_DELIVERED_STORE && (
                    <li>Заказ передан в службу доставки</li>
                  )}
                </>
              )}
              {(order.delivery === DELIVERY_COURIER || order.delivery === DELIVERY_CONSULTANT) && (
                <li>
                  <span className="text-muted">Доставка курьером по адресу:</span>
                  {" "}{order.address}
                </li>
              )}
              {(order.delivery === DELIVERY_TRANSPORT || order.delivery === DELIVERY_PICKPOINT) && (
                <>
                  <li>
                    <span className="text-muted">Доставка транспортной компанией по адресу:</span>
                    {" "}{order.address}
                  </li>
                  {order.delivery_tracking_number && (
                    <li>
                      <span className="text-muted">Трек-код:</span>
                      {" "}{order.delivery_tracking_number}
                    </li>
                  )}
                </>
              )}
              {order.delivery_info && (
                <li className="whitespace-pre-line">{order.delivery_info}</li>
              )}
              {order.delivery_dispatch_date && (
                <li>
                  <span className="text-muted">Дата отправки:</span>
                  {" "}{moment(order.delivery_dispatch_date).format('D MMMM')}
                </li>
              )}
              {order.delivery_handing_date && (
                (order.delivery === DELIVERY_COURIER || order.delivery === DELIVERY_CONSULTANT) ? (
                  <li>
                    <span className="text-muted">Дата доставки:</span>
                    {" "}{moment(order.delivery_handing_date).format('D MMMM')}
                    {order.delivery_time_from && <> с {moment(order.delivery_time_from, moment.HTML5_FMT.TIME_SECONDS).format('HH:mm')}</>}
                    {order.delivery_time_till && <> до {moment(order.delivery_time_till, moment.HTML5_FMT.TIME_SECONDS).format('HH:mm')}</>}
                  </li>
                ) : order.delivery === DELIVERY_SELF ? (
                  <li>
                    <span className="text-muted">Дата получения:</span>
                    {" "}{moment(order.delivery_handing_date).format('D MMMM')}
                    {order.delivery_time_from && <> после {moment(order.delivery_time_from, moment.HTML5_FMT.TIME_SECONDS).format('HH:mm')}</>}
                  </li>
                ) : (
                  <li>
                    <span className="text-muted">Расчётная дата получения:</span>
                    {" "}{moment(order.delivery_handing_date).format('D MMMM')}
                  </li>
                )
              )}
            </ul>
          </div>
          <div>
            <h4 className={infoTitleClass}>Оплата заказа:</h4>
            <ul className={infoListClass}>
              {order.payment === PAYMENT_UNKNOWN ? (
                <li>Способ оплаты уточняется</li>
              ) : (
                <>
                  <li><span className="text-muted">Способ оплаты:</span> {order.payment_text}</li>
                  {order.paid ? (
                    <li><span className="text-muted">Статус:</span> оплачен</li>
                  ) : (
                    order.status === STATUS_COLLECTED ? (
                      order.payment === PAYMENT_CARD || order.payment === PAYMENT_CREDIT ? (
                        <li className="pt-2">
                          <OrderPaymentButton orderId={order.id} />
                        </li>
                      ) : order.payment === PAYMENT_TRANSFER ? (
                        <li>
                          { /* TODO: external link */}
                          <a href="'shop:order_document' order.id 'bill'" target="_blank">
                            <IconPaperclip size={14} stroke={1.5} className="me-1" />Скачать счёт для оплаты в любом банке
                          </a>
                        </li>
                      ) : (
                        null
                      )
                    ) : (
                      (order.payment === PAYMENT_CARD || order.payment === PAYMENT_CREDIT || order.payment === PAYMENT_TRANSFER) && (
                        <li>
                          <Alert variant="accent" icon={<IconAlertCircle size={18} stroke={1.5} />} className="mt-4 mb-4">
                            <div className="mb-2">Возможность оплатить заказ онлайн или распечатать счёт
                              появится тут после согласования и завершения комплектования заказа.</div>
                            <div>Вы получите сообщение об этом. Пожалуйста, посетите эту страницу позже.</div>
                          </Alert>
                        </li>
                      )
                    )
                  )}
                </>
              )}
            </ul>
          </div>
          {order.is_firm && (
            <div>
              <h4 className={infoTitleClass}>Получатель:</h4>
              <ul className={infoListClass}>
                <li><span className="text-muted">Название организации:</span> {order.firm_name}</li>
                <li><span className="text-muted">Юридический адрес:</span> {order.firm_address}</li>
                <li><span className="text-muted">Сведения об организации:</span> {order.firm_details}</li>
                <li><span className="text-muted">Контактное лицо:</span> {order.name}</li>
                <li><span className="text-muted">Телефон:</span>&nbsp;{formatPhone(order.phone)}</li>
              </ul>
            </div>
          )}
        </div>
      </div>
      {order.items.map((item, index) => (
        <div className={`pb-4 sm:flex sm:justify-between sm:pb-2 ${index === 0 ? "mb-4" : "my-4"} ${index < order.items.length - 1 ? "border-b" : ""}`} key={item.product.id}>
          <div className="text-center sm:flex sm:text-start">
            <ProductLink className="relative mx-auto inline-block w-40 shrink-0" code={item.product.code}>
              {item.product.image ? (
                <Image
                  src={item.product.image}
                  fill
                  style={{ objectFit: 'contain' }}
                  sizes="10rem"
                  alt={`${item.product.whatis ? item.product.whatis + ' ' : ''}${item.product.title}`} />
              ) : (
                <NoImage size={160} />
              )}
            </ProductLink>
            <div className="pt-2 sm:ps-6">
              <h3 className="mb-2 text-base leading-[1.2] font-medium">
                <ProductLink className="text-heading hover:text-primary" code={item.product.code}>
                  {item.product.title}
                </ProductLink>
              </h3>
              {item.product.partnumber && (
                <div className="text-sm">
                  <span className="me-2 text-muted">Артикул:</span>{item.product.partnumber}
                </div>
              )}
              {item.product.article && (
                <div className="text-sm">
                  <span className="me-2 text-muted">Код товара:</span>{item.product.article}
                </div>
              )}
              <div className="text-sm">
                <span className="me-2 text-muted">Цена:</span>{item.product_price.toLocaleString('ru')}<small>&nbsp;руб</small>
              </div>
              {item.discount > 0 && (
                <div className="text-sm">
                  <span className="me-2 text-muted">Скидка:</span>{item.discount_text}
                </div>
              )}
              <div className="pt-2 text-lg text-accent">{item.price.toLocaleString('ru')}<small>&nbsp;руб</small></div>
            </div>
          </div>
          <div className="mx-auto max-w-36 pt-2 text-center sm:mx-0 sm:ps-4">
            <div className="mb-2 text-muted">Количество:</div>
            {item.quantity}
          </div>
        </div>
      ))}
      {site.phone && [STATUS_NEW, STATUS_ACCEPTED, STATUS_COLLECTING, STATUS_FROZEN, STATUS_COLLECTED].includes(order.status) && (
        <Alert variant="info" icon={<IconBell size={18} stroke={1.5} />} className="mt-12 mb-4">
          Если Вы хотите внести изменения в заказ, позвоните по телефону{" "}
          <a className="whitespace-nowrap" href={"tel:" + site.phone}>{formatPhone(site.phone)}</a>
        </Alert>
      )}
    </>
  )
}
