import { Metadata } from 'next'

import { pageContentWrapper } from '@/components/layout/page-content-wrapper'
import CartContents from '@/components/cart/contents'

// The page is static, the basket and the session are loaded in the browser
export const metadata: Metadata = {
  title: 'Корзина',
  robots: { index: false },
}

export default function CartPage() {
  return pageContentWrapper({
    title: 'Ваша корзина',
    dark: true,
    overlapped: true,
    children: (
      <div className="mb-2 grid px-3 pb-12 md:mb-6 lg:grid-cols-3 lg:gap-x-6">
        <CartContents />
      </div>
    ),
  })
}
