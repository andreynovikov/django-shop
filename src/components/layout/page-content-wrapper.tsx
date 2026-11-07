import { ReactNode } from 'react'

import Breadcrumbs, { Breadcrumb } from './breadcrumbs'

type PageHeaderProps = {
  secondaryTitle?: ReactNode,
  dark?: boolean,
  overlapped?: boolean,
  children?: ReactNode
}

// The frame of the page header, children are the title. A layout renders it around a title from a slot.
// An overlapped header is taller and the block after it is pulled up over its bottom.
export function PageHeader({ secondaryTitle, dark = false, overlapped, children }: PageHeaderProps) {
  return (
    <div className={`${dark ? 'bg-dark' : 'bg-gray-100'} ${overlapped ? 'pt-6 pb-22 md:pb-[6.375rem] [&+*]:-mt-[4.875rem]' : 'py-6'}`}>
      <div className="container py-2 lg:flex lg:justify-between lg:py-4">
        <div className="mb-4 shrink lg:order-2 lg:mb-0 lg:pt-2">
          {secondaryTitle}
        </div>
        <div className="max-w-full shrink-0 text-center lg:order-1 lg:pe-6 lg:text-start">
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
      <h1 className={`mb-0 text-h3 ${dark ? 'text-white' : 'text-dark'}`}>{title}</h1>
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
