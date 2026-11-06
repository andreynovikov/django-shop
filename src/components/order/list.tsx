'use client'

import { useEffect } from 'react'
import Link from 'next/link'
import { useRouter } from 'next/navigation'
import { useQuery } from '@tanstack/react-query'
import { parseAsInteger, parseAsString, useQueryStates } from 'nuqs'

import UserTopbar from '@/components/user/topbar'
import OrderPaymentButton from '@/components/order/payment-button'
import OrderStatusBadge from '@/components/order/status-badge'
import PageSelector from '@/components/page-selector'
import { PageLoading } from '@/components/loading'
import Tooltip from '@/components/ui/tooltip'
import { inputClass } from '@/components/ui/form'

import { useSession } from '@/lib/session'
import { useSite } from '@/lib/site'
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
        <div className="me-4 flex w-full text-center">&nbsp;</div>
      </UserTopbar>
      <PageLoading />
    </>
  )
}

export default function OrderList() {
  const [{ page, filter, track }, setParams] = useQueryStates(orderListParams)
  const router = useRouter()
  const { status } = useSession()
  const { site } = useSite()

  const { data: lastOrder } = useQuery({
    queryKey: orderKeys.last(),
    queryFn: () => getLastOrder(),
    enabled: status === 'authenticated' && track !== null
  })

  // keep showing the loader until redirected to the last order, if there is one
  const isTracking = track !== null && !(lastOrder !== undefined && !lastOrder.id)

  useEffect(() => {
    if (isTracking && lastOrder?.id)
      router.push(orderPathname(lastOrder.id))
  }, [lastOrder, router, isTracking])

  // pending until the session and the site are loaded too, so the list doesn't say there are no orders meanwhile.
  // Only the orders made on this site are listed, the site is the same for every query of the storefront.
  // eslint-disable-next-line @tanstack/query/exhaustive-deps
  const { data: orders, isSuccess, isPending } = useQuery({
    queryKey: orderKeys.list(page, filter),
    queryFn: () => loadOrders(page, filter, site.id),
    enabled: status === 'authenticated' && site.id !== undefined
  })

  // the filter is kept in the query, a new filter starts from the first page
  const onFilterChanged = (value: string) => setParams({ filter: value || null, page: null })

  return (
    <>
      <UserTopbar>
        <div className="me-4 flex flex-nowrap items-center sm:me-6">
          {isSuccess && !isTracking && (orders.results.length > 0 || !!filter) ? (
            <>
              <label className="me-2 hidden text-sm whitespace-nowrap text-muted sm:block" htmlFor="sw-order-filter">Отображать:</label>
              <select className={inputClass()} id="sw-order-filter" value={filter} onChange={(e) => onFilterChanged(e.target.value)}>
                <option value="">Все</option>
                <option value="active">Активные</option>
                <option value="done">Выполненные</option>
                <option value="canceled">Отмененные</option>
              </select>
            </>
          ) : (
            <div className="me-4 flex w-full text-center">&nbsp;</div>
          )}
        </div>
      </UserTopbar>

      {isSuccess && !isTracking && orders.results.length > 0 ? (
        <>
          <div className="overflow-x-auto text-md">
            <table className="w-full text-black">
              <thead>
                <tr className="border-b">
                  <th className="p-2 text-start"><span className="hidden sm:inline">Заказ </span>№</th>
                  <th className="p-2 text-start">Дата<span className="hidden sm:inline"> оформления</span></th>
                  <th className="p-2 text-start">Статус</th>
                  <th className="hidden p-2 text-start sm:table-cell">Сумма</th>
                </tr>
              </thead>
              <tbody>
                {orders.results.map((order) => (
                  <tr className="border-b hover:bg-black/5" key={order.id} onClick={() => router.push(orderPathname(order.id))} style={{ cursor: "pointer" }}>
                    <td className="px-2 py-4">
                      <Link className="text-sm font-medium" href={orderPathname(order.id)}>
                        {order.id}
                      </Link>
                    </td>
                    <td className="px-2 py-4">
                      <Tooltip content={moment(order.created).format('LLL')}>
                        <span>{moment(order.created).calendar().toLowerCase()}</span>
                      </Tooltip>
                    </td>
                    <td className="px-2 py-4"><OrderStatusBadge status={order.status} text={order.status_text} /></td>
                    <td className="hidden px-2 py-4 sm:table-cell">
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
        <p className="mb-4 text-lg font-light">У вас нет {
          filter === 'active' ? "активных"
            : filter === 'done' ? "выполненных"
              : filter === 'canceled' ? "отменённых"
                : "оформленных"
        } заказов</p>
      )}
    </>
  )
}
