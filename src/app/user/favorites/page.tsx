import { Metadata } from 'next'

import { userPageContentWrapper } from '@/components/layout/user-page-content-wrapper'
import UserFavorites from '@/components/user/favorites'

const title = 'Избранное'

export const metadata: Metadata = {
  title,
}

export default function FavoritesPage() {
  return userPageContentWrapper({
    title,
    breadcrumbs: [{ label: 'Личный кабинет', href: '/user/profile/' }],
    children: <UserFavorites />,
  })
}
