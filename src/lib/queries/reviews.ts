import { PaginatedResult, ProductReview, ProductReviewForm } from '@/lib/types'
import { apiFetch } from './fetch'

export const reviewKeys = {
  all: ['reviews'],
  lists: () => [...reviewKeys.all, 'list'],
  list: (productId: number) => [...reviewKeys.lists(), { productId }],
  rating: (productId: number) => [...reviewKeys.list(productId), 'rating'],
  form: (productId: number) => [...reviewKeys.list(productId), 'form'],
  details: () => [...reviewKeys.all, 'detail'],
  detail: (productId: number, id: number) => [...reviewKeys.details(), { productId, id }],
}

interface ProductRatingAverage {
  value: number
  text: string
  count: number
}

interface ProductReviewList extends PaginatedResult<ProductReview> {
  statistics: {
    value: number
    text: string
    ratings: {
      rating: number
      count: number
    }[]
  }
}

interface FormDataJson {
    [k: string]: FormDataEntryValue
}

export async function getProductRating(id: number) {
  return await apiFetch<ProductRatingAverage>(`reviews/shop.product/${id}/average/`)
}

export async function getReviewForm(id: number) {
  return await apiFetch<ProductReviewForm>(`reviews/shop.product/${id}/form/`)
}

export async function createProductReview(id: number, formData: FormData) {
  const body = Object.fromEntries(formData)
  return await apiFetch<ProductReview, FormDataJson>(`reviews/shop.product/${id}/`, { body })
}

export async function loadProductReviews(id: number) {
  return await apiFetch<ProductReviewList>(`reviews/shop.product/${id}/`)
}

export async function loadProductReview(id: number, reviewId: number) {
  return await apiFetch<ProductReview>(`reviews/shop.product/${id}/${reviewId}/`)
}

export async function updateProductReview(id: number, reviewId: number, formData: FormData) {
  const body = Object.fromEntries(formData)
  return await apiFetch<ProductReview, FormDataJson>(`reviews/shop.product/${id}/${reviewId}/`, {
    body,
    method: 'PUT',
  })
}

export async function loadPromoReviews() {
  return await apiFetch<ProductReviewList>("reviews/?model=shop.product&user=1&site=10&page_size=10")
}