import { basketKeys } from './baskets'
import { comparisonKeys } from './comparisons'
import { favoriteKeys } from './favorites'
import { orderKeys } from './orders'
import { productKeys } from './products'

export * from './api'
export * from './baskets'
export * from './blog'
export * from './categories'
export * from './comparisons'
export * from './favorites'
export * from './fetch'
export * from './forum'
export * from './orders'
export * from './pages'
export * from './products'
export * from './reviews'
export * from './sales-actions'
export * from './serials'
export * from './service-centers'
export * from './site'
export * from './stores'
export * from './tokenized'
export * from './users'

// those queries are reset on user logout
export const userReferences = [
  orderKeys.all,
  favoriteKeys.all,
  comparisonKeys.all
]

// those queries are invalidated on user login/logout
export const userDependencies = [
  productKeys.lists(),
  productKeys.details(),
  basketKeys.all
]