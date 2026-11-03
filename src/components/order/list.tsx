'use client'

import { useEffect } from 'react'
import Link from 'next/link'
import { useQuery } from '@tanstack/react-query'
import { parseAsInteger, parseAsString, useQueryStates } from 'nuqs'

import UserTopbar from '@/components/user/topbar'
import OrderPaymentButton from '@/components/order/payment-button'
import OrderStatusBadge from '@/components/order/status-badge'
import PageSelector from '@/components/page-selector'
import { PageLoading } from '@/components/loading'
import Tooltip from '@/components/ui/tooltip'

import { useSession } from '@/lib/session'
import { useNavigation } from '@/lib/navigation'
import { orderKeys, loadOrders, getLastOrder } from '@/lib/queries'
import {
  STATUS_COLLECTED,
  PAYMENT_CARD,
  PAYMENT_CREDIT,
} from '@/components/order/status-badge'

import moment from 'moment'

const orderListParams = {
  page: parseAsInteger.withDefault(1),
  filter: parseAsString.withDefault(''),
  track: parseAsString, // "?track" without a value opens the last order
}

const orderPathname = (id: number) => `/user/orders/${id}/`

// Shown by the static page until the query is read in the browser
export function OrderListLoading() {
  return (
    <>
      <UserTopbar>
        <div className="d-flex w-100 text-light text-center me-3">&nbsp;</div>
      </UserTopbar>
      <PageLoading />
    </>
  )
}

export default function OrderList() {
  const [{ page, filter, track }, setParams] = useQueryStates(orderListParams)
  const { navigate } = useNavigation()
  const { status } = useSession()

  const { data: lastOrder } = useQuery({
    queryKey: orderKeys.last(),
    queryFn: () => getLastOrder(),
    enabled: status === 'authenticated' && track !== null
  })

  // keep showing the loader until redirected to the last order, if there is one
  const isTracking = track !== null && !(lastOrder !== undefined && !lastOrder.id)

  useEffect(() => {
    if (isTracking && lastOrder?.id)
      navigate(orderPathname(lastOrder.id))
  }, [lastOrder, navigate, isTracking])

  // pending until the session is loaded too, so the list doesn't say there are no orders meanwhile
  const { data: orders, isSuccess, isPending } = useQuery({
    queryKey: orderKeys.list(page, filter),
    queryFn: () => loadOrders(page, filter),
    enabled: status === 'authenticated'
  })

  // the filter is kept in the query, a new filter starts from the first page
  const onFilterChanged = (value: string) => setParams({ filter: value || null, page: null })

  return (
    <>
      <UserTopbar>
        <div className="d-flex align-items-center flex-nowrap me-3 me-sm-4">
          {isSuccess && !isTracking && (orders.results.length > 0 || !!filter) ? (
            <>
              <label className="text-light opacity-75 text-nowrap fs-sm me-2 d-none d-sm-block" htmlFor="sw-order-filter">Отображать:</label>
              <select className="form-select" id="sw-order-filter" value={filter} onChange={(e) => onFilterChanged(e.target.value)}>
                <option value="">Все</option>
                <option value="active">Активные</option>
                <option value="done">Выполненные</option>
                <option value="canceled">Отмененные</option>
              </select>
            </>
          ) : (
            <div className="d-flex w-100 text-light text-center me-3">&nbsp;</div>
          )}
        </div>
      </UserTopbar>

      {isSuccess && !isTracking && orders.results.length > 0 ? (
        <>
          <div className="table-responsive fs-md">
            <table className="table table-hover mb-0">
              <thead>
                <tr>
                  <th><span className="d-none d-sm-inline">Заказ </span>№</th>
                  <th>Дата<span className="d-none d-sm-inline"> оформления</span></th>
                  <th>Статус</th>
                  <th className="d-none d-sm-table-cell">Сумма</th>
                </tr>
              </thead>
              <tbody>
                {orders.results.map((order) => (
                  <tr key={order.id} onClick={() => navigate(orderPathname(order.id))} style={{ cursor: "pointer" }}>
                    <td className="py-3">
                      <Link className="nav-link-style fw-medium fs-sm" href={orderPathname(order.id)}>
                        {order.id}
                      </Link>
                    </td>
                    <td className="py-3">
                      <Tooltip content={moment(order.created).format('LLL')}>
                        <span>{moment(order.created).calendar().toLowerCase()}</span>
                      </Tooltip>
                    </td>
                    <td className="py-3"><OrderStatusBadge status={order.status} text={order.status_text} /></td>
                    <td className="d-none d-sm-table-cell py-3">
                      {order.total.toLocaleString('ru')}<small>&nbsp;руб</small>
                      {(order.status === STATUS_COLLECTED && !order.paid && (order.payment === PAYMENT_CARD || order.payment === PAYMENT_CREDIT)) && (
                        <span className="ps-2">
                          <OrderPaymentButton orderId={order.id} iconOnly />
                        </span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          {orders.totalPages > 1 && (
            <PageSelector
              pathname="/user/orders/"
              query={filter ? { filter } : {}}
              totalPages={orders.totalPages}
              currentPage={orders.currentPage} />
          )}
        </>
      ) : (isPending || isTracking) ? (
        <PageLoading />
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
