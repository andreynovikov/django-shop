import { Metadata } from 'next'

import { PageTitle } from '@/components/layout/page-content-wrapper'

const title = 'Список заказов'

export const metadata: Metadata = {
  title,
}

export default function OrdersHeader() {
  return <PageTitle title={title} breadcrumbs={[{ label: 'Личный кабинет', href: '/user/profile/' }]} dark />
}
