import { useEffect, useSyncExternalStore } from 'react'
import { useNavigation } from '@/lib/navigation'

export function useCatalog() {
  const { path } = useNavigation()

  useEffect(() => {
    if (path)
      sessionStorage.setItem('lastCatalogPath', path)
  }, [path])
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
