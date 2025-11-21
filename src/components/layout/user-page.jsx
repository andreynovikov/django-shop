import PageLayout, { pageContentWrapper } from './page'
import UserSidebar from '@/components/user/sidebar'

const userPageContentWrapper = ({ children, ...props }) => {
  return pageContentWrapper({
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
    ...props
  })
}

export default function UserPageLayout({
  dark = true,
  overlapped = true,
  contentWrapper = userPageContentWrapper,
  ...props
}) {
  return (
    <PageLayout
      dark={dark}
      overlapped={overlapped}
      contentWrapper={contentWrapper}
      {...props} />
  )
};
