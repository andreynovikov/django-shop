import { notFound, redirect } from 'next/navigation'

// Current page from the optional [[...page]] segment of a paginated App Router route,
// the first page is served at {pathname} only
export function parsePageParam(page: string[] | undefined, pathname: string) {
  if (page === undefined)
    return 1

  if (page.length > 1 || !/^[1-9]\d*$/.test(page[0]))
    notFound()

  const currentPage = Number(page[0])
  if (currentPage === 1)
    redirect(pathname)

  return currentPage
}
