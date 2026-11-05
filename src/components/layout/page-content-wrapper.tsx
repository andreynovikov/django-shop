import { ReactNode } from 'react'

export type Breadcrumb = {
  label: string,
  href?: string
}

// Singer's page title block with the props of cartzilla's page header, so pages copied from cartzilla work unchanged.
// Singer pages have no breadcrumbs, secondary title or dark header; overlapped headers are the ones without a border.

type PageHeaderProps = {
  secondaryTitle?: ReactNode,
  dark?: boolean,
  overlapped?: boolean,
  children?: ReactNode
}

// The frame of the page header, children are the title. A layout renders it around a title from a slot.
export function PageHeader({ overlapped, children }: PageHeaderProps) {
  return (
    <div className="mt-3 mb-2" style={overlapped ? {} : { borderBottom: "2px solid #D7D2CB" }}>
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
      <h1>{title}</h1>
      {titleAddon}
    </>
  )
}

type PageContentProps = Omit<PageHeaderProps, 'children'> & PageTitleProps & {
  children?: ReactNode
}

// Kept free of hooks so server components can use it
export const pageContentWrapper = ({ title, titleAddon, overlapped, children }: PageContentProps) => {
  return (
    <>
      <PageHeader overlapped={overlapped}>
        <PageTitle title={title} titleAddon={titleAddon} />
      </PageHeader>
      {children}
    </>
  )
}
