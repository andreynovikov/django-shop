import { ReactNode } from 'react'

import Breadcrumbs, { Breadcrumb } from './breadcrumbs'

type PageHeaderProps = {
  secondaryTitle?: ReactNode,
  dark?: boolean,
  overlapped?: boolean,
  children?: ReactNode
}

// The frame of the page header, children are the title. A layout renders it around a title from a slot.
export function PageHeader({ secondaryTitle, dark = false, overlapped, children }: PageHeaderProps) {
  return (
    <div className={`bg-${dark ? 'dark' : 'secondary'} ${overlapped ? 'page-title-overlap pt-4' : 'py-4'}`}>
      <div className="container d-lg-flex justify-content-between py-2 py-lg-3">
        <div className="order-lg-2 flex-shrink-1 mb-3 mb-lg-0 pt-lg-2">
          {secondaryTitle}
        </div>
        <div className="order-lg-1 flex-shrink-0 mw-100 pe-lg-4 text-center text-lg-start">
          {children}
        </div>
      </div>
    </div>
  )
}

type PageTitleProps = {
  title?: ReactNode,
  titleAddon?: ReactNode,
  dark?: boolean,
  breadcrumbs?: Breadcrumb[]
}

export function PageTitle({ title, titleAddon, dark = false, breadcrumbs }: PageTitleProps) {
  return (
    <>
      {breadcrumbs && <Breadcrumbs items={breadcrumbs} dark={dark} />}
      <h1 className={`h3 mb-0 text-${dark ? 'light' : 'dark'}`}>{title}</h1>
      {titleAddon}
    </>
  )
}

type PageContentProps = Omit<PageHeaderProps, 'children'> & PageTitleProps & {
  children?: ReactNode
}

// Kept free of hooks so server components can use it
export const pageContentWrapper = ({ title, titleAddon, secondaryTitle, dark = false, overlapped, breadcrumbs, children }: PageContentProps) => {
  return (
    <>
      <PageHeader secondaryTitle={secondaryTitle} dark={dark} overlapped={overlapped}>
        <PageTitle title={title} titleAddon={titleAddon} dark={dark} breadcrumbs={breadcrumbs} />
      </PageHeader>
      {children}
    </>
  )
}
