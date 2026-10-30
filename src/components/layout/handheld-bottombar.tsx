'use client'

import Link from 'next/link'

import { MobileCartNotice } from '@/components/cart/notice'

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
    <div className="handheld-toolbar">
      <div className="d-table table-layout-fixed w-100">
        {item}
        <a className="d-table-cell handheld-toolbar-item" onClick={handleMenuOpen} style={{ cursor: 'pointer' }}>
          <span className="handheld-toolbar-icon"><i className="ci-menu" /></span>
          <span className="handheld-toolbar-label">Меню</span>
        </a>
        {comparisons.length > 0 && (
          <Link className="d-table-cell handheld-toolbar-item" href="/compare" rel="nofollow">
            <span className="handheld-toolbar-icon">
              <i className="ci-compare" />
              <span className="badge bg-primary rounded-pill ms-1">{comparisons.length}</span>
            </span>
            <span className="handheld-toolbar-label">Сравнение</span>
          </Link>
        )}
        {status === 'authenticated' && (
          <Link className="d-table-cell handheld-toolbar-item" href="/user/favorites">
            <span className="handheld-toolbar-icon">
              <i className="ci-heart" />
              {favorites.length > 0 && <span className="badge bg-primary rounded-pill ms-1">{favorites.length}</span>}
            </span>
            <span className="handheld-toolbar-label">Избранное</span>
          </Link>
        )}
        <MobileCartNotice extraItemsCount={extraItemsCount} />
      </div>
    </div>
  )
}
