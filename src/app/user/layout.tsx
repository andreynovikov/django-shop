import { Metadata } from 'next'

import { PageHeader } from '@/components/layout/page-content-wrapper'
import UserSidebar from '@/components/user/sidebar'

// The account pages are static, the user's data is loaded in the browser
export const metadata: Metadata = {
  robots: { index: false },
}

// Each account page has its title, breadcrumbs and metadata in @header, beside the page with the same path.
// The frame and the menu stay mounted while the user moves between the pages.
export default function UserLayout({ header, children }: LayoutProps<'/user'>) {
  return (
    <>
      <PageHeader dark overlapped>
        {header}
      </PageHeader>
      <div className="container mb-2 grid pb-12 md:mb-6 lg:grid-cols-3 lg:gap-x-6">
        <UserSidebar />
        <section className="lg:col-span-2">
          {children}
        </section>
      </div>
    </>
  )
}
