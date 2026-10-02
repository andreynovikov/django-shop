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
