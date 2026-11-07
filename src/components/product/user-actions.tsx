'use client'

import { useRouter } from 'next/navigation'
import { IconHeart, IconRepeat } from '@tabler/icons-react'

import { buttonClass } from '@/components/ui/button'

import useComparison from '@/lib/comparison'
import useFavorites from '@/lib/favorites'
import { useSession } from '@/lib/session'
import { Product } from '@/lib/types'

export default function ProductUserActions({ product }: { product: Product }) {
  const router = useRouter()
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
      router.push(`/compare?kind=${product.kind![0]}`)
    else
      compare(product.id)
  }

  return (
    <div className="mb-6 flex">
      {(status === 'authenticated' && product.enabled) && (
        <button
          type="button"
          onClick={handleFavoritesClick}
          aria-pressed={favorites.includes(product.id)}
          className={buttonClass({ variant: favorites.includes(product.id) ? 'accent' : 'secondary', size: 'sm', block: true })}>
          <IconHeart size={18} stroke={1.5} className="me-2" />
          <span>
            {favorites.includes(product.id) ? "В избранном" : "Отложить"}
          </span>
        </button>
      )}
      {product.kind && (
        <button
          type="button"
          onClick={handleComparisonClick}
          className={`${buttonClass({ variant: comparisons.includes(product.id) ? 'accent' : 'secondary', size: 'sm', block: true })} ${status === 'authenticated' ? 'ms-4' : ''}`}>
          <IconRepeat size={18} stroke={1.5} className="me-2" />
          <span>
            {comparisons.includes(product.id) ? "Сравнение" : "Сравнить"}
          </span>
        </button>
      )}
    </div>

  )
}