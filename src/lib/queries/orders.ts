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

export async function createOrder() {
  return await apiFetch<Order>('orders/', { method: 'POST' })
}

export async function createPreorder(product: number) {
  return await apiFetch<Order>('orders/preorder/', {
    body: { product },
  })
}

export async function loadOrders(page: number, filter: string, site = undefined) {
  const url = 'orders/' + orderSearchParamsSerializer({
    page,
    filter: filter === '' ? null : filter,
    site
  })
  return await apiFetch<PaginatedResult<OrderInfo>>(url)
}

export async function getLastOrder() {
  return await apiFetch<{id: number | null}>('orders/last/', { method: 'POST' })
}

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