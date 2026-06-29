import BaseLayout from './base'
import Breadcrumbs from './breadcrumbs'

export const pageContentWrapper = ({ title, titleAddon, secondaryTitle, dark, overlapped, breadcrumbs, children }) => {
  return (
    <>
      <div className={`bg-${dark ? 'dark' : 'secondary'} ${overlapped ? 'page-title-overlap pt-4' : 'py-4'}`}>
        <div className="container d-lg-flex justify-content-between py-2 py-lg-3">
          <div className="order-lg-2 flex-shrink-1 mb-3 mb-lg-0 pt-lg-2">
            {secondaryTitle}
          </div>
          <div className="order-lg-1 flex-shrink-0 mw-100 pe-lg-4 text-center text-lg-start">
            {breadcrumbs && <Breadcrumbs items={breadcrumbs} dark={dark} />}
            <h1 className={`h3 mb-0 text-${dark ? 'light' : 'dark'}`}>{title}</h1>
            {titleAddon}
          </div>
        </div>
      </div>
      {children}
    </>
  )
}

export default function PageLayout({
  titleAddon = null,
  dark = false,
  overlapped = false,
  contentWrapper = pageContentWrapper,
  ...props
}) {
  return (
    <BaseLayout
      titleAddon={titleAddon}
      dark={dark}
      overlapped={overlapped}
      contentWrapper={contentWrapper}
      {...props} />
  )
};
