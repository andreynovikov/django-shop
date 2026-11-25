import { orderSearchParamsSerializer } from '@/lib/search-params'
import { Order, OrderInfo, PaginatedResult } from '@/lib/types'
import { apiFetch, FormDataJson } from './fetch'

export const orderKeys = {
  all: ['orders'],
  lists: () => [...orderKeys.all, 'list'],
  list: (page: number, filter: string) => [...orderKeys.lists(), { page, filter }],
  last: () => [...orderKeys.lists(), 'last'],
  unpaid: () => [...orderKeys.lists(), 'unpaid'],
  details: () => [...orderKeys.all, 'detail'],
  detail: (id: number) => [...orderKeys.details(), id],
}

// Orders the session's basket. Its ID is the idempotency key: Django deletes the basket with the order, and a repeat
// with the same key gets that order back, so useCreateOrder (lib/order.ts) can retry a lost answer
export async function createOrder(basketId: number) {
  return await apiFetch<Order>('orders/', {
    method: 'POST',
    headers: { 'idempotency-key': String(basketId) },
  })
}

export async function createPreorder(product: number) {
  return await apiFetch<Order>('orders/preorder/', {
    body: { product },
  })
}

export async function loadOrders(page: number, filter: string, site?: number) {
  const url = 'orders/' + orderSearchParamsSerializer({
    page,
    filter: filter === '' ? null : filter,
    site
  })
  return await apiFetch<PaginatedResult<OrderInfo>>(url)
}

// The latest order still in progress (not done, finished or canceled), for order tracking
export async function getLastOrder() {
  return await apiFetch<{id: number | null}>('orders/last/', { method: 'POST' })
}

// The latest collected order that is still to be paid by card, transfer or credit
export async function getUnpaidOrder() {
  return await apiFetch<{id: number | null}>('orders/unpaid/', { method: 'POST' })
}

export async function loadOrder(id: number) {
  return await apiFetch<Order>(`orders/${id}/`)
}

export async function updateOrder(id: number, body: FormDataJson) {
  return await apiFetch<Order, FormDataJson>(`orders/${id}/`, {
    body,
    method: 'PUT',
  })
}
