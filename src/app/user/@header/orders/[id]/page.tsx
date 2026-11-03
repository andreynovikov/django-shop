import { Metadata } from 'next'

import { PageTitle } from '@/components/layout/page-content-wrapper'

const orderTitle = (id: string) => `Заказ №${id}`

export async function generateMetadata({ params }: PageProps<'/user/orders/[id]'>): Promise<Metadata> {
  const { id } = await params
  return { title: orderTitle(id) }
}

// The page checks the id, its notFound() replaces the whole account layout including this header
export default async function OrderHeader({ params }: PageProps<'/user/orders/[id]'>) {
  const { id } = await params

  return (
    <PageTitle
      title={orderTitle(id)}
      breadcrumbs={[
        { label: 'Личный кабинет', href: '/user/profile/' },
        { label: 'Заказы', href: '/user/orders/' },
      ]}
      dark />
  )
}
