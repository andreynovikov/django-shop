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
      <div className="container pb-5 mb-2 mb-md-4">
        <div className="row">
          <UserSidebar />
          <section className="col-lg-8">
            {children}
          </section>
        </div>
      </div>
    </>
  )
}
