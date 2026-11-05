'use client'

import { navbarId } from '@/components/layout/header'
import ProductRating from '@/components/product/rating'
import { productTabsId, useProductTabs } from '@/components/product/tabs'

// Opens the reviews tab and scrolls to the tabs below the sticky navbar
export default function ProductRatingLink({ product }: { product: number }) {
  const { setTab } = useProductTabs()

  const handleClick = () => {
    setTab('reviews')

    const tabs = document.getElementById(productTabsId)
    if (tabs === null)
      return

    const stickyNavbar = document.getElementById(navbarId)
    if (stickyNavbar) {
      let offset = stickyNavbar.getBoundingClientRect().bottom
      if (stickyNavbar.dataset.fixed === undefined)
        offset = offset * 2 // because it will become fixed during scroll
      window.scrollTo({
        behavior: 'smooth',
        top: tabs.getBoundingClientRect().top - document.body.getBoundingClientRect().top - offset
      })
    } else {
      tabs.scrollIntoView({
        behavior: 'smooth'
      })
    }
  }

  return (
    <a className="flex cursor-pointer items-center text-primary hover:no-underline" onClick={handleClick}>
      <ProductRating product={product} />
    </a>
  )
}
