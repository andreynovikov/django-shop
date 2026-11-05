import { Metadata } from 'next'

import { pageContentWrapper } from '@/components/layout/page-content-wrapper'
import OrderConfirmation from '@/components/order/confirmation'

// The page is static, the last order is loaded in the browser
export const metadata: Metadata = {
  title: 'Оформление заказа',
  robots: { index: false },
}

export default function ConfirmationPage() {
  return pageContentWrapper({
    title: 'Оформление заказа',
    dark: true,
    overlapped: true,
    children: (
      <div className="mb-2 grid px-3 pb-12 md:mb-6 lg:grid-cols-3 lg:gap-x-6">
        <OrderConfirmation />
      </div>
    ),
  })
}
