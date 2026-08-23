import { apiFetch } from './fetch'

export const favoriteKeys = {
  all: ['favorites'],
  details: () => [...favoriteKeys.all, 'detail'],
}

export async function loadFavorites() {
  return await apiFetch<number[]>('favorites/')
}

export async function addToFavorites(product: number) {
  return await apiFetch<undefined>('favorites/add/', {
    body: { product }
  })
}

export async function removeFromFavorites(product: number) {
  return await apiFetch<undefined>('favorites/remove/', {
    body: { product }
  })
}