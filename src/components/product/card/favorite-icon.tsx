'use client'

import OverlayTrigger from 'react-bootstrap/OverlayTrigger'
import Tooltip from 'react-bootstrap/Tooltip'

import useFavorites from '@/lib/favorites'
import { useSession } from '@/lib/session'
import { Product } from '@/lib/types'

export default function FavoriteIcon({ product }: { product: Product }) {
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
    <OverlayTrigger
      placement="left"
      overlay={
        <Tooltip>
          {favorites.includes(product.id) ? "В избранном" : "Отложить"}
        </Tooltip>
      }
    >
      <button onClick={handleFavoritesClick} className={"btn-wishlist btn-sm" + (favorites.includes(product.id) ? " bg-accent text-light" : "")}>
        <i className="ci-heart" />
      </button>
    </OverlayTrigger>
  )
}
