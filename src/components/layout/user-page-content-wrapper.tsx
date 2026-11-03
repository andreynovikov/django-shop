import { ReactNode } from 'react'

import UserSidebar from '@/components/user/sidebar'

import { Breadcrumb } from './breadcrumbs'
import { pageContentWrapper } from './page-content-wrapper'

type UserPageContentProps = {
  title: ReactNode,
  breadcrumbs: Breadcrumb[],
  children: ReactNode
}

// Kept free of hooks so App Router server components can use it
export const userPageContentWrapper = ({ title, breadcrumbs, children }: UserPageContentProps) => {
  return pageContentWrapper({
    title,
    breadcrumbs,
    dark: true,
    overlapped: true,
    children: (
      <div className="container pb-5 mb-2 mb-md-4">
        <div className="row">
          <UserSidebar />
          <section className="col-lg-8">
            {children}
          </section>
        </div>
      </div>
    ),
  })
}
