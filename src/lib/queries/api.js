import axios from 'axios'

import {
  advertSearchParamsSerializer,
  orderSearchParamsSerializer,
} from '@/lib/search-params'

export const orderKeys = {
  all: ['orders'],
  lists: () => [...orderKeys.all, 'list'],
  list: (page, filter) => [...orderKeys.lists(), { page, filter }],
  last: () => [...orderKeys.lists(), 'last'],
  unpaid: () => [...orderKeys.lists(), 'unpaid'],
  details: () => [...orderKeys.all, 'detail'],
  detail: (id) => [...orderKeys.details(), id],
}

export const newsKeys = {
  all: ['news'],
  lists: () => [...newsKeys.all, 'list'],
}

export const advertKeys = {
  all: ['adverts'],
  lists: () => [...advertKeys.all, 'list'],
  list: (places) => [...advertKeys.lists(), places]
}

export const siteKeys = {
  all: ['sites'],
  current: () => [...siteKeys.all, 'current'],
}

const AXIOS_CONFIG = {
  baseURL: (process.env.API_SERVER ?? '') + '/api/v0',
  withCredentials: true,
}

export const apiClient = axios.create(AXIOS_CONFIG)

apiClient.defaults.headers.post['Content-Type'] = 'application/json'
apiClient.defaults.headers.put['Content-Type'] = 'application/json'

apiClient.interceptors.request.use(async function (config) {
  const session = typeof (localStorage) !== 'undefined' && localStorage.getItem('session')

  if (typeof window === 'undefined') {// set referrer when running on server
    config.headers['Referer'] = process.env.NEXT_PUBLIC_ORIGIN
    config.headers['Origin'] = process.env.NEXT_PUBLIC_ORIGIN
  }
  if (config.method === 'post' || config.method === 'put') {
    const response = await axios.get('csrf/', {
      ...AXIOS_CONFIG,
      headers: session ? { 'x-session': session } : {}
    })
    config.headers['x-csrftoken'] = response.data.csrf
  }
  if (session)
    config.headers['x-session'] = session
  return config
}, function (error) {
  return Promise.reject(error)
})

apiClient.interceptors.response.use(function (response) {
  if ('x-session' in response.headers) {
    const session = response.headers['x-session']
    localStorage.setItem("session", session)
  }
  return response
}, function (error) {
  return Promise.reject(error)
})

export async function createOrder() {
  const response = await apiClient.post('orders/')
  return response.data
}

export async function createPreorder(product) {
  const response = await apiClient.post('orders/preorder/', {
    product
  })
  return response.data
}

export async function loadOrders(page, filter, site = undefined) {
  const url = 'orders/' + orderSearchParamsSerializer({
    page,
    filter: filter === '' ? null : filter,
    site
  })
  const response = await apiClient.get(url)
  return response.data
};

export async function getLastOrder() {
  const response = await apiClient.post('orders/last/')
  return response.data
}

export async function getUnpaidOrder() {
  const response = await apiClient.post('orders/unpaid/')
  return response.data
}

export async function loadOrder(id) {
  const response = await apiClient.get(`orders/${id}/`)
  return response.data
}

export async function updateOrder(id, data) {
  const response = await apiClient.put('orders/' + id + '/', data)
  return response.data
}

export async function loadNews() {
  const response = await apiClient.get('news/')
  return response.data
}

export async function loadAdverts(places, categoryId=undefined) {
  const url = 'adverts/' + advertSearchParamsSerializer({
    category: categoryId,
    places,

  })
  const response = await apiClient.get(url)
  return response.data
}

export async function loadCurrentSite() {
  const response = await apiClient.get('sites/current/')
  return response.data
}

export async function getWarrantyCard(code) {
  return apiClient.get(`warrantycard/${encodeURIComponent(code)}/`)
}
