import { basketKeys } from './baskets'
import { comparisonKeys } from './comparisons'
import { favoriteKeys } from './favorites'
import { orderKeys } from './orders'
import { productKeys } from './products'
import { reviewKeys } from './reviews'
import { userKeys } from './users'

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

// those queries are reset when the user changes: on login, on logout, and when another user signs in in another tab
export const userReferences = [
  orderKeys.all,
  favoriteKeys.all,
  comparisonKeys.all,
  userKeys.bonus(),
  reviewKeys.all, // the user's own reviews are marked in the lists
]

// those queries are invalidated on user login/logout
export const userDependencies = [
  productKeys.lists(),
  productKeys.details(),
  basketKeys.all
]