import { Suspense } from 'react'
import { Metadata } from 'next'

import { userPageContentWrapper } from '@/components/layout/user-page-content-wrapper'
import OrderList, { OrderListLoading } from '@/components/order/list'

const title = 'Список заказов'

export const metadata: Metadata = {
  title,
}

// The page is static, the query is read in the browser. A loading.tsx here would wrap the order pages too
// and leave the header and the menu out of the static page, so the boundary is around the list only.
export default function OrdersPage() {
  return userPageContentWrapper({
    title,
    breadcrumbs: [{ label: 'Личный кабинет', href: '/user/profile/' }],
    children: (
      <Suspense fallback={<OrderListLoading />}>
        <OrderList />
      </Suspense>
    ),
  })
}
