import { Metadata } from 'next'

import { PageTitle } from '@/components/layout/page-content-wrapper'

const title = 'Профиль'

export const metadata: Metadata = {
  title,
}

export default function ProfileHeader() {
  return <PageTitle title={title} breadcrumbs={[{ label: 'Личный кабинет' }]} dark />
}
