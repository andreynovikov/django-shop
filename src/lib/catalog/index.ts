export const baseFilters = {
  enabled: true,
}

export const recomendedProductsFilters = {
  ...baseFilters,
  categories: 743,
  firstpage: true,
}

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