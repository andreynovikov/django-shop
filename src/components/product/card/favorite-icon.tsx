'use client'

import Tooltip from '@/components/ui/tooltip'

import useFavorites from '@/lib/favorites'
import { useSession } from '@/lib/session'
import { ProductInfo } from '@/lib/types'

import { SearchProduct } from '.'

export default function FavoriteIcon({ product }: { product: ProductInfo | SearchProduct }) {
  const { status } = useSession()
  const { favorites, favoritize, unfavoritize } = useFavorites()

  const handleFavoritesClick = () => {
    if (status === 'authenticated') {
      if (favorites.includes(product.id))
        unfavoritize(product.id)
      else
        favoritize(product.id)
    }
  }

  if (status !== 'authenticated')
    return null

  return (
    <Tooltip side="left" content={favorites.includes(product.id) ? "В избранном" : "Отложить"}>
      <button onClick={handleFavoritesClick} className={"btn-wishlist btn-sm" + (favorites.includes(product.id) ? " bg-accent text-light" : "")}>
        <i className="ci-heart" />
      </button>
    </Tooltip>
  )
}
