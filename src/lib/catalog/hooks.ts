import { useEffect, useSyncExternalStore } from 'react'
import { usePathname, useSearchParams } from 'next/navigation'

// Remembers the catalog page with its filters for the cart. Reads search params, so callers need a Suspense boundary
export function useCatalog() {
  const pathname = usePathname()
  const searchParams = useSearchParams()

  useEffect(() => {
    const query = searchParams.toString()
    sessionStorage.setItem('lastCatalogPath', query ? `${pathname}?${query}` : pathname)
  }, [pathname, searchParams])
}

// sessionStorage has no change events within the same tab, so there is nothing to subscribe to
const subscribe = () => () => {}

export function useLastCatalog() {
  return useSyncExternalStore(
    subscribe,
    () => sessionStorage.getItem('lastCatalogPath') || '/',
    () => '/'
  )
}
