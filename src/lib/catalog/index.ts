import { storefront } from '@/storefront'

// The storefront's own filters of the products it lists, which every product list of the site starts from
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
