import { Fragment } from 'react'
import Link from 'next/link'
import { ParsedUrlQuery } from 'querystring'
import { IconChevronLeft, IconChevronRight } from '@tabler/icons-react'

import { navLinkClass } from '@/components/ui/nav'

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

// Cartzilla's pagination: plain links that get a light background on hover, the current page in primary
const pageItemClass = 'm-[.15rem]'
const pageLinkClass = 'flex items-center rounded-md border border-transparent px-3 py-[.3125rem] text-gray-700 transition-colors hover:border-gray-200 hover:bg-gray-200 hover:text-gray-700'
const arrowIcon = { size: 16, stroke: 1.5 }

export function SmallPageSelector({ pathname, query, pageInPath, totalPages, currentPage }: PageSelectorProps) {
  return (
    <div className="flex pb-4">
      {currentPage > 1 && (
        <Link className={`${navLinkClass({ light: true })} me-4`} href={getHref(currentPage - 1, pathname, query, pageInPath)} aria-label="Предыдущая страница">
          <IconChevronLeft {...arrowIcon} />
        </Link>
      )}
      <span className="text-md text-white">{currentPage} / {totalPages}</span>
      {currentPage < totalPages && (
        <Link className={`${navLinkClass({ light: true })} ms-4`} href={getHref(currentPage + 1, pathname, query, pageInPath)} aria-label="Следующая страница">
          <IconChevronRight {...arrowIcon} />
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
        <ul className="flex flex-wrap select-none">
          <li className={pageItemClass}>
            <Link className={pageLinkClass} href={getHref(currentPage - 1, pathname, query, pageInPath)}>
              <IconChevronLeft {...arrowIcon} className="me-2" />
              Пред<span className="hidden sm:inline md:hidden xl:inline">ыдущая</span>
            </Link>
          </li>
        </ul>
      )}
      <ul className="flex flex-wrap items-center select-none">
        <li className={`${pageItemClass} sm:hidden`}>
          <span className="block rounded-md border border-transparent px-3 py-[.3125rem] text-gray-700">{currentPage} / {totalPages}</span>
        </li>
        {Array(totalPages).fill(undefined).map((_, i) => i + 1).map((page) => (
          page === currentPage ? (
            <li className={`${pageItemClass} relative z-5 hidden cursor-default sm:block`} aria-current="page" key={page}>
              <span className="block rounded-md border border-transparent bg-primary px-3 py-[.3125rem] text-white shadow-[0_.5rem_1.125rem_-.425rem_rgb(239_127_26/.9)]">{page}<span className="sr-only">(текущая)</span></span>
            </li>
          ) : (page >= minPage && page <= maxPage || page === 1 || page === totalPages) ? (
            <Fragment key={page}>
              {(maxPage < totalPages && page === totalPages) && (
                <li className={`${pageItemClass} hidden md:block`}>&hellip;</li>
              )}
              <li className={`${pageItemClass} hidden sm:block`}>
                <Link className={pageLinkClass} href={getHref(page, pathname, query, pageInPath)}>
                  {page}
                </Link>
              </li>
              {(minPage > 1 && page === 1) && (
                <li className={`${pageItemClass} hidden md:block`}>&hellip;</li>
              )}
            </Fragment>
          ) : (null)
        ))}
      </ul>
      {currentPage < totalPages && (
        <ul className="flex flex-wrap select-none">
          <li className={pageItemClass}>
            <Link className={pageLinkClass} href={getHref(currentPage + 1, pathname, query, pageInPath)}>
              След<span className="hidden sm:inline md:hidden xl:inline">ующая</span>
              <IconChevronRight {...arrowIcon} className="ms-2" />
            </Link>
          </li>
        </ul>
      )}
    </nav>
  )
}
