import { Fragment } from 'react'
import Link from 'next/link'
import { ParsedUrlQuery } from 'querystring'

import { IconChevronCompactLeft, IconChevronCompactRight } from '@tabler/icons-react'

// Free of hooks so server components can render it
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

// A page link or the current page number
const pageClass = 'block rounded-md border px-3 py-1.5'
const pageLinkClass = `${pageClass} bg-white text-primary no-underline hover:bg-light`

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
    <div className="flex items-center pb-4">
      {currentPage > 1 && (
        <Link className="me-4" href={getHref(currentPage - 1, pathname, query, pageInPath)}>
          <IconChevronCompactLeft size={20} stroke={1.5} />
        </Link>
      )}
      <span className="text-md">{currentPage} / {totalPages}</span>
      {currentPage < totalPages && (
        <Link className="ms-4" href={getHref(currentPage + 1, pathname, query, pageInPath)}>
          <IconChevronCompactRight size={20} stroke={1.5} />
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
    <nav className="flex justify-between pt-2" aria-label="Переключение страниц">
      {currentPage > 1 && (
        <ul className="flex">
          <li>
            <Link className={pageLinkClass} href={getHref(currentPage - 1, pathname, query, pageInPath)}>
              <IconChevronCompactLeft size={20} stroke={1.5} className="me-2 inline align-text-bottom" />
              Пред<span className="hidden sm:inline md:hidden xl:inline">ыдущая</span>
            </Link>
          </li>
        </ul>
      )}
      <ul className="flex items-center gap-1">
        <li className="sm:hidden">
          <span className={`${pageClass} bg-white`}>{currentPage} / {totalPages}</span>
        </li>
        {Array(totalPages).fill(undefined).map((_, i) => i + 1).map((page) => (
          page === currentPage ? (
            <li className="hidden sm:block" aria-current="page" key={page}>
              <span className={`${pageClass} border-primary bg-primary text-white`}>{page}<span className="sr-only">(текущая)</span></span>
            </li>
          ) : (page >= minPage && page <= maxPage || page === 1 || page === totalPages) ? (
            <Fragment key={page}>
              {(maxPage < totalPages && page === totalPages) && (
                <li className="hidden px-1 md:block">&hellip;</li>
              )}
              <li className="hidden sm:block">
                <Link className={pageLinkClass} href={getHref(page, pathname, query, pageInPath)}>
                  {page}
                </Link>
              </li>
              {(minPage > 1 && page === 1) && (
                <li className="hidden px-1 md:block">&hellip;</li>
              )}
            </Fragment>
          ) : (null)
        ))}
      </ul>
      {currentPage < totalPages && (
        <ul className="flex">
          <li>
            <Link className={pageLinkClass} href={getHref(currentPage + 1, pathname, query, pageInPath)}>
              След<span className="hidden sm:inline md:hidden xl:inline">ующая</span>
              <IconChevronCompactRight size={20} stroke={1.5} className="ms-2 inline align-text-bottom" />
            </Link>
          </li>
        </ul>
      )}
    </nav>
  )
}
