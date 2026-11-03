import { Metadata } from 'next'
import { notFound } from 'next/navigation'

import { userPageContentWrapper } from '@/components/layout/user-page-content-wrapper'
import OrderDetails from '@/components/order/details'

const orderTitle = (id: string) => `Заказ №${id}`

export async function generateMetadata({ params }: PageProps<'/user/orders/[id]'>): Promise<Metadata> {
  const { id } = await params
  return { title: orderTitle(id) }
}

// Rendered on request, the order is loaded in the browser
export default async function OrderPage({ params }: PageProps<'/user/orders/[id]'>) {
  const { id } = await params
  if (!/^\d+$/.test(id))
    notFound()

  return userPageContentWrapper({
    title: orderTitle(id),
    breadcrumbs: [
      { label: 'Личный кабинет', href: '/user/profile/' },
      { label: 'Заказы', href: '/user/orders/' },
    ],
    children: <OrderDetails id={Number(id)} />,
  })
}
