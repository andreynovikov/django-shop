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
      <div className="container mb-2 pb-12 md:mb-6">
        <div className="grid gap-x-7.5 lg:grid-cols-3">
          <UserSidebar />
          <section className="min-w-0 lg:col-span-2">
            {children}
          </section>
        </div>
      </div>
    </>
  )
}
