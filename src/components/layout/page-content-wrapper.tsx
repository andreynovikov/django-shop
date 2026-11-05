import { ReactNode } from 'react'

export type Breadcrumb = {
  label: string,
  href?: string
}

// familysew's hero title block with the props of cartzilla's page header, so pages copied from cartzilla work unchanged.
// familysew pages have no breadcrumbs, secondary title, dark or overlapped headers, those props are ignored.
// The description is HTML from the backend or the page.

type PageHeaderProps = {
  secondaryTitle?: ReactNode,
  dark?: boolean,
  overlapped?: boolean,
  children?: ReactNode
}

// The frame of the page header, children are the title
export function PageHeader({ children }: PageHeaderProps) {
  return (
    <section className="hero">
      <div className="container">
        <div className="hero-content mt-3 pb-5 text-center">
          {children}
        </div>
      </div>
    </section>
  )
}

type PageTitleProps = {
  title?: ReactNode,
  titleAddon?: ReactNode,
  description?: string,
  dark?: boolean,
  breadcrumbs?: Breadcrumb[]
}

export function PageTitle({ title, titleAddon, description }: PageTitleProps) {
  return (
    <>
      <h1 className="hero-heading">{title}</h1>
      {titleAddon}
      {description && (
        <div className="row">
          <div className="col-xl-8 offset-xl-2">
            <p className="lead text-muted" dangerouslySetInnerHTML={{ __html: description }}></p>
          </div>
        </div>
      )}
    </>
  )
}

type PageContentProps = Omit<PageHeaderProps, 'children'> & PageTitleProps & {
  children?: ReactNode
}

// Kept free of hooks so server components can use it
export const pageContentWrapper = ({ title, titleAddon, description, children }: PageContentProps) => {
  return (
    <>
      <PageHeader>
        <PageTitle title={title} titleAddon={titleAddon} description={description} />
      </PageHeader>
      {children}
    </>
  )
}
