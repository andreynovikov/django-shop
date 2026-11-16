import { storefront } from '@/storefront'

export const baseFilters = storefront.productFilters

export const giftProductsFilters = {
  ...baseFilters,
  gift: true,
  firstpage: true,
}

export const newProductsFilters = {
  ...baseFilters,
  isnew: true,
  firstpage: true,
}
