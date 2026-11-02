'use client'

import useComparison from '@/lib/comparison'
import useFavorites from '@/lib/favorites'
import { useNavigation } from '@/lib/navigation'
import { useSession } from '@/lib/session'
import { Product } from '@/lib/types'

export default function ProductUserActions({ product }: { product: Product }) {
  const { navigate } = useNavigation()
  const { status } = useSession()
  const { favorites, favoritize, unfavoritize } = useFavorites()
  const { comparisons, compare } = useComparison()

  const handleFavoritesClick = () => {
    if (status === 'authenticated') {
      if (favorites.includes(product.id))
        unfavoritize(product.id)
      else
        favoritize(product.id)
    } // TODO: else show dialog or tooltip
  }

  const handleComparisonClick = () => {
    if (comparisons.includes(product.id))
      navigate(`/compare?kind=${product.kind![0]}`)
    else
      compare(product.id)
  }

  return (
    <div className="d-flex mb-4">
      {(status === 'authenticated' && product.enabled) && (
        <button
          type="button"
          onClick={handleFavoritesClick}
          className={"btn btn-sm btn-" + (favorites.includes(product.id) ? "accent" : "secondary") + " d-block w-100"}>
          <i className="ci-heart fs-lg me-2" />
          <span>
            {favorites.includes(product.id) ? "В избранном" : "Отложить"}
          </span>
        </button>
      )}
      {product.kind && (
        <button
          type="button"
          onClick={handleComparisonClick}
          className={"btn btn-sm btn-" + (comparisons.includes(product.id) ? "accent" : "secondary") + " d-block w-100" + (status === 'authenticated' ? " ms-3" : "")}>
          <i className="ci-compare fs-lg me-2" />
          <span>
            {comparisons.includes(product.id) ? "Сравнение" : "Сравнить"}
          </span>
        </button>
      )}
    </div>

  )
}