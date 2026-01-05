import { createContext, useContext, useMemo } from 'react'
import { useQuery } from '@tanstack/react-query'

import { siteKeys, loadCurrentSite } from '@/lib/queries'

export const SiteContext = createContext({ status: 'loading', site: {} })

export function useSite() {
  return useContext(SiteContext)
}

export function SiteProvider({ children }) {
  const { data: site, isSuccess, isLoading } = useQuery({
    queryKey: siteKeys.current(),
    queryFn: () => loadCurrentSite(),
    staleTime: Infinity,
    refetchOnWindowFocus: false,
  })

  const value = useMemo(() => ({
    site: site ?? {},
    status: isLoading ? 'loading' : isSuccess ? 'success' : 'error'
  }), [site, isLoading, isSuccess])

  return (
    <SiteContext.Provider value={value}>{children}</SiteContext.Provider>
  )
}
