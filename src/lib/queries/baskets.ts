import { Basket } from '@/lib/types'
import { apiFetch } from './fetch'

export const basketKeys = {
  all: ['baskets'],
  details: () => [...basketKeys.all, 'detail'],
}

export async function loadBaskets() {
  return await apiFetch<Basket[]>('baskets/')
}

export async function createBasket() {
  return await apiFetch<Basket>('baskets/', { method: 'POST' })
}

export async function addBasketItem(basketId: number, product: number, quantity: number) {
  return await apiFetch<void>(`baskets/${basketId}/add/`, {
    body: {
      product,
      quantity
    }
  })
}

export async function removeBasketItem(basketId: number, product: number) {
  return await apiFetch<void>(`baskets/${basketId}/remove/`, {
    body: { product }
  })
}

export async function updateBasketItem(basketId: number, product: number, quantity: number) {
  return await apiFetch<void>(`baskets/${basketId}/update/`, {
    body: {
      product,
      quantity
    }
  })
}

// The links in the abandoned basket email open storefront pages at their paths, which send the link's data here
export async function restoreBasket(contents: string, utmSource: string | null) {
  return await apiFetch<void>('baskets/restore/', {
    body: {
      contents,
      ...(utmSource ? { utm_source: utmSource } : {})
    }
  })
}

export async function clearBasket(sign: string) {
  return await apiFetch<void>('baskets/clear/', {
    body: { sign }
  })
}
