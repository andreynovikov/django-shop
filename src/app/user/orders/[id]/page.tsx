import { notFound } from 'next/navigation'

import OrderDetails from '@/components/order/details'

// Rendered on request, the order is loaded in the browser
export default async function OrderPage({ params }: PageProps<'/user/orders/[id]'>) {
  const { id } = await params
  if (!/^\d+$/.test(id))
    notFound()

  return <OrderDetails id={Number(id)} />
}
