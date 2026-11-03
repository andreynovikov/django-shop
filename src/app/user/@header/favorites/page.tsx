import { Metadata } from 'next'

import { PageTitle } from '@/components/layout/page-content-wrapper'

const title = 'Избранное'

export const metadata: Metadata = {
  title,
}

export default function FavoritesHeader() {
  return <PageTitle title={title} breadcrumbs={[{ label: 'Личный кабинет', href: '/user/profile/' }]} dark />
}
