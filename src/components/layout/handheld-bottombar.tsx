'use client'

import Link from 'next/link'
import { IconHeart, IconMenu2, IconRepeat } from '@tabler/icons-react'

import { MobileCartNotice } from '@/components/cart/notice'
import { handheldBadgeClass, handheldIconClass, handheldItemClass, handheldLabelClass, handheldToolbarClass } from '@/components/ui/handheld-toolbar'

import useComparison from '@/lib/comparison'
import useFavorites from '@/lib/favorites'
import { useSession } from '@/lib/session'
import { useToolbar } from '@/lib/toolbar'
import { useTopbar } from '@/lib/topbar'

export default function HandheldBottomBar() {
  const { status } = useSession()
  const { comparisons } = useComparison()
  const { favorites } = useFavorites()
  const { item } = useToolbar()
  const { topMenuOpen, toggleTopMenu } = useTopbar()

  const handleMenuOpen = () => {
    if (!topMenuOpen)
      window.scrollTo(0, 0)
    toggleTopMenu()
  }

  const extraItemsCount =
    (item ? 1 : 0)
    + (comparisons.length > 0 ? 1 : 0)
    + (favorites.length > 0 ? 1 : 0)

  return (
    <div className={handheldToolbarClass}>
      {item}
      <button type="button" className={handheldItemClass} onClick={handleMenuOpen}>
        <span className={handheldIconClass}><IconMenu2 size={20} stroke={1.5} /></span>
        <span className={handheldLabelClass}>Меню</span>
      </button>
      {comparisons.length > 0 && (
        <Link className={handheldItemClass} href="/compare" rel="nofollow" aria-label="Сравнение">
          <span className={handheldIconClass}>
            <IconRepeat size={20} stroke={1.5} />
            <span className={handheldBadgeClass}>{comparisons.length}</span>
          </span>
          <span className={handheldLabelClass}>Сравнение</span>
        </Link>
      )}
      {status === 'authenticated' && (
        <Link className={handheldItemClass} href="/user/favorites" aria-label="Избранное">
          <span className={handheldIconClass}>
            <IconHeart size={20} stroke={1.5} />
            {favorites.length > 0 && <span className={handheldBadgeClass}>{favorites.length}</span>}
          </span>
          <span className={handheldLabelClass}>Избранное</span>
        </Link>
      )}
      <MobileCartNotice extraItemsCount={extraItemsCount} />
    </div>
  )
}
