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
      <div className="container pb-5 mb-2 mb-md-4">
        <div className="row">
          <OrderConfirmation />
        </div>
      </div>
    ),
  })
}
