import { ReactNode } from 'react'

export type Breadcrumb = {
  label: string,
  href?: string
}

// Dor Tak's page title block with the props of cartzilla's page header, so pages copied from cartzilla work unchanged.
// Dor Tak pages have no breadcrumbs, secondary title or dark header.

type PageHeaderProps = {
  secondaryTitle?: ReactNode,
  dark?: boolean,
  overlapped?: boolean,
  children?: ReactNode
}

// The frame of the page header, children are the title. A layout renders it around a title from a slot.
export function PageHeader({ children }: PageHeaderProps) {
  return (
    <div className="container mt-4 mb-2">
      {children}
    </div>
  )
}

type PageTitleProps = {
  title?: ReactNode,
  titleAddon?: ReactNode,
  dark?: boolean,
  breadcrumbs?: Breadcrumb[]
}

export function PageTitle({ title, titleAddon }: PageTitleProps) {
  return (
    <>
      <h1 className="mb-2 text-h1">{title}</h1>
      {titleAddon}
    </>
  )
}

type PageContentProps = Omit<PageHeaderProps, 'children'> & PageTitleProps & {
  children?: ReactNode
}

// Kept free of hooks so server components can use it
export const pageContentWrapper = ({ title, titleAddon, children }: PageContentProps) => {
  return (
    <>
      <PageHeader>
        <PageTitle title={title} titleAddon={titleAddon} />
      </PageHeader>
      {children}
    </>
  )
}
