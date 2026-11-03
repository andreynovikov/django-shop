import { Metadata } from 'next'

import { userPageContentWrapper } from '@/components/layout/user-page-content-wrapper'
import UserProfile from '@/components/user/profile'

const title = 'Профиль'

export const metadata: Metadata = {
  title,
}

export default function ProfilePage() {
  return userPageContentWrapper({
    title,
    breadcrumbs: [{ label: 'Личный кабинет' }],
    children: <UserProfile />,
  })
}
