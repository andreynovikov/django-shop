'use client'

import { IconHeart } from '@tabler/icons-react'

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
      <button
        onClick={handleFavoritesClick}
        className={`absolute top-3 right-3 z-5 flex size-8 items-center justify-center rounded-full transition-colors ${favorites.includes(product.id) ? 'bg-accent text-white' : 'bg-gray-200 text-gray-800 hover:text-primary'}`}
        aria-label={favorites.includes(product.id) ? "Убрать из избранного" : "Отложить"}
        aria-pressed={favorites.includes(product.id)}>
        <IconHeart size={14} stroke={1.5} />
      </button>
    </Tooltip>
  )
}
