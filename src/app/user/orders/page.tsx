import { Suspense } from 'react'

import OrderList, { OrderListLoading } from '@/components/order/list'

// The page is static, the query is read in the browser. A loading.tsx here would wrap the order pages too,
// so the boundary is around the list only.
export default function OrdersPage() {
  return (
    <Suspense fallback={<OrderListLoading />}>
      <OrderList />
    </Suspense>
  )
}
