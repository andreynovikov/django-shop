export const baseFilters = {
  enabled: true,
  show_on_sw: true,
}

export const recomendedProductsFilters = {
  ...baseFilters,
  categories: 473,
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