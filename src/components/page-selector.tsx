import { Fragment } from 'react'
import Link from 'next/link'
import { ParsedUrlQuery } from 'querystring'

// Free of hooks so it renders both in App Router server components and in Pages Router pages
interface PageSelectorProps {
  pathname: string,                     /* path of the first page with trailing slash, e.g.:
                                           "/blog/tags/sewing/" */
  query?: ParsedUrlQuery,               /* current query string params, page number is
                                           put in query string, e.g. "/search/?q=pfaff&page=2" */
  pageInPath?: boolean,                 /* put page number in path instead, e.g.:
                                           "/blog/tags/sewing/2/", the first page is {pathname} */
  totalPages: number,
  currentPage: number,
}

const getHref = (page: number, pathname: string, query: ParsedUrlQuery | undefined, pageInPath: boolean | undefined) => {
  if (pageInPath)
    return page > 1 ? `${pathname}${page}/` : pathname

  const params = new URLSearchParams()
  for (const [key, value] of Object.entries(query ?? {}))
    if (key !== 'page')
      for (const item of Array.isArray(value) ? value : value === undefined ? [] : [value])
        params.append(key, item)
  params.set('page', String(page))
  return `${pathname}?${params}`
}

export function SmallPageSelector({ pathname, query, pageInPath, totalPages, currentPage }: PageSelectorProps) {
  return (
    <div className="d-flex pb-3">
      {currentPage > 1 && (
        <Link className="nav-link-style nav-link-light me-3" href={getHref(currentPage - 1, pathname, query, pageInPath)}>
          <i className="ci-arrow-left" />
        </Link>
      )}
      <span className="fs-md text-light">{currentPage} / {totalPages}</span>
      {currentPage < totalPages && (
        <Link className="nav-link-style nav-link-light ms-3" href={getHref(currentPage + 1, pathname, query, pageInPath)}>
          <i className="ci-arrow-right" />
        </Link>
      )}
    </div>
  )
}

export default function PageSelector({ pathname, query, pageInPath, totalPages, currentPage }: PageSelectorProps) {
  // количество переключателей страниц лимитировано дизайном
  const pageRange = currentPage > 1 && currentPage < totalPages ? 7 : 10
  let minPage = currentPage - pageRange + Math.min(4, totalPages - currentPage)
  if (minPage < 4)
    minPage = 1
  let maxPage = currentPage + pageRange - Math.min(4, currentPage - 1)
  if (maxPage > totalPages - 3)
    maxPage = totalPages

  return (
    <nav className="d-flex justify-content-between pt-2" aria-label="Переключение страниц">
      {currentPage > 1 && (
        <ul className="pagination">
          <li className="page-item">
            <Link className="page-link" href={getHref(currentPage - 1, pathname, query, pageInPath)}>
              <i className="ci-arrow-left me-2" />
              Пред<span className="d-none d-sm-inline d-md-none d-xl-inline">ыдущая</span>
            </Link>
          </li>
        </ul>
      )}
      <ul className="pagination">
        <li className="page-item d-sm-none">
          <span className="page-link page-link-static">{currentPage} / {totalPages}</span>
        </li>
        {Array(totalPages).fill(undefined).map((_, i) => i + 1).map((page) => (
          page === currentPage ? (
            <li className="page-item active d-none d-sm-block" aria-current="page" key={page}>
              <span className="page-link">{page}<span className="visually-hidden">(текущая)</span></span>
            </li>
          ) : (page >= minPage && page <= maxPage || page === 1 || page === totalPages) ? (
            <Fragment key={page}>
              {(maxPage < totalPages && page === totalPages) && (
                <li className="page-item d-none d-md-block">&hellip;</li>
              )}
              <li className="page-item d-none d-sm-block">
                <Link className="page-link" href={getHref(page, pathname, query, pageInPath)}>
                  {page}
                </Link>
              </li>
              {(minPage > 1 && page === 1) && (
                <li className="page-item d-none d-md-block">&hellip;</li>
              )}
            </Fragment>
          ) : (null)
        ))}
      </ul>
      {currentPage < totalPages && (
        <ul className="pagination">
          <li className="page-item">
            <Link className="page-link" href={getHref(currentPage + 1, pathname, query, pageInPath)}>
              След<span className="d-none d-sm-inline d-md-none d-xl-inline">ующая</span>
              <i className="ci-arrow-right ms-2" />
            </Link>
          </li>
        </ul>
      )}
    </nav>
  )
}
